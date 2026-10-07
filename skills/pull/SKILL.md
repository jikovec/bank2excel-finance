---
name: pull
description: Safely synchronize local repository state with upstream while preserving unrelated work and reconciling conflicts according to repository conventions.
---

# Pull

## Shared contracts

Read `AGENTS.md`, then the workflow's contracts:

- [core](../../.agent/contracts/core.md)
- [authorization](../../.agent/contracts/authorization.md)
- [git-github](../../.agent/contracts/git-github.md)
- [handoff](../../.agent/contracts/handoff.md)

## Project context

Use `.agent/project.yaml` for discovery and the existing `00_Index.md` routing.
Consult task-relevant source, commands, and accepted decisions; resolve paths
from the repository root. Follow scoped instructions without loading unrelated
contracts or private finance content.

## Workflow

1. Inspect current instructions, worktree/index/untracked status, active branch,
   upstream, remotes, and concurrent worktrees. Capture a preservation baseline.
2. Fetch the canonical remote and determine divergence from the intended
   upstream. Distinguish remote-tracking refresh from checkout synchronization.
3. Prefer fast-forward integration when safe. With dirty or concurrent work,
   use isolation or stop only the dependent integration; do not reset/stash/clean
   another worker's changes. Analyze divergence before a rebase or merge.
4. Resolve understood conflicts according to source and repository conventions.
   Surface unresolved semantic conflicts instead of guessing or accepting all
   of either side. Verify affected behavior after integration.
5. Read back branch/ref/status and compare preserved work to the baseline.

## Decision rules

A question about divergence belongs to investigate; an instruction to integrate
upstream belongs here. Destructive reset is not synchronization. A rebase of
shared/protected history requires the authority and safeguards in the Git contract.

Load verification contract when running checks, and follow private-safe
validation. No private workbook build or unrelated dependency installation is
implied by synchronization. Do not manufacture a new release or deployment.

## Completion and handoff

Report prior/resulting refs, fetched upstream, integration method, conflicts,
checks, and preserved changes. Say clearly if only fetch completed and local
integration remains blocked. Do not claim the checkout is current merely
because origin/main was refreshed.
