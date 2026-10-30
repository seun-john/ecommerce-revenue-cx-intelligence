# Reproduce on Windows 11

## Requirements

Python 3.11 or newer (3.12 recommended), Git, internet access for dependency/data download and approximately 1 GB free disk space. Python must include the `py` launcher, or replace `py -3` below with the absolute path to python.exe. Power BI Desktop is needed only to assemble the native report.

```powershell
Set-Location 'C:\path\to\ecommerce-revenue-cx-intelligence'
py -3 -m venv .venv
& .venv\Scripts\python.exe -m pip install -e '.[dev]'
& .venv\Scripts\python.exe -m src.acquire
& .venv\Scripts\python.exe -m src.pipeline
& .venv\Scripts\python.exe -m pytest -q
```

Run those commands in order and stop if any exit code is nonzero. Alternatively run `powershell -ExecutionPolicy Bypass -File scripts\run.ps1` (process invocation only; no persistent policy change). No virtual-environment activation is necessary.

The acquisition step downloads the original archive from the public Kaggle dataset API. It extracts only the nine expected CSV basenames, preventing archive path traversal. Existing source files are retained; their SHA-256 hashes and byte sizes are written to `reports/source_manifest.json`. To compare source versions, retain that manifest before replacing files. A successful run writes the raw audit before cleaning, builds DuckDB, executes all 12 numbered SQL files, exports Power BI CSVs and produces reports and figures.

## If Kaggle requires authentication

The build in this project used the original public endpoint without credentials. Access requirements may change. If it returns a login page, 401 or 403:

1. Sign into Kaggle and visit the [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). Read its licence and any access terms.
2. Click Download. Save the downloaded ZIP as `data.zip` in the project root. Run `python -m src.acquire` again using the environment executable above.
3. Alternatively extract all nine CSVs directly into `data\raw` and run the pipeline. The names must match `src/acquire.py`; no renamed files or synthetic replacements are accepted for final findings.
4. If using Kaggle CLI, install it in this virtual environment and follow Kaggle's account authentication setup outside the project. Run `kaggle datasets download -d olistbr/brazilian-ecommerce -p .`; rename the archive to `data.zip` if necessary. Never store tokens, `.env`, `kaggle.json` or credentials in Git.

Synthetic fixture tests can run without the dataset; real-data integration tests are skipped when `data/olist.duckdb` is absent. A data-free test run alone does not validate final business findings. DAX cannot be executed by pytest; use the Desktop acceptance checklist in `powerbi/DASHBOARD_SPEC.md`.

## Outputs

| Path | Contents |
|---|---|
| data/raw | Nine original CSVs, Git ignored |
| data/olist.duckdb | Relational staging and analytical model, Git ignored |
| reports/DATA_QUALITY.md | Complete raw schema, row counts, duplicates, missingness, dates and FK audit |
| reports/source_manifest.json | Source file byte sizes and hashes; metadata only |
| reports/cleaning_log.json | Cleaning decisions and outcome counts |
| reports/sql | Twelve executed query result CSVs |
| reports/metrics.json | Verified executive KPI values |
| reports/statistical_comparison.json | Review comparison, sample sizes, intervals and caveats |
| reports/figures | Actual generated analytical graphics |
| reports/EXECUTIVE_REPORT.md | Evidence and management actions |
| powerbi/exports | Full-grain model CSVs, Git ignored |

## SQL exploration

```python
import duckdb
from pathlib import Path
with duckdb.connect('data/olist.duckdb', read_only=True) as db:
    print(db.sql(Path('sql/08_delivery_reviews.sql').read_text()).df())
```

## Git and publication

The project is published to the owner's approved public GitHub repository, with the dashboard deployed through GitHub Pages. Before staging future changes, inspect `git status --short` and `git diff --cached`. Keep raw CSVs, ZIPs, database, full BI row exports, PBIX and credentials excluded. The public dashboard includes a minimised derived analytical extract with coded identifiers; see `PUBLISHING.md` for its exact contents. The dataset and derived outputs retain noncommercial/share-alike obligations. Do not add GitHub publishing credentials to this project.

## Operating constraints

Close DuckDB readers before rebuilding. The pipeline is a batch job for a fixed public extract, not a live order service. Source files may contain free-text reviews; they are treated as data and never executed, sent to an API or included in the executive report. A run manifest records package versions; `requirements-lock.txt` locks the complete environment used for delivery. On a new compatible environment use `pip install -r requirements-lock.txt` then `pip install -e . --no-deps` for the exact dependency set. Hashes allow input drift to be detected; no upstream version is silently assumed.
