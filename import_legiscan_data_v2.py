"""
Import California legislative data from LegiScan datasets to Supabase.

LegiScan provides weekly dataset snapshots in CSV format.
Download from: https://legiscan.com/CA/datasets

This script properly handles the LegiScan data structure:
- bills.csv → rollcalls.csv → votes.csv
- bills.csv + people.csv → sponsors.csv (bill authors)
"""

from __future__ import annotations
import argparse
import csv
import os
from pathlib import Path
from typing import Dict, List, Optional

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
        description="Import California LegiScan dataset sessions into Supabase"
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default="./legiscan_ca_data/CA",
        help="Directory containing session folders (each with a csv/ subdir)",
    )
    parser.add_argument(
        "--session",
        dest="sessions",
        action="append",
        help="Limit import to specific session name(s) (e.g., 2025-2026). "
             "Can be provided multiple times or as a comma-separated list.",
    )
    parser.add_argument(
        "--max-sessions",
        type=int,
        default=None,
        help="Optional cap on the number of sessions processed (after filtering)",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Optional cap on rows processed per CSV (dev/testing)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse files and log progress without writing to Supabase",
    )
    return parser.parse_args()


def import_legislators(
    csv_path: str,
    dry_run: bool = False,
    record_limit: Optional[int] = None,
) -> int:
    """Import legislators from people.csv"""
    log_step(f"📥 Importing legislators from {csv_path}...")

    if not Path(csv_path).exists():
        log_step(f"❌ File not found: {csv_path}")
        return 0

    legislators: List[Dict] = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Check if this is a committee (committee_id != 0)
            is_committee = row.get('committee_id') and row.get('committee_id') != '0'

            # Map chamber: role can be "Sen" or "Rep" (Representative) for CA
            role = row.get('role', '')
            if role == 'Sen':
                chamber = 'Senate'
            elif role == 'Rep':
                chamber = 'Assembly'
            else:
                chamber = 'Unknown'

            legislator = {
                'id': row['people_id'],
                'name': row['name'],
                'party': row.get('party', 'Unknown'),
                'chamber': chamber,
                'district': row.get('district', 'Unknown'),
                'email': None,  # Not in LegiScan data
                'phone': None,  # Not in LegiScan data
                'website': None,  # Not in LegiScan data
                'is_committee': is_committee
            }

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


def import_bills(
    csv_path: str,
    session_name: Optional[str] = None,
    dry_run: bool = False,
    record_limit: Optional[int] = None,
) -> int:
    """Import bills from bills.csv"""
    log_step(f"📥 Importing bills from {csv_path}...")

    if not Path(csv_path).exists():
        log_step(f"❌ File not found: {csv_path}")
        return 0

    bills: List[Dict] = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            bill = {
                'id': row['bill_id'],
                'bill_number': row['bill_number'],
                'title': row.get('title') or row.get('description', ''),
                'session': row['session_id'],  # Always from CSV
                'session_name': row.get('session_name') or session_name,
                'status': row.get('status_desc', 'Unknown'),
                'last_action': row.get('last_action', ''),
                'last_action_date': row.get('last_action_date'),
                'subjects': []  # LegiScan doesn't have subjects in CSV
            }

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


def import_sponsors(
    csv_path: str,
    dry_run: bool = False,
    record_limit: Optional[int] = None,
) -> int:
    """Import bill authors from sponsors.csv"""
    log_step(f"📥 Importing bill sponsors from {csv_path}...")

    if not Path(csv_path).exists():
        log_step(f"❌ File not found: {csv_path}")
        return 0

    sponsors: List[Dict] = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            sponsor = {
                'bill_id': row['bill_id'],
                'legislator_id': row['people_id']
            }
            sponsors.append(sponsor)

            if record_limit and len(sponsors) >= record_limit:
                break

    if not sponsors:
        return 0

    sponsors_dict = {(s['bill_id'], s['legislator_id']): s for s in sponsors}
    unique_sponsors = list(sponsors_dict.values())
    duplicates_removed = len(sponsors) - len(unique_sponsors)

    if duplicates_removed > 0:
        log_step(f"  Removed {duplicates_removed} duplicate sponsors")

    if dry_run:
        log_step(f"[DRY-RUN] Would import {len(unique_sponsors)} bill authors")
        return len(unique_sponsors)

    log_step(f"  Importing {len(unique_sponsors)} unique bill authors...")
    total_imported = 0
    for chunk in chunked(unique_sponsors, 500):
        try:
            supabase.table('bill_authors').upsert(
                chunk,
                on_conflict='bill_id,legislator_id'
            ).execute()
            total_imported += len(chunk)
            log_step(f"  Imported {total_imported}/{len(unique_sponsors)} bill authors")
        except Exception as e:
            log_step(f"❌ Error importing sponsors chunk: {e}")
            log_step("   Continuing with next chunk...")

    log_step(f"✅ Imported {total_imported} bill authors total")
    return total_imported


def import_rollcalls(
    csv_path: str,
    dry_run: bool = False,
    record_limit: Optional[int] = None,
) -> int:
    """Import roll call summaries from rollcalls.csv"""
    log_step(f"📥 Importing roll calls from {csv_path}...")

    if not Path(csv_path).exists():
        log_step(f"❌ File not found: {csv_path}")
        return 0

    rollcalls: List[Dict] = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            rollcall = {
                'id': row['roll_call_id'],
                'bill_id': row['bill_id'],
                'vote_date': row['date'],
                'chamber': row.get('chamber', 'Unknown'),
                'description': row.get('description', ''),
                'yea': int(row.get('yea', 0)),
                'nay': int(row.get('nay', 0)),
                'nv': int(row.get('nv', 0)),
                'absent': int(row.get('absent', 0)),
                'total': int(row.get('total', 0))
            }
            rollcalls.append(rollcall)

            if record_limit and len(rollcalls) >= record_limit:
                break

    if not rollcalls:
        return 0

    if dry_run:
        log_step(f"[DRY-RUN] Would import {len(rollcalls)} roll calls")
        return len(rollcalls)

    total_imported = 0
    for chunk in chunked(rollcalls, 500):
        try:
            supabase.table('rollcalls').upsert(chunk).execute()
            total_imported += len(chunk)
            log_step(f"  Imported {total_imported}/{len(rollcalls)} roll calls")
        except Exception as e:
            log_step(f"❌ Error importing rollcalls chunk: {e}")

    log_step(f"✅ Imported {total_imported} roll calls total")
    return total_imported


def import_bill_history(
    csv_path: str,
    dry_run: bool = False,
    record_limit: Optional[int] = None,
) -> int:
    """Import bill action history from history.csv"""
    log_step(f"📥 Importing bill history from {csv_path}...")

    if not Path(csv_path).exists():
        log_step(f"❌ File not found: {csv_path}")
        return 0

    history: List[Dict] = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            action = {
                'bill_id': row['bill_id'],
                'action_date': row['date'],
                'chamber': row.get('chamber', ''),
                'sequence': int(row.get('sequence', 0)),
                'action': row['action']
            }
            history.append(action)

            if record_limit and len(history) >= record_limit:
                break

    if not history:
        return 0

    if dry_run:
        log_step(f"[DRY-RUN] Would import {len(history)} history actions")
        return len(history)

    total_imported = 0
    for chunk in chunked(history, 500):
        try:
            supabase.table('bill_history').upsert(
                chunk,
                on_conflict='bill_id,action_date,sequence'
            ).execute()
            total_imported += len(chunk)
            if total_imported % 5000 == 0 or total_imported == len(history):
                log_step(f"  Imported {total_imported}/{len(history)} history actions")
        except Exception as e:
            log_step(f"❌ Error importing history chunk: {e}")
            log_step("   Continuing with next chunk...")

    log_step(f"✅ Imported {total_imported} history actions total")
    return total_imported


def import_bill_documents(
    csv_path: str,
    dry_run: bool = False,
    record_limit: Optional[int] = None,
) -> int:
    """Import bill documents from documents.csv"""
    log_step(f"📥 Importing bill documents from {csv_path}...")

    if not Path(csv_path).exists():
        log_step(f"❌ File not found: {csv_path}")
        return 0

    documents: List[Dict] = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            document = {
                'id': row['document_id'],
                'bill_id': row['bill_id'],
                'document_type': row.get('document_type', ''),
                'document_size': int(row.get('document_size', 0)) if row.get('document_size') else None,
                'document_mime': row.get('document_mime', ''),
                'document_desc': row.get('document_desc', ''),
                'url': row.get('url', ''),
                'state_link': row.get('state_link', '')
            }
            documents.append(document)

            if record_limit and len(documents) >= record_limit:
                break

    if not documents:
        return 0

    if dry_run:
        log_step(f"[DRY-RUN] Would import {len(documents)} documents")
        return len(documents)

    total_imported = 0
    for chunk in chunked(documents, 250):
        try:
            supabase.table('bill_documents').upsert(chunk).execute()
            total_imported += len(chunk)
            if total_imported % 2500 == 0 or total_imported == len(documents):
                log_step(f"  Imported {total_imported}/{len(documents)} documents")
        except Exception as e:
            log_step(f"❌ Error importing documents chunk: {e}")
            log_step("   Continuing with next chunk...")

    log_step(f"✅ Imported {total_imported} documents total")
    return total_imported


def import_votes(
    votes_csv: str,
    rollcalls_csv: str,
    bills_csv: str,
    dry_run: bool = False,
    record_limit: Optional[int] = None,
) -> int:
    """
    Import votes by joining votes.csv with rollcalls.csv

    votes.csv has: roll_call_id, people_id, vote, vote_desc
    rollcalls.csv has: bill_id, roll_call_id, date, chamber, description, yea, nay, nv, absent

    We need to join them to get bill_id for each vote.
    """
    log_step(f"📥 Importing votes from {votes_csv} and {rollcalls_csv}...")

    if not Path(votes_csv).exists():
        log_step(f"❌ File not found: {votes_csv}")
        return 0

    if not Path(rollcalls_csv).exists():
        log_step(f"❌ File not found: {rollcalls_csv}")
        return 0

    if not Path(bills_csv).exists():
        log_step(f"❌ File not found: {bills_csv}")
        return 0

    # Get session_id from bills.csv
    log_step("  Getting session info from bills.csv...")
    with open(bills_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        first_bill = next(reader)
        session_id = first_bill['session_id']
    log_step(f"  Session ID: {session_id}")

    # First, load rollcalls into memory to create a lookup
    log_step("  Loading rollcalls data...")
    rollcalls = {}
    with open(rollcalls_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rollcalls[row['roll_call_id']] = {
                'bill_id': row['bill_id'],
                'date': row['date'],
                'chamber': row['chamber'],
                'motion': row['description'],
                'passed': int(row.get('yea', 0)) > int(row.get('nay', 0))  # Simple majority check
            }

    log_step(f"  Loaded {len(rollcalls)} roll calls")

    # Now process votes and join with rollcalls
    log_step("  Processing individual votes...")
    votes = []
    skipped = 0

    with open(votes_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            roll_call_id = row['roll_call_id']

            # Look up the roll call info
            if roll_call_id not in rollcalls:
                skipped += 1
                continue

            rollcall = rollcalls[roll_call_id]

            # Normalize vote type from vote_desc
            vote_desc = row.get('vote_desc', '').lower()
            if vote_desc in ['yea', 'aye', 'yes']:
                vote_type = 'yes'
            elif vote_desc in ['nay', 'no']:
                vote_type = 'no'
            elif vote_desc in ['nv', 'not voting']:
                vote_type = 'not voting'
            elif vote_desc in ['absent', 'excused']:
                vote_type = 'absent'
            else:
                vote_type = 'abstain'

            vote = {
                'bill_id': rollcall['bill_id'],
                'legislator_id': row['people_id'],
                'vote_type': vote_type,
                'vote_date': rollcall['date'],
                'session': session_id,
                'chamber': rollcall['chamber'],
                'motion': rollcall['motion'],
                'passed': rollcall['passed']
            }

            votes.append(vote)

            if record_limit and len(votes) >= record_limit:
                break

    log_step(f"  Processed {len(votes)} votes ({skipped} skipped due to missing rollcall)")

    # Deduplicate votes based on UNIQUE constraint (bill_id, legislator_id, vote_date, motion)
    # LegiScan data can have duplicates within the same CSV
    votes_dict = {}
    for vote in votes:
        key = (vote['bill_id'], vote['legislator_id'], vote['vote_date'], vote['motion'])
        votes_dict[key] = vote  # Last occurrence wins

    unique_votes = list(votes_dict.values())
    duplicates_removed = len(votes) - len(unique_votes)

    if duplicates_removed > 0:
        log_step(f"  Removed {duplicates_removed} duplicate votes")

    log_step(f"  Importing {len(unique_votes)} unique votes...")

    if not unique_votes:
        return 0

    if dry_run:
        log_step(f"[DRY-RUN] Would import {len(unique_votes)} votes")
        return len(unique_votes)

    total_imported = 0
    for chunk in chunked(unique_votes, 500):
        try:
            supabase.table('votes').upsert(
                chunk,
                on_conflict='bill_id,legislator_id,vote_date,motion'
            ).execute()
            total_imported += len(chunk)
            if total_imported % 5000 == 0 or total_imported == len(unique_votes):
                log_step(f"  Imported {total_imported}/{len(unique_votes)} votes")
        except Exception as e:
            log_step(f"❌ Error importing votes chunk: {e}")
            log_step(f"   First vote in chunk: {chunk[0] if chunk else 'empty'}")

    log_step(f"✅ Imported {total_imported} votes total")
    return total_imported


def import_session(
    session_dir: Path,
    dry_run: bool = False,
    record_limit: Optional[int] = None,
):
    """Import data for a single legislative session."""
    csv_dir = session_dir / "csv"

    if not csv_dir.exists():
        log_step(f"⚠️  CSV directory not found: {csv_dir}")
        return

    session_name = derive_session_name_from_path(session_dir)

    log_header(f"📅 IMPORTING SESSION: {session_name}")
    log_step(f"📁 From: {csv_dir}")

    # Import in correct order
    people_file = csv_dir / "people.csv"
    bills_file = csv_dir / "bills.csv"
    sponsors_file = csv_dir / "sponsors.csv"
    rollcalls_file = csv_dir / "rollcalls.csv"
    votes_file = csv_dir / "votes.csv"
    history_file = csv_dir / "history.csv"
    documents_file = csv_dir / "documents.csv"

    # 1. Import legislators
    if people_file.exists():
        import_legislators(str(people_file), dry_run=dry_run, record_limit=record_limit)
    else:
        log_step("⚠️  people.csv not found")

    # 2. Import bills
    if bills_file.exists():
        import_bills(
            str(bills_file),
            session_name,
            dry_run=dry_run,
            record_limit=record_limit,
        )
    else:
        log_step("⚠️  bills.csv not found")

    # 3. Import sponsors (bill authors)
    if sponsors_file.exists():
        import_sponsors(str(sponsors_file), dry_run=dry_run, record_limit=record_limit)
    else:
        log_step("⚠️  sponsors.csv not found")

    # 4. Import roll calls (vote summaries)
    if rollcalls_file.exists():
        import_rollcalls(str(rollcalls_file), dry_run=dry_run, record_limit=record_limit)
    else:
        log_step("⚠️  rollcalls.csv not found")

    # 5. Import votes (requires votes.csv, rollcalls.csv, and bills.csv)
    if votes_file.exists() and rollcalls_file.exists() and bills_file.exists():
        import_votes(
            str(votes_file),
            str(rollcalls_file),
            str(bills_file),
            dry_run=dry_run,
            record_limit=record_limit,
        )
    else:
        if not votes_file.exists():
            log_step("⚠️  votes.csv not found")
        if not rollcalls_file.exists():
            log_step("⚠️  rollcalls.csv not found")
        if not bills_file.exists():
            log_step("⚠️  bills.csv not found (needed for session info)")

    # 6. Import bill history (action timeline)
    if history_file.exists():
        import_bill_history(str(history_file), dry_run=dry_run, record_limit=record_limit)
    else:
        log_step("⚠️  history.csv not found")

    # 7. Import bill documents
    if documents_file.exists():
        import_bill_documents(str(documents_file), dry_run=dry_run, record_limit=record_limit)
    else:
        log_step("⚠️  documents.csv not found")

    log_step(f"✅ Session {session_name} import complete!")


def main():
    """Main import process - imports all sessions."""
    args = parse_args()
    base_dir = Path(args.base_dir).expanduser()

    log_header("🚀 LegiScan Dataset Import to Supabase (v2)")
    log_step(f"Base directory: {base_dir}")
    if args.sessions:
        session_filters = []
        for value in args.sessions:
            session_filters.extend([v.strip() for v in value.split(',') if v.strip()])
        log_step(f"Session filter: {', '.join(session_filters)}")
    else:
        session_filters = []
    if args.max_sessions:
        log_step(f"Max sessions: {args.max_sessions}")
    if args.max_records:
        log_step(f"Record limit per CSV: {args.max_records}")
    if args.dry_run:
        log_step("Running in DRY-RUN mode (no writes)")

    if not base_dir.exists():
        log_step(f"❌ Directory not found: {base_dir}")
        log_step("Please extract LegiScan datasets to the base directory above.")
        return

    session_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir()])
    if not session_dirs:
        log_step(f"❌ No session directories found in {base_dir}")
        return

    if session_filters:
        raw_filters = {f for f in session_filters}
        normalized_filters = {derive_session_name_from_path(Path(f)) for f in session_filters}
        session_dirs = [
            d for d in session_dirs
            if derive_session_name_from_path(d) in normalized_filters or d.name in raw_filters
        ]

    if args.max_sessions:
        session_dirs = session_dirs[:args.max_sessions]

    if not session_dirs:
        log_step("No sessions matched the provided filters.")
        return

    log_step(f"Importing {len(session_dirs)} session(s)")

    for session_dir in session_dirs:
        try:
            import_session(session_dir, dry_run=args.dry_run, record_limit=args.max_records)
        except Exception as e:
            log_step(f"❌ Error importing {session_dir.name}: {e}")
            log_step("Continuing with next session...")
            continue

    log_header("✅ ALL SESSIONS IMPORT COMPLETE!")
    log_step("Verify Supabase tables: legislators, bills, bill_authors, rollcalls, votes, bill_history, bill_documents")
    log_step("You can now search bills by session (e.g., '2017-2018', '2025-2026')")


if __name__ == "__main__":
    main()
