"""
Import California legislative data from LegiScan datasets to Supabase.

LegiScan provides weekly dataset snapshots in CSV format.
Download from: https://legiscan.com/CA/datasets

This script processes the CSV files and imports them to Supabase.
"""

from __future__ import annotations
import os
import csv
from pathlib import Path
from supabase import create_client, Client

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


def import_legiscan_legislators(csv_path: str) -> int:
    """
    Import legislators from LegiScan people CSV.

    Args:
        csv_path: Path to the legislators/people CSV file

    Returns:
        Number of legislators imported
    """
    print(f"📥 Importing legislators from {csv_path}...")

    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return 0

    legislators = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Map LegiScan CSV fields to our schema
            # Adjust field names based on actual LegiScan CSV structure
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

            # Only add if we have at least an ID and name
            if legislator['id'] and legislator['name']:
                legislators.append(legislator)

    if legislators:
        try:
            supabase.table('legislators').upsert(legislators).execute()
            print(f"✅ Imported {len(legislators)} legislators")
            return len(legislators)
        except Exception as e:
            print(f"❌ Error importing legislators: {e}")
            return 0

    return 0


def import_legiscan_bills(csv_path: str) -> int:
    """
    Import bills from LegiScan bills CSV.

    Args:
        csv_path: Path to the bills CSV file

    Returns:
        Number of bills imported
    """
    print(f"📥 Importing bills from {csv_path}...")

    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return 0

    bills = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Map LegiScan CSV fields to our schema
            bill = {
                'id': row.get('bill_id') or row.get('id'),
                'bill_number': row.get('bill_number') or row.get('bill_no'),
                'title': row.get('title') or row.get('description'),
                'session': row.get('session') or row.get('session_id'),
                'status': row.get('status') or row.get('status_desc'),
                'last_action': row.get('last_action') or row.get('last_action_desc'),
                'last_action_date': row.get('last_action_date'),
                'subjects': row.get('subjects', '').split(',') if row.get('subjects') else []
            }

            # Only add if we have at least an ID and bill number
            if bill['id'] and bill['bill_number']:
                bills.append(bill)

    if bills:
        # Import in chunks to avoid timeouts
        chunk_size = 100
        total_imported = 0

        for i in range(0, len(bills), chunk_size):
            chunk = bills[i:i + chunk_size]
            try:
                supabase.table('bills').upsert(chunk).execute()
                total_imported += len(chunk)
                print(f"  Imported {total_imported}/{len(bills)} bills")
            except Exception as e:
                print(f"❌ Error importing bills chunk: {e}")

        print(f"✅ Imported {total_imported} bills total")
        return total_imported

    return 0


def import_legiscan_votes(csv_path: str) -> int:
    """
    Import votes from LegiScan roll call/votes CSV.

    Args:
        csv_path: Path to the votes/roll call CSV file

    Returns:
        Number of votes imported
    """
    print(f"📥 Importing votes from {csv_path}...")

    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return 0

    votes = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Map LegiScan CSV fields to our schema
            vote = {
                'bill_id': row.get('bill_id'),
                'legislator_id': row.get('people_id') or row.get('person_id'),
                'vote_type': row.get('vote_text', '').lower(),  # 'yea', 'nay', 'nv', etc.
                'vote_date': row.get('date') or row.get('roll_call_date'),
                'session': row.get('session') or row.get('session_id'),
                'chamber': row.get('chamber'),
                'motion': row.get('desc') or row.get('motion'),
                'passed': row.get('passed') == '1' or row.get('passed') == 'true'
            }

            # Normalize vote types
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

            # Only add if we have required fields
            if vote['bill_id'] and vote['legislator_id']:
                votes.append(vote)

    if votes:
        # Import in chunks
        chunk_size = 500
        total_imported = 0

        for i in range(0, len(votes), chunk_size):
            chunk = votes[i:i + chunk_size]
            try:
                supabase.table('votes').upsert(chunk, on_conflict='bill_id,legislator_id,vote_date,motion').execute()
                total_imported += len(chunk)
                print(f"  Imported {total_imported}/{len(votes)} votes")
            except Exception as e:
                print(f"❌ Error importing votes chunk: {e}")

        print(f"✅ Imported {total_imported} votes total")
        return total_imported

    return 0


def main():
    """Main import process."""
    print("🚀 LegiScan Dataset Import to Supabase")
    print("=" * 60)
    print()
    print("Instructions:")
    print("1. Download CA dataset from https://legiscan.com/CA/datasets")
    print("2. Extract the ZIP file to a folder")
    print("3. Update the paths below to point to your extracted CSV files")
    print()
    print("=" * 60)
    print()

    # Update these paths to your downloaded LegiScan files
    # The actual filenames may vary - check your downloaded dataset
    dataset_dir = Path("./legiscan_ca_data")  # Change this to your extracted folder

    # Alternative names to try
    alt_files = {
        'legislators': ['people.csv', 'legislators.csv', 'members.csv'],
        'bills': ['bills.csv', 'legislation.csv'],
        'votes': ['roll_calls.csv', 'votes.csv', 'roll_call.csv']
    }

    # Find legislators file
    legislators_path = None
    for filename in alt_files['legislators']:
        path = dataset_dir / filename
        if path.exists():
            legislators_path = path
            break

    # Find bills file
    bills_path = None
    for filename in alt_files['bills']:
        path = dataset_dir / filename
        if path.exists():
            bills_path = path
            break

    # Find votes file
    votes_path = None
    for filename in alt_files['votes']:
        path = dataset_dir / filename
        if path.exists():
            votes_path = path
            break

    # Import data
    if legislators_path:
        import_legiscan_legislators(str(legislators_path))
    else:
        print("⚠️  Legislators file not found. Tried:", alt_files['legislators'])

    print()

    if bills_path:
        import_legiscan_bills(str(bills_path))
    else:
        print("⚠️  Bills file not found. Tried:", alt_files['bills'])

    print()

    if votes_path:
        import_legiscan_votes(str(votes_path))
    else:
        print("⚠️  Votes file not found. Tried:", alt_files['votes'])

    print()
    print("=" * 60)
    print("✅ Import complete!")
    print()
    print("Check your Supabase dashboard to verify the data was imported.")


if __name__ == "__main__":
    main()
