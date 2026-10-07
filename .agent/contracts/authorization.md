# Authorization contract

## Provenance and standing grant

The user explicitly requested the Repository Agent Toolkit Bootstrap, including
its standing user-owned workflow policy and delivery through merge. [D-008](../../docs/decisions.md)
adopts that policy and replaces the earlier blanket per-operation Git approval
rule. The bootstrap request itself authorizes this adoption and its delivery;
the proposed file does not authorize itself.

`jikovec/*` and `mind-seed-systems/*`, and other repositories established by
valid evidence as user-owned, qualify for ordinary task-related repository
workflow. This repository's `jikovec/bank2excel-finance` origin and personal
owner support `ownership.class: user-owned`. Namespace rules do not authorize
work in other repositories merely because an agent can reach them.

For assigned work in this repository, standing authority covers branches,
worktrees, edits, coherent commits, fetch/pull, non-destructive rebase/merge,
push, PR creation/update, task-caused check/review remediation, ordinary
Issue/Project maintenance, merge after applicable requirements pass, and
completed task branch cleanup. Use current source and live work state; avoid
duplicate work objects. No repeated approval is needed for covered effects.

## Limits

- A narrower task controls: read-only, source-only, no-commit, no-push, or
  no-deploy instructions remain binding. Scope cannot fabricate authority.
- Preserve explicit private-data, file-removal, and unrelated-work boundaries
  in `AGENTS.md`. This grant does not authorize private finance inspection.
- Release, deployment, and force publication require the requested outcome to
  cover those effects. Ordinary source delivery is not release authorization.
- Settings, collaborators, billing, new CI, credentials, cross-domain changes,
  protected-history rewrites, and data migrations need applicable authority.
  Check indirect effects such as push-triggered deployments before delivery.
- Dropie and VaultGuard follow their own repository/organization governance.
  Unknown ownership is unresolved; do not guess a grant from identity labels.
- Memory, session state, credentials, tool availability, administrative access,
  and successful checks cannot create authority.
- External branch protections, Rulesets, required checks/reviews, environment
  approvals, organization governance, IAM, and provider controls remain binding.
  Do not bypass them, including through administrator options.

Revalidate governing policy and grants at start/resume, before consequential
effects, and on observed change or revocation. Amend governance only through
explicit policy-authoring authority before or atomically with governed work.
If authority is missing, complete safe preparation and request only the exact
missing authority; name its source and the blocked effect.
