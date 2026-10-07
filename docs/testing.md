# Testing

The current repo has no dedicated automated test suite and no CI workflow
directory. Validation is a combination of non-mutating checks, optional local
builds, generated validation summaries, and privacy checks.

## Safe Checks For Docs-Only Work

Use these checks when validating documentation or project memory:

Explicit command from `README.md`, `AGENTS.md`, and `docs/commands.md`:

```bash
python build_finance_workbook.py --help
```

Inferred command based on the current Python module layout:

```bash
python -m py_compile build_finance_workbook.py bank_parsers/common.py bank_parsers/investments.py bank_parsers/revolut.py bank_parsers/slsp.py bank_parsers/tatrabanka.py
```

CLI help verifies importability and the current argument surface without reading
private input files. Compile checks catch syntax errors but can write
`__pycache__` bytecode in normal Python configurations.

## Agent Toolkit Checks

Run `python .agent/hooks/validate-toolkit.py` for metadata, frontmatter,
adapter parity, local links, and routing-case coverage. See
[hook contract](../.agent/hooks/README.md). Review routing cases semantically
and test provider discovery separately when available. Structural success
does not prove skill behavior or application correctness.

## Build Verification

Explicit command from `README.md` and `scripts/run_build.ps1`:

Run a normal build only when build validation is in scope:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx
```

Explicit command from `README.md` and `scripts/run_build_offline.ps1`:

Run offline when external FX downloads should be disabled:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx --no-fx-download
```

Builds read ignored private input data and can rewrite:

- `output/Personal_Finance_Analysis.xlsx`
- `reports/validation_summary.md`
- `cache/currency_rates_cache.csv`

## Validation Report Review

After a build, review `reports/validation_summary.md`. It can include private
paths and transaction evidence, so keep it in ignored root `reports/` unless it
has been scrubbed for `docs/reports/`.

Important sections:

- Source file import table.
- Investment snapshot import table.
- FX status.
- Parser warnings.
- Manual review recommendations.
- Workbook validation warnings.

## Privacy Verification

Explicit Git safety checks from `AGENTS.md` and `docs/commands.md`:

Before staging or handing off a commit-ready state:

```bash
git status --ignored
git diff --cached
```

Confirm that private exports, workbooks, caches, generated reports, `.env`, and
non-example config files are not staged.

## Known Gaps

- No `tests/` directory was found during the 2026-07-07 memory validation.
- No `.github/` CI workflow directory was found.
- `requirements.txt` does not list `matplotlib`, although the CLI imports it.
- Full build behavior depends on local private data and was not revalidated
  during the memory-first docs check.

See also `docs/testing/verification.md`.
