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
col1, col2, col3 = st.columns(3, gap="large")

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
    """)

    if st.button("📊 Launch Campaign Finance Analyzer", type="primary", use_container_width=True):
        st.switch_page("pages/1_Campaign_Finance.py")

with col2:
    st.markdown("## 🏛️ California Legislative Vote Tracker")

    st.markdown("""
    Search California state legislators and track their voting records on legislation.

    **Features:**
    - 🔍 Search legislators by name, party, chamber
    - 📜 Search bills by number or keyword
    - 🗳️ View voting records and bill details
    - 📅 Filter by legislative session (2009-2026)
    - 📊 16 years of legislative history with 4.5M votes
    """)

    if st.button("🏛️ Launch Vote Tracker", type="primary", use_container_width=True):
        st.switch_page("pages/2_Vote_Tracker.py")

with col3:
    st.markdown("## 🌾 Agricultural Tracker")

    st.markdown("""
    Track California legislation related to farm workers and agricultural labor.

    **Features:**
    - 🔍 Filter by category, priority, session
    - ✊ Farm worker rights & union organizing
    - 🛡️ Safety, wages, and working conditions
    - 🤖 Auto-classification with keyword detection
    - 👤 Manual curation support
    """)

    if st.button("🌾 Launch Agricultural Tracker", type="primary", use_container_width=True):
        st.switch_page("pages/3_Agricultural_Tracker.py")

st.divider()

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
    1. Launch the vote tracker
    2. Search for legislators or bills
    3. View voting records and details
    4. Filter by session (2009-2026)

    **Agricultural Tracker:**
    1. Launch the agricultural tracker
    2. Browse farm worker legislation
    3. Filter by category and priority
    4. View bill classifications
    """)
