# Commands

Run commands from the repository root.

## Discovered Command Sources

Found:

- `requirements.txt`
- `README.md`
- `scripts/setup_local.ps1`
- `scripts/run_build.ps1`
- `scripts/run_build_offline.ps1`

Not found during the 2026-07-09 index update:

- `package.json`
- `pyproject.toml`
- `Makefile`
- `.github/` workflow files

## Setup

Explicit command from `scripts/setup_local.ps1`:

Create local private folders and copy example config only where missing:

```powershell
.\scripts\setup_local.ps1
```

Explicit dependency flow from `README.md` and `requirements.txt`:

Manual dependency setup:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux, activate with:

```bash
source .venv/bin/activate
```

Clean-environment note: `build_finance_workbook.py` imports `matplotlib`, but
`requirements.txt` does not currently list it. Verify the environment before
assuming dependency installation is complete.

## CLI Help

Explicit command from `README.md`, `AGENTS.md`, and existing docs:

```bash
python build_finance_workbook.py --help
```

The current CLI options are:

- `--input`
- `--output`
- `--accounts`
- `--categories`
- `--currency-rates`
- `--cache`
- `--report`
- `--settings`
- `--package-dir`
- `--no-fx-download`
- `--fx-provider`
- `--fx-mode`

## Build

Explicit command from `README.md`:

Normal build:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx
```

Explicit command from `scripts/run_build.ps1`:

PowerShell wrapper:

```powershell
.\scripts\run_build.ps1
```

Explicit command from `README.md` and `scripts/run_build_offline.ps1`:

Offline FX build:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx --no-fx-download
```

PowerShell wrapper:

```powershell
.\scripts\run_build_offline.ps1
```

Builds can read private input files and rewrite ignored outputs, reports, and
caches. Do not run them for docs-only tasks unless the user asks.

## Non-Mutating Validation

Explicit command from `README.md`, `AGENTS.md`, and existing docs:

```bash
python build_finance_workbook.py --help
```

Inferred command based on the current Python module layout:

```bash
python -m py_compile build_finance_workbook.py bank_parsers/common.py bank_parsers/investments.py bank_parsers/revolut.py bank_parsers/slsp.py bank_parsers/tatrabanka.py
```

## Privacy Checks

Explicit Git safety checks from `AGENTS.md` and existing docs:

```bash
git status --ignored
git diff --cached
```

Use these before staging or reporting that a change is safe to commit.

## Documentation Link Check

There is no tracked Markdown linter. A local PowerShell relative-link check is
documented in `docs/reports/2026-07-07-documentation-reorganization.md`.
