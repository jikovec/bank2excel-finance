# Current State

Reviewed on 2026-08-03 for the v0.0.2 documentation and vault release. No private
financial inputs or generated artifacts were opened during this review.

## Product Shape

This repository is a local Python CLI pipeline that builds a personal finance
Excel workbook from bank exports and private config.

It currently contains:

- One CLI entrypoint: `build_finance_workbook.py`.
- Parser modules under `bank_parsers/`.
- PowerShell helper scripts under `scripts/`.
- Example config under `config/`.
- Ignored private runtime folders for `input/`, `output/`, `cache/`, and
  `reports/`.
- Documentation under `docs/`.
- A human-facing finance-vault layer through `01_Finance_Home.md` and
  `finance/`, with tracked templates and an ignored `finance/private/` area.
- Repo-root Obsidian/VaultGuard project-memory scaffolding through
  `.obsidian/`, `00_Index.md`, `AGENTS.md`, and `handoffs/`.
- Future-agent and Obsidian orientation docs through `docs/AGENT-INDEX.md`,
  `docs/OBSIDIAN.md`, `docs/SOURCE-MAP.md`, `docs/CONNECTIONS.md`,
  `docs/agent-index.json`, and `handoffs/INDEX.md`.

It does not currently contain:

- A web server.
- HTTP routes.
- An OpenAPI document.
- A frontend app.
- A dedicated `tests/` directory.
- A `.github/` CI workflow directory.
- `package.json`, `pyproject.toml`, or `Makefile`.

## Supported Inputs

Transaction discovery is registered for these source keys in
`discover_transactions()`:

- `revolut`
- `tatrabanka`
- `tatra`
- `slsp`
- `slovenska_sporitelna`
- `slovenska sporitelna`
- `slovenská sporiteľňa`
- `legacy`

Investment snapshot discovery is registered for SLSP-style investment folders
under `input/investments/`.

The shared reader supports `.csv`, `.xlsx`, and `.xls` tabular files. PDF files
are discovered but intentionally unsupported unless a specific reliable parser is
added later.

## Outputs

Normal builds write private generated artifacts:

- `output/Personal_Finance_Analysis.xlsx`
- `reports/validation_summary.md`
- `cache/currency_rates_cache.csv`, when FX cache updates are needed

These locations are ignored by Git and can contain private financial data.

## Finance Vault Snapshot

The vault now defines a point-in-time current-situation format:

- `finance/current-situation.schema.json` - machine-readable field contract.
- `finance/current-situation.example.json` - tracked null-valued example.
- `finance/current-situation.template.md` - tracked narrative template.
- `finance/private/current-situation.json` - ignored local structured state.
- `finance/private/current-situation.md` - ignored local readable state.

The local snapshot was initialized on 2026-08-01 with status `not_populated`.
All financial values remain `null`; no private inputs, config, workbooks, or
reports were inspected. The snapshot is manual and is not currently generated
by `build_finance_workbook.py`.

## Dependencies

`requirements.txt` currently lists:

- `pandas`
- `openpyxl`
- `xlsxwriter`
- `xlrd`
- `PyYAML`

`build_finance_workbook.py` also imports `matplotlib`. Existing docs correctly
flag this as a clean-environment gap to verify before assuming
`pip install -r requirements.txt` is complete.

## Validation Snapshot

Observed locally during memory validation:

- `python --version` returned Python 3.11.9.
- `python build_finance_workbook.py --help` passed and listed the documented CLI
  options.
- No `tests/` directory was found.
- No `.github/` directory was found.
- A full workbook build was not run during memory validation to avoid rewriting
  private generated outputs.

On 2026-07-09, the repo path and Git backing were rechecked for cross-project
memory indexing. `.obsidian/` and `handoffs/` are present for repo-root
Obsidian/VaultGuard use.

On 2026-07-09, the Obsidian and future-agent indexing layer was implemented as
documentation-only work. No application source, build logic, parser behavior,
or private finance data was changed.

On 2026-08-01, the human-facing finance-vault layer and private snapshot format
were added as documentation-only work. No application behavior or financial
figures were changed.

## Git And Release State

The historical repo tag `v0.0.1` is an annotated tag object that peels to commit
`67d02c4`. Version `v0.0.2` consolidates the documentation reorganization,
memory-first workflow, Obsidian and future-agent indexes, finance-vault
structure, and privacy rules documented in
[`docs/releases/v0.0.2.md`](releases/v0.0.2.md).

No application source, parser behavior, build logic, dependency declaration,
or generated workbook format changed in v0.0.2. The release is a tracked
documentation, navigation, privacy-boundary, and local-vault milestone.
