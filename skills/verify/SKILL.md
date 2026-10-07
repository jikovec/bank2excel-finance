---
name: verify
description: Independently verify claimed repository, branch, PR, release, deployment, or live state using current evidence.
---

# Verify

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

1. Translate the claim into falsifiable criteria and identify its target:
   worktree, commit, PR head, source release, runtime, or observed live state.
2. Obtain current source and relevant evidence independently of the previous
   agent's report. Read Git/GitHub or deployment contracts for those domains;
   read scope/memory contracts only when their claims are being verified.
3. Select proportionate checks through
   `.agent/workflows/private-safe-validation.md`. Verify exact targets; a
   passing old revision does not establish a changed revision.
4. Execute available checks and classify every relevant result. Distinguish
   structural metadata checks, semantic review, and actual provider discovery.
5. Compare evidence with the original criteria without weakening them.

## Decision rules

Default to verification only. Do not fix source or change policy to manufacture
a pass. Reviewing a patch for unknown defects belongs to `review`; verifying
that a claimed fix actually exists and works belongs here.

No test suite, missing dependencies, or unavailable CI must remain visible.
Never infer a release from a notes filename or live acceptance from a merge.

## Completion and handoff

Return the claim, target, verdict, evidence, and material limitations. State
which criteria passed, failed, were unavailable, intentionally bypassed, or
not required. A constrained static check must not become a broader success claim.
