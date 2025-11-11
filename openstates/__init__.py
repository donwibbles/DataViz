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
        search_bills
    )
else:
    from .api import (
        fetch_legislators,
        fetch_legislator_votes,
        fetch_bill_details,
        search_bills
    )

__all__ = [
    'Legislator',
    'Bill',
    'Vote',
    'fetch_legislators',
    'fetch_legislator_votes',
    'fetch_bill_details',
    'search_bills'
]
