# DataViz Toolkit

Streamlit dashboards, CLI helpers, and Supabase import scripts for exploring California
legislative data (campaign finance, vote tracking, agricultural tagging, and CSV analysis).

The repository contains:

- `Home.py` and `pages/` – the multipage Streamlit application.
- `visualizer.py` – CLI helper that samples large CSV files and produces Plotly charts.
- `import_legiscan_data*.py` – scripts that ingest LegiScan datasets into Supabase.
- `openstates/agricultural_classifier.py` plus supporting scripts for automated bill tagging.

## Quick Start

```bash
streamlit run Home.py
```

Run the Streamlit app from the project root with your Supabase environment variables exported
(`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, etc.).

## Development Environment

### Requirements

- macOS (Intel or Apple Silicon) or Linux
- Python **3.13** (python.org universal2 build recommended on macOS)
- Supabase project credentials for data access

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# quick sanity check – this previously segfaulted on some machines
python -c "import pandas; import pyarrow; print('imports ok')"

# run the automated tests
pytest
```

Place any LegiScan dataset dumps under `legiscan_ca_data/` so the import scripts can discover
them, then run (for example):

```bash
python import_legiscan_data_v2.py --base-dir legiscan_ca_data/CA
```

### Apple Silicon / macOS Notes

- Use the official Python 3.13 universal2 installer from python.org. Homebrew’s latest Python can
  lag behind or miss Arm wheels for pandas/pyarrow.
- If you see a segfault during `python -c "import pandas"`, pin to the most stable Arm wheels:
  `pip install --force-reinstall "pandas==2.2.3" "numpy==1.26.4" "pyarrow==16.1.0"`.
- Keep Xcode Command Line Tools (`xcode-select --install`) up to date so cryptography and reportlab
  can compile native extensions when wheels are unavailable.
- When the pip cache causes permission warnings, clear it via `rm -rf ~/Library/Caches/pip` or run
  `PIP_NO_CACHE_DIR=1 pip install ...`.

## Testing

`pytest` covers the CSV visualizer sampling logic and the shared importer utilities. Add new tests
alongside the corresponding modules (e.g., `tests/test_import_utils.py`). Run the suite after any
changes to classifiers, data loaders, or CLI parsing:

```bash
pytest
```

## CSV Visualizer CLI

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

- `--chart`: `line` (default), `bar`, `scatter`, `hist`.
- `--max-rows`: upper bound for rows kept via reservoir sampling.
- `--chunk-size`: number of rows streamed per chunk while sampling.
- `--datetime-columns`: columns pandas should parse as datetimes.
- `--open-browser`: automatically launch the resulting Plotly HTML.

Because Plotly writes standalone HTML, the output can be shared or hosted without extra assets.
