# Bank Export Guide

Put real bank exports in the matching ignored input folder. Do not commit files from `input/`.

## Supported File Types

The shared file reader supports `.csv`, `.xlsx`, and `.xls` for tabular imports. PDF files are discovered, but PDF parsing is intentionally unsupported unless a reliable extraction path is added for a specific bank export layout.

Temporary Office lock files beginning with `~$` are skipped.

## Transaction Exports

Use these folders for current tracked defaults:

| Source | Folder | Notes |
| --- | --- | --- |
| Revolut | `input/revolut/` | CSV or XLSX tabular exports are expected. |
| Tatra banka | `input/tatrabanka/` | XLS or XLSX tabular exports are expected. |
| Slovenska sporitelna | `input/slsp/` | XLS or XLSX tabular exports are expected. The parser can detect metadata rows before the actual header. |

The discovery code also recognizes locally created aliases such as `input/tatra/`, `input/slovenska_sporitelna/`, and `input/legacy/`.

## Investment Snapshots

Investment valuation snapshots are point-in-time holdings, not transactions.

Place SLSP investment or savings valuation snapshots in:

```text
input/investments/slsp/
```

Snapshots are imported into `Investment_Snapshots` and summarized separately from transaction income and expenses.

## Unsupported Or Unidentified Files

Unsupported or unidentified files are preserved in `input/` and reported in the generated validation summary. The parser does not invent rows when it cannot identify a file layout.

After a build, review:

```text
reports/validation_summary.md
```

The source-file import table lists detected formats, parsed rows, skipped rows, skipped reasons, date ranges, currencies, and parser warnings.
