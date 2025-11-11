"""API wrapper for California legislative data using OpenStates."""

from __future__ import annotations
import requests
from typing import List, Optional, Dict, Any
import streamlit as st

from .models import Legislator, Bill, Vote
from .cache import get_cached_or_fetch


BASE_URL = "https://v3.openstates.org"


def get_api_key() -> Optional[str]:
    """Get OpenStates API key from secrets or environment."""
    try:
        return st.secrets.get("OPENSTATES_API_KEY")
    except:
        pass

    # Try session state
    return st.session_state.get("openstates_api_key")


def make_api_request(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """
    Make a request to the OpenStates API with error handling.

    Args:
        endpoint: API endpoint (e.g., "/people")
        params: Query parameters

    Returns:
        JSON response or None if error
    """
    api_key = get_api_key()
    if not api_key:
        st.warning("⚠️ OpenStates API key not configured. Please add OPENSTATES_API_KEY to your secrets.")
        return None

    url = f"{BASE_URL}{endpoint}"
    params = params or {}
    params["apikey"] = api_key

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("API request timed out. Please try again.")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            st.error("Rate limit exceeded. Please wait a few minutes.")
        elif e.response.status_code == 401:
            st.error("Invalid API key. Please check your configuration.")
        else:
            st.error(f"API error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def fetch_legislators(
    chamber: Optional[str] = None,
    party: Optional[str] = None
) -> List[Legislator]:
    """
    Fetch current California state legislators.

    Args:
        chamber: Filter by 'upper' (Senate) or 'lower' (Assembly)
        party: Filter by party ('Democratic', 'Republican', etc.)

    Returns:
        List of Legislator objects
    """
    cache_key = f"legislators_ca_{chamber}_{party}"

    def _fetch():
        params = {
            "jurisdiction": "ca",
            "per_page": 200
        }

        if chamber:
            params["org_classification"] = chamber

        data = make_api_request("/people", params)
        if not data:
            return []

        legislators = []
        for person in data.get("results", []):
            # Get current role info
            current_role = person.get("current_role", {})

            # Map chamber names
            chamber_name = current_role.get("org_classification", "")
            if chamber_name == "upper":
                chamber_name = "Senate"
            elif chamber_name == "lower":
                chamber_name = "Assembly"

            leg = Legislator(
                id=person["id"],
                name=person["name"],
                party=person.get("party", "Unknown"),
                chamber=chamber_name,
                district=current_role.get("division_id", "").split("/")[-1] if current_role else "Unknown",
                email=person.get("email"),
                website=person.get("links", [{}])[0].get("url") if person.get("links") else None
            )

            # Filter by party if specified
            if party and leg.party != party:
                continue

            legislators.append(leg)

        return [vars(leg) for leg in legislators]

    # Fetch with 24-hour cache
    cached_data = get_cached_or_fetch(cache_key, _fetch, ttl_hours=24, cache_subdir="legislators")

    # Convert back to Legislator objects
    return [Legislator(**data) for data in cached_data]


def fetch_legislator_votes(
    legislator_id: str,
    session: str = "2023-2024"
) -> List[Vote]:
    """
    Fetch voting record for a specific legislator.

    Args:
        legislator_id: OpenStates person ID
        session: Legislative session (e.g., "2023-2024")

    Returns:
        List of Vote objects
    """
    cache_key = f"votes_{legislator_id}_{session}"

    def _fetch():
        # Get legislator's sponsorships and votes through bills
        params = {
            "jurisdiction": "ca",
            "session": session,
            "per_page": 100
        }

        data = make_api_request("/bills", params)
        if not data:
            return []

        votes = []
        # Note: OpenStates API structure makes this complex
        # For MVP, we'll return placeholder data
        # In production, you'd parse bill votes to find this legislator's votes

        return votes

    cached_data = get_cached_or_fetch(cache_key, _fetch, ttl_hours=6, cache_subdir="votes")
    return [Vote(**data) for data in cached_data] if cached_data else []


def search_bills(
    query: str = "",
    session: str = "2023-2024",
    subject: Optional[str] = None
) -> List[Bill]:
    """
    Search for California bills.

    Args:
        query: Search query (bill number or keyword)
        session: Legislative session
        subject: Filter by subject

    Returns:
        List of Bill objects
    """
    cache_key = f"bills_{query}_{session}_{subject}"

    def _fetch():
        params = {
            "jurisdiction": "ca",
            "session": session,
            "per_page": 50
        }

        if query:
            params["q"] = query
        if subject:
            params["subject"] = subject

        data = make_api_request("/bills", params)
        if not data:
            return []

        bills = []
        for bill_data in data.get("results", []):
            bill = Bill(
                id=bill_data["id"],
                bill_number=bill_data["identifier"],
                title=bill_data["title"],
                authors=[s["name"] for s in bill_data.get("sponsorships", [])[:3]],
                session=bill_data.get("session", session),
                status=bill_data.get("latest_action_description", "Unknown"),
                last_action=bill_data.get("latest_action_description", ""),
                last_action_date=bill_data.get("latest_action_date", "")
            )
            bills.append(bill)

        return [vars(bill) for bill in bills]

    cached_data = get_cached_or_fetch(cache_key, _fetch, ttl_hours=6, cache_subdir="bills")
    return [Bill(**data) for data in cached_data]


def fetch_bill_details(bill_id: str) -> Optional[Bill]:
    """
    Fetch detailed information about a specific bill.

    Args:
        bill_id: OpenStates bill ID

    Returns:
        Bill object or None
    """
    cache_key = f"bill_detail_{bill_id}"

    def _fetch():
        data = make_api_request(f"/bills/{bill_id}")
        if not data:
            return None

        bill = Bill(
            id=data["id"],
            bill_number=data["identifier"],
            title=data["title"],
            authors=[s["name"] for s in data.get("sponsorships", [])],
            session=data.get("session", ""),
            status=data.get("latest_action_description", "Unknown"),
            last_action=data.get("latest_action_description", ""),
            last_action_date=data.get("latest_action_date", "")
        )

        # Get vote counts from votes array
        votes_data = data.get("votes", [])
        if votes_data:
            latest_vote = votes_data[0]
            bill.ayes = len([v for v in latest_vote.get("votes", []) if v["option"] == "yes"])
            bill.noes = len([v for v in latest_vote.get("votes", []) if v["option"] == "no"])

        return vars(bill)

    cached_data = get_cached_or_fetch(cache_key, _fetch, ttl_hours=6, cache_subdir="bills")
    return Bill(**cached_data) if cached_data else None
