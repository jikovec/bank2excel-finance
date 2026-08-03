---
type: finance-home
scope: personal-finance-vault
privacy: shareable-structure
last_reviewed: 2026-08-03
---

# Finance Home

This is the human-facing entry point for the finance vault. Use
[00_Index.md](00_Index.md) for project and agent memory, and use this page for
the current financial picture, the refresh routine, and interpretation rules.

Actual balances, income, expenses, account details, and personal notes stay in
the ignored `finance/private/` folder. The tracked files describe the structure
without publishing personal values.

## Current Situation

The private snapshot has been initialized but is **not populated**. No bank
exports, private config, workbooks, or generated reports were read to create it.
Unknown values are stored as `null`, never as an invented zero.

Local working files:

- `finance/private/current-situation.json` - structured snapshot.
- `finance/private/current-situation.md` - readable interpretation and actions.

Tracked starting points:

- [Finance vault guide](finance/README.md)
- [How the finance system works](finance/how-it-works.md)
- [Markdown snapshot template](finance/current-situation.template.md)
- [JSON snapshot example](finance/current-situation.example.json)
- [JSON snapshot schema](finance/current-situation.schema.json)

## Vault Map

| Area | Purpose | Privacy |
| --- | --- | --- |
| `finance/` | Finance concepts, templates, and machine-readable contract. | Tracked and shareable. |
| `finance/private/` | Current personal snapshot and narrative. | Local and ignored. |
| `docs/` | Software operation, architecture, testing, and security. | Tracked and shareable. |
| `input/` | Original bank exports and investment snapshots. | Local and ignored. |
| `output/` | Generated workbook. | Local and ignored. |
| `reports/` | Validation evidence and private reports. | Local and ignored. |

## Regular Workflow

1. Add new exports under `input/` and update private config only when needed.
2. Build the workbook using the documented local command.
3. Review the workbook dashboards and `reports/validation_summary.md`.
4. Copy verified aggregate values into the private JSON snapshot.
5. Update the private Markdown note with context, risks, and next actions.
6. Mark the snapshot `current` only when its date, coverage, and validation are
   known.

See [How the finance system works](finance/how-it-works.md) for definitions and
the source-of-truth order.

Tags: #finance/snapshot #finance/privacy #obsidian/local #repo/index
