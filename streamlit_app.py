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


def get_filter_context(selected_committees, date_min, date_max, amount_min, amount_max,
                       contributor_search, selected_states) -> tuple:
    """Generate filter context for chart titles and filenames."""
    title_parts = []
    filename_parts = []

    if selected_committees:
        if len(selected_committees) == 1:
            title_parts.append(f"{selected_committees[0]}")
            filename_parts.append(selected_committees[0].replace(' ', '_').replace(',', ''))
        else:
            title_parts.append(f"{len(selected_committees)} Committees")
            filename_parts.append(f"{len(selected_committees)}_committees")

    if date_min and date_max:
        if date_min != date_max:
            title_parts.append(f"{date_min} to {date_max}")
            filename_parts.append(f"{date_min}_to_{date_max}")

    if amount_min is not None and amount_max is not None:
        title_parts.append(f"${amount_min:,.0f}-${amount_max:,.0f}")
        filename_parts.append(f"{int(amount_min)}_to_{int(amount_max)}")

    if contributor_search:
        title_parts.append(f"'{contributor_search}'")
        filename_parts.append(contributor_search.replace(' ', '_'))

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


def create_downloadable_chart(fig, base_title: str, filter_context: tuple = ("", "")):
    """Display a Plotly chart with download button and filter context in title."""
    title_suffix, filename_suffix = filter_context

    # Update chart title to include filter context
    if title_suffix:
        fig.update_layout(title=fig.layout.title.text + title_suffix)

    # Configure chart to show download options
    config = {
        'toImageButtonOptions': {
            'format': 'png',
            'filename': base_title.replace(' ', '_').lower() + filename_suffix,
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

    # Committee filter (checkboxes)
    selected_committees = []
    if "Recipient Committee" in df_full.columns:
        committees = sorted(df_full["Recipient Committee"].dropna().unique().tolist())

        with st.expander("📋 Select Committee(s)", expanded=True):
            st.caption(f"{len(committees)} committees available")

            # Add "Select All" / "Deselect All" buttons
            col1, col2 = st.columns(2)
            select_all = col1.button("Select All", key="select_all_committees")
            deselect_all = col2.button("Deselect All", key="deselect_all_committees")

            # Initialize session state for checkboxes
            if "committee_selections" not in st.session_state:
                st.session_state.committee_selections = {c: False for c in committees}

            # Handle select/deselect all - update all and trigger rerun
            if select_all:
                st.session_state.committee_selections = {c: True for c in committees}
                st.rerun()
            if deselect_all:
                st.session_state.committee_selections = {c: False for c in committees}
                st.rerun()

            # Show checkboxes for each committee
            for committee in committees:
                if committee not in st.session_state.committee_selections:
                    st.session_state.committee_selections[committee] = False

                # Checkbox updates session state on change
                checked = st.checkbox(
                    committee,
                    value=st.session_state.committee_selections[committee],
                    key=f"committee_checkbox_{committee}"
                )
                # Update session state
                st.session_state.committee_selections[committee] = checked

                if checked:
                    selected_committees.append(committee)

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
        valid_amounts = df_full[df_full["Amount"] >= 0]["Amount"].dropna()
        if len(valid_amounts) > 0:
            min_amt = max(0.0, float(valid_amounts.min()))
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

# Generate filter context for chart titles and filenames
filter_context = get_filter_context(
    selected_committees,
    date_min,
    date_max,
    amount_min,
    amount_max,
    contributor_search,
    selected_states
)


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
        create_downloadable_chart(fig, "contributions_by_committee", filter_context)

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
        create_downloadable_chart(fig, "contribution_count_by_range", filter_context)

    with col2:
        fig = px.bar(
            amount_dist,
            x="Amount Range",
            y="Total Amount",
            title="Total Contribution Amount by Range",
            labels={"Total Amount": "Total Amount ($)"}
        )
        create_downloadable_chart(fig, "contribution_total_by_range", filter_context)


# =============================================================================
# GEOGRAPHIC VISUALIZATIONS - MAPS
# =============================================================================
st.header("🗺️ Geographic Distribution")

# Simple geocoding dictionary for common cities (lat, lon)
CITY_COORDS = {
    # California cities
    "Los Angeles, CA": (34.0522, -118.2437),
    "San Francisco, CA": (37.7749, -122.4194),
    "San Diego, CA": (32.7157, -117.1611),
    "San Jose, CA": (37.3382, -121.8863),
    "Sacramento, CA": (38.5816, -121.4944),
    "Oakland, CA": (37.8044, -122.2712),
    "Fresno, CA": (36.7378, -119.7871),
    "Long Beach, CA": (33.7701, -118.1937),
    "Bakersfield, CA": (35.3733, -119.0187),
    "Anaheim, CA": (33.8366, -117.9143),
    "Santa Ana, CA": (33.7455, -117.8677),
    "Riverside, CA": (33.9533, -117.3962),
    "Stockton, CA": (37.9577, -121.2908),
    "Irvine, CA": (33.6846, -117.8265),
    "Chula Vista, CA": (32.6401, -117.0842),
    "Fremont, CA": (37.5485, -121.9886),
    "San Bernardino, CA": (34.1083, -117.2898),
    "Modesto, CA": (37.6391, -120.9969),
    "Fontana, CA": (34.0922, -117.4350),
    "Oxnard, CA": (34.1975, -119.1771),
    "Moreno Valley, CA": (33.9425, -117.2297),
    "Huntington Beach, CA": (33.6603, -117.9992),
    "Glendale, CA": (34.1425, -118.2551),
    "Santa Clarita, CA": (34.3917, -118.5426),
    "Garden Grove, CA": (33.7746, -117.9415),
    "Oceanside, CA": (33.1959, -117.3795),
    "Rancho Cucamonga, CA": (34.1064, -117.5931),
    "Ontario, CA": (34.0633, -117.6509),
    "Lancaster, CA": (34.6868, -118.1542),
    "Elk Grove, CA": (38.4088, -121.3716),
    "Palmdale, CA": (34.5794, -118.1165),
    "Corona, CA": (33.8753, -117.5664),
    "Salinas, CA": (36.6777, -121.6555),
    "Pomona, CA": (34.0551, -117.7500),
    "Hayward, CA": (37.6688, -122.0808),
    "Escondido, CA": (33.1192, -117.0864),
    "Torrance, CA": (33.8358, -118.3406),
    "Sunnyvale, CA": (37.3688, -122.0363),
    "Orange, CA": (33.7879, -117.8531),
    "Fullerton, CA": (33.8704, -117.9242),
    "Pasadena, CA": (34.1478, -118.1445),
    "Thousand Oaks, CA": (34.1706, -118.8376),
    "Visalia, CA": (36.3302, -119.2921),
    "Simi Valley, CA": (34.2694, -118.7815),
    "Concord, CA": (37.9780, -122.0311),
    "Roseville, CA": (38.7521, -121.2880),
    "Santa Rosa, CA": (38.4404, -122.7141),
    "Victorville, CA": (34.5362, -117.2928),
    "Vallejo, CA": (38.1041, -122.2566),
    "Berkeley, CA": (37.8715, -122.2730),
    "El Monte, CA": (34.0686, -118.0276),
    "Downey, CA": (33.9401, -118.1332),
    "Costa Mesa, CA": (33.6411, -117.9187),
    "Inglewood, CA": (33.9617, -118.3531),
    "Carlsbad, CA": (33.1581, -117.3506),
    "San Buenaventura, CA": (34.2746, -119.2290),
    "Fairfield, CA": (38.2494, -122.0400),
    "West Covina, CA": (34.0686, -117.9390),
    "Murrieta, CA": (33.5539, -117.2139),
    "Richmond, CA": (37.9358, -122.3477),
    "Norwalk, CA": (33.9022, -118.0817),
    "Antioch, CA": (38.0049, -121.8058),
    "Temecula, CA": (33.4936, -117.1484),
    "Burbank, CA": (34.1808, -118.3090),
    "Daly City, CA": (37.6879, -122.4702),
    "Rialto, CA": (34.1064, -117.3703),
    "Santa Maria, CA": (34.9530, -120.4357),
    "El Cajon, CA": (32.7948, -116.9625),
    "San Mateo, CA": (37.5630, -122.3255),
    "Clovis, CA": (36.8252, -119.7029),
    "Compton, CA": (33.8958, -118.2201),
    "Jurupa Valley, CA": (33.9971, -117.4854),
    "Vista, CA": (33.2000, -117.2425),
    "South Gate, CA": (33.9548, -118.2120),
    "Mission Viejo, CA": (33.6000, -117.6720),
    "Vacaville, CA": (38.3566, -121.9877),
    "Carson, CA": (33.8314, -118.2820),
    "Hesperia, CA": (34.4264, -117.3009),
    "Santa Monica, CA": (34.0195, -118.4912),
    "Westminster, CA": (33.7513, -117.9940),
    "Redding, CA": (40.5865, -122.3917),
    "Santa Barbara, CA": (34.4208, -119.6982),
    "Chico, CA": (39.7285, -121.8375),
    "Newport Beach, CA": (33.6189, -117.9289),
    "San Leandro, CA": (37.7249, -122.1561),
    "San Marcos, CA": (33.1434, -117.1661),
    "Whittier, CA": (33.9792, -118.0328),
    "Hawthorne, CA": (33.9164, -118.3526),
    "Citrus Heights, CA": (38.7071, -121.2811),
    "Tracy, CA": (37.7397, -121.4252),
    "Alhambra, CA": (34.0953, -118.1270),
    "Livermore, CA": (37.6819, -121.7680),
    "Buena Park, CA": (33.8675, -117.9981),
    "Menifee, CA": (33.6803, -117.1859),
    "Hemet, CA": (33.7475, -116.9719),
    "Lakewood, CA": (33.8536, -118.1339),
    "Merced, CA": (37.3022, -120.4830),
    "Chino, CA": (34.0122, -117.6889),
    "Indio, CA": (33.7206, -116.2156),
    "Redwood City, CA": (37.4852, -122.2364),
    "Lake Forest, CA": (33.6469, -117.6892),
    "Napa, CA": (38.2975, -122.2869),
    "Tustin, CA": (33.7458, -117.8261),
    "Bellflower, CA": (33.8817, -118.1170),
    "Mountain View, CA": (37.3861, -122.0839),
    "Chino Hills, CA": (33.9898, -117.7320),
    "Baldwin Park, CA": (34.0853, -117.9609),
    "Alameda, CA": (37.7652, -122.2416),
    "Upland, CA": (34.0975, -117.6484),
    "San Ramon, CA": (37.7799, -121.9780),
    "Folsom, CA": (38.6779, -121.1760),
    "Pleasanton, CA": (37.6624, -121.8747),
    "Union City, CA": (37.5933, -122.0438),
    "Perris, CA": (33.7825, -117.2286),
    "Manteca, CA": (37.7974, -121.2161),
    "Lynwood, CA": (33.9303, -118.2115),
    "Apple Valley, CA": (34.5008, -117.1859),
    "Redlands, CA": (34.0556, -117.1825),
    "Turlock, CA": (37.4947, -120.8466),
    "Milpitas, CA": (37.4283, -121.9066),
    "Redondo Beach, CA": (33.8492, -118.3884),
    "Rancho Cordova, CA": (38.5891, -121.3027),
    "Yorba Linda, CA": (33.8886, -117.8131),
    "Palo Alto, CA": (37.4419, -122.1430),
    "Davis, CA": (38.5449, -121.7405),
    "Camarillo, CA": (34.2164, -119.0376),
    "Walnut Creek, CA": (37.9101, -122.0652),
    "Pittsburg, CA": (38.0280, -121.8847),
    "South San Francisco, CA": (37.6547, -122.4077),
    "Yuba City, CA": (39.1404, -121.6169),
    "San Clemente, CA": (33.4270, -117.6120),
    "Laguna Niguel, CA": (33.5225, -117.7076),
    "Pico Rivera, CA": (33.9830, -118.0967),
    "Montebello, CA": (34.0165, -118.1137),
    "Lodi, CA": (38.1302, -121.2725),
    "Madera, CA": (36.9613, -120.0607),
    "Santa Cruz, CA": (36.9741, -122.0308),
    "La Habra, CA": (33.9319, -117.9462),
    "Encinitas, CA": (33.0370, -117.2920),
    "Monterey Park, CA": (34.0625, -118.1228),
    "Tulare, CA": (36.2077, -119.3473),
    "Cupertino, CA": (37.3230, -122.0322),
    # Major US cities
    "New York, NY": (40.7128, -74.0060),
    "Chicago, IL": (41.8781, -87.6298),
    "Houston, TX": (29.7604, -95.3698),
    "Phoenix, AZ": (33.4484, -112.0740),
    "Philadelphia, PA": (39.9526, -75.1652),
    "San Antonio, TX": (29.4241, -98.4936),
    "Dallas, TX": (32.7767, -96.7970),
    "Austin, TX": (30.2672, -97.7431),
    "Jacksonville, FL": (30.3322, -81.6557),
    "Fort Worth, TX": (32.7555, -97.3308),
    "Columbus, OH": (39.9612, -82.9988),
    "Charlotte, NC": (35.2271, -80.8431),
    "Indianapolis, IN": (39.7684, -86.1581),
    "Seattle, WA": (47.6062, -122.3321),
    "Denver, CO": (39.7392, -104.9903),
    "Washington, DC": (38.9072, -77.0369),
    "Boston, MA": (42.3601, -71.0589),
    "El Paso, TX": (31.7619, -106.4850),
    "Nashville, TN": (36.1627, -86.7816),
    "Detroit, MI": (42.3314, -83.0458),
    "Oklahoma City, OK": (35.4676, -97.5164),
    "Portland, OR": (45.5152, -122.6784),
    "Las Vegas, NV": (36.1699, -115.1398),
    "Memphis, TN": (35.1495, -90.0490),
    "Louisville, KY": (38.2527, -85.7585),
    "Baltimore, MD": (39.2904, -76.6122),
    "Milwaukee, WI": (43.0389, -87.9065),
    "Albuquerque, NM": (35.0844, -106.6504),
    "Tucson, AZ": (32.2226, -110.9747),
    "Mesa, AZ": (33.4152, -111.8315),
    "Kansas City, MO": (39.0997, -94.5786),
    "Atlanta, GA": (33.7490, -84.3880),
    "Miami, FL": (25.7617, -80.1918),
    "Raleigh, NC": (35.7796, -78.6382),
    "Omaha, NE": (41.2565, -95.9345),
    "Minneapolis, MN": (44.9778, -93.2650),
    "Tulsa, OK": (36.1540, -95.9928),
    "Cleveland, OH": (41.4993, -81.6944),
    "Wichita, KS": (37.6872, -97.3301),
    "Arlington, TX": (32.7357, -97.1081),
    "Tampa, FL": (27.9506, -82.4572),
    "New Orleans, LA": (29.9511, -90.0715),
    "Honolulu, HI": (21.3099, -157.8581),
    "Anaheim, CA": (33.8366, -117.9143),
    "St. Louis, MO": (38.6270, -90.1994),
    "Pittsburgh, PA": (40.4406, -79.9959),
    "Cincinnati, OH": (39.1031, -84.5120),
    "Greensboro, NC": (36.0726, -79.7920),
    "Newark, NJ": (40.7357, -74.1724),
    "Plano, TX": (33.0198, -96.6989),
    "Henderson, NV": (36.0395, -114.9817),
    "Lincoln, NE": (40.8136, -96.7026),
    "Orlando, FL": (28.5383, -81.3792),
    "Jersey City, NJ": (40.7178, -74.0431),
    "Chandler, AZ": (33.3062, -111.8413),
    "Buffalo, NY": (42.8864, -78.8784),
    "Durham, NC": (35.9940, -78.8986),
    "St. Paul, MN": (44.9537, -93.0900),
    "Madison, WI": (43.0731, -89.4012),
    "Lubbock, TX": (33.5779, -101.8552),
    "Scottsdale, AZ": (33.4942, -111.9261),
    "Reno, NV": (39.5296, -119.8138),
    "Virginia Beach, VA": (36.8529, -75.9780),
}


def get_city_coords(city: str, state: str) -> tuple:
    """Get coordinates for a city, with fallback to state center."""
    key = f"{city}, {state}"
    if key in CITY_COORDS:
        return CITY_COORDS[key]
    # Return None if not found, we'll filter these out
    return None


if "Contributor City" in df.columns and "Contributor State" in df.columns and "Amount" in df.columns:

    # US Map - City-level scatter points
    st.subheader("United States Contribution Map (by City)")

    city_state_data = (
        df.groupby(["Contributor City", "Contributor State"])
        .agg({
            "Amount": "sum",
            "Contributor Name": "nunique"
        })
        .reset_index()
        .sort_values("Amount", ascending=False)
        .head(100)  # Top 100 cities
    )

    # Add coordinates
    city_state_data["coords"] = city_state_data.apply(
        lambda row: get_city_coords(row["Contributor City"], row["Contributor State"]),
        axis=1
    )

    # Filter out cities without coordinates
    city_state_data = city_state_data[city_state_data["coords"].notna()].copy()
    city_state_data[["lat", "lon"]] = pd.DataFrame(
        city_state_data["coords"].tolist(),
        index=city_state_data.index
    )
    city_state_data["City, State"] = city_state_data["Contributor City"] + ", " + city_state_data["Contributor State"]

    if len(city_state_data) > 0:
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
        create_downloadable_chart(fig, "us_city_contribution_map", filter_context)
    else:
        st.warning("No city data with known coordinates found for mapping")

    # California Map (if CA data exists)
    ca_data = df[df["Contributor State"] == "CA"]
    if len(ca_data) > 0 and "Contributor City" in df.columns:
        st.subheader("California Contribution Map (by City)")

        ca_city_data = (
            ca_data.groupby("Contributor City")
            .agg({
                "Amount": "sum",
                "Contributor Name": "nunique"
            })
            .reset_index()
            .sort_values("Amount", ascending=False)
            .head(50)  # Top 50 CA cities
        )

        # Add coordinates for CA cities
        ca_city_data["coords"] = ca_city_data["Contributor City"].apply(
            lambda city: get_city_coords(city, "CA")
        )

        # Filter out cities without coordinates
        ca_city_data = ca_city_data[ca_city_data["coords"].notna()].copy()
        ca_city_data[["lat", "lon"]] = pd.DataFrame(
            ca_city_data["coords"].tolist(),
            index=ca_city_data.index
        )

        if len(ca_city_data) > 0:
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
            fig.update_geos(
                center=dict(lat=37, lon=-119),
                projection_scale=6
            )
            fig.update_layout(height=600)
            create_downloadable_chart(fig, "california_city_contribution_map", filter_context)
        else:
            st.warning("No California city data with known coordinates found for mapping")

        # Also show bar chart for CA cities
        st.subheader("Top California Cities")
        fig = px.bar(
            ca_city_data.head(15),
            x="Amount",
            y="Contributor City",
            orientation="h",
            title="Top 15 California Cities by Contribution Amount"
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "california_cities_bar", filter_context)


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
        create_downloadable_chart(fig, "top_cities", filter_context)

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
        create_downloadable_chart(fig, "top_states", filter_context)


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
            create_downloadable_chart(fig, "daily_amounts", filter_context)

        with col2:
            fig = px.line(
                daily_contributions,
                x="Date",
                y="Number of Contributions",
                title="Daily Number of Contributions",
                labels={"Number of Contributions": "Count"}
            )
            fig.update_traces(line_color='#ff7f0e', line_width=2)
            create_downloadable_chart(fig, "daily_counts", filter_context)

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
        create_downloadable_chart(fig, "monthly_contributions", filter_context)


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
        create_downloadable_chart(fig, "top_occupations", filter_context)


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
