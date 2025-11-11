#!/usr/bin/env python3
"""
Quick fix for legislator chambers.
Re-reads people.csv files and updates only the chamber field.
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

# Find all people.csv files
base_dir = Path('legiscan_ca_data/CA')
session_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir()])

print(f"📊 Found {len(session_dirs)} session directories\n")

# Track updates
updates = {}  # people_id -> chamber

for session_dir in session_dirs:
    people_csv = session_dir / 'csv' / 'people.csv'

    if not people_csv.exists():
        continue

    print(f"📂 Reading {session_dir.name}...")

    with open(people_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            people_id = row['people_id']
            role = row.get('role', '')

            # Map chamber correctly
            if role == 'Sen':
                chamber = 'Senate'
            elif role == 'Rep':
                chamber = 'Assembly'
            else:
                chamber = 'Unknown'

            # Track this mapping (latest session wins if there are duplicates)
            updates[people_id] = chamber

print(f"\n✅ Found {len(updates)} unique legislators")

# Count by chamber
chamber_counts = {}
for chamber in updates.values():
    chamber_counts[chamber] = chamber_counts.get(chamber, 0) + 1

print("\nChamber distribution:")
for chamber, count in sorted(chamber_counts.items()):
    print(f"  {chamber}: {count}")

# Apply updates in batches
print(f"\n🔄 Updating database...")
batch_size = 50
updated = 0
errors = 0

for i, (people_id, chamber) in enumerate(updates.items(), 1):
    try:
        supabase.table('legislators').update({'chamber': chamber}).eq('id', people_id).execute()
        updated += 1

        if i % batch_size == 0:
            print(f"   Progress: {i}/{len(updates)}")

    except Exception as e:
        errors += 1
        if errors <= 5:  # Only show first 5 errors
            print(f"   ⚠️ Error updating {people_id}: {e}")

print(f"\n✅ Updated {updated} legislators")
if errors > 0:
    print(f"⚠️ {errors} errors")

print("\n🎉 Done! Verify with this SQL query:")
print("SELECT chamber, COUNT(*) as count FROM legislators WHERE is_committee = false GROUP BY chamber;")
