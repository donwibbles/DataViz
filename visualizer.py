"""CLI utility for exploring large CSV files with quick Plotly charts."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

import pandas as pd
import plotly.express as px


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sample (or fully load) a CSV file and build an interactive chart.",
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "--chart",
        choices=["line", "bar", "scatter", "hist"],
        default="line",
        help="Type of visualization to create.",
    )
    parser.add_argument(
        "--x-column",
        "-x",
        help="Column to plot on the X axis (required for line/bar/scatter).",
    )
    parser.add_argument(
        "--value-columns",
        "-y",
        nargs="+",
        help="Column(s) to plot on the Y axis (or to use for histograms).",
    )
    parser.add_argument(
        "--title",
        help="Optional custom chart title.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("chart.html"),
        help="Where to write the interactive HTML chart.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=50000,
        help="Maximum number of rows to retain via reservoir sampling.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50000,
        help="Number of rows per chunk when streaming the CSV.",
    )
    parser.add_argument(
        "--delimiter",
        "-d",
        default=",",
        help="Custom field delimiter if the file is not comma separated.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="File encoding passed to pandas.read_csv.",
    )
    parser.add_argument(
        "--datetime-columns",
        nargs="*",
        default=[],
        help="Column names that should be parsed as datetimes.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=13,
        help="Random seed that controls the row sampling.",
    )
    parser.add_argument(
        "--nbins",
        type=int,
        default=30,
        help="Number of bins for histogram charts.",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the resulting HTML file in the default browser.",
    )
    parser.add_argument(
        "--no-sampling",
        action="store_true",
        help="Load the entire file instead of sampling (may require large memory).",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {args.csv_path}")

    if args.chart in {"line", "bar", "scatter"}:
        if not args.x_column:
            raise ValueError("--x-column is required for line, bar, and scatter charts.")
        if not args.value_columns:
            raise ValueError("--value-columns is required for line, bar, and scatter charts.")

    if args.chart == "hist":
        if not args.value_columns and not args.x_column:
            raise ValueError(
                "Provide either --value-columns or --x-column to build a histogram.",
            )

    if args.max_rows <= 0:
        raise ValueError("--max-rows must be a positive integer.")

    if args.chunk_size <= 0:
        raise ValueError("--chunk-size must be a positive integer.")


def _columns_needed(args: argparse.Namespace) -> List[str]:
    cols: List[str] = []
    if args.x_column:
        cols.append(args.x_column)
    if args.value_columns:
        cols.extend(args.value_columns)
    # Deduplicate while preserving order.
    seen = set()
    ordered: List[str] = []
    for col in cols:
        if col not in seen:
            seen.add(col)
            ordered.append(col)
    return ordered


def load_dataframe(args: argparse.Namespace) -> pd.DataFrame:
    cols = _columns_needed(args) or None
    parse_dates = args.datetime_columns or None

    if args.no_sampling:
        return pd.read_csv(
            args.csv_path,
            usecols=cols,
            parse_dates=parse_dates,
            sep=args.delimiter,
            encoding=args.encoding,
        )

    rng = random.Random(args.seed)
    reservoir: list[dict] = []
    total_rows = 0

    for chunk in pd.read_csv(
        args.csv_path,
        usecols=cols,
        parse_dates=parse_dates,
        sep=args.delimiter,
        encoding=args.encoding,
        chunksize=args.chunk_size,
    ):
        required = [c for c in (args.x_column,) if c]
        if args.value_columns:
            required.extend(args.value_columns)
        required = [c for c in required if c in chunk.columns]
        if required:
            chunk = chunk.dropna(subset=required)

        records = chunk.to_dict(orient="records")
        for record in records:
            total_rows += 1
            if len(reservoir) < args.max_rows:
                reservoir.append(record)
            else:
                idx = rng.randint(0, total_rows - 1)
                if idx < args.max_rows:
                    reservoir[idx] = record

    if not reservoir:
        raise ValueError("No rows were collected; check column names and filters.")

    return pd.DataFrame(reservoir)


def build_chart(df: pd.DataFrame, args: argparse.Namespace):
    title = args.title or f"{args.chart.title()} chart for {args.csv_path.name}"
    if args.chart == "line":
        return px.line(df, x=args.x_column, y=args.value_columns, title=title)
    if args.chart == "bar":
        return px.bar(df, x=args.x_column, y=args.value_columns, title=title, barmode="group")
    if args.chart == "scatter":
        return px.scatter(df, x=args.x_column, y=args.value_columns[0], title=title)

    # Histogram
    hist_column = (args.value_columns or [args.x_column])[0]
    return px.histogram(df, x=hist_column, nbins=args.nbins, title=title)


def main() -> None:
    args = parse_args()
    try:
        validate_args(args)
        df = load_dataframe(args)
        fig = build_chart(df, args)
        fig.write_html(args.output)
        print(f"Chart written to {args.output.resolve()}")
        if args.open_browser:
            import webbrowser

            webbrowser.open(args.output.resolve().as_uri())
    except Exception as exc:  # pragma: no cover - CLI entry point
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
