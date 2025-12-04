"""
Campaign Finance Analyzer
Analyze campaign contribution data with interactive visualizations.
"""

from __future__ import annotations

import atexit
import io
import json
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors as rl_colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# =============================================================================
# CONSTANTS
# =============================================================================

# Thresholds for insights
LARGE_DONATION_MULTIPLIER = 10
MOMENTUM_INCREASE_THRESHOLD = 1.5
MOMENTUM_DECREASE_THRESHOLD = 0.5
TOP_DONOR_SIGNIFICANT_PCT = 5
GEOGRAPHIC_CONCENTRATION_PCT = 30

# Chart configuration
CHART_EXPORT_WIDTH = 1200
CHART_EXPORT_HEIGHT = 800
CHART_EXPORT_SCALE = 2

# Amount range bins
AMOUNT_BINS = [0, 50, 100, 250, 500, 1000, 2500, 5000, float('inf')]
AMOUNT_LABELS = ['$0-50', '$50-100', '$100-250', '$250-500', '$500-1K', '$1K-2.5K', '$2.5K-5K', '$5K+']

# Chart colors for comparison
COMPARISON_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(page_title="Campaign Finance | DataViz", page_icon="", layout="wide")

st.title("Campaign Finance Analyzer")
st.write("Upload campaign finance CSV data to analyze contributions, donors, committees, and trends.")

# =============================================================================
# TEMP FILE MANAGEMENT
# =============================================================================

_temp_files: list[Path] = []


def _cleanup_temp_files() -> None:
    """Clean up temporary files on exit."""
    for path in _temp_files:
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass


atexit.register(_cleanup_temp_files)


def _persist_uploaded_file(uploaded_file) -> Optional[Path]:
    """Write the uploaded CSV to a temp file so pandas can access it."""
    if uploaded_file is None:
        return None

    metadata = st.session_state.get("uploaded_file_meta")
    if (
        metadata
        and metadata.get("name") == uploaded_file.name
        and metadata.get("size") == uploaded_file.size
    ):
        return Path(metadata["path"])

    suffix = Path(uploaded_file.name).suffix or ".csv"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            temp_path = Path(tmp.name)
            _temp_files.append(temp_path)
    except Exception as e:
        st.error(f"Failed to save uploaded file: {e}")
        return None

    st.session_state["uploaded_file_meta"] = {
        "name": uploaded_file.name,
        "size": uploaded_file.size,
        "path": str(temp_path),
    }
    return temp_path


# =============================================================================
# CITY COORDINATES
# =============================================================================

@st.cache_data
def load_city_coordinates() -> dict[str, tuple[float, float]]:
    """Load city coordinates from JSON file."""
    coords_path = Path(__file__).parent.parent / "data" / "city_coordinates.json"
    try:
        with open(coords_path) as f:
            data = json.load(f)
            return {k: tuple(v) for k, v in data.items()}
    except Exception:
        return {}


def get_city_coords(city: str, state: str) -> Optional[tuple[float, float]]:
    """Get coordinates for a city."""
    coords = load_city_coordinates()
    key = f"{city}, {state}"
    return coords.get(key)


# =============================================================================
# CACHED AGGREGATION HELPERS
# =============================================================================

@st.cache_data(show_spinner=False)
def get_committee_stats(_df_hash: int, df: pd.DataFrame) -> pd.DataFrame:
    """Cached committee statistics aggregation."""
    return (
        df.groupby("Recipient Committee")
        .agg({"Amount": ["sum", "count", "mean"]})
    )


@st.cache_data(show_spinner=False)
def get_comparison_stats(_df_hash: int, df: pd.DataFrame) -> pd.DataFrame:
    """Cached comparison statistics aggregation."""
    stats = (
        df.groupby("Recipient Committee")
        .agg({
            "Amount": ["sum", "count", "mean"],
            "Contributor Name": "nunique"
        })
    )
    stats.columns = ["Total $", "# Contributions", "Avg $", "# Donors"]
    return stats.reset_index()


@st.cache_data(show_spinner=False)
def get_city_state_stats(_df_hash: int, df: pd.DataFrame, top_n: int = 100) -> pd.DataFrame:
    """Cached city/state aggregation with nlargest optimization."""
    grouped = (
        df.groupby(["Contributor City", "Contributor State"])
        .agg({"Amount": "sum", "Contributor Name": "nunique"})
        .reset_index()
    )
    return grouped.nlargest(top_n, "Amount")


@st.cache_data(show_spinner=False)
def get_city_stats(_df_hash: int, df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Cached city statistics with nlargest."""
    grouped = (
        df.groupby("Contributor City")
        .agg({"Amount": "sum", "Contributor Name": "nunique"})
        .reset_index()
    )
    result = grouped.nlargest(top_n, "Amount")
    result.columns = ["City", "Total Amount", "Unique Donors"]
    return result


@st.cache_data(show_spinner=False)
def get_state_stats(_df_hash: int, df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Cached state statistics with nlargest."""
    grouped = (
        df.groupby("Contributor State")
        .agg({"Amount": "sum", "Contributor Name": "nunique"})
        .reset_index()
    )
    result = grouped.nlargest(top_n, "Amount")
    result.columns = ["State", "Total Amount", "Unique Donors"]
    return result


@st.cache_data(show_spinner=False)
def get_daily_contributions(_df_hash: int, df: pd.DataFrame) -> pd.DataFrame:
    """Cached daily contribution aggregation."""
    df_time = df[df["Start Date"].notna()]
    if len(df_time) == 0:
        return pd.DataFrame()

    daily = (
        df_time.groupby(df_time["Start Date"].dt.date)
        .agg({"Amount": "sum", "Contributor Name": "count"})
        .reset_index()
    )
    daily.columns = ["Date", "Total Amount", "Number of Contributions"]
    return daily


@st.cache_data(show_spinner=False)
def get_monthly_contributions(_df_hash: int, df: pd.DataFrame) -> pd.DataFrame:
    """Cached monthly contribution aggregation."""
    df_time = df[df["Start Date"].notna()]
    if len(df_time) == 0:
        return pd.DataFrame()

    df_time = df_time.copy()
    df_time["Month"] = df_time["Start Date"].dt.to_period('M').astype(str)
    monthly = (
        df_time.groupby("Month")
        .agg({"Amount": "sum", "Contributor Name": "count"})
        .reset_index()
    )
    monthly.columns = ["Month", "Total Amount", "Number of Contributions"]
    return monthly


@st.cache_data(show_spinner=False)
def get_top_contributors(_df_hash: int, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Cached top contributors aggregation."""
    grouped = df.groupby("Contributor Name")["Amount"].sum().reset_index()
    result = grouped.nlargest(top_n, "Amount")
    result.columns = ["Contributor", "Total Amount"]
    return result


@st.cache_data(show_spinner=False)
def get_occupation_stats(_df_hash: int, df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Cached occupation statistics with nlargest."""
    df_occ = df[df["Contributor Occupation"].notna()]
    if len(df_occ) == 0:
        return pd.DataFrame()

    grouped = (
        df_occ.groupby("Contributor Occupation")
        .agg({"Amount": "sum", "Contributor Name": "nunique"})
        .reset_index()
    )
    result = grouped.nlargest(top_n, "Amount")
    result.columns = ["Occupation", "Total Amount", "Unique Donors"]
    return result


@st.cache_data(show_spinner=False)
def get_ca_city_stats(_df_hash: int, df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
    """Cached California city statistics."""
    ca_data = df[df["Contributor State"] == "CA"]
    if len(ca_data) == 0:
        return pd.DataFrame()

    grouped = (
        ca_data.groupby("Contributor City")
        .agg({"Amount": "sum", "Contributor Name": "nunique"})
        .reset_index()
    )
    return grouped.nlargest(top_n, "Amount")


def get_df_hash(df: pd.DataFrame) -> int:
    """Generate a hash for DataFrame caching."""
    if len(df) < 10000:
        return hash(tuple(df.index.tolist()))
    return hash((len(df), df["Amount"].sum() if "Amount" in df.columns else 0))


# =============================================================================
# COLUMN MAPPING
# =============================================================================

EXPECTED_COLUMNS = {
    "Amount": {
        "required": True,
        "keywords": ["amount", "donation", "contribution", "total", "sum"],
        "description": "Contribution amount (numeric)"
    },
    "Start Date": {
        "required": True,
        "keywords": ["date", "start", "received", "transaction", "contrib"],
        "description": "Contribution date"
    },
    "Recipient Committee": {
        "required": False,
        "keywords": ["committee", "recipient", "candidate", "committee name", "payee"],
        "description": "Committee or candidate receiving contribution"
    },
    "Contributor Name": {
        "required": True,
        "keywords": ["contributor", "donor", "name", "contributor name", "donor name"],
        "description": "Name of contributor/donor"
    },
    "Contributor City": {
        "required": False,
        "keywords": ["city", "contributor city", "donor city"],
        "description": "Contributor's city"
    },
    "Contributor State": {
        "required": False,
        "keywords": ["state", "contributor state", "donor state", "st"],
        "description": "Contributor's state (2-letter code)"
    },
    "Contributor Zip Code": {
        "required": False,
        "keywords": ["zip", "zipcode", "postal", "contributor zip"],
        "description": "Contributor's zip code"
    },
    "Contributor Employer": {
        "required": False,
        "keywords": ["employer", "company", "organization"],
        "description": "Contributor's employer"
    },
    "Contributor Occupation": {
        "required": False,
        "keywords": ["occupation", "job", "profession"],
        "description": "Contributor's occupation"
    }
}


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

            # Exact match gets highest priority
            if col_lower in config["keywords"]:
                best_match = original_col
                break

            # Partial keyword match
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

    # Parse dates
    if "Start Date" in df_mapped.columns:
        df_mapped["Start Date"] = pd.to_datetime(df_mapped["Start Date"], errors='coerce')

    # Parse amount
    if "Amount" in df_mapped.columns:
        df_mapped["Amount"] = pd.to_numeric(df_mapped["Amount"], errors='coerce')

    return df_mapped


# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data(show_spinner=False)
def load_contribution_data(path_str: str, max_rows: Optional[int] = None) -> pd.DataFrame:
    """Load contribution CSV."""
    return pd.read_csv(path_str, nrows=max_rows, low_memory=False)


# =============================================================================
# FILTER HELPERS
# =============================================================================

def sanitize_filename(text: str) -> str:
    """Sanitize text for use in filenames."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', str(text))[:50]


def get_filter_context(
    selected_committees: list[str],
    date_min,
    date_max,
    amount_min: Optional[float],
    amount_max: Optional[float],
    contributor_search: str,
    selected_states: list[str]
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

    if contributor_search:
        title_parts.append(f"'{contributor_search}'")
        filename_parts.append(sanitize_filename(contributor_search))

    if selected_states:
        if len(selected_states) <= 3:
            title_parts.append(", ".join(selected_states))
            filename_parts.append("_".join(selected_states))
        else:
            title_parts.append(f"{len(selected_states)} States")
            filename_parts.append(f"{len(selected_states)}_states")

    title_suffix = f" ({' | '.join(title_parts)})" if title_parts else ""
    filename_suffix = "_" + "_".join(filename_parts) if filename_parts else ""

    return title_suffix, filename_suffix


def create_downloadable_chart(
    fig,
    base_title: str,
    filter_context: tuple[str, str] = ("", ""),
    chart_key: Optional[str] = None
) -> None:
    """Display a Plotly chart with download button and filter context in title."""
    title_suffix, filename_suffix = filter_context

    # Create a copy to avoid mutating the original
    if title_suffix and fig.layout.title and fig.layout.title.text:
        fig = go.Figure(fig)
        fig.update_layout(title=fig.layout.title.text + title_suffix)

    # Store figure in session state for PDF export
    if chart_key:
        if "pdf_charts" not in st.session_state:
            st.session_state.pdf_charts = {}
        st.session_state.pdf_charts[chart_key] = fig

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
# SMART INSIGHTS
# =============================================================================

@st.cache_data(show_spinner=False)
def generate_smart_insights(_df_hash: int, df: pd.DataFrame, single_committee_mode: bool = False) -> list[dict]:
    """Generate smart insights and alerts from the data."""
    insights = []

    if "Amount" not in df.columns or len(df) == 0:
        return insights

    amounts = df["Amount"].dropna()
    if len(amounts) == 0:
        return insights

    total_amount = amounts.sum()
    if total_amount == 0:
        return insights

    if single_committee_mode:
        # Large donation alert
        avg_amount = amounts.mean()
        if avg_amount > 0:
            large_threshold = avg_amount * LARGE_DONATION_MULTIPLIER
            large_donations = df[df["Amount"] > large_threshold]

            if len(large_donations) > 0:
                insights.append({
                    "type": "alert",
                    "icon": "!",
                    "title": "Large Donations Detected",
                    "message": f"{len(large_donations)} contributions over ${large_threshold:,.0f} ({LARGE_DONATION_MULTIPLIER}x average)"
                })

        # Contribution velocity
        if "Start Date" in df.columns:
            df_with_dates = df[df["Start Date"].notna()].copy()
            if len(df_with_dates) > 7:
                df_with_dates = df_with_dates.sort_values("Start Date")
                df_with_dates["Week"] = df_with_dates["Start Date"].dt.isocalendar().week
                weekly_counts = df_with_dates.groupby("Week").size()

                if len(weekly_counts) >= 4:
                    recent_avg = weekly_counts.tail(2).mean()
                    older_avg = weekly_counts.iloc[:-2].mean()

                    if older_avg > 0:
                        if recent_avg > older_avg * MOMENTUM_INCREASE_THRESHOLD:
                            insights.append({
                                "type": "positive",
                                "icon": "+",
                                "title": "Increasing Momentum",
                                "message": f"Recent weeks show {(recent_avg/older_avg - 1)*100:.0f}% more contributions"
                            })
                        elif recent_avg < older_avg * MOMENTUM_DECREASE_THRESHOLD:
                            insights.append({
                                "type": "warning",
                                "icon": "-",
                                "title": "Declining Activity",
                                "message": f"Recent contributions down {(1 - recent_avg/older_avg)*100:.0f}% from earlier period"
                            })

        # Top donor contribution percentage
        if "Contributor Name" in df.columns:
            donor_totals = df.groupby("Contributor Name")["Amount"].sum().sort_values(ascending=False)
            if len(donor_totals) > 0:
                top_donor_pct = (donor_totals.iloc[0] / total_amount) * 100
                if top_donor_pct > TOP_DONOR_SIGNIFICANT_PCT:
                    insights.append({
                        "type": "info",
                        "icon": "i",
                        "title": "Top Donor Impact",
                        "message": f"Single largest donor: {top_donor_pct:.1f}% of total contributions"
                    })

    # Geographic concentration
    if "Contributor City" in df.columns:
        city_counts = df["Contributor City"].value_counts()
        if len(city_counts) > 0:
            top_city_pct = (city_counts.iloc[0] / len(df)) * 100
            if top_city_pct > GEOGRAPHIC_CONCENTRATION_PCT:
                insights.append({
                    "type": "info",
                    "icon": "i",
                    "title": "Geographic Concentration",
                    "message": f"{top_city_pct:.0f}% of contributions from {city_counts.index[0]}"
                })

    return insights


# =============================================================================
# PDF GENERATION
# =============================================================================

def generate_pdf_report(
    selected_charts: dict[str, str],
    summary_stats: dict[str, str],
    filter_info: str,
    chart_figures: dict
) -> bytes:
    """Generate a PDF report with selected charts and summary statistics."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=rl_colors.HexColor('#1f77b4'),
        spaceAfter=30,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=rl_colors.HexColor('#2c3e50'),
        spaceAfter=12,
    )

    # Title Page
    story.append(Paragraph("Campaign Contribution Analysis Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    if filter_info:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(f"<b>Filters Applied:</b> {filter_info}", styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    # Summary Statistics Table
    story.append(Paragraph("Summary Statistics", heading_style))
    summary_data = [[k, v] for k, v in summary_stats.items()]
    summary_table = Table(summary_data, colWidths=[3 * inch, 3 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), rl_colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), rl_colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, rl_colors.white),
    ]))
    story.append(summary_table)
    story.append(PageBreak())

    # Add selected charts
    for chart_key, chart_name in selected_charts.items():
        if chart_key not in chart_figures:
            continue

        story.append(Paragraph(chart_name, heading_style))
        try:
            img_bytes = chart_figures[chart_key].to_image(
                format="png",
                width=700,
                height=500,
                scale=2
            )
            img = Image(io.BytesIO(img_bytes), width=6.5 * inch, height=4.5 * inch)
            story.append(img)
            story.append(Spacer(1, 0.3 * inch))
        except Exception as e:
            story.append(Paragraph(f"Error rendering chart: {e}", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))

        story.append(PageBreak())

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# =============================================================================
# SIDEBAR CONFIGURATION
# =============================================================================

with st.sidebar:
    if st.button("Back to Home", key="back_to_home_top"):
        st.switch_page("Home.py")
    st.divider()

    st.header("Configuration")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv", "txt"])
    manual_path = st.text_input("Or enter a CSV path", value="")

    load_entire_file = st.toggle(
        "Load entire file",
        value=True,
        help="Enable to load every row. Disable to cap rows for faster previews."
    )

    max_rows_input = st.number_input(
        "Max rows to load",
        min_value=1000,
        max_value=10000000,
        value=100000,
        step=10000,
        help="Disable 'Load entire file' to limit how many rows are read.",
        disabled=load_entire_file
    )

    st.divider()
    st.caption("Upload your campaign finance CSV to begin analysis")

max_rows: Optional[int] = None if load_entire_file else int(max_rows_input)

csv_path: Optional[Path] = None
if uploaded_file is not None:
    csv_path = _persist_uploaded_file(uploaded_file)
elif manual_path.strip():
    csv_path = Path(manual_path).expanduser()
else:
    # Check if we have a previously uploaded file in session state
    metadata = st.session_state.get("uploaded_file_meta")
    if metadata and metadata.get("path"):
        saved_path = Path(metadata["path"])
        if saved_path.exists():
            csv_path = saved_path

if csv_path is None:
    st.info("Upload a CSV file or enter a path to begin analysis")
    st.stop()

# Load data
try:
    with st.spinner("Loading CSV..."):
        df_raw = load_contribution_data(str(csv_path), max_rows)
except Exception as exc:
    st.error(f"Failed to load CSV: {exc}")
    st.stop()

# =============================================================================
# COLUMN MAPPING
# =============================================================================

st.header("Column Mapping")
st.write("Map your CSV columns to the expected format. We've auto-detected likely matches.")

# Reset mapping if columns changed
current_columns = tuple(sorted(df_raw.columns.tolist()))
if "last_columns" not in st.session_state or st.session_state.last_columns != current_columns:
    st.session_state.column_mapping = auto_detect_column_mapping(df_raw.columns.tolist())
    st.session_state.last_columns = current_columns

mapping = st.session_state.column_mapping

with st.expander("Configure Column Mapping", expanded=False):
    st.caption(f"Your CSV has {len(df_raw.columns)} columns. Map them to the expected fields below.")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("**Expected Field** (Required fields marked with *)")
    with col2:
        st.write("**Your CSV Column**")

    st.divider()

    options = ["(skip)"] + df_raw.columns.tolist()
    updated_mapping = {}

    for target_col, config in EXPECTED_COLUMNS.items():
        col1, col2 = st.columns([1, 1])

        with col1:
            required_marker = " *" if config["required"] else ""
            st.write(f"**{target_col}**{required_marker}")
            st.caption(config["description"])

        with col2:
            current_value = mapping.get(target_col, "(skip)")
            if current_value not in options:
                current_value = "(skip)"

            selected = st.selectbox(
                f"Map {target_col}",
                options=options,
                index=options.index(current_value),
                key=f"mapping_{target_col}",
                label_visibility="collapsed"
            )

            if selected != "(skip)":
                updated_mapping[target_col] = selected

    st.divider()

    # Validation
    missing_required = [
        col for col, config in EXPECTED_COLUMNS.items()
        if config["required"] and col not in updated_mapping
    ]

    if missing_required:
        st.error(f"Missing required fields: {', '.join(missing_required)}")
        st.caption("Please map all required fields (*) to continue.")
        st.stop()

    # Preview
    with st.expander("Preview Mapped Data", expanded=False):
        try:
            df_preview = apply_column_mapping(df_raw.head(100), updated_mapping)
            st.dataframe(df_preview, width="stretch")
        except Exception as e:
            st.error(f"Error previewing mapped data: {e}")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Apply Mapping", type="primary"):
            st.session_state.column_mapping = updated_mapping
            st.rerun()

    with col2:
        if st.button("Reset to Auto-Detect"):
            st.session_state.column_mapping = auto_detect_column_mapping(df_raw.columns.tolist())
            st.rerun()

# Apply mapping
try:
    df_full = apply_column_mapping(df_raw, st.session_state.column_mapping)
    st.success(f"Loaded and mapped {len(df_full):,} contribution records")
except Exception as exc:
    st.error(f"Failed to apply column mapping: {exc}")
    st.stop()


# =============================================================================
# FILTERS
# =============================================================================

with st.sidebar:
    st.divider()
    st.header("Filters")

    # Committee filter
    selected_committees = []
    if "Recipient Committee" in df_full.columns:
        committees = sorted(df_full["Recipient Committee"].dropna().unique().tolist())

        selected_committees = st.multiselect(
            "Select Committee(s)",
            options=committees,
            default=committees,
            help=f"{len(committees)} committees available. Type to search.",
            key="committee_filter"
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
            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                date_min, date_max = date_range

    # Amount range filter
    amount_min, amount_max = None, None
    if "Amount" in df_full.columns:
        valid_amounts = df_full[df_full["Amount"] >= 0]["Amount"].dropna()
        if len(valid_amounts) > 0:
            min_amt = 0.0
            max_amt = float(valid_amounts.max())

            amount_range = st.slider(
                "Amount Range ($)",
                min_value=min_amt,
                max_value=max_amt,
                value=(min_amt, max_amt),
                help="Filter by contribution amount",
                format="$%.0f"
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


# =============================================================================
# APPLY FILTERS (using boolean masks for efficiency)
# =============================================================================

mask = pd.Series(True, index=df_full.index)
active_filters = []

if selected_committees:
    mask &= df_full["Recipient Committee"].isin(selected_committees)
    active_filters.append(f"Committees: {len(selected_committees)} selected")

if date_min and date_max and "Start Date" in df_full.columns:
    mask &= (df_full["Start Date"].dt.date >= date_min) & (df_full["Start Date"].dt.date <= date_max)
    active_filters.append(f"Dates: {date_min} to {date_max}")

if amount_min is not None and amount_max is not None and "Amount" in df_full.columns:
    mask &= (df_full["Amount"] >= amount_min) & (df_full["Amount"] <= amount_max)
    active_filters.append(f"Amount: ${amount_min:,.0f} to ${amount_max:,.0f}")

if contributor_search and "Contributor Name" in df_full.columns:
    mask &= df_full["Contributor Name"].astype(str).str.contains(contributor_search, case=False, na=False)
    active_filters.append(f"Contributor: '{contributor_search}'")

if selected_states and "Contributor State" in df_full.columns:
    mask &= df_full["Contributor State"].isin(selected_states)
    active_filters.append(f"States: {', '.join(selected_states)}")

df = df_full[mask]

# Clear PDF chart storage to prevent memory leak
if "pdf_charts" in st.session_state:
    st.session_state.pdf_charts = {}

# Compute hash for caching
df_hash = get_df_hash(df)

filter_context = get_filter_context(
    selected_committees, date_min, date_max,
    amount_min, amount_max, contributor_search, selected_states
)

# Display filter status
if active_filters:
    st.info(f"**Active Filters:** {' | '.join(active_filters)}")
    if len(df_full) > 0:
        st.caption(f"Showing {len(df):,} of {len(df_full):,} records ({len(df)/len(df_full)*100:.1f}%)")
else:
    st.info(f"Showing all {len(df):,} records")

# Raw data preview
with st.expander("View Raw Data (first 100 rows)", expanded=False):
    st.dataframe(df.head(100), width="stretch")


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================

st.header("Summary Statistics")

col1, col2, col3, col4 = st.columns(4)

total_contributions = df["Amount"].sum() if "Amount" in df.columns else 0
num_contributions = len(df)
avg_contribution = df["Amount"].mean() if "Amount" in df.columns and len(df) > 0 else 0
unique_donors = df["Contributor Name"].nunique() if "Contributor Name" in df.columns else 0

with col1:
    st.metric("Total Contributions", f"${total_contributions:,.2f}")
with col2:
    st.metric("Number of Contributions", f"{num_contributions:,}")
with col3:
    st.metric("Average Contribution", f"${avg_contribution:,.2f}")
with col4:
    st.metric("Unique Donors", f"{unique_donors:,}")


# =============================================================================
# SMART INSIGHTS
# =============================================================================

st.header("Smart Insights")

single_committee_mode = len(selected_committees) == 1
if not single_committee_mode and len(selected_committees) > 1:
    st.info("Select a single committee to see detailed insights (large donations, momentum trends, top donors)")

with st.spinner("Analyzing data for insights..."):
    insights = generate_smart_insights(df_hash, df, single_committee_mode=single_committee_mode)

if insights:
    insight_display = {
        "alert": st.error,
        "warning": st.warning,
        "positive": st.success,
        "info": st.info
    }
    for insight in insights:
        display_fn = insight_display.get(insight["type"], st.info)
        display_fn(f"**{insight['title']}**: {insight['message']}")
elif single_committee_mode:
    st.info("No significant patterns detected in current data")


# =============================================================================
# COMMITTEE COMPARISON
# =============================================================================

if len(selected_committees) >= 2 and "Recipient Committee" in df.columns:
    with st.expander("Committee Comparison", expanded=False):
        st.subheader("Side-by-Side Committee Analysis")

        # Compute comparison stats using cached function
        if "Amount" in df.columns:
            comparison_stats = get_comparison_stats(df_hash, df)

            st.dataframe(
                comparison_stats.style.format({
                    "Total $": "${:,.2f}",
                    "# Contributions": "{:,}",
                    "Avg $": "${:,.2f}",
                    "# Donors": "{:,}"
                }),
                width="stretch"
            )

        # Time series overlay
        if "Start Date" in df.columns:
            st.subheader("Contribution Trends Over Time")

            fig = go.Figure()
            df_with_dates = df[df["Start Date"].notna()]

            for idx, committee in enumerate(selected_committees):
                committee_df = df_with_dates[df_with_dates["Recipient Committee"] == committee]

                if len(committee_df) > 0:
                    daily_data = (
                        committee_df.groupby(committee_df["Start Date"].dt.date)["Amount"]
                        .sum()
                        .reset_index()
                    )
                    daily_data.columns = ["Date", "Amount"]

                    fig.add_trace(go.Scatter(
                        x=daily_data["Date"],
                        y=daily_data["Amount"],
                        mode='lines+markers',
                        name=committee,
                        line=dict(color=COMPARISON_COLORS[idx % len(COMPARISON_COLORS)], width=2)
                    ))

            fig.update_layout(
                title="Daily Contribution Amount by Committee",
                xaxis_title="Date",
                yaxis_title="Total Amount ($)",
                hovermode="x unified",
                height=500
            )
            create_downloadable_chart(fig, "committee_comparison_timeline", filter_context, "comparison_timeline")


# =============================================================================
# CONTRIBUTIONS BY COMMITTEE
# =============================================================================

if not selected_committees and "Recipient Committee" in df.columns and "Amount" in df.columns:
    st.header("Contributions by Committee")

    committee_stats = get_committee_stats(df_hash, df)
    committee_stats.columns = ["Total Amount", "Number of Contributions", "Average Amount"]
    committee_stats = committee_stats.nlargest(15, "Total Amount").reset_index()

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            committee_stats,
            x="Total Amount",
            y="Recipient Committee",
            orientation="h",
            title="Top 15 Committees by Total Contributions",
            labels={"Total Amount": "Total Amount ($)", "Recipient Committee": "Committee"}
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "contributions_by_committee", filter_context, "committee")

    with col2:
        st.dataframe(
            committee_stats.set_index("Recipient Committee").style.format({
                "Total Amount": "${:,.2f}",
                "Number of Contributions": "{:,.0f}",
                "Average Amount": "${:,.2f}"
            }),
            width="stretch",
            height=500
        )


# =============================================================================
# CONTRIBUTION AMOUNT DISTRIBUTION
# =============================================================================

st.header("Contribution Amount Distribution")

if "Amount" in df.columns:
    df_amounts = df[df["Amount"] > 0].copy()

    if len(df_amounts) > 0:
        df_amounts["Amount Range"] = pd.cut(
            df_amounts["Amount"],
            bins=AMOUNT_BINS,
            labels=AMOUNT_LABELS,
            right=False
        )

        amount_dist = (
            df_amounts.groupby("Amount Range", observed=True)
            .agg({"Amount": ["sum", "count"]})
            .reset_index()
        )
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
            create_downloadable_chart(fig, "contribution_count_by_range", filter_context, "amount_count")

        with col2:
            fig = px.bar(
                amount_dist,
                x="Amount Range",
                y="Total Amount",
                title="Total Contribution Amount by Range",
                labels={"Total Amount": "Total Amount ($)"}
            )
            create_downloadable_chart(fig, "contribution_total_by_range", filter_context, "amount_total")


# =============================================================================
# GEOGRAPHIC VISUALIZATIONS
# =============================================================================

st.header("Geographic Distribution")

if "Contributor City" in df.columns and "Contributor State" in df.columns and "Amount" in df.columns:
    # US Map
    st.subheader("United States Contribution Map (by City)")

    # Use cached aggregation
    city_state_data = get_city_state_stats(df_hash, df, top_n=100)

    # Add coordinates using vectorized apply instead of iterrows
    city_coords_cache = load_city_coordinates()
    city_state_data["coords"] = city_state_data.apply(
        lambda row: city_coords_cache.get(f"{row['Contributor City']}, {row['Contributor State']}"),
        axis=1
    )
    city_state_data = city_state_data[city_state_data["coords"].notna()]

    if len(city_state_data) > 0:
        city_state_data[["lat", "lon"]] = pd.DataFrame(
            city_state_data["coords"].tolist(),
            index=city_state_data.index
        )
        city_state_data["City, State"] = city_state_data["Contributor City"] + ", " + city_state_data["Contributor State"]

        fig = px.scatter_geo(
            city_state_data,
            lat="lat",
            lon="lon",
            size="Amount",
            hover_name="City, State",
            hover_data={
                "Amount": ":$,.2f",
                "Contributor Name": ":,",
                "lat": False,
                "lon": False
            },
            labels={"Contributor Name": "Unique Donors"},
            title=f"Top {len(city_state_data)} US Cities by Contribution Amount",
            scope="usa",
            size_max=40
        )
        fig.update_layout(height=600, geo=dict(projection_type="albers usa"))
        create_downloadable_chart(fig, "us_city_contribution_map", filter_context, "us_map")
    else:
        st.warning("No city data with known coordinates found for mapping")

    # California Map - use cached aggregation
    ca_city_data = get_ca_city_stats(df_hash, df, top_n=50)
    if len(ca_city_data) > 0:
        st.subheader("California Contribution Map (by City)")

        # Add coordinates using vectorized approach
        ca_city_data["coords"] = ca_city_data["Contributor City"].apply(
            lambda city: city_coords_cache.get(f"{city}, CA")
        )
        ca_city_data = ca_city_data[ca_city_data["coords"].notna()]

        if len(ca_city_data) > 0:
            ca_city_data[["lat", "lon"]] = pd.DataFrame(
                ca_city_data["coords"].tolist(),
                index=ca_city_data.index
            )

            fig = px.scatter_geo(
                ca_city_data,
                lat="lat",
                lon="lon",
                size="Amount",
                hover_name="Contributor City",
                hover_data={
                    "Amount": ":$,.2f",
                    "Contributor Name": ":,",
                    "lat": False,
                    "lon": False
                },
                labels={"Contributor Name": "Unique Donors"},
                title=f"Top {len(ca_city_data)} California Cities by Contribution Amount",
                scope="usa",
                size_max=50
            )
            fig.update_geos(center=dict(lat=37, lon=-119), projection_scale=6)
            fig.update_layout(height=600)
            create_downloadable_chart(fig, "california_city_contribution_map", filter_context, "ca_map")

            # Bar chart for CA cities
            st.subheader("Top California Cities")
            fig = px.bar(
                ca_city_data.head(15),
                x="Amount",
                y="Contributor City",
                orientation="h",
                title="Top 15 California Cities by Contribution Amount"
            )
            fig.update_layout(height=500)
            create_downloadable_chart(fig, "california_cities_bar", filter_context, "ca_cities")
        else:
            st.warning("No California city data with known coordinates found for mapping")


# =============================================================================
# TOP LOCATIONS
# =============================================================================

st.header("Top Contributing Locations")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 15 Cities")
    if "Contributor City" in df.columns and "Amount" in df.columns:
        city_stats = get_city_stats(df_hash, df, top_n=15)

        fig = px.bar(
            city_stats,
            x="Total Amount",
            y="City",
            orientation="h",
            title="Top 15 Cities by Contribution Amount",
            labels={"Total Amount": "Total Amount ($)"}
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "top_cities", filter_context, "top_cities")

with col2:
    st.subheader("Top 15 States")
    if "Contributor State" in df.columns and "Amount" in df.columns:
        state_stats = get_state_stats(df_hash, df, top_n=15)

        fig = px.bar(
            state_stats,
            x="Total Amount",
            y="State",
            orientation="h",
            title="Top 15 States by Contribution Amount",
            labels={"Total Amount": "Total Amount ($)"}
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "top_states", filter_context, "top_states")


# =============================================================================
# TIME SERIES ANALYSIS
# =============================================================================

st.header("Contributions Over Time")

if "Start Date" in df.columns and "Amount" in df.columns:
    daily_contributions = get_daily_contributions(df_hash, df)

    if len(daily_contributions) > 0:
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
            create_downloadable_chart(fig, "daily_amounts", filter_context, "daily_amounts")

        with col2:
            fig = px.line(
                daily_contributions,
                x="Date",
                y="Number of Contributions",
                title="Daily Number of Contributions",
                labels={"Number of Contributions": "Count"}
            )
            fig.update_traces(line_color='#ff7f0e', line_width=2)
            create_downloadable_chart(fig, "daily_counts", filter_context, "daily_counts")

        # Monthly aggregation - use cached function
        monthly_contributions = get_monthly_contributions(df_hash, df)

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
        create_downloadable_chart(fig, "monthly_contributions", filter_context, "monthly")


# =============================================================================
# ADDITIONAL INSIGHTS
# =============================================================================

st.header("Additional Insights")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 20 Contributors")
    if "Contributor Name" in df.columns and "Amount" in df.columns:
        top_contributors = get_top_contributors(df_hash, df, top_n=20)

        st.dataframe(
            top_contributors.style.format({"Total Amount": "${:,.2f}"}),
            width="stretch",
            height=400
        )

with col2:
    st.subheader("Top 15 Occupations")
    if "Contributor Occupation" in df.columns and "Amount" in df.columns:
        occupation_stats = get_occupation_stats(df_hash, df, top_n=15)

        if len(occupation_stats) > 0:
            fig = px.bar(
                occupation_stats,
                x="Total Amount",
                y="Occupation",
                orientation="h",
                title="Top 15 Occupations by Contribution Amount"
            )
            fig.update_layout(height=400)
            create_downloadable_chart(fig, "top_occupations", filter_context, "occupations")
        else:
            st.info("No occupation data available")


# =============================================================================
# EXPORT & REPORTS
# =============================================================================

st.header("Export & Reports")

# CSV Exports
st.subheader("CSV Exports")
col1, col2 = st.columns(2)

with col1:
    try:
        csv_data = df.to_csv(index=False).encode('utf-8', errors='replace')
        st.download_button(
            label="Download Filtered Dataset (CSV)",
            data=csv_data,
            file_name=f"contributions_filtered_{len(df)}_records_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error generating CSV: {e}")

with col2:
    date_range_str = "N/A"
    if "Start Date" in df.columns:
        min_dt = df["Start Date"].min()
        max_dt = df["Start Date"].max()
        if pd.notna(min_dt) and pd.notna(max_dt):
            date_range_str = f"{min_dt} to {max_dt}"

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
            date_range_str
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

st.divider()

# PDF Report Generator
st.subheader("Custom PDF Report")

with st.expander("Select Charts for PDF Report", expanded=False):
    st.write("**Select which charts to include in your PDF report:**")

    available_charts = {
        "committee": "Committee Breakdown",
        "amount_count": "Amount Distribution (Count)",
        "amount_total": "Amount Distribution (Total)",
        "us_map": "US Contribution Map",
        "ca_map": "California Contribution Map",
        "ca_cities": "Top California Cities",
        "top_cities": "Top 15 Cities",
        "top_states": "Top 15 States",
        "daily_amounts": "Daily Contribution Amounts",
        "daily_counts": "Daily Contribution Count",
        "monthly": "Monthly Contributions",
        "occupations": "Top Occupations"
    }

    btn_col1, btn_col2, _ = st.columns([1, 1, 2])

    if "pdf_chart_selections" not in st.session_state:
        st.session_state.pdf_chart_selections = {}

    if btn_col1.button("Select All Available", key="select_all_pdf_charts"):
        if "pdf_charts" in st.session_state:
            for key in available_charts:
                if key in st.session_state.pdf_charts:
                    st.session_state.pdf_chart_selections[key] = True
        st.rerun()

    if btn_col2.button("Deselect All", key="deselect_all_pdf_charts"):
        st.session_state.pdf_chart_selections = {k: False for k in available_charts}
        st.rerun()

    col1, col2, col3 = st.columns(3)
    selected_for_pdf = {}

    for idx, (key, name) in enumerate(available_charts.items()):
        col = [col1, col2, col3][idx % 3]
        with col:
            is_available = "pdf_charts" in st.session_state and key in st.session_state.pdf_charts

            if key not in st.session_state.pdf_chart_selections:
                st.session_state.pdf_chart_selections[key] = is_available

            checkbox_value = st.session_state.pdf_chart_selections.get(key, False) and is_available

            checked = st.checkbox(
                name,
                value=checkbox_value,
                key=f"pdf_{key}",
                disabled=not is_available
            )

            st.session_state.pdf_chart_selections[key] = checked

            if checked and is_available:
                selected_for_pdf[key] = name

    st.divider()

    if selected_for_pdf:
        if st.button("Generate PDF Report", type="primary"):
            with st.spinner("Generating PDF report..."):
                try:
                    summary_stats = {
                        "Total Contributions": f"${total_contributions:,.2f}",
                        "Number of Contributions": f"{num_contributions:,}",
                        "Average Contribution": f"${avg_contribution:,.2f}",
                        "Unique Donors": f"{unique_donors:,}",
                    }

                    filter_info = ' | '.join(active_filters) if active_filters else "No filters applied"

                    pdf_bytes = generate_pdf_report(
                        selected_for_pdf,
                        summary_stats,
                        filter_info,
                        st.session_state.pdf_charts
                    )

                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"contribution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                    st.success("PDF generated successfully!")
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")
                    st.caption("Make sure kaleido, reportlab, and Pillow are installed.")
    else:
        st.info("Select at least one chart to generate a PDF report")

    st.caption("Charts must be rendered on the page before they can be included in the PDF")

st.divider()
st.caption("Tip: Use the camera icon in the top-right of any chart to download it as a PNG image")
