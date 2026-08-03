# Future-Agent Index

This file is the human-readable orientation guide for future Codex or agent
work in this repository.

## Start Workflow

1. Read [AGENTS.md](../AGENTS.md).
2. Read [00_Index.md](../00_Index.md).
3. Read [Finance Home](../01_Finance_Home.md) and the
   [finance-vault guide](../finance/README.md) when the task concerns the current
   financial picture or snapshot structure.
4. Read [current state](current-state.md) and [decisions](decisions.md).
5. Read [commands](commands.md), [testing](testing.md), and
   [security model](security-model.md) before running checks.
6. Use [source map](SOURCE-MAP.md) and [connection map](CONNECTIONS.md) to find
   the owning source, docs, reports, and handoffs for the task.
7. Review [agent-index.json](agent-index.json) when a machine-readable summary
   is useful.

## Safety Rules

- Do not read or edit `.env`, private config files, bank exports, generated
  workbooks, caches, private finance snapshots, or private root reports unless
  the user explicitly asks.
- Do not run a full workbook build for docs-only work.
- Do not commit, push, publish, tag, deploy, or release without an explicit user
  request.
- Preserve existing dirty worktree changes.
- Treat current source, config examples, scripts, `.gitignore`, and safe command
  output as the source of truth when docs disagree.

## Current Product Shape

The repo is a local Python CLI workbook generator. It is not a web service and
does not currently contain HTTP routes, an OpenAPI contract, a frontend,
deployment workflow, a dedicated `tests/` directory, or CI.

Primary implementation areas:

- `build_finance_workbook.py`
- `bank_parsers/`
- `scripts/`
- `config/*.example.*`

Private runtime areas:

- `input/`
- `output/`
- `cache/`
- `reports/`
- `finance/private/`
- `.env`
- non-example files under `config/`

## Update Obligations

After meaningful documentation, source, parser, command, or safety changes:

- Update [current state](current-state.md) when the repo shape changes.
- Update [commands](commands.md) when supported commands change.
- Update [testing](testing.md) and [verification workflow](testing/verification.md)
  when validation behavior changes.
- Update [source map](SOURCE-MAP.md), [connection map](CONNECTIONS.md), and
  [agent-index.json](agent-index.json) when paths or ownership change.
- Add a handoff under [handoffs](../handoffs/INDEX.md) when future agents need
  context that should not live in a permanent doc.
- Keep private generated evidence in root `reports/`; use `docs/reports/` only
  for scrubbed summaries.

Tags: #agent/orientation #repo/index #finance/privacy
