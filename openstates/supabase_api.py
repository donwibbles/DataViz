"""API wrapper for California legislative data using Supabase backend."""

from __future__ import annotations
import os
from typing import List, Optional, Dict
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
    session: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> List[Vote]:
    """
    Fetch voting record for a specific legislator from Supabase.

    Args:
        legislator_id: Legislator ID
        session: Optional legislative session filter (e.g., "2025-2026")
        limit: Optional limit on number of votes (None = no limit)
        offset: Offset for pagination (default 0)

    Returns:
        List of Vote objects
    """
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        # Query votes with bill information (including session from bills table)
        query = supabase.table('votes') \
            .select('*, bills(bill_number, title, session_name, agricultural_tags)') \
            .eq('legislator_id', legislator_id) \
            .order('vote_date', desc=True)

        # Apply limit and offset if specified
        if limit:
            query = query.limit(limit).range(offset, offset + limit - 1)

        response = query.execute()

        # Convert to Vote objects
        votes = []
        for row in response.data:
            bill_info = row.get('bills', {})
            if not bill_info:
                continue

            # Filter by session if specified
            bill_session = bill_info.get('session_name', '')
            if session and bill_session != session:
                continue

            vote = Vote(
                legislator_id=row['legislator_id'],
                bill_id=row['bill_id'],
                bill_number=bill_info.get('bill_number', 'Unknown'),
                bill_title=bill_info.get('title', 'Unknown'),
                vote_type=row['vote_type'],
                vote_date=row.get('vote_date', ''),
                session=bill_session,
                passed=row.get('passed', False)
            )

            # Add agricultural flag if present
            if bill_info.get('agricultural_tags'):
                vote.is_agricultural = bill_info['agricultural_tags'].get('is_agricultural', False)

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
        def _base_query():
            query_builder = supabase.table('bills') \
                .select('*, bill_authors(legislator_id, legislators(name, is_committee))') \
                .eq('session_name', session)

            if subject:
                query_builder = query_builder.contains('subjects', [subject])

            return query_builder

        bills_data = []

        if query:
            # Bill number lookup
            bill_num_response = _base_query() \
                .ilike('bill_number', f'%{query}%') \
                .order('last_action_date', desc=True) \
                .limit(50) \
                .execute()

            bills_data = bill_num_response.data or []

            if not bills_data:
                # Rebuild the query for title search to avoid bill_number filters leaking through
                title_response = _base_query() \
                    .ilike('title', f'%{query}%') \
                    .order('last_action_date', desc=True) \
                    .limit(50) \
                    .execute()
                bills_data = title_response.data or []
        else:
            # No query, just get recent bills
            bills_data = _base_query() \
                .order('last_action_date', desc=True) \
                .limit(50) \
                .execute() \
                .data

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
                session=row.get('session_name') or row.get('session', ''),
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


def fetch_authored_bills(legislator_id: str, session: Optional[str] = None) -> List[Bill]:
    """
    Fetch bills authored (primary sponsor) by a specific legislator.

    Args:
        legislator_id: Legislator ID
        session: Optional session filter (e.g., "2025-2026")

    Returns:
        List of Bill objects
    """
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        # Query bills where legislator is author
        query = supabase.table('bill_authors') \
            .select('bills(id, bill_number, title, session_name, status, last_action_date, agricultural_tags)') \
            .eq('legislator_id', legislator_id) \
            .order('bills(last_action_date)', desc=True)

        response = query.execute()

        bills = []
        for row in response.data:
            bill_data = row.get('bills')
            if not bill_data:
                continue

            # Filter by session if specified
            if session and bill_data.get('session_name') != session:
                continue

            bill = Bill(
                id=bill_data['id'],
                bill_number=bill_data['bill_number'],
                title=bill_data['title'],
                authors=[],  # Don't need full author list here
                session=bill_data.get('session_name', ''),
                status=bill_data.get('status', 'Unknown'),
                last_action=bill_data.get('last_action', ''),
                last_action_date=bill_data.get('last_action_date', '')
            )

            # Add agricultural flag
            if bill_data.get('agricultural_tags'):
                bill.is_agricultural = bill_data['agricultural_tags'].get('is_agricultural', False)

            bills.append(bill)

        return bills

    except Exception as e:
        st.error(f"Error fetching authored bills: {e}")
        return []


def get_legislator_sessions(legislator_id: str) -> List[str]:
    """
    Get list of sessions where a legislator has votes.

    Args:
        legislator_id: Legislator ID

    Returns:
        List of session names, most recent first
    """
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        # Query distinct sessions from bills that have votes from this legislator
        response = supabase.table('votes') \
            .select('bills(session_name)') \
            .eq('legislator_id', legislator_id) \
            .execute()

        # Extract unique session names
        sessions = set()
        for row in response.data:
            bill_info = row.get('bills', {})
            if bill_info and bill_info.get('session_name'):
                sessions.add(bill_info['session_name'])

        # Sort most recent first
        session_list = sorted(list(sessions), reverse=True)
        return session_list

    except Exception as e:
        st.error(f"Error fetching legislator sessions: {e}")
        return []


def get_legislator_stats(legislator_id: str) -> Dict:
    """
    Get summary statistics for a legislator.

    Args:
        legislator_id: Legislator ID

    Returns:
        Dict with counts: authored, cosponsored, votes, ag_votes
    """
    supabase = get_supabase_client()
    if not supabase:
        return {}

    try:
        stats = {}

        # Count authored bills
        authored = supabase.table('bill_authors') \
            .select('bills(id)', count='exact') \
            .eq('legislator_id', legislator_id) \
            .execute()
        stats['authored'] = authored.count if hasattr(authored, 'count') else 0

        # Count votes
        votes = supabase.table('votes') \
            .select('id', count='exact') \
            .eq('legislator_id', legislator_id) \
            .execute()
        stats['votes'] = votes.count if hasattr(votes, 'count') else 0

        # Count agricultural bill votes
        ag_votes = supabase.table('votes') \
            .select('*, bills!inner(agricultural_tags)') \
            .eq('legislator_id', legislator_id) \
            .not_.is_('bills.agricultural_tags', 'null') \
            .execute()
        stats['ag_votes'] = len(ag_votes.data) if ag_votes.data else 0

        return stats

    except Exception as e:
        st.error(f"Error fetching legislator stats: {e}")
        return {}
