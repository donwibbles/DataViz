"""California Legislative Vote Tracker Module."""

import os
from .models import Legislator, Bill, Vote

# Choose backend based on environment variable
# Set USE_SUPABASE=true to use Supabase backend (no rate limits!)
# Default to OpenStates API for backwards compatibility
USE_SUPABASE = os.environ.get('USE_SUPABASE', 'false').lower() == 'true'

if USE_SUPABASE:
    from .supabase_api import (
        fetch_legislators,
        fetch_legislator_votes,
        fetch_bill_details,
        search_bills,
        get_available_sessions
    )
else:
    from .api import (
        fetch_legislators,
        fetch_legislator_votes,
        fetch_bill_details,
        search_bills
    )
    # Fallback for API - return hardcoded sessions
    def get_available_sessions():
        return ["2023-2024", "2021-2022", "2019-2020"]

__all__ = [
    'Legislator',
    'Bill',
    'Vote',
    'fetch_legislators',
    'fetch_legislator_votes',
    'fetch_bill_details',
    'search_bills',
    'get_available_sessions'
]
