"""
Campaign Finance Analyzer (Simplified)
Upload CSV data to quickly chart contributions and filter between candidates.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# CONSTANTS
# =============================================================================

AMOUNT_BINS = [0, 50, 100, 250, 500, 1000, 2500, 5000, float('inf')]
AMOUNT_LABELS = ['$0-50', '$50-100', '$100-250', '$250-500', '$500-1K', '$1K-2.5K', '$2.5K-5K', '$5K+']

CHART_EXPORT_WIDTH = 1200
CHART_EXPORT_HEIGHT = 800
CHART_EXPORT_SCALE = 2

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(page_title="Campaign Finance | DataViz", page_icon="", layout="wide")

st.title("Campaign Finance Analyzer")
st.caption("Upload campaign finance CSV data to analyze contributions and filter between candidates.")

# =============================================================================
# COLUMN MAPPING CONFIG (Simplified to 4 essential fields)
# =============================================================================

EXPECTED_COLUMNS = {
    "Amount": {
        "required": True,
        "keywords": ["amount", "donation", "contribution", "total", "sum"],
        "description": "Contribution amount"
    },
    "Start Date": {
        "required": True,
        "keywords": ["date", "start", "received", "transaction", "contrib"],
        "description": "Contribution date"
    },
    "Committee": {
        "required": True,
        "keywords": ["committee", "recipient", "candidate", "payee", "filer"],
        "description": "Committee or candidate name"
    },
    "Contributor Name": {
        "required": False,
        "keywords": ["contributor", "donor", "name", "contributor name"],
        "description": "Donor name (optional)"
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def auto_detect_column_mapping(df_columns: list[str]) -> dict[str, str]:
    """Auto-detect likely column mappings based on keywords."""
    mapping = {}
    mapped_columns: set[str] = set()
    df_columns_lower = {col: col.lower() for col in df_columns}

    for target_col, config in EXPECTED_COLUMNS.items():
        best_match = None
        best_score = 0

        for original_col, col_lower in df_columns_lower.items():
            if original_col in mapped_columns:
                continue

            if col_lower in config["keywords"]:
                best_match = original_col
                break

            score = sum(1 for keyword in config["keywords"] if keyword in col_lower)
            if score > best_score:
                best_score = score
                best_match = original_col

        if best_match:
            mapping[target_col] = best_match
            mapped_columns.add(best_match)

    return mapping


def apply_column_mapping(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Apply column mapping and parse data types."""
    reverse_mapping = {v: k for k, v in mapping.items() if v}
    df_mapped = df.rename(columns=reverse_mapping)

    if "Start Date" in df_mapped.columns:
        df_mapped["Start Date"] = pd.to_datetime(df_mapped["Start Date"], errors='coerce')

    if "Amount" in df_mapped.columns:
        df_mapped["Amount"] = pd.to_numeric(df_mapped["Amount"], errors='coerce')

    return df_mapped


def sanitize_filename(text: str) -> str:
    """Sanitize text for use in filenames."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', str(text))[:50]


def get_filter_context(
    selected_committees: list[str],
    date_min,
    date_max,
    amount_min: Optional[float],
    amount_max: Optional[float]
) -> tuple[str, str]:
    """Generate filter context for chart titles and filenames."""
    title_parts = []
    filename_parts = []

    if selected_committees:
        if len(selected_committees) == 1:
            title_parts.append(f"{selected_committees[0]}")
            filename_parts.append(sanitize_filename(selected_committees[0]))
        else:
            title_parts.append(f"{len(selected_committees)} Committees")
            filename_parts.append(f"{len(selected_committees)}_committees")

    if date_min and date_max and date_min != date_max:
        title_parts.append(f"{date_min} to {date_max}")
        filename_parts.append(f"{date_min}_to_{date_max}")

    if amount_min is not None and amount_max is not None:
        title_parts.append(f"${amount_min:,.0f}-${amount_max:,.0f}")
        filename_parts.append(f"{int(amount_min)}_to_{int(amount_max)}")

    title_suffix = f" ({' | '.join(title_parts)})" if title_parts else ""
    filename_suffix = "_" + "_".join(filename_parts) if filename_parts else ""

    return title_suffix, filename_suffix


def create_downloadable_chart(
    fig,
    base_title: str,
    filter_context: tuple[str, str] = ("", "")
) -> None:
    """Display a Plotly chart with download button and filter context in title."""
    title_suffix, filename_suffix = filter_context

    if title_suffix and fig.layout.title and fig.layout.title.text:
        fig = go.Figure(fig)
        fig.update_layout(title=fig.layout.title.text + title_suffix)

    config = {
        'toImageButtonOptions': {
            'format': 'png',
            'filename': sanitize_filename(base_title) + filename_suffix,
            'height': CHART_EXPORT_HEIGHT,
            'width': CHART_EXPORT_WIDTH,
            'scale': CHART_EXPORT_SCALE
        }
    }
    st.plotly_chart(fig, width="stretch", config=config)


# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data(show_spinner=False)
def load_contribution_data(path_str: str, max_rows: Optional[int] = None) -> pd.DataFrame:
    """Load contribution CSV."""
    return pd.read_csv(path_str, nrows=max_rows, low_memory=False)


# =============================================================================
# SIDEBAR CONFIGURATION
# =============================================================================

with st.sidebar:
    if st.button("Back to Home", key="back_to_home"):
        st.switch_page("Home.py")
    st.divider()

    st.header("Data")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv", "txt"])

    load_entire_file = st.toggle("Load entire file", value=True,
        help="Disable to limit rows for faster previews")

    max_rows_input = st.number_input(
        "Max rows", min_value=1000, max_value=10000000, value=100000, step=10000,
        disabled=load_entire_file
    )

max_rows: Optional[int] = None if load_entire_file else int(max_rows_input)

# Check for uploaded file
if uploaded_file is None:
    st.info("Upload a CSV file to begin analysis")
    st.stop()

# Load data
try:
    with st.spinner("Loading CSV..."):
        df_raw = pd.read_csv(uploaded_file, nrows=max_rows, low_memory=False)
except Exception as exc:
    st.error(f"Failed to load CSV: {exc}")
    st.stop()

# =============================================================================
# COLUMN MAPPING (Simplified UI)
# =============================================================================

st.header("Column Mapping")

# Auto-detect and allow override
if "column_mapping" not in st.session_state:
    st.session_state.column_mapping = auto_detect_column_mapping(df_raw.columns.tolist())

mapping = st.session_state.column_mapping
options = ["(skip)"] + df_raw.columns.tolist()

with st.expander("Configure Column Mapping", expanded=False):
    cols = st.columns(len(EXPECTED_COLUMNS))
    updated_mapping = {}

    for idx, (target_col, config) in enumerate(EXPECTED_COLUMNS.items()):
        with cols[idx]:
            current_value = mapping.get(target_col, "(skip)")
            if current_value not in options:
                current_value = "(skip)"

            required_marker = " *" if config["required"] else ""
            selected = st.selectbox(
                f"{target_col}{required_marker}",
                options=options,
                index=options.index(current_value),
                key=f"map_{target_col}",
                help=config["description"]
            )
            if selected != "(skip)":
                updated_mapping[target_col] = selected

    if st.button("Apply Mapping", type="primary"):
        st.session_state.column_mapping = updated_mapping
        st.rerun()

# Validate required columns
missing_required = [col for col, cfg in EXPECTED_COLUMNS.items()
                    if cfg["required"] and col not in st.session_state.column_mapping]

if missing_required:
    st.error(f"Missing required columns: {', '.join(missing_required)}")
    st.caption("Please configure column mapping above.")
    st.stop()

# Apply mapping
try:
    df_full = apply_column_mapping(df_raw, st.session_state.column_mapping)
    st.success(f"Loaded {len(df_full):,} records")
except Exception as exc:
    st.error(f"Failed to apply column mapping: {exc}")
    st.stop()

# =============================================================================
# FILTERS (in sidebar)
# =============================================================================

with st.sidebar:
    st.divider()
    st.header("Filters")

    # Committee filter
    committees = sorted(df_full["Committee"].dropna().unique().tolist())
    selected_committees = st.multiselect(
        "Committee(s)",
        options=committees,
        default=committees,
        help=f"{len(committees)} available"
    )

    # Date range filter
    date_min, date_max = None, None
    if "Start Date" in df_full.columns:
        valid_dates = df_full["Start Date"].dropna()
        if len(valid_dates) > 0:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                date_min, date_max = date_range

    # Amount range filter
    amount_min, amount_max = None, None
    if "Amount" in df_full.columns:
        valid_amounts = df_full[df_full["Amount"] >= 0]["Amount"].dropna()
        if len(valid_amounts) > 0:
            min_amt, max_amt = 0.0, float(valid_amounts.max())
            amount_range = st.slider(
                "Amount Range ($)",
                min_value=min_amt,
                max_value=max_amt,
                value=(min_amt, max_amt),
                format="$%.0f"
            )
            amount_min, amount_max = amount_range

# =============================================================================
# APPLY FILTERS
# =============================================================================

mask = pd.Series(True, index=df_full.index)

if selected_committees:
    mask &= df_full["Committee"].isin(selected_committees)

if date_min and date_max and "Start Date" in df_full.columns:
    mask &= (df_full["Start Date"].dt.date >= date_min) & (df_full["Start Date"].dt.date <= date_max)

if amount_min is not None and amount_max is not None:
    mask &= (df_full["Amount"] >= amount_min) & (df_full["Amount"] <= amount_max)

df = df_full[mask]

filter_context = get_filter_context(selected_committees, date_min, date_max, amount_min, amount_max)

# Show filter status
if len(df) < len(df_full):
    st.caption(f"Showing {len(df):,} of {len(df_full):,} records ({len(df)/len(df_full)*100:.1f}%)")
else:
    st.caption(f"Showing all {len(df):,} records")

# =============================================================================
# SUMMARY STATISTICS
# =============================================================================

st.header("Summary")

total = df["Amount"].sum() if "Amount" in df.columns else 0
count = len(df)
avg = df["Amount"].mean() if "Amount" in df.columns and count > 0 else 0
unique_donors = df["Contributor Name"].nunique() if "Contributor Name" in df.columns else "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Contributions", f"${total:,.0f}")
col2.metric("Number of Contributions", f"{count:,}")
col3.metric("Average Contribution", f"${avg:,.0f}")
col4.metric("Unique Donors", f"{unique_donors:,}" if isinstance(unique_donors, int) else unique_donors)

# =============================================================================
# CHART 1: Contributions by Committee
# =============================================================================

st.header("Contributions by Committee")

committee_stats = (
    df.groupby("Committee")["Amount"]
    .agg(["sum", "count", "mean"])
    .reset_index()
)
committee_stats.columns = ["Committee", "Total Amount", "Count", "Average"]
committee_stats = committee_stats.sort_values("Total Amount", ascending=True)

fig = px.bar(
    committee_stats,
    x="Total Amount",
    y="Committee",
    orientation="h",
    title="Total Contributions by Committee",
    labels={"Total Amount": "Total Amount ($)"}
)
fig.update_layout(height=max(400, len(committee_stats) * 35))
create_downloadable_chart(fig, "contributions_by_committee", filter_context)

# =============================================================================
# CHART 2: Contributions Over Time
# =============================================================================

if "Start Date" in df.columns:
    st.header("Contributions Over Time")

    df_time = df[df["Start Date"].notna()]
    if len(df_time) > 0:
        daily = (
            df_time.groupby(df_time["Start Date"].dt.date)["Amount"]
            .agg(["sum", "count"])
            .reset_index()
        )
        daily.columns = ["Date", "Amount", "Count"]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily["Date"], y=daily["Amount"],
            mode='lines', name='Daily Amount',
            line=dict(color='#1f77b4', width=2)
        ))
        fig.update_layout(
            title="Daily Contribution Amounts",
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            height=400
        )
        create_downloadable_chart(fig, "contributions_over_time", filter_context)

# =============================================================================
# CHART 3: Amount Distribution
# =============================================================================

st.header("Amount Distribution")

if "Amount" in df.columns:
    df_amounts = df[df["Amount"] > 0].copy()
    if len(df_amounts) > 0:
        df_amounts["Range"] = pd.cut(
            df_amounts["Amount"],
            bins=AMOUNT_BINS,
            labels=AMOUNT_LABELS,
            right=False
        )
        amount_dist = df_amounts.groupby("Range", observed=True).size().reset_index(name="Count")

        fig = px.bar(
            amount_dist,
            x="Range",
            y="Count",
            title="Number of Contributions by Amount Range",
            labels={"Range": "Amount Range", "Count": "Number of Contributions"}
        )
        create_downloadable_chart(fig, "amount_distribution", filter_context)

# =============================================================================
# CHART 4: Top Contributors (if available)
# =============================================================================

if "Contributor Name" in df.columns:
    st.header("Top 20 Contributors")

    top_contributors = (
        df.groupby("Contributor Name")["Amount"]
        .sum()
        .nlargest(20)
        .reset_index()
    )
    top_contributors.columns = ["Contributor", "Total Amount"]

    fig = px.bar(
        top_contributors.sort_values("Total Amount", ascending=True),
        x="Total Amount",
        y="Contributor",
        orientation="h",
        title="Top 20 Contributors by Total Amount",
        labels={"Total Amount": "Total Amount ($)"}
    )
    fig.update_layout(height=500)
    create_downloadable_chart(fig, "top_contributors", filter_context)

# =============================================================================
# DATA EXPORT
# =============================================================================

st.header("Export")

col1, col2 = st.columns(2)

with col1:
    csv_data = df.to_csv(index=False).encode('utf-8', errors='replace')
    st.download_button(
        "Download Filtered Data (CSV)",
        data=csv_data,
        file_name=f"contributions_{len(df)}_records.csv",
        mime="text/csv"
    )

with col2:
    with st.expander("View Raw Data"):
        st.dataframe(df.head(100), width="stretch")

st.divider()
st.caption("Tip: Use the camera icon on any chart to download as PNG")
