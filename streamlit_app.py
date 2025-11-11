from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile


st.set_page_config(page_title="Campaign Contribution Analyzer", layout="wide")

st.title("📊 Campaign Contribution Analyzer")
st.write("Upload campaign finance CSV data to analyze contributions, donors, committees, and trends.")


def _persist_uploaded_file(uploaded_file: UploadedFile) -> Optional[Path]:
    """Write the uploaded CSV to a temp file so pandas can access it."""
    if uploaded_file is None:
        return None

    metadata = st.session_state.get("uploaded_file_meta")
    if metadata and metadata.get("name") == uploaded_file.name and metadata.get("size") == uploaded_file.size:
        return Path(metadata["path"])

    suffix = Path(uploaded_file.name).suffix or ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        temp_path = Path(tmp.name)

    st.session_state["uploaded_file_meta"] = {
        "name": uploaded_file.name,
        "size": uploaded_file.size,
        "path": str(temp_path),
    }
    return temp_path


@st.cache_data(show_spinner=False)
def load_contribution_data(path_str: str, max_rows: Optional[int] = None) -> pd.DataFrame:
    """Load contribution CSV and parse dates."""
    df = pd.read_csv(path_str, nrows=max_rows, low_memory=False)

    date_columns = ["Start Date", "End Date"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    if "Amount" in df.columns:
        df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce')

    return df


def create_downloadable_chart(fig, title: str):
    """Display a Plotly chart with download button."""
    # Configure chart to show download options
    config = {
        'toImageButtonOptions': {
            'format': 'png',
            'filename': title.replace(' ', '_').lower(),
            'height': 800,
            'width': 1200,
            'scale': 2
        }
    }
    st.plotly_chart(fig, use_container_width=True, config=config)


# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv", "txt"])
    manual_path = st.text_input("Or enter a CSV path", value="")

    max_rows = st.number_input(
        "Max rows to load (blank = all)",
        min_value=1000,
        value=None,
        step=10000,
        help="Leave empty to load all rows"
    )

    st.divider()
    st.caption("Upload your campaign finance CSV to begin analysis")


csv_path: Optional[Path] = None
if uploaded_file is not None:
    csv_path = _persist_uploaded_file(uploaded_file)
elif manual_path.strip():
    csv_path = Path(manual_path).expanduser()

if csv_path is None:
    st.info("👆 Upload a CSV file or enter a path to begin analysis")
    st.stop()

# Load data
try:
    with st.spinner("Loading contribution data..."):
        df_full = load_contribution_data(str(csv_path), max_rows)
    st.success(f"✅ Loaded {len(df_full):,} contribution records")
except Exception as exc:
    st.error(f"Failed to load CSV: {exc}")
    st.stop()


# =============================================================================
# FILTERS
# =============================================================================
with st.sidebar:
    st.divider()
    st.header("🔍 Filters")

    # Committee filter (multi-select)
    selected_committees = []
    if "Recipient Committee" in df_full.columns:
        committees = sorted(df_full["Recipient Committee"].dropna().unique().tolist())
        selected_committees = st.multiselect(
            "Select Committee(s)",
            options=committees,
            help="Leave empty to show all committees"
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
                max_value=max_date,
                help="Filter contributions by date"
            )
            if isinstance(date_range, tuple) and len(date_range) == 2:
                date_min, date_max = date_range

    # Amount range filter
    amount_min, amount_max = None, None
    if "Amount" in df_full.columns:
        valid_amounts = df_full["Amount"].dropna()
        if len(valid_amounts) > 0:
            min_amt = float(valid_amounts.min())
            max_amt = float(valid_amounts.max())

            amount_range = st.slider(
                "Amount Range ($)",
                min_value=min_amt,
                max_value=max_amt,
                value=(min_amt, max_amt),
                help="Filter by contribution amount"
            )
            amount_min, amount_max = amount_range

    # Contributor search
    contributor_search = st.text_input(
        "Search Contributor Name",
        help="Case-insensitive search in contributor names"
    )

    # State filter
    selected_states = []
    if "Contributor State" in df_full.columns:
        states = sorted(df_full["Contributor State"].dropna().unique().tolist())
        selected_states = st.multiselect(
            "Filter by State(s)",
            options=states,
            help="Leave empty to show all states"
        )


# Apply filters
df = df_full.copy()
active_filters = []

if selected_committees:
    df = df[df["Recipient Committee"].isin(selected_committees)]
    active_filters.append(f"Committees: {', '.join(selected_committees)}")

if date_min and date_max and "Start Date" in df.columns:
    df = df[(df["Start Date"].dt.date >= date_min) & (df["Start Date"].dt.date <= date_max)]
    active_filters.append(f"Dates: {date_min} to {date_max}")

if amount_min is not None and amount_max is not None and "Amount" in df.columns:
    df = df[(df["Amount"] >= amount_min) & (df["Amount"] <= amount_max)]
    active_filters.append(f"Amount: ${amount_min:,.2f} to ${amount_max:,.2f}")

if contributor_search:
    df = df[df["Contributor Name"].str.contains(contributor_search, case=False, na=False)]
    active_filters.append(f"Contributor: '{contributor_search}'")

if selected_states:
    df = df[df["Contributor State"].isin(selected_states)]
    active_filters.append(f"States: {', '.join(selected_states)}")


# Display active filters
if active_filters:
    st.info(f"🔎 **Active Filters:** {' | '.join(active_filters)}")
    st.caption(f"Showing {len(df):,} of {len(df_full):,} records ({len(df)/len(df_full)*100:.1f}%)")
else:
    st.info(f"📊 Showing all {len(df):,} records")


# Display raw data preview
with st.expander("📄 View Raw Data (first 100 rows)", expanded=False):
    st.dataframe(df.head(100), use_container_width=True)


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================
st.header("📈 Summary Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_contributions = df["Amount"].sum() if "Amount" in df.columns else 0
    st.metric("Total Contributions", f"${total_contributions:,.2f}")

with col2:
    num_contributions = len(df)
    st.metric("Number of Contributions", f"{num_contributions:,}")

with col3:
    avg_contribution = df["Amount"].mean() if "Amount" in df.columns else 0
    st.metric("Average Contribution", f"${avg_contribution:,.2f}")

with col4:
    unique_donors = df["Contributor Name"].nunique() if "Contributor Name" in df.columns else 0
    st.metric("Unique Donors", f"{unique_donors:,}")


# =============================================================================
# CONTRIBUTIONS BY COMMITTEE (only show if not filtered to specific committees)
# =============================================================================
if not selected_committees and "Recipient Committee" in df.columns and "Amount" in df.columns:
    st.header("🏛️ Contributions by Committee")

    committee_stats = (
        df.groupby("Recipient Committee")
        .agg({
            "Amount": ["sum", "count", "mean"]
        })
        .round(2)
    )
    committee_stats.columns = ["Total Amount", "Number of Contributions", "Average Amount"]
    committee_stats = committee_stats.sort_values("Total Amount", ascending=False).head(15)

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            committee_stats.reset_index(),
            x="Total Amount",
            y="Recipient Committee",
            orientation="h",
            title="Top 15 Committees by Total Contributions",
            labels={"Total Amount": "Total Amount ($)", "Recipient Committee": "Committee"}
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "contributions_by_committee")

    with col2:
        st.dataframe(
            committee_stats.style.format({
                "Total Amount": "${:,.2f}",
                "Number of Contributions": "{:,.0f}",
                "Average Amount": "${:,.2f}"
            }),
            use_container_width=True,
            height=500
        )


# =============================================================================
# CONTRIBUTION AMOUNT RANGES
# =============================================================================
st.header("💵 Contribution Amount Distribution")

if "Amount" in df.columns:
    bins = [0, 50, 100, 250, 500, 1000, 2500, 5000, float('inf')]
    labels = ['$0-50', '$50-100', '$100-250', '$250-500', '$500-1K', '$1K-2.5K', '$2.5K-5K', '$5K+']

    df_amounts = df[df["Amount"] > 0].copy()
    df_amounts["Amount Range"] = pd.cut(df_amounts["Amount"], bins=bins, labels=labels, right=False)

    amount_dist = df_amounts.groupby("Amount Range", observed=True).agg({
        "Amount": ["sum", "count"]
    }).reset_index()
    amount_dist.columns = ["Amount Range", "Total Amount", "Count"]

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            amount_dist,
            x="Amount Range",
            y="Count",
            title="Number of Contributions by Amount Range",
            labels={"Count": "Number of Contributions"}
        )
        create_downloadable_chart(fig, "contribution_count_by_range")

    with col2:
        fig = px.bar(
            amount_dist,
            x="Amount Range",
            y="Total Amount",
            title="Total Contribution Amount by Range",
            labels={"Total Amount": "Total Amount ($)"}
        )
        create_downloadable_chart(fig, "contribution_total_by_range")


# =============================================================================
# GEOGRAPHIC VISUALIZATIONS - MAPS
# =============================================================================
st.header("🗺️ Geographic Distribution")

if "Contributor State" in df.columns and "Amount" in df.columns:

    # US State Map
    st.subheader("United States Contribution Map")

    state_data = (
        df.groupby("Contributor State")
        .agg({
            "Amount": "sum",
            "Contributor Name": "nunique"
        })
        .reset_index()
    )
    state_data.columns = ["State", "Total Amount", "Unique Donors"]

    fig = px.choropleth(
        state_data,
        locations="State",
        locationmode="USA-states",
        color="Total Amount",
        hover_name="State",
        hover_data={"Total Amount": ":$,.2f", "Unique Donors": ":,"},
        scope="usa",
        title="Contributions by State",
        color_continuous_scale="Blues"
    )
    fig.update_layout(height=500)
    create_downloadable_chart(fig, "us_contribution_map")

    # California Map (if CA data exists)
    ca_data = df[df["Contributor State"] == "CA"]
    if len(ca_data) > 0 and "Contributor City" in df.columns:
        st.subheader("California Contribution Map")

        ca_city_data = (
            ca_data.groupby("Contributor City")
            .agg({
                "Amount": "sum",
                "Contributor Name": "count"
            })
            .reset_index()
        )
        ca_city_data.columns = ["City", "Total Amount", "Number of Contributions"]
        ca_city_data = ca_city_data.sort_values("Total Amount", ascending=False).head(30)

        # For better visualization, create a scatter geo map
        fig = px.scatter_geo(
            ca_city_data,
            locations=["CA"] * len(ca_city_data),
            locationmode="USA-states",
            size="Total Amount",
            hover_name="City",
            hover_data={"Total Amount": ":$,.2f", "Number of Contributions": ":,"},
            title="Top 30 California Cities by Contribution Amount",
            scope="usa",
            size_max=50
        )
        fig.update_geos(
            center=dict(lat=37, lon=-119),
            projection_scale=5
        )
        fig.update_layout(height=600)
        create_downloadable_chart(fig, "california_contribution_map")

        # Also show bar chart for CA cities
        st.subheader("Top California Cities")
        fig = px.bar(
            ca_city_data.head(15),
            x="Total Amount",
            y="City",
            orientation="h",
            title="Top 15 California Cities by Contribution Amount"
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "california_cities_bar")


# =============================================================================
# TOP LOCATIONS (for non-map view)
# =============================================================================
st.header("📍 Top Contributing Locations")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 15 Cities")
    if "Contributor City" in df.columns and "Amount" in df.columns:
        city_stats = (
            df.groupby("Contributor City")
            .agg({
                "Amount": "sum",
                "Contributor Name": "nunique"
            })
            .sort_values("Amount", ascending=False)
            .head(15)
            .reset_index()
        )
        city_stats.columns = ["City", "Total Amount", "Unique Donors"]

        fig = px.bar(
            city_stats,
            x="Total Amount",
            y="City",
            orientation="h",
            title="Top 15 Cities by Contribution Amount",
            labels={"Total Amount": "Total Amount ($)"}
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "top_cities")

with col2:
    st.subheader("Top 15 States")
    if "Contributor State" in df.columns and "Amount" in df.columns:
        state_stats = (
            df.groupby("Contributor State")
            .agg({
                "Amount": "sum",
                "Contributor Name": "nunique"
            })
            .sort_values("Amount", ascending=False)
            .head(15)
            .reset_index()
        )
        state_stats.columns = ["State", "Total Amount", "Unique Donors"]

        fig = px.bar(
            state_stats,
            x="Total Amount",
            y="State",
            orientation="h",
            title="Top 15 States by Contribution Amount",
            labels={"Total Amount": "Total Amount ($)"}
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "top_states")


# =============================================================================
# TIME SERIES ANALYSIS
# =============================================================================
st.header("📅 Contributions Over Time")

if "Start Date" in df.columns and "Amount" in df.columns:
    df_time = df[df["Start Date"].notna()].copy()

    if len(df_time) > 0:
        daily_contributions = (
            df_time.groupby(df_time["Start Date"].dt.date)
            .agg({
                "Amount": "sum",
                "Contributor Name": "count"
            })
            .reset_index()
        )
        daily_contributions.columns = ["Date", "Total Amount", "Number of Contributions"]

        col1, col2 = st.columns(2)

        with col1:
            fig = px.line(
                daily_contributions,
                x="Date",
                y="Total Amount",
                title="Daily Contribution Amounts",
                labels={"Total Amount": "Total Amount ($)"}
            )
            fig.update_traces(line_color='#1f77b4', line_width=2)
            create_downloadable_chart(fig, "daily_amounts")

        with col2:
            fig = px.line(
                daily_contributions,
                x="Date",
                y="Number of Contributions",
                title="Daily Number of Contributions",
                labels={"Number of Contributions": "Count"}
            )
            fig.update_traces(line_color='#ff7f0e', line_width=2)
            create_downloadable_chart(fig, "daily_counts")

        # Monthly aggregation
        df_time["Month"] = df_time["Start Date"].dt.to_period('M').astype(str)
        monthly_contributions = (
            df_time.groupby("Month")
            .agg({
                "Amount": "sum",
                "Contributor Name": "count"
            })
            .reset_index()
        )
        monthly_contributions.columns = ["Month", "Total Amount", "Number of Contributions"]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_contributions["Month"],
            y=monthly_contributions["Total Amount"],
            name="Total Amount",
            yaxis="y",
            marker_color='#1f77b4'
        ))
        fig.add_trace(go.Scatter(
            x=monthly_contributions["Month"],
            y=monthly_contributions["Number of Contributions"],
            name="Number of Contributions",
            yaxis="y2",
            mode='lines+markers',
            marker_color='#ff7f0e',
            line=dict(width=3)
        ))

        fig.update_layout(
            title="Monthly Contributions: Amount vs Count",
            xaxis=dict(title="Month"),
            yaxis=dict(title="Total Amount ($)", side="left"),
            yaxis2=dict(title="Number of Contributions", overlaying="y", side="right"),
            hovermode="x unified",
            height=500
        )
        create_downloadable_chart(fig, "monthly_contributions")


# =============================================================================
# ADDITIONAL INSIGHTS
# =============================================================================
st.header("🔍 Additional Insights")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 20 Contributors")
    if "Contributor Name" in df.columns and "Amount" in df.columns:
        top_contributors = (
            df.groupby("Contributor Name")
            ["Amount"]
            .sum()
            .sort_values(ascending=False)
            .head(20)
            .reset_index()
        )
        top_contributors.columns = ["Contributor", "Total Amount"]

        st.dataframe(
            top_contributors.style.format({"Total Amount": "${:,.2f}"}),
            use_container_width=True,
            height=400
        )

with col2:
    st.subheader("Top 15 Occupations")
    if "Contributor Occupation" in df.columns and "Amount" in df.columns:
        occupation_stats = (
            df.groupby("Contributor Occupation")
            .agg({
                "Amount": "sum",
                "Contributor Name": "nunique"
            })
            .sort_values("Amount", ascending=False)
            .head(15)
            .reset_index()
        )
        occupation_stats.columns = ["Occupation", "Total Amount", "Unique Donors"]

        fig = px.bar(
            occupation_stats,
            x="Total Amount",
            y="Occupation",
            orientation="h",
            title="Top 15 Occupations by Contribution Amount"
        )
        fig.update_layout(height=400)
        create_downloadable_chart(fig, "top_occupations")


# =============================================================================
# DATA EXPORT
# =============================================================================
st.header("📥 Export Data")

col1, col2 = st.columns(2)

with col1:
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Download Filtered Dataset (CSV)",
        data=csv_data,
        file_name=f"contributions_filtered_{len(df)}_records.csv",
        mime="text/csv"
    )

with col2:
    summary_data = {
        "Metric": [
            "Total Contributions",
            "Number of Contributions",
            "Average Contribution",
            "Unique Donors",
            "Date Range"
        ],
        "Value": [
            f"${total_contributions:,.2f}",
            f"{num_contributions:,}",
            f"${avg_contribution:,.2f}",
            f"{unique_donors:,}",
            f"{df['Start Date'].min()} to {df['Start Date'].max()}" if "Start Date" in df.columns else "N/A"
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_csv = summary_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📊 Download Summary Report (CSV)",
        data=summary_csv,
        file_name="contribution_summary.csv",
        mime="text/csv"
    )

st.divider()
st.caption("💡 Tip: Use the camera icon in the top-right of any chart to download it as a PNG image")
