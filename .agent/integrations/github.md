# GitHub

Canonical binding: `repository` in [project.yaml](../project.yaml), verified
against the configured `origin` remote and live `jikovec/bank2excel-finance`
metadata. This is a personal user-owned repository, not an organization binding.
Git manages source; GitHub owns live PRs, Issues, checks, Projects, protections,
and release records. Historical snapshots do not replace current queries.

Use `git` and an authenticated `gh` CLI or an available GitHub connector.
Authentication comes from the user's existing credential manager/CLI/connector;
never copy credentials into files, command output, or PRs. The tools are not a
grant. Reads inspect metadata/work state; push, PR/Issue changes, merge, and
release are mutations governed by [authorization](../contracts/authorization.md).

Before delivery inspect matching open work, current default branch/protections,
required checks, and push-triggered workflows. Inspect Projects only when
needed for current work management; do not invent a board or issue requirement.
No tracked CI or deployment workflow exists. New CI, Pages, Packages, Codespaces
with financial input, wiki duplication, collaborators, and billing changes are
not incidental delivery work. Preserve source-only processing boundaries.

Use releases for explicitly requested versioned source milestones. Public
records may contain scrubbed source evidence only, never private finance data.
