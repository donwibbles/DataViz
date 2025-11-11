"""
DataViz Toolkit - Political Data Analysis Tools
Landing page for selecting analysis tools
"""

from __future__ import annotations
import streamlit as st

# Page config
st.set_page_config(
    page_title="DataViz Toolkit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header
st.title("📊 DataViz Toolkit")
st.markdown("### Political Data Analysis Tools for Campaigns & Advocacy")

st.divider()

# Introduction
st.markdown("""
Welcome to DataViz, a suite of tools for analyzing political data. Choose a tool below to get started.
""")

st.divider()

# Tool cards
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("## 💰 Campaign Finance Analyzer")

    st.markdown("""
    Upload and analyze campaign contribution data with interactive visualizations and insights.

    **Features:**
    - 📊 Interactive charts and geographic maps
    - ✊ Union & labor support detection
    - 💡 Smart insights and alerts
    - 📈 Committee comparison analysis
    - 📑 Customizable PDF reports
    - 📥 CSV data export

    **Perfect for:**
    - Campaign managers
    - Political researchers
    - Journalists
    - Advocacy organizations
    """)

    if st.button("📊 Launch Campaign Finance Analyzer", type="primary", use_container_width=True):
        st.switch_page("pages/1_Campaign_Finance.py")

with col2:
    st.markdown("## 🏛️ California Legislative Vote Tracker")

    st.markdown("""
    Search California state legislators and track their voting records on recent legislation.

    **Features:**
    - 🔍 Search legislators by name, party, chamber
    - 📜 Search bills by number or keyword
    - 🗳️ View voting records and bill details
    - 📅 Filter by legislative session
    - 💾 Cached data for fast performance

    **Perfect for:**
    - Grassroots organizers
    - Policy advocates
    - Constituent services
    - Political accountability
    """)

    if st.button("🏛️ Launch Vote Tracker", type="primary", use_container_width=True):
        st.switch_page("pages/2_Vote_Tracker.py")

st.divider()

# Footer info
st.markdown("---")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("**📖 About**")
    st.caption("DataViz is an open-source toolkit for analyzing political data.")

with col_b:
    st.markdown("**🔧 Tools**")
    st.caption("Built with Streamlit, Pandas, and Plotly")

with col_c:
    st.markdown("**📊 Data Sources**")
    st.caption("User uploads (Campaign Finance) | OpenStates API (Vote Tracker)")

# Sidebar
with st.sidebar:
    st.markdown("## Quick Navigation")
    st.markdown("Use the buttons above to select a tool, or use the sidebar navigation.")

    st.divider()

    st.markdown("## Getting Started")
    st.markdown("""
    **Campaign Finance Analyzer:**
    1. Prepare your contribution CSV file
    2. Launch the analyzer
    3. Upload and map columns
    4. Explore insights and charts

    **Vote Tracker:**
    1. Get a free OpenStates API key
    2. Launch the vote tracker
    3. Search for legislators or bills
    4. View voting records
    """)
