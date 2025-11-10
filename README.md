# CSV Visualization Helper

`visualizer.py` is a lightweight command-line helper that can peek into very large CSV files,
sample rows, and generate interactive Plotly charts (line, bar, scatter, histogram) saved as a
self-contained HTML file.

## Setup

```bash
cd csv_viz_tool
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Usage

```bash
python visualizer.py /path/to/data.csv \
    --chart line \
    --x-column Date \
    --value-columns Sales Profit \
    --max-rows 75000 \
    --chunk-size 60000 \
    --datetime-columns Date \
    --output sales.html
```

Key options:

- `--chart` : `line` (default), `bar`, `scatter`, `hist`.
- `--x-column` / `--value-columns`: define axes/series. For histograms you can omit `--x-column` and
  only pass `--value-columns`.
- `--max-rows`: upper bound for rows kept via reservoir sampling (keeps memory flat even for huge
  files). Use `--no-sampling` if you truly need every row and your machine can fit it.
- `--chunk-size`: how many rows to stream per pass when sampling.
- `--datetime-columns`: names that pandas should parse as datetimes.
- `--delimiter`, `--encoding`: tweak parsing for TSVs or non-UTF8 data.
- `--open-browser`: automatically open the generated HTML.

The script prints where it saved the chart (default `chart.html`). Because Plotly writes standalone
HTML, you can share or host the output without additional assets.
