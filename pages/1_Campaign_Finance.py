from __future__ import annotations

import io
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
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
from streamlit.runtime.uploaded_file_manager import UploadedFile


DEFAULT_LANGUAGE = "en"
TRANSLATIONS = {
    "es": {
        "**Expected Field** (Required fields marked with *)": "**Campo esperado** (los campos obligatorios tienen *)",
        "**Select which charts to include in your PDF report:**": "**Selecciona qué gráficos incluir en tu informe PDF:**",
        "**Your CSV Column**": "**Columna de tu CSV**",
        "Amount Distribution (Count)": "Distribución de montos (cantidad)",
        "Amount Distribution (Total)": "Distribución de montos (total)",
        "Amount Range ($)": "Rango de monto ($)",
        "Amount: {low} to {high}": "Monto: {low} a {high}",
        "Average Contribution": "Contribución promedio",
        "Avg Union Contribution": "Contribución sindical promedio",
        "Back to Home": "Volver al inicio",
        "California Contribution Map": "Mapa de contribuciones de California",
        "California Contribution Map (by City)": "Mapa de contribuciones de California (por ciudad)",
        "Case-insensitive search in contributor names": "Búsqueda que no distingue mayúsculas/minúsculas en nombres de contribuyentes",
        "Committee Breakdown": "Desglose por comité",
        "Committee": "Comité",
        "Committees: {value}": "Comités: {value}",
        "{count} Committees": "{count} comités",
        "Committee or candidate receiving contribution": "Comité o candidato que recibe la contribución",
        "Contribution Trends Over Time": "Tendencias de contribuciones en el tiempo",
        "Contribution amount (numeric)": "Monto de la contribución (numérico)",
        "Contribution date": "Fecha de contribución",
        "Contributor: '{value}'": "Contribuyente: '{value}'",
        "Daily Contribution Amount by Committee": "Monto diario por comité",
        "Daily Contribution Amounts": "Montos diarios de contribución",
        "Daily Contribution Count": "Conteo diario de contribuciones",
        "Daily Number of Contributions": "Número diario de contribuciones",
        "Date": "Fecha",
        "Date Range": "Rango de fechas",
        "Dates: {start} to {end}": "Fechas: {start} a {end}",
        "{start} to {end}": "{start} a {end}",
        "Declining Activity": "Actividad en descenso",
        "Deselect All": "Deseleccionar todo",
        "Enable to load every row in the CSV. Disable to cap the number of rows for faster previews.":
            "Activa para cargar todas las filas del CSV. Desactiva para limitar filas y obtener vistas previas más rápidas.",
        "Disable 'Load entire file' to limit how many rows are read.": "Desactiva \"Cargar todo el archivo\" para limitar cuántas filas se leen.",
        "Employer/Occupation data not available for union detection": "No hay datos de empleador/ocupación para detectar sindicatos",
        "Error generating PDF: {error}": "Error al generar el PDF: {error}",
        "Error previewing mapped data: {error}": "Error al previsualizar los datos mapeados: {error}",
        "Error rendering chart: {error}": "Error al renderizar el gráfico: {error}",
        "Failed to apply column mapping: {error}": "Error al aplicar el mapeo de columnas: {error}",
        "Failed to load CSV: {error}": "Error al cargar el CSV: {error}",
        "Filter by State(s)": "Filtrar por estado(s)",
        "Filter by contribution amount": "Filtra por monto de contribución",
        "Filter contributions by date": "Filtra las contribuciones por fecha",
        "Generating PDF report...": "Generando informe PDF...",
        "Geographic Concentration": "Concentración geográfica",
        "Generated: {timestamp}": "Generado: {timestamp}",
        "Increasing Momentum": "Impulso creciente",
        "Large Donations Detected": "Se detectaron donaciones grandes",
        "Leave empty to load all rows": "Déjalo vacío para cargar todas las filas",
        "Leave empty to show all states": "Déjalo vacío para mostrar todos los estados",
        "Load entire file": "Cargar todo el archivo",
        "Loading CSV...": "Cargando CSV...",
        "Make sure all required packages are installed: kaleido, reportlab, Pillow":
            "Asegúrate de que estén instalados los paquetes requeridos: kaleido, reportlab, Pillow",
        "Map to": "Asignar a",
        "Map your CSV columns to the expected format. We've auto-detected likely matches.":
            "Asigna tus columnas del CSV al formato esperado. Detectamos posibles coincidencias automáticamente.",
        "Max rows to load": "Filas máximas a cargar",
        "Max rows to load (blank = all)": "Filas máximas a cargar (vacío = todas)",
        "Monthly Contributions: Amount vs Count": "Contribuciones mensuales: monto vs cantidad",
        "Monthly Contributions": "Contribuciones mensuales",
        "Month": "Mes",
        "N/A": "N/D",
        "No filters applied": "Sin filtros aplicados",
        "No city data with known coordinates found for mapping": "No se encontraron ciudades con coordenadas conocidas para el mapa",
        "No California city data with known coordinates found for mapping": "No se encontraron ciudades de CA con coordenadas conocidas para el mapa",
        "No significant patterns detected in current data": "No se detectaron patrones significativos en los datos actuales",
        "Non-Union": "No sindical",
        "Number of Contributions": "Número de contribuciones",
        "Number of Contributions by Amount Range": "Número de contribuciones por rango de monto",
        "Or enter a CSV path": "O ingresa una ruta de CSV",
        "Please map all required fields (*) to continue.": "Asigna todos los campos obligatorios (*) para continuar.",
        "Recent contributions down {pct}% from earlier period": "Las contribuciones recientes bajaron {pct}% frente al periodo anterior",
        "Recent weeks show {pct}% more contributions": "Las últimas semanas muestran {pct}% más contribuciones",
        "Search Contributor Name": "Buscar nombre del contribuyente",
        "Select All": "Seleccionar todo",
        "Select All Available": "Seleccionar todo lo disponible",
        "Disable 'Load entire file' to limit how many rows are read.": "Desactiva \"Cargar todo el archivo\" para limitar cuántas filas se leen.",
        "Select at least one chart to generate a PDF report": "Selecciona al menos un gráfico para generar un informe PDF",
        "Showing {filtered} of {total} records ({percent}%)": "Mostrando {filtered} de {total} registros ({percent}%)",
        "Side-by-Side Committee Analysis": "Análisis comparativo de comités",
        "Single largest donor: {pct}% of total contributions": "Mayor donante individual: {pct}% del total de contribuciones",
        "States: {value}": "Estados: {value}",
        "{count} States": "{count} estados",
        "Summary Statistics": "Estadísticas resumidas",
        "Top 15 California Cities by Contribution Amount": "Top 15 ciudades de California por monto de contribución",
        "Top 15 Cities": "Top 15 ciudades",
        "Top 15 Cities by Contribution Amount": "Top 15 ciudades por monto de contribución",
        "Top 15 Committees by Total Contributions": "Top 15 comités por contribuciones totales",
        "Top 15 Occupations": "Top 15 ocupaciones",
        "Top 15 Occupations by Contribution Amount": "Top 15 ocupaciones por monto de contribución",
        "Top 15 States": "Top 15 estados",
        "Top 15 States by Contribution Amount": "Top 15 estados por monto de contribución",
        "Top 15 Union/Labor Organizations by Contribution Amount": "Top 15 organizaciones sindicales/laborales por monto de contribución",
        "Top 20 Contributors": "Top 20 contribuyentes",
        "Top California Cities": "Principales ciudades de California",
        "Top Donor Impact": "Impacto del mayor donante",
        "Top Occupations": "Top ocupaciones",
        "Top Union/Labor Organizations": "Principales organizaciones sindicales/laborales",
        "Top {count} California Cities by Contribution Amount": "Top {count} ciudades de California por monto de contribución",
        "Top {count} US Cities by Contribution Amount": "Top {count} ciudades de EE. UU. por monto de contribución",
        "Total Amount ($)": "Monto total ($)",
        "Total Contribution Amount by Range": "Monto total de contribuciones por rango",
        "Total Contributions": "Contribuciones totales",
        "Type": "Tipo",
        "Unique Donors": "Donantes únicos",
        "City": "Ciudad",
        "State": "Estado",
        "US Contribution Map": "Mapa de contribuciones de EE. UU.",
        "United States Contribution Map (by City)": "Mapa de contribuciones de Estados Unidos (por ciudad)",
        "Upload campaign finance CSV data to analyze contributions, donors, committees, and trends.":
            "Carga un CSV de finanzas de campaña para analizar contribuciones, donantes, comités y tendencias.",
        "Upload your campaign finance CSV to begin analysis": "Sube tu CSV de finanzas de campaña para comenzar el análisis",
        "Your CSV has {count} columns. Map them to the expected fields below.": "Tu CSV tiene {count} columnas. Asigna cada una a los campos esperados abajo.",
        "{count} committees available": "Hay {count} comités disponibles",
        "{count} contributions over {amount} (10x average)": "{count} contribuciones superiores a {amount} (10x el promedio)",
        "{pct}% of contributions from {city}": "{pct}% de las contribuciones provienen de {city}",
        "🏛️ Contributions by Committee": "🏛️ Contribuciones por comité",
        "🗺️ Column Mapping": "🗺️ Mapeo de columnas",
        "🗺️ Geographic Distribution": "🗺️ Distribución geográfica",
        "📄 CSV Exports": "📄 Exportaciones CSV",
        "📄 Download Filtered Dataset (CSV)": "📄 Descargar datos filtrados (CSV)",
        "📄 View Raw Data (first 100 rows)": "📄 Ver datos originales (primeras 100 filas)",
        "📅 Contributions Over Time": "📅 Contribuciones en el tiempo",
        "📈 Summary Statistics": "📈 Estadísticas resumidas",
        "📊 Showing all {count} records": "📊 Mostrando los {count} registros completos",
        "📋 Configure Column Mapping": "📋 Configurar mapeo de columnas",
        "📋 Select Committee(s)": "📋 Seleccionar comité(s)",
        "📥 Export & Reports": "📥 Exportaciones e informes",
        "💡 Smart Insights": "💡 Ideas inteligentes",
        "💡 Select a single committee to see detailed insights (large donations, momentum trends, top donors)":
            "💡 Selecciona un solo comité para ver información detallada (donaciones grandes, tendencias, principales donantes)",
        "💵 Contribution Amount Distribution": "💵 Distribución de montos de contribución",
        "⚙️ Configuration": "⚙️ Configuración",
        "⚖️ Committee Comparison": "⚖️ Comparación de comités",
        "🌐 Show page in Spanish": "🌐 Mostrar la página en español",
        "📍 Top Contributing Locations": "📍 Principales ubicaciones aportantes",
        "📑 Custom PDF Report": "📑 Informe PDF personalizado",
        "📊 Download Summary Report (CSV)": "📊 Descargar resumen (CSV)",
        "📄 Generate PDF Report": "📄 Generar informe PDF",
        "📄 CSV Exports": "📄 Exportaciones CSV",
        "💾 Download PDF Report": "💾 Descargar informe PDF",
        "💡 Charts must be rendered on the page before they can be included in the PDF":
            "💡 Los gráficos deben mostrarse en la página antes de poder incluirse en el PDF",
        "💡 **Tip**: Use the camera icon in the top-right of any chart to download it as a PNG image":
            "💡 Consejo: Usa el ícono de cámara en la esquina superior derecha de cualquier gráfico para descargarlo como PNG",
        "🔍 Additional Insights": "🔍 Ideas adicionales",
        "🔍 Filters": "🔍 Filtros",
        "🔎 **Active Filters:** {filters}": "🔎 **Filtros activos:** {filters}",
        "🔄 Reset to Auto-Detect": "🔄 Restablecer a autodetección",
        "⚠️ Missing required fields: {fields}": "⚠️ Faltan campos obligatorios: {fields}",
        "✅ Apply Mapping": "✅ Aplicar mapeo",
        "✅ Loaded and mapped {records} contribution records": "✅ Se cargaron y mapearon {records} registros de contribuciones",
        "✅ Mapping applied!": "✅ Mapeo aplicado",
        "✅ PDF generated successfully!": "✅ ¡PDF generado correctamente!",
        "🎨 Select Charts for PDF Report": "🎨 Seleccionar gráficos para el informe PDF",
        "👁️ Preview Mapped Data": "👁️ Vista previa de datos mapeados",
        "Campaign Contribution Analysis Report": "Informe de contribuciones de campaña",
        "<b>Filters Applied:</b> {filters}": "<b>Filtros aplicados:</b> {filters}",
        "💰 Campaign Finance Analyzer": "💰 Analizador de finanzas de campaña",
        "Upload CSV": "Subir CSV",
        "← Back to Home": "← Regresar al inicio",
        "👆 Upload a CSV file or enter a path to begin analysis": "👆 Sube un archivo CSV o ingresa una ruta para comenzar el análisis",
    }
}


def _(text: str, **kwargs) -> str:
    """Return the translated string for the current language."""
    language = st.session_state.get("language", DEFAULT_LANGUAGE)
    translated = TRANSLATIONS.get(language, {}).get(text, text)
    if kwargs:
        return translated.format(**kwargs)
    return translated


st.set_page_config(page_title="Campaign Finance | DataViz", page_icon="💰", layout="wide")

st.title(_("💰 Campaign Finance Analyzer"))
st.write(_("Upload campaign finance CSV data to analyze contributions, donors, committees, and trends."))

# Back to home button in sidebar
with st.sidebar:
    if st.button(_("← Back to Home"), key="back_to_home_top"):
        st.switch_page("Home.py")

    toggle_value = st.toggle(
        _("🌐 Show page in Spanish"),
        value=st.session_state.get("language", DEFAULT_LANGUAGE) == "es",
    )
    st.session_state.language = "es" if toggle_value else "en"

    st.divider()


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


def get_expected_columns():
    """Define expected columns with keywords for auto-detection."""
    return {
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


def auto_detect_column_mapping(df_columns: list) -> dict:
    """Auto-detect likely column mappings based on keywords."""
    expected = get_expected_columns()
    mapping = {}

    # Convert all columns to lowercase for matching
    df_columns_lower = {col: col.lower() for col in df_columns}

    for target_col, config in expected.items():
        best_match = None
        best_score = 0

        for original_col, col_lower in df_columns_lower.items():
            if original_col in mapping.values():
                continue  # Skip already mapped columns

            # Check if any keyword is in the column name
            score = sum(1 for keyword in config["keywords"] if keyword in col_lower)

            # Exact match gets highest score
            if col_lower in config["keywords"]:
                score += 10

            if score > best_score:
                best_score = score
                best_match = original_col

        if best_match and best_score > 0:
            mapping[target_col] = best_match

    return mapping


def apply_column_mapping(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Apply column mapping and parse data types."""
    # Create reverse mapping (original -> target)
    reverse_mapping = {v: k for k, v in mapping.items() if v}

    # Rename columns
    df_mapped = df.rename(columns=reverse_mapping)

    # Parse dates
    date_columns = ["Start Date", "End Date"]
    for col in date_columns:
        if col in df_mapped.columns:
            df_mapped[col] = pd.to_datetime(df_mapped[col], errors='coerce')

    # Parse amount
    if "Amount" in df_mapped.columns:
        df_mapped["Amount"] = pd.to_numeric(df_mapped["Amount"], errors='coerce')

    return df_mapped


@st.cache_data(show_spinner=False)
def load_contribution_data(path_str: str, max_rows: Optional[int] = None) -> pd.DataFrame:
    """Load contribution CSV (without mapping - raw load)."""
    df = pd.read_csv(path_str, nrows=max_rows, low_memory=False)
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
            title_parts.append(_("{count} Committees", count=len(selected_committees)))
            filename_parts.append(f"{len(selected_committees)}_committees")

    if date_min and date_max:
        if date_min != date_max:
            title_parts.append(_("{start} to {end}", start=date_min, end=date_max))
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
            title_parts.append(_("{count} States", count=len(selected_states)))
            filename_parts.append(f"{len(selected_states)}_states")

    title_suffix = f" ({' | '.join(title_parts)})" if title_parts else ""
    filename_suffix = "_" + "_".join(filename_parts) if filename_parts else ""

    return title_suffix, filename_suffix


def create_downloadable_chart(fig, base_title: str, filter_context: tuple = ("", ""), chart_key: str = None):
    """Display a Plotly chart with download button and filter context in title."""
    title_suffix, filename_suffix = filter_context

    # Update chart title to include filter context
    if title_suffix:
        fig.update_layout(title=fig.layout.title.text + title_suffix)

    # Store figure in session state for PDF export
    if chart_key:
        if "pdf_charts" not in st.session_state:
            st.session_state.pdf_charts = {}
        st.session_state.pdf_charts[chart_key] = fig

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


def generate_smart_insights(df: pd.DataFrame, single_committee_mode: bool = False) -> list:
    """Generate smart insights and alerts from the data.

    Args:
        df: DataFrame to analyze
        single_committee_mode: If True, show detailed insights only relevant for single committee analysis
    """
    insights = []

    if "Amount" not in df.columns:
        return insights

    # These insights only make sense when viewing a single committee
    if single_committee_mode:
        # Large donation alert
        amounts = df["Amount"].dropna()
        if len(amounts) > 0:
            avg_amount = amounts.mean()
            large_threshold = avg_amount * 10
            large_donations = df[df["Amount"] > large_threshold]

            if len(large_donations) > 0:
                insights.append({
                    "type": "alert",
                    "icon": "🚨",
                    "title": _("Large Donations Detected"),
                    "message": _("{count} contributions over {amount} (10x average)",
                                 count=len(large_donations),
                                 amount=f"${large_threshold:,.0f}")
                })

        # Contribution velocity (if dates available)
        if "Start Date" in df.columns:
            df_with_dates = df[df["Start Date"].notna()].copy()
            if len(df_with_dates) > 7:
                df_with_dates = df_with_dates.sort_values("Start Date")
                df_with_dates["Week"] = df_with_dates["Start Date"].dt.to_period('W')
                weekly_counts = df_with_dates.groupby("Week").size()

                if len(weekly_counts) >= 2:
                    recent_avg = weekly_counts.tail(2).mean()
                    older_avg = weekly_counts.head(max(2, len(weekly_counts)-2)).mean()

                    if recent_avg > older_avg * 1.5:
                        insights.append({
                            "type": "positive",
                            "icon": "📈",
                            "title": _("Increasing Momentum"),
                            "message": _("Recent weeks show {pct}% more contributions",
                                         pct=f"{(recent_avg/older_avg - 1)*100:.0f}")
                        })
                    elif recent_avg < older_avg * 0.5:
                        insights.append({
                            "type": "warning",
                            "icon": "📉",
                            "title": _("Declining Activity"),
                            "message": _("Recent contributions down {pct}% from earlier period",
                                         pct=f"{(1 - recent_avg/older_avg)*100:.0f}")
                        })

        # Top donor contribution percentage
        if "Contributor Name" in df.columns and "Amount" in df.columns:
            donor_totals = df.groupby("Contributor Name")["Amount"].sum().sort_values(ascending=False)
            if len(donor_totals) > 0:
                top_donor_pct = (donor_totals.iloc[0] / df["Amount"].sum()) * 100
                if top_donor_pct > 5:
                    insights.append({
                        "type": "info",
                        "icon": "👤",
                        "title": _("Top Donor Impact"),
                        "message": _("Single largest donor: {pct}% of total contributions",
                                     pct=f"{top_donor_pct:.1f}")
                    })

    # Geographic concentration - useful for both single and multi-committee views
    if "Contributor City" in df.columns:
        city_counts = df["Contributor City"].value_counts()
        if len(city_counts) > 0:
            top_city_pct = (city_counts.iloc[0] / len(df)) * 100
            if top_city_pct > 30:
                insights.append({
                    "type": "info",
                    "icon": "📍",
                    "title": _("Geographic Concentration"),
                    "message": _("{pct}% of contributions from {city}",
                                 pct=f"{top_city_pct:.0f}",
                                 city=city_counts.index[0])
                })

    return insights


def generate_pdf_report(
    selected_charts: dict,
    summary_stats: dict,
    filter_info: str,
    chart_figures: dict
) -> bytes:
    """Generate a PDF report with selected charts and summary statistics."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
    )

    # Title Page
    story.append(Paragraph(_("Campaign Contribution Analysis Report"), title_style))
    story.append(Paragraph(_("Generated: {timestamp}", timestamp=datetime.now().strftime('%Y-%m-%d %H:%M')), styles['Normal']))
    if filter_info:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(_("<b>Filters Applied:</b> {filters}", filters=filter_info), styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    # Summary Statistics Table
    story.append(Paragraph(_("Summary Statistics"), heading_style))

    summary_data = [[k, v] for k, v in summary_stats.items()]
    summary_table = Table(summary_data, colWidths=[3 * inch, 3 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    story.append(summary_table)
    story.append(PageBreak())

    # Add selected charts
    for chart_key, chart_name in selected_charts.items():
        if chart_key in chart_figures:
            story.append(Paragraph(chart_name, heading_style))

            # Convert Plotly figure to image
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
                story.append(Paragraph(_("Error rendering chart: {error}", error=e), styles['Normal']))
                story.append(Spacer(1, 0.2 * inch))

            story.append(PageBreak())

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# Sidebar configuration
with st.sidebar:
    st.header(_("⚙️ Configuration"))
    uploaded_file = st.file_uploader(_("Upload CSV"), type=["csv", "txt"])
    manual_path = st.text_input(_("Or enter a CSV path"), value="")

    load_entire_file = st.toggle(
        _("Load entire file"),
        value=True,
        help=_("Enable to load every row in the CSV. Disable to cap the number of rows for faster previews.")
    )

    max_rows_input = st.number_input(
        _("Max rows to load"),
        min_value=1000,
        value=100000,
        step=10000,
        help=_("Disable 'Load entire file' to limit how many rows are read."),
        disabled=load_entire_file
    )

    st.divider()
    st.caption(_("Upload your campaign finance CSV to begin analysis"))

max_rows: Optional[int]
if load_entire_file:
    max_rows = None
else:
    max_rows = int(max_rows_input)


csv_path: Optional[Path] = None
if uploaded_file is not None:
    csv_path = _persist_uploaded_file(uploaded_file)
elif manual_path.strip():
    csv_path = Path(manual_path).expanduser()

if csv_path is None:
    st.info(_("👆 Upload a CSV file or enter a path to begin analysis"))
    st.stop()

# Load data (raw)
try:
    with st.spinner(_("Loading CSV...")):
        df_raw = load_contribution_data(str(csv_path), max_rows)
except Exception as exc:
    st.error(_("Failed to load CSV: {error}", error=exc))
    st.stop()

# =============================================================================
# COLUMN MAPPING
# =============================================================================
st.header(_("🗺️ Column Mapping"))
st.write(_("Map your CSV columns to the expected format. We've auto-detected likely matches."))

# Initialize mapping in session state
if "column_mapping" not in st.session_state:
    st.session_state.column_mapping = auto_detect_column_mapping(df_raw.columns.tolist())

expected_columns = get_expected_columns()
mapping = st.session_state.column_mapping

# Create mapping UI
with st.expander(_("📋 Configure Column Mapping"), expanded=True):
    st.caption(_("Your CSV has {count} columns. Map them to the expected fields below.", count=len(df_raw.columns)))

    col1, col2 = st.columns([1, 1])

    with col1:
        st.write(_("**Expected Field** (Required fields marked with *)"))

    with col2:
        st.write(_("**Your CSV Column**"))

    st.divider()

    # Create dropdowns for each expected column
    updated_mapping = {}
    for target_col, config in expected_columns.items():
        col1, col2 = st.columns([1, 1])

        with col1:
            required_marker = " *" if config["required"] else ""
            st.write(f"**{target_col}**{required_marker}")
            st.caption(_(config["description"]))

        with col2:
            options = ["(skip)"] + df_raw.columns.tolist()
            current_value = mapping.get(target_col, "(skip)")

            if current_value not in options:
                current_value = "(skip)"

            selected = st.selectbox(
                _("Map to"),
                options=options,
                index=options.index(current_value) if current_value in options else 0,
                key=f"mapping_{target_col}",
                label_visibility="collapsed"
            )

            if selected != "(skip)":
                updated_mapping[target_col] = selected

    st.divider()

    # Validation
    missing_required = []
    for target_col, config in expected_columns.items():
        if config["required"] and target_col not in updated_mapping:
            missing_required.append(target_col)

    if missing_required:
        st.error(_("⚠️ Missing required fields: {fields}", fields=", ".join(missing_required)))
        st.caption(_("Please map all required fields (*) to continue."))
        st.stop()

    # Show preview of mapped data
    with st.expander(_("👁️ Preview Mapped Data"), expanded=False):
        try:
            df_preview = apply_column_mapping(df_raw.head(100), updated_mapping)
            st.dataframe(df_preview, use_container_width=True)
        except Exception as e:
            st.error(_("Error previewing mapped data: {error}", error=e))

    # Save mapping button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button(_("✅ Apply Mapping"), type="primary"):
            st.session_state.column_mapping = updated_mapping
            st.success(_("✅ Mapping applied!"))
            st.rerun()

    with col2:
        if st.button(_("🔄 Reset to Auto-Detect")):
            st.session_state.column_mapping = auto_detect_column_mapping(df_raw.columns.tolist())
            st.rerun()

# Apply the mapping
try:
    df_full = apply_column_mapping(df_raw, st.session_state.column_mapping)
    st.success(_("✅ Loaded and mapped {records} contribution records", records=f"{len(df_full):,}"))
except Exception as exc:
    st.error(_("Failed to apply column mapping: {error}", error=exc))
    st.stop()


# =============================================================================
# FILTERS
# =============================================================================
with st.sidebar:
    st.divider()
    st.header(_("🔍 Filters"))

    # Committee filter (checkboxes)
    selected_committees = []
    if "Recipient Committee" in df_full.columns:
        committees = sorted(df_full["Recipient Committee"].dropna().unique().tolist())

        with st.expander(_("📋 Select Committee(s)"), expanded=True):
            st.caption(_("{count} committees available", count=len(committees)))

            # Initialize session state for checkboxes first
            if "committee_selections" not in st.session_state:
                st.session_state.committee_selections = {c: True for c in committees}

            # Ensure all committees are in session state
            for committee in committees:
                if committee not in st.session_state.committee_selections:
                    st.session_state.committee_selections[committee] = True

            # Add "Select All" / "Deselect All" buttons
            col1, col2 = st.columns(2)
            select_all = col1.button(_("Select All"), key="select_all_committees")
            deselect_all = col2.button(_("Deselect All"), key="deselect_all_committees")

            # Handle select/deselect all - update all and trigger rerun
            if select_all:
                for committee in committees:
                    st.session_state.committee_selections[committee] = True
                st.rerun()
            if deselect_all:
                for committee in committees:
                    st.session_state.committee_selections[committee] = False
                st.rerun()

            # Show checkboxes for each committee
            for committee in committees:
                # Checkbox updates session state on change
                checked = st.checkbox(
                    committee,
                    value=st.session_state.committee_selections[committee],
                    key=f"committee_checkbox_{committee}"
                )
                # Update session state based on checkbox
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
                _("Date Range"),
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                help=_("Filter contributions by date")
            )
            if isinstance(date_range, tuple) and len(date_range) == 2:
                date_min, date_max = date_range

    # Amount range filter
    amount_min, amount_max = None, None
    if "Amount" in df_full.columns:
        valid_amounts = df_full[df_full["Amount"] >= 0]["Amount"].dropna()
        if len(valid_amounts) > 0:
            min_amt = 0.0  # Always start at 0
            max_amt = float(valid_amounts.max())

            amount_range = st.slider(
                _("Amount Range ($)"),
                min_value=min_amt,
                max_value=max_amt,
                value=(min_amt, max_amt),
                help=_("Filter by contribution amount"),
                format="$%.0f"  # Show as whole dollars
            )
            amount_min, amount_max = amount_range

    # Contributor search
    contributor_search = st.text_input(
        _("Search Contributor Name"),
        help=_("Case-insensitive search in contributor names")
    )

    # State filter
    selected_states = []
    if "Contributor State" in df_full.columns:
        states = sorted(df_full["Contributor State"].dropna().unique().tolist())
        selected_states = st.multiselect(
            _("Filter by State(s)"),
            options=states,
            help=_("Leave empty to show all states")
        )


# Apply filters
df = df_full.copy()
active_filters = []

if selected_committees:
    df = df[df["Recipient Committee"].isin(selected_committees)]
    active_filters.append(_("Committees: {value}", value=", ".join(selected_committees)))

if date_min and date_max and "Start Date" in df.columns:
    df = df[(df["Start Date"].dt.date >= date_min) & (df["Start Date"].dt.date <= date_max)]
    active_filters.append(_("Dates: {start} to {end}", start=date_min, end=date_max))

if amount_min is not None and amount_max is not None and "Amount" in df.columns:
    df = df[(df["Amount"] >= amount_min) & (df["Amount"] <= amount_max)]
    active_filters.append(_("Amount: {low} to {high}", low=f"${amount_min:,.2f}", high=f"${amount_max:,.2f}"))

if contributor_search:
    df = df[df["Contributor Name"].str.contains(contributor_search, case=False, na=False)]
    active_filters.append(_("Contributor: '{value}'", value=contributor_search))

if selected_states:
    df = df[df["Contributor State"].isin(selected_states)]
    active_filters.append(_("States: {value}", value=", ".join(selected_states)))

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
    st.info(_("🔎 **Active Filters:** {filters}", filters=" | ".join(active_filters)))
    st.caption(_("Showing {filtered} of {total} records ({percent}%)",
                filtered=f"{len(df):,}",
                total=f"{len(df_full):,}",
                percent=f"{len(df)/len(df_full)*100:.1f}"))
else:
    st.info(_("📊 Showing all {count} records", count=f"{len(df):,}"))


# Display raw data preview
with st.expander(_("📄 View Raw Data (first 100 rows)"), expanded=False):
    st.dataframe(df.head(100), use_container_width=True)


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================
st.header(_("📈 Summary Statistics"))

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_contributions = df["Amount"].sum() if "Amount" in df.columns else 0
    st.metric(_("Total Contributions"), f"${total_contributions:,.2f}")

with col2:
    num_contributions = len(df)
    st.metric(_("Number of Contributions"), f"{num_contributions:,}")

with col3:
    avg_contribution = df["Amount"].mean() if "Amount" in df.columns else 0
    st.metric(_("Average Contribution"), f"${avg_contribution:,.2f}")

with col4:
    unique_donors = df["Contributor Name"].nunique() if "Contributor Name" in df.columns else 0
    st.metric(_("Unique Donors"), f"{unique_donors:,}")


# =============================================================================
# SMART INSIGHTS & ALERTS
# =============================================================================
st.header(_("💡 Smart Insights"))

# Only show detailed insights when viewing a single committee
single_committee_mode = len(selected_committees) == 1
if not single_committee_mode and len(selected_committees) > 1:
    st.info(_("💡 Select a single committee to see detailed insights (large donations, momentum trends, top donors)"))

insights = generate_smart_insights(df, single_committee_mode=single_committee_mode)

if insights:
    # Display insights in colored cards
    for insight in insights:
        if insight["type"] == "alert":
            st.error(f"{insight['icon']} **{insight['title']}**: {insight['message']}")
        elif insight["type"] == "warning":
            st.warning(f"{insight['icon']} **{insight['title']}**: {insight['message']}")
        elif insight["type"] == "positive":
            st.success(f"{insight['icon']} **{insight['title']}**: {insight['message']}")
        else:
            st.info(f"{insight['icon']} **{insight['title']}**: {insight['message']}")
else:
    if single_committee_mode:
        st.info(_("No significant patterns detected in current data"))


# =============================================================================
# COMMITTEE COMPARISON MODE
# =============================================================================
if selected_committees and len(selected_committees) >= 2 and "Recipient Committee" in df.columns:
    with st.expander(_("⚖️ Committee Comparison"), expanded=True):
        st.subheader(_("Side-by-Side Committee Analysis"))

        # Comparison metrics table
        comparison_stats = []
        for committee in selected_committees:
            committee_df = df[df["Recipient Committee"] == committee]
            comparison_stats.append({
                "Committee": committee,
                "Total $": committee_df["Amount"].sum() if "Amount" in df.columns else 0,
                "# Contributions": len(committee_df),
                "Avg $": committee_df["Amount"].mean() if "Amount" in df.columns and len(committee_df) > 0 else 0,
                "# Donors": committee_df["Contributor Name"].nunique() if "Contributor Name" in df.columns else 0
            })

        comparison_df = pd.DataFrame(comparison_stats)

        # Display comparison table
        st.dataframe(
            comparison_df.style.format({
                "Total $": "${:,.2f}",
                "# Contributions": "{:,}",
                "Avg $": "${:,.2f}",
                "# Donors": "{:,}"
            }),
            use_container_width=True
        )

        # Overlaid time series if dates available
        if "Start Date" in df.columns:
            st.subheader(_("Contribution Trends Over Time"))

            fig = go.Figure()
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

            for idx, committee in enumerate(selected_committees):
                committee_df = df[df["Recipient Committee"] == committee]
                committee_df = committee_df[committee_df["Start Date"].notna()].copy()

                if len(committee_df) > 0:
                    daily_data = committee_df.groupby(committee_df["Start Date"].dt.date).agg({
                        "Amount": "sum"
                    }).reset_index()
                    daily_data.columns = ["Date", "Amount"]

                    fig.add_trace(go.Scatter(
                        x=daily_data["Date"],
                        y=daily_data["Amount"],
                        mode='lines+markers',
                        name=committee,
                        line=dict(color=colors[idx % len(colors)], width=2)
                    ))

            fig.update_layout(
                title=_("Daily Contribution Amount by Committee"),
                xaxis_title=_("Date"),
                yaxis_title=_("Total Amount ($)"),
                hovermode="x unified",
                height=500
            )
            create_downloadable_chart(fig, "committee_comparison_timeline", filter_context, "comparison_timeline")


# =============================================================================
# CONTRIBUTIONS BY COMMITTEE (only show if not filtered to specific committees)
# =============================================================================
if not selected_committees and "Recipient Committee" in df.columns and "Amount" in df.columns:
    st.header(_("🏛️ Contributions by Committee"))

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
            title=_("Top 15 Committees by Total Contributions"),
            labels={"Total Amount": _("Total Amount ($)"), "Recipient Committee": _("Committee")}
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "contributions_by_committee", filter_context, "committee")

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
st.header(_("💵 Contribution Amount Distribution"))

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
            title=_("Number of Contributions by Amount Range"),
            labels={"Count": _("Number of Contributions"), "Amount Range": _("Amount Range ($)")}
        )
        create_downloadable_chart(fig, "contribution_count_by_range", filter_context, "amount_count")

    with col2:
        fig = px.bar(
            amount_dist,
            x="Amount Range",
            y="Total Amount",
            title=_("Total Contribution Amount by Range"),
            labels={"Total Amount": _("Total Amount ($)"), "Amount Range": _("Amount Range ($)")}
        )
        create_downloadable_chart(fig, "contribution_total_by_range", filter_context, "amount_total")


# =============================================================================
# GEOGRAPHIC VISUALIZATIONS - MAPS
# =============================================================================
st.header(_("🗺️ Geographic Distribution"))

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
    st.subheader(_("United States Contribution Map (by City)"))

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
            labels={"Contributor Name": _("Unique Donors")},
            title=_("Top {count} US Cities by Contribution Amount", count=len(city_state_data)),
            scope="usa",
            size_max=40
        )
        fig.update_layout(height=600, geo=dict(projection_type="albers usa"))
        create_downloadable_chart(fig, "us_city_contribution_map", filter_context, "us_map")
    else:
        st.warning(_("No city data with known coordinates found for mapping"))

    # California Map (if CA data exists)
    ca_data = df[df["Contributor State"] == "CA"]
    if len(ca_data) > 0 and "Contributor City" in df.columns:
        st.subheader(_("California Contribution Map (by City)"))

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
                labels={"Contributor Name": _("Unique Donors")},
                title=_("Top {count} California Cities by Contribution Amount", count=len(ca_city_data)),
                scope="usa",
                size_max=50
            )
            fig.update_geos(
                center=dict(lat=37, lon=-119),
                projection_scale=6
            )
            fig.update_layout(height=600)
            create_downloadable_chart(fig, "california_city_contribution_map", filter_context, "ca_map")
        else:
            st.warning(_("No California city data with known coordinates found for mapping"))

        # Also show bar chart for CA cities
        st.subheader(_("Top California Cities"))
        fig = px.bar(
            ca_city_data.head(15),
            x="Amount",
            y="Contributor City",
            orientation="h",
            title=_("Top 15 California Cities by Contribution Amount"),
            labels={"Amount": _("Total Amount ($)"), "Contributor City": _("City")}
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "california_cities_bar", filter_context, "ca_cities")


# =============================================================================
# TOP LOCATIONS (for non-map view)
# =============================================================================
st.header(_("📍 Top Contributing Locations"))

col1, col2 = st.columns(2)

with col1:
    st.subheader(_("Top 15 Cities"))
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
            title=_("Top 15 Cities by Contribution Amount"),
            labels={"Total Amount": _("Total Amount ($)"), "City": _("City")}
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "top_cities", filter_context, "top_cities")

with col2:
    st.subheader(_("Top 15 States"))
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
            title=_("Top 15 States by Contribution Amount"),
            labels={"Total Amount": _("Total Amount ($)"), "State": _("State")}
        )
        fig.update_layout(height=500)
        create_downloadable_chart(fig, "top_states", filter_context, "top_states")


# =============================================================================
# TIME SERIES ANALYSIS
# =============================================================================
st.header(_("📅 Contributions Over Time"))

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
            create_downloadable_chart(fig, "daily_amounts", filter_context, "daily_amounts")

        with col2:
            fig = px.line(
                daily_contributions,
                x="Date",
                y="Number of Contributions",
                title=_("Daily Number of Contributions"),
                labels={
                    "Number of Contributions": _("Number of Contributions"),
                    "Date": _("Date")
                }
            )
            fig.update_traces(line_color='#ff7f0e', line_width=2)
            create_downloadable_chart(fig, "daily_counts", filter_context, "daily_counts")

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
        create_downloadable_chart(fig, "monthly_contributions", filter_context, "monthly")


# =============================================================================
# ADDITIONAL INSIGHTS
# =============================================================================
st.header(_("🔍 Additional Insights"))

col1, col2 = st.columns(2)

with col1:
    st.subheader(_("Top 20 Contributors"))
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
    st.subheader(_("Top 15 Occupations"))
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
        create_downloadable_chart(fig, "top_occupations", filter_context, "occupations")


# =============================================================================
# DATA EXPORT
# =============================================================================
st.header(_("📥 Export & Reports"))

# CSV Exports
st.subheader(_("📄 CSV Exports"))
col1, col2 = st.columns(2)

with col1:
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=_("📄 Download Filtered Dataset (CSV)"),
        data=csv_data,
        file_name=f"contributions_filtered_{len(df)}_records.csv",
        mime="text/csv"
    )

with col2:
    summary_data = {
        "Metric": [
            _("Total Contributions"),
            _("Number of Contributions"),
            _("Average Contribution"),
            _("Unique Donors"),
            _("Date Range")
        ],
        "Value": [
            f"${total_contributions:,.2f}",
            f"{num_contributions:,}",
            f"${avg_contribution:,.2f}",
            f"{unique_donors:,}",
            f"{df['Start Date'].min()} to {df['Start Date'].max()}" if "Start Date" in df.columns else _("N/A")
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_csv = summary_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label=_("📊 Download Summary Report (CSV)"),
        data=summary_csv,
        file_name="contribution_summary.csv",
        mime="text/csv"
    )

st.divider()

# PDF Report Generator
st.subheader(_("📑 Custom PDF Report"))
with st.expander(_("🎨 Select Charts for PDF Report"), expanded=False):
    st.write(_("**Select which charts to include in your PDF report:**"))

    # Define available charts
    available_charts = {
        "committee": _("Committee Breakdown"),
        "amount_count": _("Amount Distribution (Count)"),
        "amount_total": _("Amount Distribution (Total)"),
        "us_map": _("US Contribution Map"),
        "ca_map": _("California Contribution Map"),
        "ca_cities": _("Top California Cities"),
        "top_cities": _("Top 15 Cities"),
        "top_states": _("Top 15 States"),
        "daily_amounts": _("Daily Contribution Amounts"),
        "daily_counts": _("Daily Contribution Count"),
        "monthly": _("Monthly Contributions"),
        "occupations": _("Top Occupations")
    }

    # Select All / Deselect All buttons for PDF charts
    btn_col1, btn_col2, btn_spacer = st.columns([1, 1, 2])
    select_all_pdf = btn_col1.button(_("Select All Available"), key="select_all_pdf_charts")
    deselect_all_pdf = btn_col2.button(_("Deselect All"), key="deselect_all_pdf_charts")

    # Initialize session state for PDF chart selections
    if "pdf_chart_selections" not in st.session_state:
        st.session_state.pdf_chart_selections = {}

    # Handle select/deselect all
    if select_all_pdf:
        # Select all available charts
        if "pdf_charts" in st.session_state:
            for key in available_charts.keys():
                if key in st.session_state.pdf_charts:
                    st.session_state.pdf_chart_selections[key] = True
        st.rerun()

    if deselect_all_pdf:
        st.session_state.pdf_chart_selections = {key: False for key in available_charts.keys()}
        st.rerun()

    col1, col2, col3 = st.columns(3)

    selected_for_pdf = {}
    chart_keys = list(available_charts.keys())

    # Distribute checkboxes across 3 columns
    for idx, (key, name) in enumerate(available_charts.items()):
        col = [col1, col2, col3][idx % 3]
        with col:
            # Check if chart is available in session state
            is_available = "pdf_charts" in st.session_state and key in st.session_state.pdf_charts

            # Initialize checkbox state if not present
            if key not in st.session_state.pdf_chart_selections:
                st.session_state.pdf_chart_selections[key] = is_available

            # Get value from session state
            checkbox_value = st.session_state.pdf_chart_selections.get(key, False) and is_available

            checked = st.checkbox(
                name,
                value=checkbox_value,
                key=f"pdf_{key}",
                disabled=not is_available
            )

            # Update session state
            st.session_state.pdf_chart_selections[key] = checked

            if checked and is_available:
                selected_for_pdf[key] = name

    st.divider()

    # Generate PDF button
    if selected_for_pdf:
        if st.button(_("📄 Generate PDF Report"), type="primary"):
            with st.spinner(_("Generating PDF report...")):
                try:
                    # Prepare summary statistics
                    summary_stats = {
                        _("Total Contributions"): f"${total_contributions:,.2f}",
                        _("Number of Contributions"): f"{num_contributions:,}",
                        _("Average Contribution"): f"${avg_contribution:,.2f}",
                        _("Unique Donors"): f"{unique_donors:,}",
                    }

                    # Get filter info
                    filter_info = ' | '.join(active_filters) if active_filters else _("No filters applied")

                    # Generate PDF
                    pdf_bytes = generate_pdf_report(
                        selected_for_pdf,
                        summary_stats,
                        filter_info,
                        st.session_state.pdf_charts
                    )

                    # Offer download
                    st.download_button(
                        label=_("💾 Download PDF Report"),
                        data=pdf_bytes,
                        file_name=f"contribution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                    st.success(_("✅ PDF generated successfully!"))
                except Exception as e:
                    st.error(_("Error generating PDF: {error}", error=e))
                    st.caption(_("Make sure all required packages are installed: kaleido, reportlab, Pillow"))
    else:
        st.info(_("Select at least one chart to generate a PDF report"))

    st.caption(_("💡 Charts must be rendered on the page before they can be included in the PDF"))

st.divider()
st.caption(_("💡 **Tip**: Use the camera icon in the top-right of any chart to download it as a PNG image"))
