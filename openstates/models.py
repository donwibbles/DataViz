"""Data models for California legislative data."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Legislator:
    """Represents a California state legislator."""
    id: str
    name: str
    party: str  # 'Democratic', 'Republican', 'Independent'
    chamber: str  # 'Assembly' or 'Senate'
    district: str
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    # Computed fields
    vote_count: int = 0
    yes_votes: int = 0
    no_votes: int = 0


@dataclass
class Vote:
    """Represents a single vote by a legislator."""
    legislator_id: str
    bill_id: str
    bill_number: str
    bill_title: str
    vote_type: str  # 'Aye', 'No', 'Abstain', 'Not Voting'
    vote_date: str
    session: str
    passed: bool


@dataclass
class Bill:
    """Represents a California legislative bill."""
    id: str
    bill_number: str  # e.g., "AB 123"
    title: str
    authors: List[str]
    session: str
    status: str
    last_action: str
    last_action_date: str

    # Vote totals
    ayes: int = 0
    noes: int = 0
    abstain: int = 0
