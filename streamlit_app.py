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

    # Reuse the same temp file when the upload has not changed.
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

    # Try to parse date columns
    date_columns = ["Start Date", "End Date"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Clean amount column
    if "Amount" in df.columns:
        df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce')

    return df


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


# Determine CSV path
csv_path: Optional[Path] = None
if uploaded_file is not None:
    csv_path = _persist_uploaded_file(uploaded_file)
elif manual_path.strip():
    csv_path = Path(manual_path).expanduser()


# Main analysis section
if csv_path is None:
    st.info("👆 Upload a CSV file or enter a path to begin analysis")
    st.stop()


# Load data
try:
    with st.spinner("Loading contribution data..."):
        df = load_contribution_data(str(csv_path), max_rows)

    st.success(f"✅ Loaded {len(df):,} contribution records")

except Exception as exc:
    st.error(f"Failed to load CSV: {exc}")
    st.stop()


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
# CONTRIBUTIONS BY COMMITTEE
# =============================================================================
st.header("🏛️ Contributions by Committee")

if "Recipient Committee" in df.columns and "Amount" in df.columns:
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
        st.plotly_chart(fig, use_container_width=True)

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
else:
    st.warning("Required columns not found: 'Recipient Committee' and 'Amount'")


# =============================================================================
# CONTRIBUTION AMOUNT RANGES
# =============================================================================
st.header("💵 Contribution Amount Distribution")

if "Amount" in df.columns:
    # Create amount ranges
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
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            amount_dist,
            x="Amount Range",
            y="Total Amount",
            title="Total Contribution Amount by Range",
            labels={"Total Amount": "Total Amount ($)"}
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Amount column not found")


# =============================================================================
# TOP LOCATIONS
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
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Contributor City or Amount column not found")

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
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Contributor State or Amount column not found")


# =============================================================================
# TIME SERIES ANALYSIS
# =============================================================================
st.header("📅 Contributions Over Time")

if "Start Date" in df.columns and "Amount" in df.columns:
    df_time = df[df["Start Date"].notna()].copy()

    if len(df_time) > 0:
        # Aggregate by date
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
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.line(
                daily_contributions,
                x="Date",
                y="Number of Contributions",
                title="Daily Number of Contributions",
                labels={"Number of Contributions": "Count"}
            )
            fig.update_traces(line_color='#ff7f0e', line_width=2)
            st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid dates found in Start Date column")
else:
    st.warning("Start Date or Amount column not found")


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
    else:
        st.warning("Contributor Name or Amount column not found")

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
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Contributor Occupation or Amount column not found")


# =============================================================================
# DATA EXPORT
# =============================================================================
st.header("📥 Export Data")

col1, col2 = st.columns(2)

with col1:
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Full Dataset (CSV)",
        data=csv_data,
        file_name="contributions_export.csv",
        mime="text/csv"
    )

with col2:
    # Create summary report
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
        label="Download Summary Report (CSV)",
        data=summary_csv,
        file_name="contribution_summary.csv",
        mime="text/csv"
    )
