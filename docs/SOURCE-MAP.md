# Source Map

This map connects repo areas to their responsibilities and documentation.

## Core Pipeline

| Area | Responsibility | Docs |
| --- | --- | --- |
| `build_finance_workbook.py` | CLI parsing, settings resolution, discovery, post-processing, FX handling, validation, workbook writing, and validation summary writing. | [Pipeline architecture](architecture/pipeline.md), [API and CLI surface](api/README.md) |
| `bank_parsers/common.py` | Shared normalized transaction schema, tabular reading, date/amount parsing, PDF unsupported warning, and import-report helpers. | [Pipeline architecture](architecture/pipeline.md), [Bank export guide](setup/bank-export-guide.md) |
| `bank_parsers/revolut.py` | Revolut transaction parsing. | [Bank export guide](setup/bank-export-guide.md) |
| `bank_parsers/tatrabanka.py` | Tatra banka transaction parsing. | [Bank export guide](setup/bank-export-guide.md) |
| `bank_parsers/slsp.py` | Slovenska sporitelna transaction parsing with header-row detection. | [Bank export guide](setup/bank-export-guide.md) |
| `bank_parsers/investments.py` | SLSP investment and savings valuation snapshot parsing. | [Project overview](project-overview.md), [Pipeline architecture](architecture/pipeline.md) |

## Configuration And Runtime Areas

| Area | Responsibility | Privacy |
| --- | --- | --- |
| `config/*.example.*` | Fake tracked templates for accounts, categories, manual rates, and settings. | Shareable. |
| `config/README.md` | Documents private config expectations. | Shareable. |
| `config/accounts.csv`, `config/categories.csv`, `config/currency_rates.csv`, `config/settings.yaml` | Local private config used by builds. | Ignored and private. |
| `input/` | Bank exports and investment snapshots. | Ignored and private. |
| `output/` | Generated workbook output. | Ignored and private. |
| `cache/` | FX cache artifacts. | Ignored and private. |
| `reports/` | Generated validation/build evidence and local reports. | Ignored and private by default. |
| `finance/` | Finance-vault hub, operating guide, templates, and JSON schema. | Tracked structure only; no real values. |
| `finance/private/` | Current structured snapshot and narrative financial review. | Ignored and private. |
| `docs/reports/` | Scrubbed, shareable reports. | Tracked docs only. |

## Scripts And Commands

| Area | Responsibility | Docs |
| --- | --- | --- |
| `scripts/setup_local.ps1` | Creates local folders and copies example files without overwriting private files. | [Development setup](setup/development.md), [Commands](commands.md) |
| `scripts/run_build.ps1` | Runs the normal workbook build. | [Commands](commands.md), [Testing](testing.md) |
| `scripts/run_build_offline.ps1` | Runs the workbook build with `--no-fx-download`. | [Commands](commands.md), [Testing](testing.md) |
| `requirements.txt` | Python dependency list. | [Development setup](setup/development.md), [Current state](current-state.md) |

## Documentation Ownership

| Need | Primary doc |
| --- | --- |
| Start point for humans and agents | [README](../README.md), [00_Index](../00_Index.md), [AGENTS](../AGENTS.md) |
| Repo shape and known gaps | [Current state](current-state.md) |
| Product and input/output overview | [Project overview](project-overview.md) |
| Personal financial situation and review flow | [Finance Home](../01_Finance_Home.md), [Finance vault](../finance/README.md), [How it works](../finance/how-it-works.md) |
| Architecture and data flow | [Pipeline architecture](architecture/pipeline.md) |
| CLI and parser extension surfaces | [API and CLI surface](api/README.md) |
| Commands and validation | [Commands](commands.md), [Testing](testing.md), [Verification workflow](testing/verification.md) |
| Privacy and security boundaries | [Security model](security-model.md), [Data privacy](security/data-privacy.md) |
| Future-agent routing | [Future-agent index](AGENT-INDEX.md), [Connection map](CONNECTIONS.md), [agent-index.json](agent-index.json) |

Tags: #repo/source-map #repo/architecture #python/cli #finance/workbook
