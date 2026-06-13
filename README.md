# Finance Workbook Generator

A reusable Python pipeline that imports bank exports, normalizes transactions, converts currencies, detects internal transfers, categorizes spending, finds recurring payments, imports investment snapshots, and generates a styled Excel workbook.

The project is structured for GitHub use: code and fake examples are tracked; real financial data stays local and ignored.

## Features

- Imports bank transaction exports.
- Normalizes transactions into one shared schema.
- Detects internal transfers between configured own accounts.
- Applies configurable category rules.
- Detects recurring payments.
- Converts non-EUR amounts using historical transaction-date FX rates.
- Imports investment valuation snapshots separately from transactions.
- Generates a styled Excel workbook with dashboards, raw data, validation, accounts, categories, recurring groups, currency rates, and investment sheets.

## Privacy

Never commit real files from:

- `input/`
- `output/`
- `cache/`
- `reports/`
- `.env`
- `config/accounts.csv`
- `config/categories.csv`
- `config/currency_rates.csv`
- `config/settings.yaml`

These paths are ignored by Git. Tracked `.example` files contain fake placeholders only.

## Supported Sources

- Revolut transaction exports
- Tatra banka transaction exports
- Slovenska sporitelna transaction exports
- SLSP investment valuation snapshots

## Installation

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux, activate with `source .venv/bin/activate`.

## First-Time Setup

PowerShell users can run:

```powershell
.\scripts\setup_local.ps1
```

Or copy the examples manually:

```powershell
Copy-Item config/accounts.example.csv config/accounts.csv
Copy-Item config/categories.example.csv config/categories.csv
Copy-Item config/currency_rates.example.csv config/currency_rates.csv
Copy-Item config/settings.example.yaml config/settings.yaml
```

Then fill `config/accounts.csv`, adjust `config/categories.csv`, and place exports into the correct `input/` subfolders.

## Folder Structure

```text
.
├── bank_parsers/
├── cache/
├── config/
├── docs/
├── input/
├── output/
├── reports/
├── scripts/
├── build_finance_workbook.py
├── requirements.txt
└── README.md
```

`cache/`, `input/`, `output/`, `reports/`, and real local config files are private runtime locations.

## Commands

Normal build:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx
```

Offline FX build:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx --no-fx-download
```

Custom account config:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx --accounts config/accounts.csv
```

You can also set defaults in `config/settings.yaml`; CLI arguments take precedence.

## Currency Conversion

The pipeline converts non-EUR transactions to EUR using historical rates for the transaction booking date. Manual rates are read from `config/currency_rates.csv`. Downloaded FX rates are cached in `cache/currency_rates_cache.csv`.

`--no-fx-download` disables external API calls and uses only manual/cache rates. Missing rates are flagged; rates are not invented.

## Investment Snapshots

Put SLSP investment valuation snapshots in:

```text
input/investments/slsp/
```

Snapshots represent holding values at a point in time. They are imported into `Investment_Snapshots` and summarized separately from transaction income and expenses.

## Validation

Validation reports are written to:

```text
reports/validation_summary.md
```

Warnings identify parser assumptions, missing FX rates, low-confidence categories, possible duplicate rows, missing balances, and rows needing manual review.

## Maintenance

- Add future exports to the matching `input/` subfolder and rebuild.
- Update local account identifiers in `config/accounts.csv`.
- Improve category and recurring rules in `config/categories.csv`.
- Add new bank parsers under `bank_parsers/` and register them in `build_finance_workbook.py`.

See `docs/maintenance.md` for more detail.

## Security Checklist Before Commit

Run:

```bash
git status --ignored
git diff --cached
```

Confirm that only source code, docs, scripts, `.gitignore`, `requirements.txt`, `.env.example`, `.gitkeep`, and fake `.example` files are staged. Do not stage real exports, workbooks, reports, caches, or local config.

No license file is included yet.
