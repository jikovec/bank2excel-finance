---
name: review
description: Review a change, branch, pull request, or implementation for material correctness, regression, architecture, security, and maintainability issues.
---

# Review

## Shared contracts

Read `AGENTS.md`, then the workflow's contracts:

- [core](../../.agent/contracts/core.md)
- [verification](../../.agent/contracts/verification.md)
- [handoff](../../.agent/contracts/handoff.md)

## Project context

Use `.agent/project.yaml` for discovery and the existing `00_Index.md` routing.
Consult task-relevant source, commands, and accepted decisions; resolve paths
from the repository root. Follow scoped instructions without loading unrelated
contracts or private finance content.

## Workflow

1. Establish the change, target/base, intended behavior, and governing decisions.
   Read Git/GitHub contract when reviewing branches/PRs; preserve the checkout.
2. Inspect the diff with enough surrounding source to assess data/control flow.
   Prioritize correctness and requested behavior, regressions, contracts,
   architecture, security, tests, and maintainability. Consider performance or
   accessibility only when actually relevant; avoid materiality-free style noise.
3. Check boundary conditions and realistic failure cases using safe source or
   input-independent evidence. Follow the private-safe validation workflow.
4. Separate defects introduced by this change from historical issues. Explain
   the concrete trigger, consequence, and affected source location.
5. Check that claimed validation and delivery match evidence at the actual head.

## Decision rules

Default to review only; do not implement repairs or post comments externally
unless the task authorizes those effects. Use `fix` when repairs are requested.
Use `verify` for a specific completion claim rather than open-ended defect search.

Do not require private financial examples to make a review concrete. Clearly
label potential concerns that lack enough evidence to count as findings.

## Completion and handoff

Lead with material findings, ordered by impact, with precise paths/lines and
reasoning. If no actionable findings exist, say so with the review scope and
verification limits. No findings is not a certification or proof of live safety.
