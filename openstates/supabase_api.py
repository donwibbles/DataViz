"""API wrapper for California legislative data using Supabase backend."""

from __future__ import annotations
import os
from typing import List, Optional
import streamlit as st
from supabase import create_client, Client

from .models import Legislator, Bill, Vote


def get_supabase_client() -> Optional[Client]:
    """Get Supabase client with credentials from environment or secrets."""
    try:
        # Try environment variables first, then secrets
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")

        # Fall back to secrets if available
        if not url or not key:
            try:
                url = url or st.secrets.get("SUPABASE_URL")
                key = key or st.secrets.get("SUPABASE_ANON_KEY")
            except (FileNotFoundError, KeyError):
                pass  # Secrets file doesn't exist, that's ok

        if not url or not key:
            st.warning("⚠️ Supabase credentials not configured")
            return None

        return create_client(url, key)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None


def fetch_legislators(
    chamber: Optional[str] = None,
    party: Optional[str] = None
) -> List[Legislator]:
    """
    Fetch current California state legislators from Supabase.

    Args:
        chamber: Filter by 'upper' (Senate) or 'lower' (Assembly)
        party: Filter by party ('Democratic', 'Republican', etc.)

    Returns:
        List of Legislator objects
    """
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        # Build query
        query = supabase.table('legislators').select('*')

        # Map chamber filter
        if chamber:
            if chamber == "upper":
                query = query.eq('chamber', 'Senate')
            elif chamber == "lower":
                query = query.eq('chamber', 'Assembly')

        # Apply party filter
        if party:
            query = query.eq('party', party)

        # Execute query
        response = query.execute()

        # Convert to Legislator objects
        legislators = []
        for row in response.data:
            leg = Legislator(
                id=row['id'],
                name=row['name'],
                party=row.get('party', 'Unknown'),
                chamber=row.get('chamber', 'Unknown'),
                district=row.get('district', 'Unknown'),
                email=row.get('email'),
                phone=row.get('phone'),
                website=row.get('website')
            )
            legislators.append(leg)

        return legislators

    except Exception as e:
        st.error(f"Error fetching legislators: {e}")
        return []


def fetch_legislator_votes(
    legislator_id: str,
    session: str = "2023-2024"
) -> List[Vote]:
    """
    Fetch voting record for a specific legislator from Supabase.

    Args:
        legislator_id: Legislator ID
        session: Legislative session (e.g., "2023-2024")

    Returns:
        List of Vote objects
    """
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        # Query votes with bill information
        response = supabase.table('votes') \
            .select('*, bills(bill_number, title)') \
            .eq('legislator_id', legislator_id) \
            .eq('session', session) \
            .order('vote_date', desc=True) \
            .limit(100) \
            .execute()

        # Convert to Vote objects
        votes = []
        for row in response.data:
            bill_info = row.get('bills', {})
            vote = Vote(
                legislator_id=row['legislator_id'],
                bill_id=row['bill_id'],
                bill_number=bill_info.get('bill_number', 'Unknown'),
                bill_title=bill_info.get('title', 'Unknown'),
                vote_type=row['vote_type'],
                vote_date=row.get('vote_date', ''),
                session=row['session'],
                passed=row.get('passed', False)
            )
            votes.append(vote)

        return votes

    except Exception as e:
        st.error(f"Error fetching votes: {e}")
        return []


def get_available_sessions() -> List[str]:
    """
    Get list of available legislative sessions from the database.

    Returns:
        List of session names (e.g., ['2025-2026', '2023-2024'])
    """
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        # Get distinct session names, ordered by most recent first
        response = supabase.table('bills') \
            .select('session_name') \
            .order('session_name', desc=True) \
            .execute()

        # Extract unique session names
        sessions = list(set([row['session_name'] for row in response.data if row.get('session_name')]))
        sessions.sort(reverse=True)  # Most recent first
        return sessions

    except Exception as e:
        st.error(f"Error fetching sessions: {e}")
        return []


def search_bills(
    query: str = "",
    session: str = "2025-2026",
    subject: Optional[str] = None
) -> List[Bill]:
    """
    Search for California bills in Supabase.

    Args:
        query: Search query (bill number or keyword in title)
        session: Legislative session name (e.g., '2025-2026')
        subject: Filter by subject

    Returns:
        List of Bill objects
    """
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        # Build query using session_name, include authors
        db_query = supabase.table('bills').select('*, bill_authors(legislator_id, legislators(name, is_committee))').eq('session_name', session)

        # Search by bill number or title
        if query:
            # Try exact bill number match first
            bill_num_response = db_query.ilike('bill_number', f'%{query}%').limit(50).execute()
            if bill_num_response.data:
                bills_data = bill_num_response.data
            else:
                # Search in title
                bills_data = db_query.ilike('title', f'%{query}%').limit(50).execute().data
        else:
            # No query, just get recent bills
            bills_data = db_query.order('last_action_date', desc=True).limit(50).execute().data

        # Convert to Bill objects
        bills = []
        for row in bills_data:
            # Extract author names, filter out committees
            authors = []
            for author in row.get('bill_authors', []):
                if author.get('legislators'):
                    leg = author['legislators']
                    # Only show actual legislators, not committees
                    if not leg.get('is_committee', False):
                        authors.append(leg['name'])

            bill = Bill(
                id=row['id'],
                bill_number=row['bill_number'],
                title=row['title'],
                authors=authors,
                session=row['session'],
                status=row.get('status', 'Unknown'),
                last_action=row.get('last_action', ''),
                last_action_date=row.get('last_action_date', '')
            )
            bills.append(bill)

        return bills

    except Exception as e:
        st.error(f"Error searching bills: {e}")
        return []


def fetch_bill_details(bill_id: str) -> Optional[Bill]:
    """
    Fetch detailed information about a specific bill from Supabase.

    Args:
        bill_id: Bill ID

    Returns:
        Bill object or None
    """
    supabase = get_supabase_client()
    if not supabase:
        return None

    try:
        # Get bill with authors and vote counts
        response = supabase.table('bills') \
            .select('*, bill_authors(legislator_id, legislators(name, is_committee))') \
            .eq('id', bill_id) \
            .single() \
            .execute()

        if not response.data:
            return None

        row = response.data

        # Extract author names, filter out committees
        authors = []
        for a in row.get('bill_authors', []):
            if a.get('legislators'):
                leg = a['legislators']
                # Only show actual legislators, not committees
                if not leg.get('is_committee', False):
                    authors.append(leg['name'])

        bill = Bill(
            id=row['id'],
            bill_number=row['bill_number'],
            title=row['title'],
            authors=authors,
            session=row.get('session_name') or row['session'],  # Prefer session_name
            status=row.get('status', 'Unknown'),
            last_action=row.get('last_action', ''),
            last_action_date=row.get('last_action_date', '')
        )

        # Get vote counts
        vote_response = supabase.table('votes') \
            .select('vote_type') \
            .eq('bill_id', bill_id) \
            .execute()

        if vote_response.data:
            bill.ayes = sum(1 for v in vote_response.data if v['vote_type'] == 'yes')
            bill.noes = sum(1 for v in vote_response.data if v['vote_type'] == 'no')
            bill.abstain = sum(1 for v in vote_response.data if v['vote_type'] == 'abstain')

        return bill

    except Exception as e:
        st.error(f"Error fetching bill details: {e}")
        return None
