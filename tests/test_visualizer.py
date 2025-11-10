from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd

import visualizer

DATA_PATH = Path(__file__).parent / "data" / "sample.csv"


def make_args(**overrides):
    defaults = {
        "csv_path": DATA_PATH,
        "chart": "line",
        "x_column": "Date",
        "value_columns": ["Sales", "Profit"],
        "title": None,
        "output": Path("chart.html"),
        "max_rows": 5000,
        "chunk_size": 3,
        "delimiter": ",",
        "encoding": "utf-8",
        "datetime_columns": ["Date"],
        "seed": 123,
        "nbins": 20,
        "open_browser": False,
        "no_sampling": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_load_dataframe_without_sampling_reads_all_rows():
    args = make_args(no_sampling=True)
    df = visualizer.load_dataframe(args)
    assert len(df) == 10
    assert list(df.columns) == ["Date", "Sales", "Profit"]
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])


def test_load_dataframe_with_sampling_caps_row_count_and_is_deterministic():
    args = make_args(no_sampling=False, max_rows=5, chunk_size=2, seed=99)
    df_first = visualizer.load_dataframe(args)
    df_second = visualizer.load_dataframe(args)
    assert len(df_first) == 5
    assert df_first["Sales"].between(80, 150).all()
    pd.testing.assert_frame_equal(df_first.reset_index(drop=True), df_second.reset_index(drop=True))
