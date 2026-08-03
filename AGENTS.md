# Codex Project Memory

This repo uses a memory-first workflow for future Codex work. Start with
`00_Index.md`, then follow the task-specific docs it links before inspecting
source files.

## Required Read Order

Before meaningful work in this repo:

1. Read `AGENTS.md`.
2. Read `00_Index.md`.
3. Read `docs/current-state.md`.
4. Read `docs/decisions.md`.
5. Inspect relevant `reports/` or `handoffs/` entries when they exist and are
   safe to read.

## Operating Rules

- Treat current source, config examples, scripts, and Git state as the source of truth.
- Keep real financial data private. Do not read or edit `.env`, non-example config
  files, bank exports, generated workbooks, caches, private finance snapshots,
  or private report contents unless the user explicitly asks.
- Do not move, delete, or rename files unless the user explicitly asks.
- Do not commit, push, or publish without an explicit user request.
- Prefer documentation-only fixes for memory tasks. Do not edit application source
  code during documentation validation unless the user changes the scope.
- Avoid full workbook builds unless the user asks for build validation, because
  builds read private `input/` data and rewrite ignored `output/`, `cache/`, and
  `reports/` artifacts.
- Preserve existing behavior unless the user explicitly asks for a behavior
  change.
- After meaningful changes, update `docs/current-state.md` or create a handoff
  note under `handoffs/` when future agents need context.

## Repo Summary

This is a local Python CLI workbook generator. It is not a web app and does not
contain HTTP routes, an OpenAPI contract, or a frontend.

Primary entrypoints:

- `build_finance_workbook.py`
- `bank_parsers/`
- `scripts/setup_local.ps1`
- `scripts/run_build.ps1`
- `scripts/run_build_offline.ps1`

Project memory and handoff docs:

- `01_Finance_Home.md`
- `finance/README.md`
- `finance/how-it-works.md`
- `finance/current-situation.template.md`
- `finance/current-situation.example.json`
- `finance/current-situation.schema.json`
- `00_Index.md`
- `docs/current-state.md`
- `docs/decisions.md`
- `docs/commands.md`
- `docs/testing.md`
- `docs/security-model.md`
- `docs/README.md`
- `docs/AGENT-INDEX.md`
- `docs/OBSIDIAN.md`
- `docs/SOURCE-MAP.md`
- `docs/CONNECTIONS.md`
- `docs/agent-index.json`
- `handoffs/`

Private current-finance state belongs under `finance/private/`. The tracked
files under `finance/` define its structure but must not contain real balances
or personal financial details.

## Validation Expectations

Safe non-private checks:

```bash
python build_finance_workbook.py --help
```

```bash
python -m py_compile build_finance_workbook.py bank_parsers/common.py bank_parsers/investments.py bank_parsers/revolut.py bank_parsers/slsp.py bank_parsers/tatrabanka.py
```

Privacy checks before staging:

```bash
git status --ignored
git diff --cached
```

See `docs/testing.md` and `docs/commands.md` for the full command reference.
## GitHub Pro repository memory

<!-- github-pro-memory:2026-07-30 -->
- Identity: `jikovec/bank2excel-finance`; visibility: public; remote default: `main`; personal-account repository where applicable.
- Observed state (2026-07-30): protection: not protected; Pages: not enabled; wiki enabled: True; observed Actions runs: 0 in the fixed 2026-06-30..2026-07-30 window.
- Use selectively: Keep Releases for versioned source milestones; Optional lightweight public CI only after tests are input-independent
- Explicitly avoid: GitHub Pages; GitHub Packages; Codespaces with financial input; Wiki duplication; Mandatory human approval
- Actions: provisional private-minute allocation **0/month**; priority: none. Exact billed minutes remain unverified.
- Branch target: Optional status-check protection if input-independent CI is added; no required human approval for the solo maintainer.
- CODEOWNERS: No value while there is one owner.
- Packages: None; requirements are application dependencies, not a reusable package product.
- Codespaces: Unsuitable because real work depends on private local bank exports; keep processing local.
- Pages/wiki: Do not enable; public documentation adds little and increases the chance of publishing financial examples or paths. Keep repository Markdown and local memory authoritative despite the enabled wiki flag.
- Pending remote action only: None until an input-independent CI proposal is separately approved.
- Safety: this is local guidance only. It does not authorize commit, push, PR, deployment, publication, workflow execution, remote settings, collaborators or billing. Preserve all stricter project-specific no-push/no-deploy and protected-path rules above.
- Central authority: local project-memory GitHub Pro guidance outside this
  repository; its machine-specific absolute path is intentionally omitted.
