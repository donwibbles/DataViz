"""California Legislative Vote Tracker Module (Supabase backend only)."""

from .models import Legislator, Bill, Vote
from .supabase_api import (
    fetch_legislators,
    fetch_legislator_votes,
    fetch_bill_details,
    search_bills,
    get_available_sessions,
    fetch_authored_bills,
    get_legislator_sessions,
    get_legislator_stats,
)

__all__ = [
    'Legislator',
    'Bill',
    'Vote',
    'fetch_legislators',
    'fetch_legislator_votes',
    'fetch_bill_details',
    'search_bills',
    'get_available_sessions',
    'fetch_authored_bills',
    'get_legislator_sessions',
    'get_legislator_stats'
]
