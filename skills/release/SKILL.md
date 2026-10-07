---
name: release
description: Prepare and complete the repository's normal release workflow, including versioning, notes, tags, artifacts, or release records where applicable.
---

# Release

## Shared contracts

Read `AGENTS.md`, then the workflow's contracts:

- [core](../../.agent/contracts/core.md)
- [authorization](../../.agent/contracts/authorization.md)
- [verification](../../.agent/contracts/verification.md)
- [git-github](../../.agent/contracts/git-github.md)
- [deployment](../../.agent/contracts/deployment.md)
- [handoff](../../.agent/contracts/handoff.md)

## Project context

Use `.agent/project.yaml` for discovery and the existing `00_Index.md` routing.
Consult task-relevant source, commands, and accepted decisions; resolve paths
from the repository root. Follow scoped instructions without loading unrelated
contracts or private finance content.

## Workflow

1. Confirm the requested source milestone and intended revision. Inspect live
   tags/releases and `docs/releases/`, including changelog and prior conventions.
2. Discover actual versioning and artifact mechanics. This repository has Git
   source milestones and release notes, not an application package registry or
   configured release automation. Do not invent a version file or CI pipeline.
3. Prepare the scoped notes/version changes and verify the relevant source.
   Resolve the exact tag target after required repository delivery is complete.
4. Create the authorized tag/release records with only reviewed public source
   artifacts. Verify tag resolution and the resulting release metadata/assets.
5. Record what exists remotely, distinguishing notes, tags, draft releases,
   published source releases, and any independently requested deployment.

## Decision rules

A `v...md` document does not prove that tag/release exists. Do not rewrite an
existing tag or publish a generated financial workbook. Inspect ignore and
staged boundaries through the private-safe workflow before source publication.

`push` delivers completed source changes without creating a versioned milestone.
`deploy` changes a configured live target. Release does neither implicitly;
perform only the applicable effects covered by the requested release scope.

## Completion and handoff

Report version, exact source/tag identity, notes and release links, verified
artifact scope, and check limitations. An unavailable publishing service means
prepared release material, not a remotely completed release.
