---
name: fix
description: Diagnose and repair a known defect, failed check, incomplete prior change, review finding, or inconsistency between authoritative project states.
---

# Fix

## Shared contracts

Read `AGENTS.md`, then the workflow's contracts:

- [core](../../.agent/contracts/core.md)
- [authorization](../../.agent/contracts/authorization.md)
- [verification](../../.agent/contracts/verification.md)
- [git-github](../../.agent/contracts/git-github.md)
- [handoff](../../.agent/contracts/handoff.md)

## Project context

Use `.agent/project.yaml` for discovery and the existing `00_Index.md` routing.
Consult task-relevant source, commands, and accepted decisions; resolve paths
from the repository root. Follow scoped instructions without loading unrelated
contracts or private finance content.

## Workflow

1. Establish the defect, failing criterion, current baseline, and intended
   behavior. Inspect source and diagnostics before proposing changes.
2. Reproduce through the smallest safe input-independent case when possible.
   If reproduction requires private input, retain that evidence limitation
   rather than opening protected data or fabricating a synthetic reproduction.
3. Trace and repair the causal defect. Preserve architecture and unrelated work;
   do not mask failures with retries, sleeps, weaker checks, or wider exceptions.
4. Recheck the failure case and affected behavior through private-safe validation.
   Correct stale canonical docs when the repaired behavior warrants it.
5. Complete applicable repository delivery, check current PR evidence, and verify
   the remote target when merge is in scope.

## Reconciliation intent

`reconcile` invokes this skill. Compare source, documentation, Git, GitHub,
runtime/deployment, registry, memory, and prior handoffs as distinct evidence
owners. Update the incorrect representation, not the authority hierarchy.
Read memory/scopes only when reconciliation crosses persistent state. Reuse
existing work objects; do not create competing Issues, identities, or records.

## Completion and handoff

Explain the cause, repair, regression evidence, unresolved verification limits,
and actual delivery state. Adjacent improvements are separate follow-up.
A substantial new capability belongs to `build`; diagnosis alone to `investigate`.
