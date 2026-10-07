---
name: push
description: Finalize completed local work through the repository's normal commit, push, pull-request, check, and merge workflow.
---

# Push

## Shared contracts

Read `AGENTS.md`, then the workflow's contracts:

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

1. Inspect completed local work, current branch/upstream, and task ownership.
   Read project metadata and current GitHub state; preserve unrelated edits.
2. Review the diff and run proportionate private-safe validation. Stage only
   reviewed task paths and check ignored/staged content before publication.
3. Create coherent commits, reconcile the current upstream safely, and push the
   task branch. Do not invent version changes or rewrite protected history.
4. Create/update the task PR, report actual checks and limitations, inspect
   current requirements/reviews at the exact head, and repair task-caused failures.
5. Merge when covered and all applicable requirements pass. Fetch and verify
   the PR merge and default-branch ancestry; report any checkout left behind
   to preserve dirty work.

## Decision rules

This skill finalizes already implemented work. Use build/fix for missing
implementation, not an empty commit that pretends completion. A narrower
no-merge or draft-only request stops delivery at that boundary.

Creating a version tag or release belongs to release. A push-triggered
production change is an additional effect that must be covered before push.
Never use administrator bypasses or treat absent CI as successful CI.

## Completion and handoff

Provide commit/PR/merge identities, current remote status, check categories,
and preservation status. If blocked, report the exact remaining requirement
and prepared state. Push success alone is not merge or release completion.
