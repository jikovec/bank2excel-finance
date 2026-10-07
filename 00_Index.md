# Project Memory Index

Project name: `bank2excel-finance`

Project path: repository root. Local absolute checkout paths are intentionally
omitted from tracked documentation.

This is the first file to read for future Codex work in this repository. It is
an Obsidian/VaultGuard-style project memory adapted to this local finance
workbook repo.

For the human-facing personal-finance view, start at
[01_Finance_Home.md](01_Finance_Home.md). Project memory and private financial
state are intentionally separate.

## Project Profile

Apparent purpose from repo contents: local Python CLI workbook generator for
personal finance analysis. It imports bank exports and investment snapshots,
normalizes transactions, applies FX handling, and writes an Excel workbook plus
validation evidence while keeping real financial data out of Git.

Apparent stack:

- Python CLI entrypoint: `build_finance_workbook.py`
- Parser package: `bank_parsers/`
- PowerShell helper scripts: `scripts/`
- Python dependencies declared in `requirements.txt`
- Markdown documentation under `docs/`

Key source and runtime folders:

- `bank_parsers/` - parser modules for transactions and investment snapshots.
- `config/` - tracked examples plus ignored private local config.
- `scripts/` - local setup and build wrappers.
- `input/` - ignored private bank exports.
- `output/` - ignored generated workbooks.
- `cache/` - ignored FX/cache artifacts.
- `reports/` - ignored private validation/build evidence.
- `docs/` - tracked project documentation and memory docs.
- `finance/` - tracked finance-vault guides and templates plus ignored private
  point-in-time snapshots under `finance/private/`.
- `handoffs/` - future handoff notes for agent work.

## Start Here

1. Read `AGENTS.md` for operating rules and privacy boundaries.
2. Read `01_Finance_Home.md` when the task concerns the personal financial
   picture rather than application implementation.
3. Read `docs/current-state.md` for the current repo shape and known gaps.
4. Read `docs/commands.md` before running setup, validation, or build commands.
5. Read `docs/security-model.md` before touching input, config, output, cache, or
   report paths.
6. Read `docs/testing.md` before claiming a validation result.
7. Read `docs/AGENT-INDEX.md` when planning multi-file docs, source, or
   handoff work.

## Agent Toolkit

[Portable workflow routing](.agent/README.md) and
[stable project identity](.agent/project.yaml) supplement this product index.
`AGENTS.md` remains the first contract; `skills/` owns the canonical workflows.

## Memory Files

- [Agent instructions](AGENTS.md)
- [Personal finance home](01_Finance_Home.md)
- [Finance vault guide](finance/README.md)
- [How the finance system works](finance/how-it-works.md)
- [Current state](docs/current-state.md)
- [Decisions](docs/decisions.md)
- [Commands](docs/commands.md)
- [Testing](docs/testing.md)
- [Security model](docs/security-model.md)
- [Future-agent index](docs/AGENT-INDEX.md)
- [Obsidian guide](docs/OBSIDIAN.md)
- [Source map](docs/SOURCE-MAP.md)
- [Connection map](docs/CONNECTIONS.md)
- [Machine-readable agent index](docs/agent-index.json)
- [Handoffs](handoffs/)

## Existing Documentation

- [Documentation index](docs/README.md)
- [Project overview](docs/project-overview.md)
- [Personal finance home](01_Finance_Home.md)
- [Finance vault guide](finance/README.md)
- [Current-situation snapshot format](finance/current-situation.template.md)
- [Pipeline architecture](docs/architecture/pipeline.md)
- [API and CLI surface](docs/api/README.md)
- [Development setup](docs/setup/development.md)
- [Bank export guide](docs/setup/bank-export-guide.md)
- [Maintenance](docs/setup/maintenance.md)
- [Data privacy](docs/security/data-privacy.md)
- [Verification workflow](docs/testing/verification.md)
- [Reports index](docs/reports/README.md)
- [Handoff index](handoffs/INDEX.md)
- [Future-agent index](docs/AGENT-INDEX.md)
- [Obsidian guide](docs/OBSIDIAN.md)
- [Source map](docs/SOURCE-MAP.md)
- [Connection map](docs/CONNECTIONS.md)
- [Changelog](docs/releases/changelog.md)

Equivalent architecture documentation exists at
`docs/architecture/pipeline.md`; do not create a duplicate `docs/architecture.md`
unless the documentation structure is intentionally changed.

Versioned release notes are stored under `docs/releases/`. The historical Git
tag `v0.0.1` remains the only pre-documentation release tag found during the
inventory.

## Reports And Handoffs

- Tracked report index: `docs/reports/README.md`
- Ignored local report area: `reports/`
- Handoff index: `handoffs/INDEX.md`

Current local validation report:

- `reports/project-memory-validation-2026-07-07.md`

Root `reports/` is ignored because it can contain private data. The current
validation report was written there because the user explicitly requested a
report in `reports/`.
