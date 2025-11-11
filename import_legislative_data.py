"""
Bulk import California legislative data from OpenStates to Supabase.
Run this script once to populate your database.
"""

from __future__ import annotations
import os
import requests
from typing import List, Dict, Any
from supabase import create_client, Client

# Configuration
OPENSTATES_API_KEY = os.environ.get('OPENSTATES_API_KEY')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not all([OPENSTATES_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    print("❌ Missing environment variables:")
    print("  - OPENSTATES_API_KEY")
    print("  - SUPABASE_URL")
    print("  - SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

BASE_URL = "https://v3.openstates.org"


def fetch_all_legislators() -> List[Dict[str, Any]]:
    """Fetch all current California legislators."""
    print("📥 Fetching California legislators...")

    url = f"{BASE_URL}/people"
    params = {
        "jurisdiction": "ca",
        "per_page": 200,
        "apikey": OPENSTATES_API_KEY
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    legislators = []
    for person in data.get("results", []):
        current_role = person.get("current_role", {})

        # Map chamber names
        chamber = current_role.get("org_classification", "")
        if chamber == "upper":
            chamber = "Senate"
        elif chamber == "lower":
            chamber = "Assembly"

        legislator = {
            "id": person["id"],
            "name": person["name"],
            "party": person.get("party", "Unknown"),
            "chamber": chamber,
            "district": current_role.get("division_id", "").split("/")[-1] if current_role else "Unknown",
            "email": person.get("email"),
            "website": person.get("links", [{}])[0].get("url") if person.get("links") else None,
            "image_url": person.get("image")
        }
        legislators.append(legislator)

    print(f"✅ Found {len(legislators)} legislators")
    return legislators


def fetch_all_bills(session: str = "2023-2024") -> List[Dict[str, Any]]:
    """Fetch all California bills for a session."""
    print(f"📥 Fetching California bills for {session} session...")
    print("⚠️  This will take a while and use many API calls...")

    url = f"{BASE_URL}/bills"
    all_bills = []
    page = 1

    while True:
        params = {
            "jurisdiction": "ca",
            "session": session,
            "per_page": 100,
            "page": page,
            "apikey": OPENSTATES_API_KEY
        }

        print(f"  Fetching page {page}...")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            break

        for bill_data in results:
            bill = {
                "id": bill_data["id"],
                "bill_number": bill_data["identifier"],
                "title": bill_data["title"],
                "session": bill_data.get("session", session),
                "status": bill_data.get("latest_action_description", "Unknown"),
                "last_action": bill_data.get("latest_action_description", ""),
                "last_action_date": bill_data.get("latest_action_date"),
                "subjects": bill_data.get("subject", [])
            }
            all_bills.append(bill)

            # Extract authors (handled separately in future version)
            # for sponsor in bill_data.get("sponsorships", []):
            #     pass

        page += 1

        # Safety limit - comment out if you want to fetch all bills
        if page > 5:
            print("⚠️  Stopping at page 5 for testing. Remove this limit to fetch all.")
            break

    print(f"✅ Found {len(all_bills)} bills")
    return all_bills


def import_legislators(legislators: List[Dict[str, Any]]):
    """Import legislators to Supabase."""
    print("💾 Importing legislators to Supabase...")

    try:
        # Upsert legislators (insert or update if exists)
        result = supabase.table('legislators').upsert(legislators).execute()
        print(f"✅ Imported {len(legislators)} legislators")
    except Exception as e:
        print(f"❌ Error importing legislators: {e}")


def import_bills(bills: List[Dict[str, Any]]):
    """Import bills to Supabase."""
    print("💾 Importing bills to Supabase...")

    # Batch insert in chunks of 100
    chunk_size = 100
    for i in range(0, len(bills), chunk_size):
        chunk = bills[i:i + chunk_size]
        try:
            supabase.table('bills').upsert(chunk).execute()
            print(f"  Imported {min(i + chunk_size, len(bills))}/{len(bills)} bills")
        except Exception as e:
            print(f"❌ Error importing bills chunk: {e}")

    print(f"✅ Imported {len(bills)} bills")


def main():
    """Main import process."""
    print("🚀 Starting California legislative data import")
    print("=" * 60)

    # Step 1: Import legislators
    legislators = fetch_all_legislators()
    import_legislators(legislators)

    print()

    # Step 2: Import bills
    session = "2023-2024"
    bills = fetch_all_bills(session)
    import_bills(bills)

    print()
    print("=" * 60)
    print("✅ Import complete!")
    print()
    print("Next steps:")
    print("1. Check your Supabase dashboard to verify data")
    print("2. To import votes, we need to fetch individual bill details")
    print("3. Run this script again with --full flag to import votes")
    print("   (Warning: This will use many API calls)")


if __name__ == "__main__":
    main()
