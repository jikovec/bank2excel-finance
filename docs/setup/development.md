# Development Setup

## Requirements

Python 3.11 or newer is recommended.

Install the tracked dependency list:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Source imports observed in `build_finance_workbook.py` include `pandas`, `yaml`, `matplotlib`, `openpyxl`, and `xlsxwriter`. `requirements.txt` currently lists `pandas`, `openpyxl`, `xlsxwriter`, `xlrd`, and `PyYAML`. If a clean environment fails on a missing charting import, resolve that environment gap before running builds.

## First-Time Local Setup

Run the setup helper from the repo root:

```powershell
.\scripts\setup_local.ps1
```

The script:

- Creates `config/`, `input/`, `output/`, `cache/`, and `reports/` folders.
- Creates supported input subfolders.
- Copies `.env.example` and config `.example` files only when the private destination does not already exist.
- Does not overwrite existing private files.

Manual equivalent:

```powershell
Copy-Item config/accounts.example.csv config/accounts.csv
Copy-Item config/categories.example.csv config/categories.csv
Copy-Item config/currency_rates.example.csv config/currency_rates.csv
Copy-Item config/settings.example.yaml config/settings.yaml
```

Then fill the private files:

- `config/accounts.csv` - own accounts, aliases, account identifiers, and transfer hints.
- `config/categories.csv` - local category and recurring rules.
- `config/currency_rates.csv` - manual dated FX rates.
- `config/settings.yaml` - default paths and FX options.

## Configuration Precedence

The build uses code defaults first, then `config/settings.yaml`, then CLI arguments. CLI arguments take precedence over settings-file values.

Default settings from the tracked example:

```yaml
paths:
  input: input
  output: output/Personal_Finance_Analysis.xlsx
  accounts: config/accounts.csv
  categories: config/categories.csv
  currency_rates: config/currency_rates.csv
  cache: cache/currency_rates_cache.csv
  report: reports/validation_summary.md
fx:
  provider: frankfurter
  mode: historical
  no_download: false
```

## Build Commands

Normal build:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx
```

Offline FX build:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx --no-fx-download
```

PowerShell wrappers:

```powershell
.\scripts\run_build.ps1
.\scripts\run_build_offline.ps1
```

## Expected Outputs

- Workbook: `output/Personal_Finance_Analysis.xlsx`
- Validation report: `reports/validation_summary.md`
- FX cache: `cache/currency_rates_cache.csv`

All three can contain private data and are ignored by Git.
