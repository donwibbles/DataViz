#!/usr/bin/env python3
"""
Bulk Agricultural Bill Classification

Automatically classify all bills in the database as agricultural/farm worker related.
Uses SERVICE_ROLE key for direct database writes (run locally only).

This script should be run:
1. After initial data import (one-time classification of all existing bills)
2. After updating keyword patterns (re-classification)
3. Periodically to classify newly imported bills

Usage:
    # Classify all bills that don't have agricultural_tags
    python bulk_classify_agricultural_bills.py

    # Force re-classification of all bills (even those already tagged)
    python bulk_classify_agricultural_bills.py --force-reclassify

    # Only classify bills from specific sessions
    python bulk_classify_agricultural_bills.py --session "2025-2026"

    # Dry run (show what would be tagged without making changes)
    python bulk_classify_agricultural_bills.py --dry-run

Expected Results:
    - ~44,000 total bills in database (2009-2026)
    - ~500-1500 bills tagged as agricultural (~1-3%)
    - ~5-10 minutes to complete
"""

from __future__ import annotations
import os
import sys
import argparse
from typing import Optional, List, Dict
from supabase import create_client, Client
from openstates.agricultural_classifier import classify_agricultural_bill


def get_supabase_admin_client() -> Optional[Client]:
    """Get Supabase client with SERVICE_ROLE key (admin access)."""
    url = os.environ.get('SUPABASE_URL')
    service_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not service_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        print("\nSet environment variables:")
        print("  export SUPABASE_URL='your-url'")
        print("  export SUPABASE_SERVICE_ROLE_KEY='your-service-key'")
        return None

    return create_client(url, service_key)


def fetch_bills_to_classify(
    client: Client,
    session: Optional[str] = None,
    force_reclassify: bool = False,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Fetch bills that need classification.

    Args:
        client: Supabase admin client
        session: Filter by session_name (e.g., "2025-2026")
        force_reclassify: If True, include bills already tagged
        limit: Max number of bills to fetch (for testing)

    Returns:
        List of bill rows
    """
    print("\n📊 Fetching bills to classify...")

    query = client.table('bills').select('id, bill_number, title, description, session_name')

    # Filter by session if specified
    if session:
        query = query.eq('session_name', session)
        print(f"   Filtering by session: {session}")

    # Skip already-tagged bills unless force-reclassify
    if not force_reclassify:
        query = query.is_('agricultural_tags', 'null')
        print("   Only classifying untagged bills")
    else:
        print("   Re-classifying all bills (including already tagged)")

    # Apply limit for testing
    if limit:
        query = query.limit(limit)
        print(f"   Limiting to {limit} bills")

    response = query.execute()
    bills = response.data

    print(f"✅ Found {len(bills)} bills to classify\n")
    return bills


def classify_and_update_bills(
    client: Client,
    bills: List[Dict],
    dry_run: bool = False,
    batch_size: int = 100
) -> Dict[str, int]:
    """
    Classify bills and update database.

    Args:
        client: Supabase admin client
        bills: List of bill rows to classify
        dry_run: If True, don't actually update database
        batch_size: Number of bills to update per batch

    Returns:
        Statistics dict with counts
    """
    stats = {
        'total': len(bills),
        'agricultural': 0,
        'not_agricultural': 0,
        'errors': 0,
        'by_priority': {'high': 0, 'medium': 0, 'low': 0},
        'by_category': {}
    }

    print(f"🔍 Classifying {len(bills)} bills...")
    if dry_run:
        print("   DRY RUN MODE - no changes will be made\n")

    updates_batch = []

    for i, bill in enumerate(bills, 1):
        try:
            # Classify bill
            classification = classify_agricultural_bill(
                title=bill.get('title', ''),
                description=bill.get('description')
            )

            if classification:
                stats['agricultural'] += 1
                stats['by_priority'][classification['priority']] += 1

                # Count categories
                for category in classification['categories']:
                    stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

                # Show sample of tagged bills
                if stats['agricultural'] <= 10:
                    print(f"   ✓ {bill['bill_number']}: {classification['categories']} (Priority: {classification['priority']})")
                    print(f"      {bill['title'][:70]}...")

                # Prepare update
                if not dry_run:
                    updates_batch.append({
                        'id': bill['id'],
                        'agricultural_tags': classification
                    })

            else:
                stats['not_agricultural'] += 1

            # Show progress
            if i % 500 == 0:
                print(f"   Progress: {i}/{len(bills)} ({stats['agricultural']} agricultural)")

            # Batch update
            if not dry_run and len(updates_batch) >= batch_size:
                _batch_update(client, updates_batch)
                updates_batch = []

        except Exception as e:
            stats['errors'] += 1
            print(f"   ❌ Error classifying bill {bill.get('id')}: {e}")

    # Final batch update
    if not dry_run and updates_batch:
        _batch_update(client, updates_batch)

    return stats


def _batch_update(client: Client, updates: List[Dict]) -> None:
    """
    Update bills in batch using upsert.

    Args:
        client: Supabase admin client
        updates: List of {id, agricultural_tags} dicts
    """
    try:
        # Use upsert to update multiple rows
        for update in updates:
            client.table('bills').update({
                'agricultural_tags': update['agricultural_tags']
            }).eq('id', update['id']).execute()

    except Exception as e:
        print(f"   ⚠️ Batch update error: {e}")


def print_statistics(stats: Dict[str, int]) -> None:
    """Print classification statistics."""
    print("\n" + "="*60)
    print("📊 CLASSIFICATION RESULTS")
    print("="*60)

    print(f"\nTotal Bills Processed: {stats['total']}")
    print(f"  ✓ Agricultural: {stats['agricultural']} ({stats['agricultural']/stats['total']*100:.1f}%)")
    print(f"  ✗ Not Agricultural: {stats['not_agricultural']} ({stats['not_agricultural']/stats['total']*100:.1f}%)")

    if stats['errors'] > 0:
        print(f"  ❌ Errors: {stats['errors']}")

    print(f"\nBy Priority:")
    for priority in ['high', 'medium', 'low']:
        count = stats['by_priority'][priority]
        if count > 0:
            print(f"  {priority.capitalize()}: {count}")

    if stats['by_category']:
        print(f"\nBy Category:")
        for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")

    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Bulk classify California bills as agricultural/farm worker related',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--session', type=str, help='Only classify bills from this session (e.g., "2025-2026")')
    parser.add_argument('--force-reclassify', action='store_true', help='Re-classify bills that are already tagged')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be tagged without making changes')
    parser.add_argument('--limit', type=int, help='Limit number of bills to classify (for testing)')

    args = parser.parse_args()

    # Get Supabase client
    client = get_supabase_admin_client()
    if not client:
        sys.exit(1)

    # Fetch bills
    bills = fetch_bills_to_classify(
        client,
        session=args.session,
        force_reclassify=args.force_reclassify,
        limit=args.limit
    )

    if not bills:
        print("✅ No bills to classify")
        sys.exit(0)

    # Classify and update
    stats = classify_and_update_bills(client, bills, dry_run=args.dry_run)

    # Print results
    print_statistics(stats)

    if args.dry_run:
        print("\n💡 This was a dry run. Run without --dry-run to apply changes.")

    print("\n✅ Classification complete!")


if __name__ == '__main__':
    main()
