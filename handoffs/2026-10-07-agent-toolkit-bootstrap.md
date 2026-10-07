# Agent toolkit bootstrap — 2026-10-07

## Scope and identity

Implemented the user-requested portable agent toolkit against source baseline
`b7c28b35e9fbd4f41653da8371d51cc08ca09ee4` in an isolated task worktree.
The original checkout had 17 modified tracked files and one untracked handoff;
they were excluded from this change. No private inputs, config, exports,
workbooks, caches, root reports, or finance snapshots were opened or changed.

Live repository metadata established `jikovec/bank2excel-finance`, public,
personal user ownership, and default branch `main`. Stable project identity is
`github:jikovec/bank2excel-finance`, with null organization fields. There was
no configured external project registry or memory binding to reconcile; no
external registry lookup or mutation is claimed. Mind-Seed stays disabled.
No scope IDs or memory mutation rights were fabricated.

## Result and decisions

The prior Markdown/JSON memory indexes remain product navigation. The large
root contract is replaced by a concise router and eight concern-owned contracts,
with adoption recorded in D-008. The explicitly requested standing repository
grant replaces the old per-operation Git approval rule. Privacy and external
protection boundaries remain intact; source delivery does not imply release.

The toolkit adds eleven canonical workflows, one shared private-safe validation
workflow, GitHub integration guidance, a manual deterministic validator, and
55 routing examples. No project-specific skill, automatic hook, CI, hosted
runtime, new external integration, or release pipeline was invented.

Codex adapters live in `.agents/skills/`; Claude adapters live in
`.claude/skills/`, with `CLAUDE.md` importing `AGENTS.md`. An initial native
probe showed that duplicate `.codex/skills` adapters were also loaded by the
installed Codex. Those newly generated duplicates were removed before delivery;
`.codex/skills/README.md` now holds the compatibility pointer. There is one
canonical body per workflow and no independent provider policy.

## Verification

- Passed: Python syntax compilation of the existing CLI/parser files and the
  new toolkit validator. This does not exercise application behavior.
- Passed: toolkit structural validation of YAML metadata, eleven canonical
  skills, 22 adapters, local toolkit links, and 55 minimum routing cases.
- Passed: skill-creator frontmatter validation for all 33 canonical/adapter
  files; 293 relative Markdown links; `git diff --check`.
- Passed: six isolated negative validator cases rejected invalid names, adapter
  drift, identity mismatch, broken links, missing routing cases, and duplicate
  YAML keys. Clean fixtures passed before and after the negative cases.
- Passed: Codex CLI 0.159.2 `app-server` initialization and `skills/list` with
  forced reload returned exactly eleven enabled repository skills and no
  repository skill errors. No model turn or skill mutation was executed.
- Reviewed: all 55 routing cases and additional alias/force-publication
  boundaries by source inspection. This is not a provider behavior benchmark.
- Blocked/unavailable: ordinary `python build_finance_workbook.py --help`
  failed to import pandas. The application's environment was not changed.
- Not required: full private workbook build, release, deployment, and live
  acceptance. They are outside this source/toolkit bootstrap.
- Not required: hosted CI execution; no workflow or required checks were
  configured at baseline. Absence of CI is not a CI pass.
- Limitation: Claude Code 2.1.284 was present. Frontmatter, adapter targets,
  and its documented import/discovery layout were checked statically; actual
  Claude session discovery and runtime workflow behavior were not exercised.

PyYAML was absent from the host Python. Toolkit parsing used a disposable
validation environment containing the already-declared PyYAML dependency;
this is toolkit-only evidence, not a repaired application environment.

## Delivery and preservation

The bootstrap task authorizes branch, commit, push, PR, checks, and merge.
Exact delivery identities are recorded in Git/PR history and the task result;
this pre-commit handoff does not predict a merge SHA. Original dirty files and
local main are preserved; remote completion does not synchronize that checkout.

Baseline live reads found no open Issues/PRs, linked Projects, rulesets, or
Actions runs; main was unprotected, Pages was disabled, and the sole published
release was v0.0.1. These are dated observations, not standing policy or future
protection evidence. Refresh them before later consequential actions.

The pre-existing matplotlib dependency-declaration gap and private-data build
validation remain separate follow-up. No external memory writes occurred.
