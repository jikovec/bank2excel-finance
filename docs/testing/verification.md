# Testing And Verification

The current repo does not include a dedicated automated test suite or CI config. Verification is currently a combination of Python import/compile checks, local builds, the workbook validation built into `build_finance_workbook.py`, generated validation reports, and privacy-oriented Git checks.

## Basic Python Check

Compile the Python entrypoint and parser modules:

```bash
python -m py_compile build_finance_workbook.py bank_parsers/common.py bank_parsers/investments.py bank_parsers/revolut.py bank_parsers/slsp.py bank_parsers/tatrabanka.py
```

This catches syntax errors without reading private input files or writing outputs.

## Build Verification

Normal build:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx
```

Offline build:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx --no-fx-download
```

The build writes:

- `output/Personal_Finance_Analysis.xlsx`
- `reports/validation_summary.md`
- `cache/currency_rates_cache.csv`, when FX cache updates are needed

These files are private and ignored by Git.

## Built-In Workbook Validation

After writing the workbook, the script calls `validate_workbook_file()`. It checks that required workbook sheets exist and scans worksheet formulas for common error tokens such as `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, and `#N/A`.

Any workbook validation warnings are folded into the generated validation summary.

## Validation Report Review

Review `reports/validation_summary.md` after each meaningful data or parser change. Important sections include:

- Source file import table.
- Investment snapshot import table.
- Checks performed.
- Parser warnings and assumptions.
- Final cleanup pass.
- Manual review recommendations.

Warnings are not always failures. Some warnings intentionally preserve uncertainty, such as transfer-like rows that lack own-account evidence or recurring-like groups with weak cadence evidence.

## Privacy Check

Before staging changes:

```bash
git status --ignored
git diff --cached
```

Confirm that ignored private files remain ignored and that staged files do not include real exports, workbooks, private config, caches, or generated reports.

## Documentation Link Check

There is no tracked Markdown linter or link checker config. A basic local link check can be run with PowerShell by scanning Markdown links and confirming that relative file targets exist. The documentation reorganization report records the exact command used for the 2026-07-07 cleanup.
