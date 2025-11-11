"""
California Agricultural & Farm Worker Bill Tracker

Browse and filter California legislation related to agriculture, farm workers, and labor organizing.
"""

from __future__ import annotations
import os
import streamlit as st
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Agricultural Tracker | DataViz",
    page_icon="🌾",
    layout="wide"
)

st.title("🌾 California Agricultural & Farm Worker Bill Tracker")
st.markdown("""
Track California legislation related to farm workers, agricultural labor, and organizing rights.
Bills are automatically classified using keyword detection and can be manually curated.
""")

st.divider()

# Check if using Supabase backend
use_supabase = os.environ.get('USE_SUPABASE', 'false').lower() == 'true'

if not use_supabase:
    st.warning("⚠️ Agricultural Tracker requires Supabase backend")
    st.markdown("""
    This feature requires the Supabase backend to be enabled.
    Set `USE_SUPABASE=true` in your environment variables.
    """)
    st.stop()

# Import Supabase API
try:
    from openstates.supabase_api import get_supabase_client, get_available_sessions
except ImportError as e:
    st.error(f"Error importing Supabase API: {e}")
    st.stop()

# Get Supabase client
supabase = get_supabase_client()
if not supabase:
    st.error("Could not connect to Supabase")
    st.stop()

# =============================================================================
# FILTERS
# =============================================================================

with st.expander("🔍 Filters", expanded=True):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Category filter
        categories = [
            "All Categories",
            "Farm Worker Rights",
            "Safety",
            "Union Organizing",
            "Wages",
            "Immigration",
            "Working Conditions"
        ]
        category_filter = st.selectbox("Category", categories, key="ag_category_filter")

    with col2:
        # Priority filter
        priorities = ["All Priorities", "High", "Medium", "Low"]
        priority_filter = st.selectbox("Priority", priorities, key="ag_priority_filter")

    with col3:
        # Session filter
        available_sessions = get_available_sessions()
        if not available_sessions:
            available_sessions = ["2025-2026"]
        session_filter = st.selectbox("Session", ["All Sessions"] + available_sessions, key="ag_session_filter")

    with col4:
        # Curation filter
        curation_options = ["All Bills", "Auto-Tagged Only", "Manually Curated Only"]
        curation_filter = st.selectbox("Curation", curation_options, key="ag_curation_filter")

# =============================================================================
# QUERY BILLS
# =============================================================================

@st.cache_data(ttl=600)  # Cache for 10 minutes
def fetch_agricultural_bills(
    category: str = "All Categories",
    priority: str = "All Priorities",
    session: str = "All Sessions",
    curation: str = "All Bills"
):
    """Fetch agricultural bills from Supabase with filters."""
    try:
        # Build query
        query = supabase.table('bills').select(
            'id, bill_number, title, session_name, last_action_date, status, agricultural_tags, '
            'bill_authors(legislator_id, legislators(name, is_committee))'
        )

        # Filter by agricultural_tags existence
        query = query.not_.is_('agricultural_tags', 'null')

        # Apply session filter
        if session != "All Sessions":
            query = query.eq('session_name', session)

        # Execute query
        response = query.order('last_action_date', desc=True).limit(500).execute()
        bills = response.data

        # Apply additional filters in Python (JSONB queries are complex)
        filtered_bills = []

        for bill in bills:
            tags = bill.get('agricultural_tags', {})
            if not tags or not tags.get('is_agricultural'):
                continue

            # Category filter
            if category != "All Categories":
                category_key = category.lower().replace(' ', '_')
                if category_key not in tags.get('categories', []):
                    continue

            # Priority filter
            if priority != "All Priorities":
                if tags.get('priority', '').lower() != priority.lower():
                    continue

            # Curation filter
            if curation == "Auto-Tagged Only":
                if tags.get('manually_curated', False):
                    continue
            elif curation == "Manually Curated Only":
                if not tags.get('manually_curated', False):
                    continue

            # Extract authors (filter out committees)
            authors = []
            for author in bill.get('bill_authors', []):
                if author.get('legislators'):
                    leg = author['legislators']
                    if not leg.get('is_committee', False):
                        authors.append(leg['name'])

            bill['authors'] = authors
            filtered_bills.append(bill)

        return filtered_bills

    except Exception as e:
        st.error(f"Error fetching bills: {e}")
        return []


# Fetch bills with filters
with st.spinner("Loading agricultural bills..."):
    bills = fetch_agricultural_bills(
        category=category_filter,
        priority=priority_filter,
        session=session_filter,
        curation=curation_filter
    )

# =============================================================================
# DISPLAY RESULTS
# =============================================================================

if not bills:
    st.info("No agricultural bills found matching your filters")
else:
    st.success(f"Found {len(bills)} agricultural bills")

    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        high_priority = sum(1 for b in bills if b.get('agricultural_tags', {}).get('priority') == 'high')
        st.metric("High Priority", high_priority)

    with col2:
        medium_priority = sum(1 for b in bills if b.get('agricultural_tags', {}).get('priority') == 'medium')
        st.metric("Medium Priority", medium_priority)

    with col3:
        low_priority = sum(1 for b in bills if b.get('agricultural_tags', {}).get('priority') == 'low')
        st.metric("Low Priority", low_priority)

    with col4:
        manually_curated = sum(1 for b in bills if b.get('agricultural_tags', {}).get('manually_curated', False))
        st.metric("Manually Curated", manually_curated)

    st.divider()

    # Display bills
    for bill in bills[:50]:  # Limit to 50 for performance
        with st.container():
            tags = bill.get('agricultural_tags', {})
            priority = tags.get('priority', 'unknown')

            # Priority indicator
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(priority, '⚪')

            # Curation indicator
            curation_badge = " 👤" if tags.get('manually_curated', False) else " 🤖"

            # Bill header
            col_a, col_b = st.columns([4, 1])

            with col_a:
                st.markdown(f"### {priority_emoji} {bill['bill_number']}{curation_badge}")
                st.markdown(f"**{bill['title']}**")

                # Categories
                categories_display = ", ".join([
                    c.replace('_', ' ').title()
                    for c in tags.get('categories', [])
                ])
                st.caption(f"📋 Categories: {categories_display}")

                # Session and status
                st.caption(f"📅 {bill.get('session_name', 'Unknown')} • Status: {bill.get('status', 'Unknown')}")

                # Authors
                if bill.get('authors'):
                    st.caption(f"✍️ Authors: {', '.join(bill['authors'][:3])}")

                # Curator notes
                if tags.get('notes'):
                    st.info(f"💬 **Note:** {tags['notes']}")

            with col_b:
                if st.button("View Details", key=f"ag_view_{bill['id']}"):
                    st.session_state.selected_ag_bill = bill['id']

            st.divider()

    if len(bills) > 50:
        st.info(f"Showing first 50 of {len(bills)} results. Use filters to narrow your search.")

# =============================================================================
# BILL DETAILS VIEW
# =============================================================================

if "selected_ag_bill" in st.session_state and st.session_state.selected_ag_bill:
    st.divider()

    # Find selected bill in current results
    selected_bill = next((b for b in bills if b['id'] == st.session_state.selected_ag_bill), None)

    if selected_bill:
        tags = selected_bill.get('agricultural_tags', {})

        st.subheader(f"📜 {selected_bill['bill_number']}: {selected_bill['title']}")

        # Bill metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Session", selected_bill.get('session_name', 'Unknown'))
        with col2:
            st.metric("Status", selected_bill.get('status', 'Unknown'))
        with col3:
            st.metric("Priority", tags.get('priority', 'unknown').capitalize())

        # Authors
        if selected_bill.get('authors'):
            st.markdown(f"**✍️ Authors:** {', '.join(selected_bill['authors'])}")

        # Categories
        st.markdown("**📋 Categories:**")
        for category in tags.get('categories', []):
            st.markdown(f"- {category.replace('_', ' ').title()}")

        # Auto-detected keywords
        if tags.get('auto_detected_keywords'):
            st.markdown("**🔍 Auto-Detected Keywords:**")
            keywords_display = ", ".join(tags['auto_detected_keywords'][:10])
            st.caption(keywords_display)

        # Curation info
        if tags.get('manually_curated'):
            st.info("👤 This bill has been manually curated")
            if tags.get('notes'):
                st.markdown(f"**💬 Curator Notes:** {tags['notes']}")
        else:
            st.caption("🤖 Auto-tagged by keyword detection")

        # Classification date
        if tags.get('classification_date'):
            try:
                date = datetime.fromisoformat(tags['classification_date'].replace('Z', '+00:00'))
                st.caption(f"🕒 Classified: {date.strftime('%Y-%m-%d %H:%M UTC')}")
            except:
                pass

        if st.button("← Back to list"):
            del st.session_state.selected_ag_bill
            st.rerun()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("## About Agricultural Tracker")
    st.markdown("""
    This tool tracks California legislation related to:
    - **Farm Worker Rights**: Labor protections for agricultural workers
    - **Safety**: Heat illness, pesticides, workplace safety
    - **Union Organizing**: Collective bargaining, ALRA, UFW
    - **Wages**: Overtime, minimum wage, piece rates
    - **Immigration**: H-2A visas, labor contractors
    - **Working Conditions**: Housing, sanitation, transportation

    Bills are automatically classified using keyword detection and can be manually curated for accuracy.
    """)

    st.divider()

    st.markdown("## Priority Levels")
    st.markdown("""
    - 🔴 **High**: Landmark legislation, major policy changes
    - 🟡 **Medium**: Incremental improvements, enforcement
    - 🟢 **Low**: Minor amendments, technical changes
    """)

    st.divider()

    st.markdown("## Curation Badges")
    st.markdown("""
    - 🤖 Auto-tagged by keyword detection
    - 👤 Manually curated for accuracy
    """)

    st.divider()

    if st.button("← Back to Home"):
        st.switch_page("Home.py")
