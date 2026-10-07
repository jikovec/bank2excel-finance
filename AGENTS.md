# Repository Agent Contract

Bank2Excel Finance is a local Python CLI workbook generator, owned by the
user in `jikovec/bank2excel-finance`. It has no hosted runtime, HTTP API,
frontend, or deployment target. Project identity is
`github:jikovec/bank2excel-finance`; stable discovery metadata lives in
[.agent/project.yaml](.agent/project.yaml).

## Start here

Before meaningful work:

1. Read this file and applicable scoped instructions.
2. Read [00_Index.md](00_Index.md).
3. Read [current state](docs/current-state.md) and [decisions](docs/decisions.md).
4. Consult relevant safe handoffs or scrubbed reports; ignored root reports
   require explicit private-data authorization.
5. Select the canonical workflow through [.agent/README.md](.agent/README.md).
   Load only the contracts and project documents relevant to the task.

The existing finance vault and documentation indexes remain navigation aids.
Source, config examples, scripts, and current Git state establish technical
truth. Historical notes do not establish current operational state.

## Scope and authority

Complete the requested outcome and its authorized repository delivery workflow.
Do not expand a task into adjacent cleanup, redesign, release, or deployment.
Preserve existing behavior unless a behavior change is requested.

[Authorization](.agent/contracts/authorization.md) owns the standing grant
adopted by the user-requested toolkit bootstrap; [D-008](docs/decisions.md)
records its provenance. Ordinary task-related branches, edits, commits, push,
PRs, checks, and merge are authorized for this user-owned repository, subject
to task restrictions and external controls. Do not repeatedly ask for that
same authority. Release, deployment, and force publication require scope
covering those outcomes. Repository settings and billing are separate scope.

Credentials, tools, identity labels, memory, and a green check do not grant
powers. Never circumvent external protections, required reviews, environment
approvals, organization policy, IAM, or provider controls. Policy amendments
require explicit policy-authoring authority and cannot authorize themselves.

## Preserve work and privacy

- Inspect current instructions, source, and Git state before changes. Preserve
  unrelated dirty, untracked, and concurrent work; use isolation when needed.
- Do not move, delete, or rename existing files without explicit task coverage.
- Keep real financial data private. Do not read or edit `.env`, non-example
  config, bank exports, generated workbooks, caches, private finance snapshots,
  or private report contents unless the user explicitly asks.
- Prefer documentation-only fixes for memory tasks. Do not edit application
  source during documentation validation unless the user changes the scope.
- Do not run full workbook builds for documentation/toolkit work. Builds read
  private input and rewrite ignored output, cache, and report artifacts.
- Keep real financial values under ignored `finance/private/`. Tracked finance
  templates describe structure and must not contain personal financial details.
- Keep financial inputs out of Codespaces and remote agent environments.
  Do not enable Pages, Packages, wiki duplication, or CI as incidental work.
- Follow [security model](docs/security-model.md) before interacting with
  protected paths. Keep credentials, local absolute paths, and private evidence
  out of tracked files, commits, PRs, and external tools.

## Tooling and evidence

`build_finance_workbook.py`, `bank_parsers/`, and `scripts/*.ps1` are the
application entrypoints. [Commands](docs/commands.md) and
[testing](docs/testing.md) own command details. Use the project Python
environment and declared `requirements.txt`; report unavailable dependencies.
The known `matplotlib` declaration gap is not permission to change dependencies
as part of unrelated work.

Verify proportionately. Never report an unexecuted check as passed. Keep local
checks, remote checks, merge, release, deployment, and live acceptance distinct.
Review allowed paths and the staged diff before committing. Update current
state or a safe handoff when meaningful changes need durable context.

## Discovery and context

Canonical workflows live in `skills/`; reusable project extensions, when
justified, live in `skills/project/`. `develop` means `build`; `reconcile` means
`fix` with reconciliation intent. Neither alias has a second implementation.

Provider adapters contain discovery pointers only: `.agents/skills` for
current Codex and `.claude/skills` for Claude Code. `.codex/skills` holds a compatibility pointer to avoid duplicate
discovery. `CLAUDE.md` imports this contract.

[Shared contracts](.agent/README.md) own detailed execution policy. Load memory
and scope contracts only for persistent context, registry/relationship work,
or memory promotion. No Mind-Seed enrollment or external memory binding is
established here. Memory remains contextual, and access is not write authority.
