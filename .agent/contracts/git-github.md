# Git and GitHub workflow

Mutation authority is owned by [authorization](authorization.md). Read it
before writing. Apply [GitHub integration](../integrations/github.md).

## Baseline and isolation

Inspect `git status --porcelain=v2 --branch`, remotes, worktrees, and relevant
refs. Fetch the canonical remote without changing another checkout. Establish
the current default branch and compare the target range. Inspect live matching
Issues/PRs, Projects, checks, branches, tags/releases, and protections where
relevant. Reuse task-related records; an empty backlog does not require a new
Issue for every task.

Preserve unrelated dirty/index/untracked work. Prefer an isolated worktree from
the verified target when the current checkout is dirty. Use `codex/` as the
default task branch prefix unless instructed otherwise; it has no authority
semantics. Never reset, stash, clean, or broad-stage unrelated work. Do not
modify a branch checked out by another worker.

## Integration and delivery

1. Review the task diff and run relevant verification. Check ignored/staged
   paths for privacy before publication; stage only reviewed task paths/hunks.
2. Commit cohesive changes using the established concise convention (for
   example `docs: ...`). Do not invent issue IDs or attribution trailers.
3. Fetch/recheck upstream before push. Rebase only an unpublished isolated task
   branch when appropriate; otherwise use a normal merge that preserves shared
   history. Resolve only understood conflicts and repeat affected checks.
4. Push the task branch. Create or update a PR against the verified target.
   Start as draft when applicable, then mark ready when the requested merge
   workflow and actual verification justify it. Explain problem, behavior,
   validation, and material limitations; exclude private data and chat excerpts.
5. Inspect current checks/reviews and branch/ruleset requirements at the exact
   PR head. Repair task-caused failures; never weaken controls. If no checks
   are configured, report that fact and use relevant local evidence.
6. Merge using an allowed repository method only after requirements pass.
   With no documented preference, use a normal supported merge method and
   record it. Never use an administrative bypass.
7. Fetch and verify the PR merge record and resulting default-branch ancestry.
   Keep merge success separate from release/deployment/live acceptance.
   Clean up a completed task branch only when it is no longer in use.

A protected original checkout may remain behind after remote merge; report
that explicitly. Do not synchronize it by overwriting preserved work.

## Pull and force constraints

For synchronization, prefer fast-forward when possible. Analyze divergence
before selecting merge or a permitted rebase. Stop dependent integration when
conflicts cannot be resolved from evidence; continue independent preparation.

Force push is not the default. Never rewrite protected/shared history without
express authority and current-state safeguards. Where explicitly authorized
on a task branch, use an exact expected-commit lease, never an unrestricted
force. A failed lease requires fresh reconciliation, not a stronger override.
