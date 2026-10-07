---
name: publish
description: Force-publish the intended state by bypassing only eligible repository or deployment-process gates while preserving external platform protections.
---

# Publish

## Shared contracts

Read `AGENTS.md`, then the workflow's contracts:

- [core](../../.agent/contracts/core.md)
- [authorization](../../.agent/contracts/authorization.md)
- [verification](../../.agent/contracts/verification.md)
- [deployment](../../.agent/contracts/deployment.md)
- [handoff](../../.agent/contracts/handoff.md)

## Project context

Use `.agent/project.yaml` for discovery and the existing `00_Index.md` routing.
Consult task-relevant source, commands, and accepted decisions; resolve paths
from the repository root. Follow scoped instructions without loading unrelated
contracts or private finance content.

## Workflow

1. Confirm explicit force-publication intent, target, revision, and applicable
   authority. Ordinary requests to push source or create a release do not imply
   these semantics; route them to push or release instead.
2. Inspect actual deployment configuration. This local CLI has no target or
   publication workflow: report that prerequisite and do not invent a force path.
3. If a real deployment exists, identify exactly why normal deployment is
   blocked and who controls the gate. Classify before taking any force action.
4. Apply only the minimum eligible repository/deployment-process bypass covered
   by authority. Preserve failed and intentionally bypassed check statuses.
5. Verify the resulting revision and live state, reporting any partial failure,
   rollback, or unverified acceptance explicitly.

## Decision rules

External branch protections, Rulesets, required checks/reviews, environment
approvals, organization governance, hosting protections, IAM, and cloud policy
cannot be bypassed. Administrative access never makes them eligible.

Privacy and authorization are not bypassable process gates. Do not weaken
checks, remove protections, or silently substitute a different target. A normal
governed deployment belongs to deploy; release does not imply live publication.

## Completion and handoff

Identify the blocker, its classification, any eligible bypass actually used,
all failed/skipped checks, and live verification. For this repository as
configured, report the absent target; no force publication has occurred.
