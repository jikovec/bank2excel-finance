---
name: build
description: Implement substantial repository changes and carry them through relevant verification and normal repository completion workflow.
---

# Build

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

1. Establish the requested end state, relevant source baseline, current Git
   state, and acceptance criteria. Read the owning architecture/decision docs.
2. Inspect existing implementation and choose the narrowest design that meets
   the request. Preserve unrelated work, terminology, and established behavior.
3. Implement the complete requested change. Use synthetic inputs when focused
   regression evidence is necessary; do not inspect real exports by default.
4. Follow `.agent/workflows/private-safe-validation.md`; fix task-caused
   failures and rerun affected checks. Update stale canonical documentation.
5. Complete the applicable Git/GitHub workflow under its contract, through merge
   when covered. Verify the resulting target rather than assuming push is done.

## Decision rules

`develop` is an alias for this workflow. A bounded known defect belongs to `fix`;
read-only causal work belongs to `investigate`. This skill implements repository
changes; its name does not authorize running a private workbook build.

Load memory and scopes only when durable context, cross-project identity, or
promotion is actually involved. Do not turn ordinary code work into a memory
write. Do not automatically release, deploy, or publish after implementation.

## Completion and handoff

Report implemented behavior, scope, relevant checks and limitations, and actual
commit/PR/merge state. Separate unavailable checks and out-of-scope findings.
A partial implementation or unverified delivery is not a completed outcome.
