"""
California Legislative Vote Tracker
Search CA legislators and bills, view voting records
"""

from __future__ import annotations
import os
import streamlit as st
import pandas as pd

# Page config
st.set_page_config(
    page_title="CA Vote Tracker | DataViz",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ California Legislative Vote Tracker")
st.markdown("Search for California state legislators and view their voting records on recent bills.")

st.divider()

# =============================================================================
# CALIFORNIA LEGISLATIVE VOTE TRACKER
# =============================================================================

with st.expander("📊 Track CA Legislators & Votes", expanded=True):
    # Check if using Supabase backend
    use_supabase = os.environ.get('USE_SUPABASE', 'false').lower() == 'true'

    if use_supabase:
        st.markdown("""
        Search California state legislators and view their voting records.
        Data includes 16 years of legislative history (2009-2026) with 4.5M votes.
        """)
    else:
        st.markdown("""
        Search for California state legislators and view their voting records on recent bills.
        Data sourced from OpenStates API.
        """)

    # Check if API key is configured (only needed if not using Supabase)
    needs_api_key = not use_supabase and not st.secrets.get("OPENSTATES_API_KEY", None) and "openstates_api_key" not in st.session_state

    if needs_api_key:
        st.warning("⚠️ OpenStates API key required")
        st.markdown("""
        To use this feature:
        1. Get a free API key at [OpenStates.org](https://openstates.org/accounts/signup/)
        2. Add to Railway environment variables: `OPENSTATES_API_KEY`

        Or enter temporarily below:
        """)

        temp_key = st.text_input("Enter API Key (temporary)", type="password", key="temp_api_key")
        if temp_key:
            st.session_state.openstates_api_key = temp_key
            st.success("✅ API key set for this session")
            st.rerun()
    else:
        # Import vote tracker module
        try:
            from openstates import fetch_legislators, search_bills, get_available_sessions

            # Create tabs for different search modes
            tab1, tab2 = st.tabs(["🔍 Find Legislators", "📜 Find Bills"])

            with tab1:
                st.subheader("Search California Legislators")

                col1, col2, col3 = st.columns(3)

                with col1:
                    chamber_filter = st.selectbox(
                        "Chamber",
                        options=["All", "Senate", "Assembly"],
                        key="vote_chamber_filter"
                    )

                with col2:
                    party_filter = st.selectbox(
                        "Party",
                        options=["All", "Democratic", "Republican"],
                        key="vote_party_filter"
                    )

                with col3:
                    search_name = st.text_input(
                        "Search by name",
                        placeholder="Enter legislator name...",
                        key="vote_name_search"
                    )

                # Show selected legislator's profile (if one is selected)
                if "selected_legislator" in st.session_state and st.session_state.selected_legislator:
                    from openstates import (
                        fetch_legislator_votes, fetch_authored_bills,
                        get_legislator_sessions, get_legislator_stats
                    )

                    st.divider()

                    # Header with back button
                    col_header1, col_header2 = st.columns([4, 1])
                    with col_header1:
                        st.subheader(f"📋 {st.session_state.selected_legislator_name}")
                        # Show legislator details if available
                        if "selected_legislator_details" in st.session_state:
                            leg = st.session_state.selected_legislator_details
                            st.caption(f"{leg.party} • {leg.chamber} • District {leg.district}")
                    with col_header2:
                        if st.button("← Back", key="back_from_profile"):
                            del st.session_state.selected_legislator
                            del st.session_state.selected_legislator_name
                            if "selected_legislator_details" in st.session_state:
                                del st.session_state.selected_legislator_details
                            st.rerun()

                    # Load stats
                    with st.spinner("Loading legislator stats..."):
                        stats = get_legislator_stats(st.session_state.selected_legislator)

                    # Stats Overview
                    if stats:
                        st.markdown("### Quick Stats")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("📝 Bills Authored", stats.get('authored', 0))
                        with col2:
                            st.metric("🗳️ Total Votes", stats.get('votes', 0))
                        with col3:
                            st.metric("🌾 Ag Bill Votes", stats.get('ag_votes', 0))
                        with col4:
                            ag_pct = (stats.get('ag_votes', 0) / stats.get('votes', 1) * 100) if stats.get('votes', 0) > 0 else 0
                            st.metric("🌾 Ag Vote %", f"{ag_pct:.1f}%")

                        st.divider()

                    # Authored Bills Section (Collapsible)
                    with st.expander(f"📝 Authored/Sponsored Bills ({stats.get('authored', 0)})", expanded=False):
                        if stats.get('authored', 0) > 0:
                            with st.spinner("Loading authored bills..."):
                                authored_bills = fetch_authored_bills(st.session_state.selected_legislator)

                            if authored_bills:
                                # Search box for authored bills
                                search_authored = st.text_input("Search authored bills", key="search_authored", placeholder="Search by bill number or title...")

                                # Filter authored bills
                                filtered_authored = authored_bills
                                if search_authored:
                                    filtered_authored = [
                                        b for b in authored_bills
                                        if search_authored.lower() in b.bill_number.lower() or
                                           search_authored.lower() in b.title.lower()
                                    ]

                                if filtered_authored:
                                    st.caption(f"Showing {len(filtered_authored)} of {len(authored_bills)} bills")

                                    for bill in filtered_authored[:50]:  # Limit display
                                        ag_icon = " 🌾" if hasattr(bill, 'is_agricultural') and bill.is_agricultural else ""
                                        st.markdown(f"**{bill.bill_number}**{ag_icon} - {bill.title}")
                                        st.caption(f"📅 {bill.session} • {bill.status}")
                                        st.divider()

                                    if len(filtered_authored) > 50:
                                        st.info(f"Showing first 50 of {len(filtered_authored)} bills")
                                else:
                                    st.info("No bills match your search")
                            else:
                                st.info("No authored bills found")
                        else:
                            st.info("This legislator has not authored any bills in the database")

                    st.divider()

                    # Voting Record Section (Always visible)
                    st.markdown("### 🗳️ Voting Record")

                    # Get sessions for this legislator
                    sessions = get_legislator_sessions(st.session_state.selected_legislator)

                    # Session picker and search
                    col_filter1, col_filter2 = st.columns([1, 2])
                    with col_filter1:
                        session_options = ["All Sessions"] + sessions
                        selected_session = st.selectbox(
                            "Session",
                            session_options,
                            key="vote_session_filter"
                        )
                    with col_filter2:
                        vote_search = st.text_input(
                            "Search votes by bill number or title",
                            key="vote_search",
                            placeholder="e.g. AB 123 or 'farm worker'"
                        )

                    # Load votes based on session
                    session_param = None if selected_session == "All Sessions" else selected_session

                    with st.spinner("Loading votes..."):
                        if session_param:
                            # Load all votes for single session (no limit)
                            votes = fetch_legislator_votes(
                                st.session_state.selected_legislator,
                                session=session_param
                            )
                        else:
                            # Load first 500 for all sessions
                            votes = fetch_legislator_votes(
                                st.session_state.selected_legislator,
                                limit=500
                            )

                    if votes:
                        # Filter votes by search
                        filtered_votes = votes
                        if vote_search:
                            filtered_votes = [
                                v for v in votes
                                if vote_search.lower() in v.bill_number.lower() or
                                   vote_search.lower() in v.bill_title.lower()
                            ]

                        st.success(f"Found {len(filtered_votes)} votes" + (f" (filtered from {len(votes)})" if vote_search else ""))

                        # Create DataFrame with agricultural indicator
                        vote_data = []
                        for vote in filtered_votes:
                            ag_icon = "🌾" if hasattr(vote, 'is_agricultural') and vote.is_agricultural else ""
                            vote_data.append({
                                "Bill": vote.bill_number,
                                "Title": vote.bill_title[:60] + "..." if len(vote.bill_title) > 60 else vote.bill_title,
                                "Vote": vote.vote_type,
                                "Date": vote.vote_date,
                                "Session": vote.session,
                                "🌾": ag_icon
                            })

                        votes_df = pd.DataFrame(vote_data)
                        st.dataframe(votes_df, use_container_width=True, hide_index=True)

                        # Show "Load More" button if showing all sessions and there might be more
                        if session_param is None and len(votes) == 500:
                            st.info("💡 Showing first 500 votes across all sessions. Select a specific session to see all votes for that session.")
                    else:
                        st.warning(f"No votes found for {st.session_state.selected_legislator_name}")
                        st.info("This could mean the legislator hasn't voted on any bills in the database.")

                else:
                    # Show search interface only if no legislator is selected
                    if st.button("Search Legislators", type="primary", key="search_legislators_btn"):
                        with st.spinner("Fetching California legislators..."):
                            # Map chamber names to API values
                            chamber_param = None
                            if chamber_filter == "Senate":
                                chamber_param = "upper"
                            elif chamber_filter == "Assembly":
                                chamber_param = "lower"

                            # Map party names
                            party_param = None
                            if party_filter != "All":
                                party_param = party_filter

                            # Fetch legislators
                            legislators = fetch_legislators(chamber=chamber_param, party=party_param)

                            # Filter by name if provided
                            if search_name:
                                legislators = [
                                    leg for leg in legislators
                                    if search_name.lower() in leg.name.lower()
                                ]

                            # Store results in session state
                            st.session_state.search_results = legislators

                    # Display search results if available
                    if "search_results" in st.session_state:
                        legislators = st.session_state.search_results

                        if legislators:
                            st.success(f"Found {len(legislators)} legislators")

                            # Display as cards
                            for legislator in legislators[:20]:  # Limit to 20
                                with st.container():
                                    col_a, col_b = st.columns([3, 1])

                                    with col_a:
                                        st.markdown(f"### {legislator.name}")
                                        st.caption(f"{legislator.party} • {legislator.chamber} • District {legislator.district}")
                                        if legislator.email:
                                            st.caption(f"📧 {legislator.email}")

                                    with col_b:
                                        if st.button("View Profile", key=f"view_votes_{legislator.id}"):
                                            st.session_state.selected_legislator = legislator.id
                                            st.session_state.selected_legislator_name = legislator.name
                                            st.session_state.selected_legislator_details = legislator
                                            st.rerun()

                                    st.divider()

                            if len(legislators) > 20:
                                st.info(f"Showing first 20 of {len(legislators)} results. Refine your search to see more.")

                        else:
                            st.warning("No legislators found matching your criteria")

            with tab2:
                st.subheader("Search California Bills")

                col1, col2 = st.columns(2)

                with col1:
                    bill_query = st.text_input(
                        "Search bills",
                        placeholder="Enter bill number (e.g., AB 123) or keyword...",
                        key="bill_search_query"
                    )

                with col2:
                    # Get available sessions from database
                    available_sessions = get_available_sessions()
                    if not available_sessions:
                        available_sessions = ["2025-2026"]  # Fallback

                    session_filter = st.selectbox(
                        "Legislative Session",
                        options=available_sessions,
                        key="session_filter"
                    )

                if st.button("Search Bills", type="primary", key="search_bills_btn"):
                    with st.spinner("Searching California bills..."):
                        bills = search_bills(query=bill_query, session=session_filter)

                        if bills:
                            st.success(f"Found {len(bills)} bills")

                            for bill in bills[:15]:  # Show first 15
                                with st.container():
                                    st.markdown(f"**{bill.bill_number}** - {bill.title}")
                                    st.caption(f"📅 Last Action: {bill.last_action_date} - {bill.status}")
                                    if bill.authors:
                                        st.caption(f"✍️ Authors: {', '.join(bill.authors[:3])}")

                                    if st.button("View Details", key=f"view_bill_{bill.id}"):
                                        st.session_state.selected_bill = bill.id

                                    st.divider()

                            if len(bills) > 15:
                                st.info(f"Showing first 15 of {len(bills)} results")
                        else:
                            st.warning("No bills found matching your search")

                # Show selected bill details
                if "selected_bill" in st.session_state and st.session_state.selected_bill:
                    st.divider()

                    from openstates import fetch_bill_details

                    with st.spinner("Loading bill details..."):
                        bill = fetch_bill_details(st.session_state.selected_bill)

                    if bill:
                        st.subheader(f"📜 {bill.bill_number}: {bill.title}")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Session", bill.session)
                        with col2:
                            st.metric("Status", bill.status)
                        with col3:
                            if bill.last_action_date:
                                st.metric("Last Action", bill.last_action_date)

                        if bill.authors:
                            st.markdown(f"**✍️ Authors:** {', '.join(bill.authors)}")

                        if bill.last_action:
                            st.markdown(f"**📋 Latest Action:** {bill.last_action}")

                        # Show vote summary if available
                        if hasattr(bill, 'ayes') or hasattr(bill, 'noes'):
                            st.markdown("### Vote Summary")
                            vote_col1, vote_col2, vote_col3 = st.columns(3)
                            with vote_col1:
                                st.metric("Ayes", getattr(bill, 'ayes', 0))
                            with vote_col2:
                                st.metric("Noes", getattr(bill, 'noes', 0))
                            with vote_col3:
                                st.metric("Abstain", getattr(bill, 'abstain', 0))

                        if st.button("← Back to search"):
                            del st.session_state.selected_bill
                            st.rerun()
                    else:
                        st.error("Could not load bill details")
                        if st.button("← Back to search"):
                            del st.session_state.selected_bill
                            st.rerun()

        except ImportError as e:
            st.error(f"Vote tracker module not found: {e}")
            st.info("The vote tracker feature requires the openstates module to be installed.")

# Sidebar info
with st.sidebar:
    st.markdown("## About Vote Tracker")
    st.markdown("""
    Track California state legislators and their voting records using data from OpenStates.

    **Features:**
    - Search by legislator name, party, chamber
    - Search bills by number or keyword
    - View voting records (coming soon)
    - Filter by legislative session
    """)

    st.divider()

    st.markdown("## Data Source")
    st.markdown("""
    Data provided by [OpenStates](https://openstates.org/),
    a nonprofit providing legislative data for all 50 states.
    """)

    st.divider()

    if st.button("← Back to Home"):
        st.switch_page("Home.py")
