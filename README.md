# Finance Workbook Generator

A local Python pipeline that imports bank exports, normalizes transactions, converts currencies, detects internal transfers, categorizes spending, finds recurring payments, imports investment snapshots, and generates a styled Excel workbook.

The repository is arranged so reusable code, examples, and documentation can be tracked while real financial data stays local and ignored.

Current documented release: [v0.0.2](docs/releases/v0.0.2.md).

## Start Here

- Personal finance vault: [01_Finance_Home.md](01_Finance_Home.md)
- Finance snapshot guide: [finance/README.md](finance/README.md)
- Codex project memory: [00_Index.md](00_Index.md)
- Agent operating rules: [AGENTS.md](AGENTS.md)
- Documentation index: [docs/README.md](docs/README.md)
- Future-agent orientation: [docs/AGENT-INDEX.md](docs/AGENT-INDEX.md)
- Obsidian/local graph guide: [docs/OBSIDIAN.md](docs/OBSIDIAN.md)
- Source map: [docs/SOURCE-MAP.md](docs/SOURCE-MAP.md)
- Connection map: [docs/CONNECTIONS.md](docs/CONNECTIONS.md)
- First-time setup: [docs/setup/development.md](docs/setup/development.md)
- Bank export placement: [docs/setup/bank-export-guide.md](docs/setup/bank-export-guide.md)
- Pipeline architecture: [docs/architecture/pipeline.md](docs/architecture/pipeline.md)
- Privacy and commit checks: [docs/security/data-privacy.md](docs/security/data-privacy.md)
- Validation workflow: [docs/testing/verification.md](docs/testing/verification.md)
- Release notes: [docs/releases/v0.0.2.md](docs/releases/v0.0.2.md)

## Current Scope

This is a CLI-only workbook generator. The current repo does not contain a web server, HTTP API, or application routes. See [docs/api/README.md](docs/api/README.md) for the CLI interface and the internal parser surfaces.

Supported source types in the current code:

- Revolut transaction exports.
- Tatra banka transaction exports.
- Slovenska sporitelna transaction exports.
- SLSP investment and savings valuation snapshots.
- A legacy prototype transaction import path, when `input/legacy/` exists locally.

Generated workbook sheets include `Dashboard`, `Raw_Transactions`, `Investment_Snapshots`, `Investment_Dashboard`, `Accounts`, `Categories`, `Currency_Rates`, `Recurring`, yearly sheets, `Validation`, and hidden chart data.

## Quick Setup

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux, activate with `source .venv/bin/activate`.

PowerShell users can prepare local private folders and config files with:

```powershell
.\scripts\setup_local.ps1
```

The setup script creates local folders and copies example files only when the private destination does not already exist.

## Build Commands

Normal build:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx
```

Offline FX build:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx --no-fx-download
```

Custom settings:

```bash
python build_finance_workbook.py --settings config/settings.yaml --accounts config/accounts.csv --categories config/categories.csv --currency-rates config/currency_rates.csv
```

Defaults can also be set in `config/settings.yaml`; CLI arguments take precedence.

## Generated Artifacts

- Workbook output: `output/Personal_Finance_Analysis.xlsx`
- Validation report: `reports/validation_summary.md`
- FX cache: `cache/currency_rates_cache.csv`

These runtime artifacts can contain private financial data and are ignored by Git.

## Privacy Before Commit

Never commit real files from:

- `input/`
- `output/`
- `cache/`
- `reports/`
- `finance/private/`
- `.env`
- `config/accounts.csv`
- `config/categories.csv`
- `config/currency_rates.csv`
- `config/settings.yaml`

Before committing, run:

```bash
git status --ignored
git diff --cached
```

Only source code, documentation, scripts, `.gitignore`, `requirements.txt`, `.env.example`, `.gitkeep`, and fake `.example` files should be staged.

## Repository Map

```text
bank_parsers/              Bank and investment import parsers
config/                    Tracked examples plus ignored local config
docs/                      Developer documentation
finance/                   Finance vault guides, templates, and ignored private snapshot
handoffs/                  Agent handoff notes and handoff index
input/                     Ignored local bank exports
output/                    Ignored generated workbooks
reports/                   Ignored private validation/build evidence
scripts/                   Local setup and build wrappers
build_finance_workbook.py  CLI entrypoint and workbook builder
requirements.txt           Python dependency list
```

No license file is included yet.
