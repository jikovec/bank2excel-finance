---
name: deploy
description: Deploy the intended repository state through its normal governed deployment process and verify the resulting live state.
---

# Deploy

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

1. Read project metadata and deployment contract. Confirm whether a target and
   normal deployment workflow actually exist in current source/configuration.
2. For this local CLI, report no configured deployment target. Do not create
   hosting, upload financial data, or reinterpret a workbook run as deployment.
   If deployment implementation is requested, route that separate work to build.
3. Only when a real configured target exists and scope covers it: establish
   intended revision/environment, required checks, migration/health criteria,
   provider policy, rollback route, and indirect effects.
4. Follow the normal governed process and all repository/external gates. If a
   gate blocks deployment, preserve the failure and complete safe preparation.
5. Verify the deployed revision and relevant live behavior. Record rollback or
   unverified acceptance distinctly from successful deployment.

## Decision rules

Never silently switch to `publish` to bypass a failed gate. Administrator
capability does not permit overriding external protections. Creating a source
release belongs to `release`; merging a PR is not evidence of a deployment.

Read Git/GitHub only if deployment actually involves repository delivery.
Do not load memory or scope contracts for an ordinary target check.

## Completion and handoff

Report intended and observed target/revision, verification, and any required
next action. Here, absent infrastructure is a blocked deployment prerequisite,
not a passed deployment or a reason to add speculative provider files.
