"""
Import California legislative data from LegiScan datasets to Supabase.

LegiScan provides weekly dataset snapshots in CSV format.
Download from: https://legiscan.com/CA/datasets

This script properly handles the LegiScan data structure:
- bills.csv → rollcalls.csv → votes.csv
- bills.csv + people.csv → sponsors.csv (bill authors)
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


def import_legislators(csv_path: str) -> int:
    """Import legislators from people.csv"""
    print(f"📥 Importing legislators from {csv_path}...")

    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return 0

    legislators = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Skip committee entries (committee_id != 0)
            if row.get('committee_id') and row.get('committee_id') != '0':
                continue

            # Map chamber: role can be "Sen" or "Asm" for CA
            role = row.get('role', '')
            if role == 'Sen':
                chamber = 'Senate'
            elif role == 'Asm':
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
                'website': None  # Not in LegiScan data
            }

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


def import_bills(csv_path: str, session_id: str = "2172", session_name: str = None) -> int:
    """Import bills from bills.csv"""
    print(f"📥 Importing bills from {csv_path}...")

    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return 0

    bills = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            bill = {
                'id': row['bill_id'],
                'bill_number': row['bill_number'],
                'title': row.get('title') or row.get('description', ''),
                'session': row.get('session_id', session_id),
                'session_name': session_name,
                'status': row.get('status_desc', 'Unknown'),
                'last_action': row.get('last_action', ''),
                'last_action_date': row.get('last_action_date'),
                'subjects': []  # LegiScan doesn't have subjects in CSV
            }

            bills.append(bill)

    if bills:
        # Import in chunks
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


def import_sponsors(csv_path: str) -> int:
    """Import bill authors from sponsors.csv"""
    print(f"📥 Importing bill sponsors from {csv_path}...")

    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return 0

    sponsors = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            sponsor = {
                'bill_id': row['bill_id'],
                'legislator_id': row['people_id']
            }
            sponsors.append(sponsor)

    if sponsors:
        # Import in chunks
        chunk_size = 500
        total_imported = 0

        for i in range(0, len(sponsors), chunk_size):
            chunk = sponsors[i:i + chunk_size]
            try:
                supabase.table('bill_authors').upsert(
                    chunk,
                    on_conflict='bill_id,legislator_id'
                ).execute()
                total_imported += len(chunk)
                print(f"  Imported {total_imported}/{len(sponsors)} bill authors")
            except Exception as e:
                print(f"❌ Error importing sponsors chunk: {e}")

        print(f"✅ Imported {total_imported} bill authors total")
        return total_imported

    return 0


def import_rollcalls(csv_path: str) -> int:
    """Import roll call summaries from rollcalls.csv"""
    print(f"📥 Importing roll calls from {csv_path}...")

    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return 0

    rollcalls = []

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

    if rollcalls:
        # Import in chunks
        chunk_size = 500
        total_imported = 0

        for i in range(0, len(rollcalls), chunk_size):
            chunk = rollcalls[i:i + chunk_size]
            try:
                supabase.table('rollcalls').upsert(chunk).execute()
                total_imported += len(chunk)
                print(f"  Imported {total_imported}/{len(rollcalls)} roll calls")
            except Exception as e:
                print(f"❌ Error importing rollcalls chunk: {e}")

        print(f"✅ Imported {total_imported} roll calls total")
        return total_imported

    return 0


def import_bill_history(csv_path: str) -> int:
    """Import bill action history from history.csv"""
    print(f"📥 Importing bill history from {csv_path}...")

    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return 0

    history = []

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

    if history:
        # Import in chunks
        chunk_size = 1000
        total_imported = 0

        for i in range(0, len(history), chunk_size):
            chunk = history[i:i + chunk_size]
            try:
                supabase.table('bill_history').upsert(
                    chunk,
                    on_conflict='bill_id,action_date,sequence'
                ).execute()
                total_imported += len(chunk)
                if total_imported % 10000 == 0 or total_imported == len(history):
                    print(f"  Imported {total_imported}/{len(history)} history actions")
            except Exception as e:
                print(f"❌ Error importing history chunk: {e}")

        print(f"✅ Imported {total_imported} history actions total")
        return total_imported

    return 0


def import_bill_documents(csv_path: str) -> int:
    """Import bill documents from documents.csv"""
    print(f"📥 Importing bill documents from {csv_path}...")

    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return 0

    documents = []

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

    if documents:
        # Import in chunks
        chunk_size = 500
        total_imported = 0

        for i in range(0, len(documents), chunk_size):
            chunk = documents[i:i + chunk_size]
            try:
                supabase.table('bill_documents').upsert(chunk).execute()
                total_imported += len(chunk)
                if total_imported % 5000 == 0 or total_imported == len(documents):
                    print(f"  Imported {total_imported}/{len(documents)} documents")
            except Exception as e:
                print(f"❌ Error importing documents chunk: {e}")

        print(f"✅ Imported {total_imported} documents total")
        return total_imported

    return 0


def import_votes(votes_csv: str, rollcalls_csv: str, session_id: str = "2172") -> int:
    """
    Import votes by joining votes.csv with rollcalls.csv

    votes.csv has: roll_call_id, people_id, vote, vote_desc
    rollcalls.csv has: bill_id, roll_call_id, date, chamber, description, yea, nay, nv, absent

    We need to join them to get bill_id for each vote.
    """
    print(f"📥 Importing votes from {votes_csv} and {rollcalls_csv}...")

    if not Path(votes_csv).exists():
        print(f"❌ File not found: {votes_csv}")
        return 0

    if not Path(rollcalls_csv).exists():
        print(f"❌ File not found: {rollcalls_csv}")
        return 0

    # First, load rollcalls into memory to create a lookup
    print("  Loading rollcalls data...")
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

    print(f"  Loaded {len(rollcalls)} roll calls")

    # Now process votes and join with rollcalls
    print("  Processing individual votes...")
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

    print(f"  Processed {len(votes)} votes ({skipped} skipped due to missing rollcall)")

    if votes:
        # Import in chunks
        chunk_size = 500
        total_imported = 0

        for i in range(0, len(votes), chunk_size):
            chunk = votes[i:i + chunk_size]
            try:
                supabase.table('votes').upsert(
                    chunk,
                    on_conflict='bill_id,legislator_id,vote_date,motion'
                ).execute()
                total_imported += len(chunk)
                if total_imported % 5000 == 0 or total_imported == len(votes):
                    print(f"  Imported {total_imported}/{len(votes)} votes")
            except Exception as e:
                print(f"❌ Error importing votes chunk: {e}")
                print(f"   First vote in chunk: {chunk[0] if chunk else 'empty'}")

        print(f"✅ Imported {total_imported} votes total")
        return total_imported

    return 0


def main():
    """Main import process."""
    print("🚀 LegiScan Dataset Import to Supabase (v2)")
    print("=" * 60)
    print()

    # Path to extracted LegiScan CSV files
    dataset_dir = Path("./legiscan_ca_data/CA/2025-2026_Regular_Session/csv")

    if not dataset_dir.exists():
        print(f"❌ Directory not found: {dataset_dir}")
        print()
        print("Please extract LegiScan dataset to: legiscan_ca_data/CA/[session]/csv/")
        return

    # Get session info from the directory name
    session_dir = dataset_dir.parent.name  # e.g., "2025-2026_Regular_Session"
    session_id = "2172"  # Default for 2025-2026

    # Extract human-readable session name from directory
    # e.g., "2025-2026_Regular_Session" -> "2025-2026"
    session_name = session_dir.split('_')[0] if '_' in session_dir else session_dir

    print(f"📁 Importing from: {dataset_dir}")
    print(f"📅 Session: {session_name} (ID: {session_id})")
    print()

    # Import in correct order
    people_file = dataset_dir / "people.csv"
    bills_file = dataset_dir / "bills.csv"
    sponsors_file = dataset_dir / "sponsors.csv"
    rollcalls_file = dataset_dir / "rollcalls.csv"
    votes_file = dataset_dir / "votes.csv"
    history_file = dataset_dir / "history.csv"
    documents_file = dataset_dir / "documents.csv"

    # 1. Import legislators
    if people_file.exists():
        import_legislators(str(people_file))
    else:
        print("⚠️  people.csv not found")

    print()

    # 2. Import bills
    if bills_file.exists():
        import_bills(str(bills_file), session_id, session_name)
    else:
        print("⚠️  bills.csv not found")

    print()

    # 3. Import sponsors (bill authors)
    if sponsors_file.exists():
        import_sponsors(str(sponsors_file))
    else:
        print("⚠️  sponsors.csv not found")

    print()

    # 4. Import roll calls (vote summaries)
    if rollcalls_file.exists():
        import_rollcalls(str(rollcalls_file))
    else:
        print("⚠️  rollcalls.csv not found")

    print()

    # 5. Import votes (requires both votes.csv and rollcalls.csv)
    if votes_file.exists() and rollcalls_file.exists():
        import_votes(str(votes_file), str(rollcalls_file), session_id)
    else:
        if not votes_file.exists():
            print("⚠️  votes.csv not found")
        if not rollcalls_file.exists():
            print("⚠️  rollcalls.csv not found")

    print()

    # 6. Import bill history (action timeline)
    if history_file.exists():
        import_bill_history(str(history_file))
    else:
        print("⚠️  history.csv not found")

    print()

    # 7. Import bill documents
    if documents_file.exists():
        import_bill_documents(str(documents_file))
    else:
        print("⚠️  documents.csv not found")

    print()
    print("=" * 60)
    print("✅ Import complete!")
    print()
    print("Check your Supabase dashboard to verify:")
    print("  - legislators table")
    print("  - bills table")
    print("  - bill_authors table")
    print("  - rollcalls table")
    print("  - votes table")
    print("  - bill_history table")
    print("  - bill_documents table")


if __name__ == "__main__":
    main()
