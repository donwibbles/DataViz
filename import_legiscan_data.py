"""
Import California legislative data from LegiScan datasets to Supabase.

LegiScan provides weekly dataset snapshots in CSV format:
https://legiscan.com/CA/datasets

Usage examples:
    python import_legiscan_data.py \\
        --dataset-dir legiscan_ca_data/CA/2025-2026_Regular_Session/csv

    # Dry run limited to first 200 rows for smoke tests
    python import_legiscan_data.py --dataset-dir ./legiscan_ca_data/CA/2025-2026_Regular_Session/csv \\
        --max-records 200 --dry-run
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Optional

from supabase import Client, create_client

from import_utils import chunked, derive_session_name_from_path, log_header, log_step

# Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    print("❌ Missing environment variables:")
    print("  - SUPABASE_URL")
    print("  - SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a single LegiScan session (CSV directory) into Supabase"
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default="./legiscan_ca_data/CA/2025-2026_Regular_Session/csv",
        help="Path to the LegiScan CSV directory for a single session",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Optional cap on rows processed per file (for dev/testing)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse files and log counts without writing to Supabase",
    )
    return parser.parse_args()


def import_legiscan_legislators(
    csv_path: str,
    record_limit: Optional[int] = None,
    dry_run: bool = False,
) -> int:
    """Import legislators from LegiScan people CSV."""
    log_step(f"📥 Importing legislators from {csv_path}...")

    path = Path(csv_path)
    if not path.exists():
        log_step(f"❌ File not found: {csv_path}")
        return 0

    legislators = []

    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            legislator = {
                'id': row.get('people_id') or row.get('person_id') or row.get('id'),
                'name': row.get('name') or f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
                'party': row.get('party') or row.get('party_id'),
                'chamber': 'Senate' if row.get('role_name') == 'Senator' else 'Assembly',
                'district': row.get('district'),
                'email': row.get('email'),
                'phone': row.get('phone'),
                'website': row.get('url') or row.get('website')
            }

            if legislator['id'] and legislator['name']:
                legislators.append(legislator)

            if record_limit and len(legislators) >= record_limit:
                break

    if not legislators:
        return 0

    if dry_run:
        log_step(f"[DRY-RUN] Would import {len(legislators)} legislators")
        return len(legislators)

    try:
        supabase.table('legislators').upsert(legislators).execute()
        log_step(f"✅ Imported {len(legislators)} legislators")
        return len(legislators)
    except Exception as e:
        log_step(f"❌ Error importing legislators: {e}")
        return 0


def import_legiscan_bills(
    csv_path: str,
    session_name: Optional[str] = None,
    record_limit: Optional[int] = None,
    dry_run: bool = False,
) -> int:
    """Import bills from LegiScan bills CSV."""
    log_step(f"📥 Importing bills from {csv_path}...")

    path = Path(csv_path)
    if not path.exists():
        log_step(f"❌ File not found: {csv_path}")
        return 0

    bills = []

    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bill = {
                'id': row.get('bill_id') or row.get('id'),
                'bill_number': row.get('bill_number') or row.get('bill_no'),
                'title': row.get('title') or row.get('description'),
                'session': row.get('session_id') or row.get('session'),
                'session_name': row.get('session_name') or session_name,
                'status': row.get('status') or row.get('status_desc'),
                'last_action': row.get('last_action') or row.get('last_action_desc'),
                'last_action_date': row.get('last_action_date'),
                'subjects': row.get('subjects', '').split(',') if row.get('subjects') else []
            }

            if bill['id'] and bill['bill_number']:
                bills.append(bill)

            if record_limit and len(bills) >= record_limit:
                break

    if not bills:
        return 0

    if dry_run:
        log_step(f"[DRY-RUN] Would import {len(bills)} bills")
        return len(bills)

    total_imported = 0
    for chunk in chunked(bills, 100):
        try:
            supabase.table('bills').upsert(chunk).execute()
            total_imported += len(chunk)
            log_step(f"  Imported {total_imported}/{len(bills)} bills")
        except Exception as e:
            log_step(f"❌ Error importing bills chunk: {e}")

    log_step(f"✅ Imported {total_imported} bills total")
    return total_imported


def import_legiscan_votes(
    csv_path: str,
    record_limit: Optional[int] = None,
    dry_run: bool = False,
) -> int:
    """Import votes from LegiScan roll call/votes CSV."""
    log_step(f"📥 Importing votes from {csv_path}...")

    path = Path(csv_path)
    if not path.exists():
        log_step(f"❌ File not found: {csv_path}")
        return 0

    votes = []

    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vote = {
                'bill_id': row.get('bill_id'),
                'legislator_id': row.get('people_id') or row.get('person_id'),
                'vote_type': row.get('vote_text', '').lower(),
                'vote_date': row.get('date') or row.get('roll_call_date'),
                'session': row.get('session') or row.get('session_id'),
                'chamber': row.get('chamber'),
                'motion': row.get('desc') or row.get('motion'),
                'passed': row.get('passed') in {'1', 'true', 'True'}
            }

            vote_text = vote['vote_type']
            if vote_text in ['yea', 'aye', 'yes', '1']:
                vote['vote_type'] = 'yes'
            elif vote_text in ['nay', 'no', '2']:
                vote['vote_type'] = 'no'
            elif vote_text in ['nv', 'not voting', '3']:
                vote['vote_type'] = 'not voting'
            elif vote_text in ['absent', 'excused', '4']:
                vote['vote_type'] = 'absent'
            else:
                vote['vote_type'] = 'abstain'

            if vote['bill_id'] and vote['legislator_id']:
                votes.append(vote)

            if record_limit and len(votes) >= record_limit:
                break

    if not votes:
        return 0

    if dry_run:
        log_step(f"[DRY-RUN] Would import {len(votes)} votes")
        return len(votes)

    total_imported = 0
    for chunk in chunked(votes, 500):
        try:
            supabase.table('votes').upsert(
                chunk,
                on_conflict='bill_id,legislator_id,vote_date,motion'
            ).execute()
            total_imported += len(chunk)
            log_step(f"  Imported {total_imported}/{len(votes)} votes")
        except Exception as e:
            log_step(f"❌ Error importing votes chunk: {e}")

    log_step(f"✅ Imported {total_imported} votes total")
    return total_imported


def main():
    args = parse_args()
    dataset_dir = Path(args.dataset_dir).expanduser()

    if not dataset_dir.exists():
        log_step(f"❌ Dataset directory not found: {dataset_dir}")
        exit(1)

    session_root = dataset_dir.parent
    session_name = derive_session_name_from_path(session_root)

    log_header("🚀 LegiScan Dataset Import to Supabase")
    log_step(f"Session: {session_name}")
    log_step(f"CSV directory: {dataset_dir}")
    if args.max_records:
        log_step(f"Record limit: {args.max_records}")
    if args.dry_run:
        log_step("Running in DRY-RUN mode (no writes)")

    alt_files = {
        'legislators': ['people.csv', 'legislators.csv', 'members.csv'],
        'bills': ['bills.csv', 'legislation.csv'],
        'votes': ['roll_calls.csv', 'votes.csv', 'roll_call.csv']
    }

    legislators_path = next((dataset_dir / name for name in alt_files['legislators'] if (dataset_dir / name).exists()), None)
    bills_path = next((dataset_dir / name for name in alt_files['bills'] if (dataset_dir / name).exists()), None)
    votes_path = next((dataset_dir / name for name in alt_files['votes'] if (dataset_dir / name).exists()), None)

    if legislators_path:
        import_legiscan_legislators(str(legislators_path), record_limit=args.max_records, dry_run=args.dry_run)
    else:
        log_step(f"⚠️  Legislators file not found. Tried: {alt_files['legislators']}")

    if bills_path:
        import_legiscan_bills(
            str(bills_path),
            session_name=session_name,
            record_limit=args.max_records,
            dry_run=args.dry_run,
        )
    else:
        log_step(f"⚠️  Bills file not found. Tried: {alt_files['bills']}")

    if votes_path:
        import_legiscan_votes(str(votes_path), record_limit=args.max_records, dry_run=args.dry_run)
    else:
        log_step(f"⚠️  Votes file not found. Tried: {alt_files['votes']}")

    log_header("✅ Session import complete")


if __name__ == "__main__":
    main()
