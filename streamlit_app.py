from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import pandas as pd
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

import visualizer


st.set_page_config(page_title="CSV Visualization Helper", layout="wide")

st.title("CSV Visualization Helper")
st.write(
    "Upload a CSV (or provide a server path), configure how the data should be sampled, "
    "and build Plotly charts without leaving the browser.",
)


def _persist_uploaded_file(uploaded_file: UploadedFile) -> Optional[Path]:
    """Write the uploaded CSV to a temp file so pandas/visualizer can access it."""
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
def _load_preview(path_str: str, delimiter: str, encoding: str) -> pd.DataFrame:
    """Return a small preview DataFrame to drive column selectors."""
    return pd.read_csv(path_str, sep=delimiter, encoding=encoding, nrows=500)


def _build_namespace(csv_path: Path, form_values: dict) -> SimpleNamespace:
    """Translate Streamlit form values into the namespace the CLI code expects."""
    return SimpleNamespace(
        csv_path=csv_path,
        chart=form_values["chart"],
        x_column=form_values["x_column"] or None,
        value_columns=form_values["value_columns"] or None,
        title=form_values["title"] or None,
        output=Path("chart.html"),
        max_rows=int(form_values["max_rows"]),
        chunk_size=int(form_values["chunk_size"]),
        delimiter=form_values["delimiter"],
        encoding=form_values["encoding"],
        datetime_columns=form_values["datetime_columns"],
        seed=int(form_values["seed"]),
        nbins=int(form_values["nbins"]),
        open_browser=False,
        no_sampling=form_values["no_sampling"],
    )


with st.sidebar:
    uploaded_file = st.file_uploader("Upload CSV", type=["csv", "txt", "tsv"])
    manual_path = st.text_input("Or enter a CSV path available on the server", value="")

    delimiter = st.text_input("Delimiter", value=",")
    encoding = st.text_input("Encoding", value="utf-8")

    max_rows = st.number_input("Max rows (sampling cap)", min_value=1000, value=50000, step=5000)
    chunk_size = st.number_input("Chunk size", min_value=1000, value=50000, step=5000)
    seed = st.number_input("Sampling seed", min_value=0, value=13, step=1)
    no_sampling = st.checkbox("Disable sampling (load entire file)", value=False)

    nbins = st.slider("Histogram bins", min_value=5, max_value=200, value=30)

    st.caption("Sampling keeps memory flat even for huge files. Disable it only if every row matters.")


csv_path: Optional[Path] = None
if uploaded_file is not None:
    csv_path = _persist_uploaded_file(uploaded_file)
elif manual_path.strip():
    csv_path = Path(manual_path).expanduser()


preview_df: Optional[pd.DataFrame] = None
column_names: list[str] = []

if csv_path is not None:
    try:
        preview_df = _load_preview(str(csv_path), delimiter, encoding)
        column_names = preview_df.columns.tolist()
        st.success(f"Loaded preview from {csv_path}")
        with st.expander("Preview (first 500 rows)", expanded=False):
            st.dataframe(preview_df.head(50))
    except Exception as exc:
        st.error(f"Failed to preview CSV: {exc}")


with st.form("chart_form"):
    chart = st.selectbox("Chart type", ["line", "bar", "scatter", "hist"], index=0)
    x_default_index = 1 if column_names else 0
    x_column = st.selectbox(
        "X column (required for line/bar/scatter)",
        options=[""] + column_names,
        index=x_default_index,
    )

    value_columns = st.multiselect(
        "Value columns (Y axis or histogram source)",
        options=column_names,
    )

    datetime_columns = st.multiselect(
        "Parse as datetime",
        options=column_names,
    )

    title = st.text_input("Chart title", value="")

    submitted = st.form_submit_button("Build chart")


if submitted:
    if csv_path is None:
        st.error("Upload a file or enter a valid path before building a chart.")
    else:
        form_values = {
            "chart": chart,
            "x_column": x_column.strip() or None,
            "value_columns": value_columns,
            "title": title,
            "max_rows": max_rows,
            "chunk_size": chunk_size,
            "delimiter": delimiter,
            "encoding": encoding,
            "datetime_columns": datetime_columns,
            "seed": seed,
            "nbins": nbins,
            "no_sampling": no_sampling,
        }

        args = _build_namespace(csv_path, form_values)
        try:
            visualizer.validate_args(args)
        except Exception as exc:
            st.error(f"Configuration error: {exc}")
        else:
            try:
                with st.spinner("Sampling data and building chart..."):
                    df = visualizer.load_dataframe(args)
                    fig = visualizer.build_chart(df, args)

                st.subheader("Visualization")
                st.plotly_chart(fig, use_container_width=True)

                html_bytes = fig.to_html(full_html=True, include_plotlyjs="cdn").encode("utf-8")
                download_name = f"{csv_path.stem}_{chart}.html"
                st.download_button(
                    "Download standalone HTML",
                    data=html_bytes,
                    file_name=download_name,
                    mime="text/html",
                )

                st.subheader("Sampled Data (first 100 rows)")
                st.dataframe(df.head(100))
            except Exception as exc:
                st.error(f"Failed to build chart: {exc}")
