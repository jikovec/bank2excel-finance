# 2026-07-07 Documentation Reorganization Report

## Scope

This report documents a documentation-only cleanup. Source/runtime behavior was intentionally left unchanged.

## Inventory Reviewed

Tracked documentation and documentation-adjacent files reviewed:

- `README.md`
- `docs/bank_export_guide.md`
- `docs/data_privacy.md`
- `docs/maintenance.md`
- `config/README.md`
- `input/README.md`
- `requirements.txt`
- `config/settings.example.yaml`
- `scripts/setup_local.ps1`
- `scripts/run_build.ps1`
- `scripts/run_build_offline.ps1`

Ignored private report artifacts observed and preserved in root `reports/`:

- `reports/validation_summary.md`
- `reports/normal_build.log`
- `reports/offline_build.log`
- `reports/build_consistency_summary.json`
- `reports/privacy_scan_summary.json`
- `reports/git_status_ignored.txt`
- `reports/git_init.log`

## Issues Found

- Documentation had no central index.
- Setup, privacy, maintenance, and export placement docs were useful but flat and hard to navigate.
- No tracked architecture doc existed.
- No API/routes status doc existed, even though the current repo is CLI-only.
- No testing/verification doc existed.
- No changelog existed, despite the repo having tag `v0.0.1`.
- Private generated reports were present only in ignored `reports/`; they needed navigation without being moved into tracked docs.

## Files Moved Or Renamed

- `docs/bank_export_guide.md` -> `docs/setup/bank-export-guide.md`
- `docs/maintenance.md` -> `docs/setup/maintenance.md`
- `docs/data_privacy.md` -> `docs/security/data-privacy.md`

## Files Added

- `docs/README.md`
- `docs/project-overview.md`
- `docs/setup/development.md`
- `docs/architecture/pipeline.md`
- `docs/api/README.md`
- `docs/testing/verification.md`
- `docs/releases/changelog.md`
- `docs/reports/README.md`
- `docs/reports/2026-07-07-documentation-reorganization.md`

## Files Extended

- `README.md`
- `config/README.md`
- `input/README.md`
- `docs/setup/bank-export-guide.md`
- `docs/setup/maintenance.md`
- `docs/security/data-privacy.md`

## Docs Archived

No tracked docs were archived or deleted. Existing private report artifacts were intentionally left in ignored root `reports/` and documented from `docs/reports/README.md`.

## Validation Commands

Commands run:

```bash
python -m py_compile build_finance_workbook.py bank_parsers/common.py bank_parsers/investments.py bank_parsers/revolut.py bank_parsers/slsp.py bank_parsers/tatrabanka.py
```

Result: passed.

```bash
python build_finance_workbook.py --help
```

Result: passed. The CLI printed the expected options for input, output, accounts, categories, currency rates, cache, report, settings, package-dir compatibility, FX download mode, provider, and FX mode.

```powershell
$files = Get-ChildItem -Path README.md,docs,config\README.md,input\README.md -Recurse -File -Include *.md
$errors = @()
foreach ($file in $files) {
  $text = Get-Content -Raw -LiteralPath $file.FullName
  foreach ($match in [regex]::Matches($text, '\[[^\]]+\]\(([^)]+)\)')) {
    $target = $match.Groups[1].Value.Trim()
    if ($target -match '^(https?:|mailto:|#)') { continue }
    $clean = ($target -split '#')[0]
    if ([string]::IsNullOrWhiteSpace($clean)) { continue }
    $candidate = Join-Path $file.DirectoryName $clean
    if (-not (Test-Path -LiteralPath $candidate)) {
      $errors += "$($file.FullName): missing link target $target"
    }
  }
}
if ($errors.Count) { $errors; exit 1 }
"Markdown relative links OK ($($files.Count) files checked)"
```

Result: passed. Markdown relative links OK, 15 files checked.

```bash
git diff --check
```

Result: passed. Git printed LF-to-CRLF working-copy warnings for edited Markdown files, but no whitespace errors.

## Intentionally Left Unchanged

- No source/runtime files were changed.
- No private generated report was moved into tracked docs.
- No generated workbook, cache, or local config file was changed intentionally.
- No full workbook build was run during this documentation-only pass, to avoid rewriting private generated outputs after no source/runtime changes.
- No commit or push was created.
