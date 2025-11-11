#!/usr/bin/env python3
"""
Manual Agricultural Bill Tagging Script

Manually tag California bills as agricultural/farm worker related.
Uses SERVICE_ROLE key for direct database writes (run locally only).

Usage Examples:
    # Tag a specific bill
    python tag_agricultural_bills.py \\
        --bill-id "1893344" \\
        --categories "farm_worker_rights,safety" \\
        --priority "high" \\
        --notes "Landmark heat illness prevention bill"

    # Update priority only
    python tag_agricultural_bills.py \\
        --bill-id "1893344" \\
        --priority "low" \\
        --notes "Technical amendment only"

    # Add additional categories to existing tag
    python tag_agricultural_bills.py \\
        --bill-id "1893344" \\
        --add-categories "union_organizing"

    # Remove agricultural tag entirely
    python tag_agricultural_bills.py \\
        --bill-id "1893344" \\
        --remove-tag

    # Bulk tag from file (one bill_id per line)
    python tag_agricultural_bills.py \\
        --bulk-file bills.txt \\
        --categories "safety" \\
        --priority "high"

Security:
    - Requires SUPABASE_SERVICE_ROLE_KEY environment variable
    - DO NOT use ANON key (read-only)
    - DO NOT expose SERVICE_ROLE key in code or frontend
    - Run locally only
"""

from __future__ import annotations
import os
import sys
import argparse
from datetime import datetime
from typing import Optional, List, Dict
from supabase import create_client, Client
from openstates.agricultural_classifier import (
    AGRICULTURAL_CATEGORIES,
    AGRICULTURAL_PRIORITIES,
)


# Valid categories and priorities
VALID_CATEGORIES = AGRICULTURAL_CATEGORIES
VALID_PRIORITIES = AGRICULTURAL_PRIORITIES


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


def tag_bill(
    client: Client,
    bill_id: str,
    categories: Optional[List[str]] = None,
    add_categories: Optional[List[str]] = None,
    priority: Optional[str] = None,
    notes: Optional[str] = None,
    remove_tag: bool = False
) -> bool:
    """
    Tag or update a bill's agricultural classification.

    Args:
        client: Supabase admin client
        bill_id: Bill ID to tag
        categories: Full list of categories (replaces existing)
        add_categories: Categories to add to existing
        priority: Priority level
        notes: Curator notes
        remove_tag: If True, remove agricultural tag entirely

    Returns:
        True if successful
    """
    try:
        # Fetch current bill
        response = client.table('bills').select('id, bill_number, title, agricultural_tags').eq('id', bill_id).single().execute()

        if not response.data:
            print(f"❌ Bill {bill_id} not found")
            return False

        bill = response.data
        print(f"\n📜 Bill: {bill['bill_number']} - {bill['title'][:60]}...")

        # Handle tag removal
        if remove_tag:
            client.table('bills').update({'agricultural_tags': None}).eq('id', bill_id).execute()
            print("✅ Agricultural tag removed")
            return True

        # Get existing tags or create new
        existing_tags = bill.get('agricultural_tags') or {}
        print(f"Current tags: {existing_tags.get('categories', [])} (Priority: {existing_tags.get('priority', 'none')})")

        # Build new tags
        new_tags = {
            'is_agricultural': True,
            'manually_curated': True,
            'classification_date': datetime.utcnow().isoformat() + 'Z'
        }

        # Handle categories
        if categories:
            # Validate
            invalid = [c for c in categories if c not in VALID_CATEGORIES]
            if invalid:
                print(f"❌ Invalid categories: {invalid}")
                print(f"Valid categories: {', '.join(VALID_CATEGORIES)}")
                return False
            new_tags['categories'] = categories

        elif add_categories:
            # Add to existing
            invalid = [c for c in add_categories if c not in VALID_CATEGORIES]
            if invalid:
                print(f"❌ Invalid categories: {invalid}")
                return False

            existing_cats = existing_tags.get('categories', [])
            combined = list(set(existing_cats + add_categories))
            new_tags['categories'] = combined

        else:
            # Keep existing categories
            new_tags['categories'] = existing_tags.get('categories', [])

        # Handle priority
        if priority:
            if priority not in VALID_PRIORITIES:
                print(f"❌ Invalid priority: {priority}")
                print(f"Valid priorities: {', '.join(VALID_PRIORITIES)}")
                return False
            new_tags['priority'] = priority
        else:
            new_tags['priority'] = existing_tags.get('priority', 'medium')

        # Handle notes
        if notes:
            new_tags['notes'] = notes
        else:
            new_tags['notes'] = existing_tags.get('notes')

        # Preserve auto-detected keywords if they exist
        if 'auto_detected_keywords' in existing_tags:
            new_tags['auto_detected_keywords'] = existing_tags['auto_detected_keywords']

        # Update database
        client.table('bills').update({'agricultural_tags': new_tags}).eq('id', bill_id).execute()

        print(f"✅ Tagged: {new_tags['categories']} (Priority: {new_tags['priority']})")
        if notes:
            print(f"   Notes: {notes}")

        return True

    except Exception as e:
        print(f"❌ Error tagging bill {bill_id}: {e}")
        return False


def bulk_tag_from_file(
    client: Client,
    file_path: str,
    categories: Optional[List[str]] = None,
    priority: Optional[str] = None,
    notes: Optional[str] = None
) -> int:
    """
    Tag multiple bills from a file (one bill_id per line).

    Args:
        client: Supabase admin client
        file_path: Path to file with bill IDs
        categories: Categories to apply
        priority: Priority to apply
        notes: Notes to apply

    Returns:
        Number of bills successfully tagged
    """
    try:
        with open(file_path, 'r') as f:
            bill_ids = [line.strip() for line in f if line.strip()]

        print(f"\n📋 Bulk tagging {len(bill_ids)} bills from {file_path}")

        success_count = 0
        for bill_id in bill_ids:
            if tag_bill(client, bill_id, categories=categories, priority=priority, notes=notes):
                success_count += 1

        print(f"\n✅ Successfully tagged {success_count}/{len(bill_ids)} bills")
        return success_count

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return 0
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description='Manually tag California bills as agricultural/farm worker related',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Tag a bill with categories and priority
  %(prog)s --bill-id 1893344 --categories farm_worker_rights,safety --priority high

  # Add additional category to existing tag
  %(prog)s --bill-id 1893344 --add-categories union_organizing

  # Update priority and add notes
  %(prog)s --bill-id 1893344 --priority low --notes "Technical amendment only"

  # Remove agricultural tag
  %(prog)s --bill-id 1893344 --remove-tag

  # Bulk tag from file
  %(prog)s --bulk-file bills.txt --categories safety --priority high

Valid Categories: farm_worker_rights, safety, union_organizing, wages, immigration, working_conditions
Valid Priorities: high, medium, low
        """
    )

    parser.add_argument('--bill-id', type=str, help='Bill ID to tag')
    parser.add_argument('--bulk-file', type=str, help='File with bill IDs (one per line)')
    parser.add_argument('--categories', type=str, help='Comma-separated categories (replaces existing)')
    parser.add_argument('--add-categories', type=str, help='Comma-separated categories to add')
    parser.add_argument('--priority', type=str, choices=VALID_PRIORITIES, help='Priority level')
    parser.add_argument('--notes', type=str, help='Curator notes')
    parser.add_argument('--remove-tag', action='store_true', help='Remove agricultural tag entirely')

    args = parser.parse_args()

    # Validate arguments
    if not args.bill_id and not args.bulk_file:
        parser.error("Must specify --bill-id or --bulk-file")

    if args.bill_id and args.bulk_file:
        parser.error("Cannot specify both --bill-id and --bulk-file")

    if args.categories and args.add_categories:
        parser.error("Cannot specify both --categories and --add-categories")

    if args.remove_tag and (args.categories or args.add_categories or args.priority or args.notes):
        parser.error("--remove-tag cannot be combined with other options")

    # Get Supabase client
    client = get_supabase_admin_client()
    if not client:
        sys.exit(1)

    # Parse categories
    categories_list = None
    if args.categories:
        categories_list = [c.strip() for c in args.categories.split(',')]

    add_categories_list = None
    if args.add_categories:
        add_categories_list = [c.strip() for c in args.add_categories.split(',')]

    # Execute
    if args.bulk_file:
        bulk_tag_from_file(client, args.bulk_file, categories=categories_list, priority=args.priority, notes=args.notes)
    else:
        success = tag_bill(
            client,
            args.bill_id,
            categories=categories_list,
            add_categories=add_categories_list,
            priority=args.priority,
            notes=args.notes,
            remove_tag=args.remove_tag
        )
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
