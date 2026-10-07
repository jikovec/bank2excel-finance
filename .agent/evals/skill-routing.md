# Skill-routing evaluations

For each prompt select a workflow before reading the expected heading. Explain
why the neighboring skill is excluded. These cases test intent, not permission
or workflow success. Review them without executing their described mutations.
Deployment/publication positives route correctly but must stop at this repo's
absent-target prerequisite. A routing match grants no new infrastructure.

## build

- Positive: Add a parser for a newly supported bank.
- Positive: Implement a requested CLI option for source selection.
- Positive: Modernize the repository agent toolkit.
- Negative: Repair an existing parser date regression. -> fix
- Negative: Finalize and merge my completed local changes. -> push

## investigate

- Positive: Explain why the current parser rejects this synthetic header.
- Positive: Find the cause of a reported import failure without editing files.
- Positive: Explain how far the branch diverges from upstream.
- Negative: Compare the latest upstream parser-library APIs. -> research
- Negative: Integrate the latest upstream branch. -> pull

## research

- Positive: Compare maintained libraries for spreadsheet parsing using official docs.
- Positive: Find the current official Frankfurter API response contract.
- Positive: Research documented Codex and Claude skill discovery paths.
- Negative: Trace this repository parser registration. -> investigate
- Negative: Implement the selected parser library. -> build

## verify

- Positive: Check whether the claimed fix exists at this commit.
- Positive: Verify that the PR actually merged into main.
- Positive: Verify that this version has a remote tag and source release.
- Negative: Review this patch for previously unknown defects. -> review
- Negative: Repair the broken metadata links. -> fix

## review

- Positive: Review this parser diff for regressions.
- Positive: Assess this PR for material privacy leaks.
- Positive: Review the toolkit authority changes for contradictions.
- Negative: Verify the claim that CLI help passed. -> verify
- Negative: Fix the identified parser regression. -> fix

## fix

- Positive: Fix the CLI import failure caused by the requested change.
- Positive: Repair an existing parser amount-sign regression.
- Positive: Reconcile stale documentation with current source behavior.
- Negative: Add support for an entirely new bank format. -> build
- Negative: Determine the root cause without changing code. -> investigate

## release

- Positive: Create the requested versioned source milestone.
- Positive: Prepare notes and publish the requested source tag and release.
- Positive: Finish the requested draft source release for the verified commit.
- Negative: Merge these completed changes without a version milestone. -> push
- Negative: Deploy this revision through the normal live process. -> deploy

## deploy

- Positive: Deploy the intended revision through the normal process.
- Positive: Run the configured deployment and verify health.
- Positive: Deploy the approved source state to its configured target.
- Negative: Force publication past an eligible process gate. -> publish
- Negative: Create a source version tag and release notes. -> release

## publish

- Positive: Force-publish past an eligible repository deployment gate.
- Positive: Publish despite a failed optional local process check, preserving external controls.
- Positive: Use the minimum permitted force-publication path for the target.
- Negative: Deploy normally and stop at failed gates. -> deploy
- Negative: Push the reviewed source branch and merge its PR. -> push

## push

- Positive: Commit, push, and merge these completed scoped changes.
- Positive: Finish the existing task PR through its required checks and merge.
- Positive: Deliver my completed source changes without creating a release.
- Negative: Prepare a new tagged source milestone. -> release
- Negative: Synchronize this checkout from upstream. -> pull

## pull

- Positive: Synchronize this branch with upstream while preserving edits.
- Positive: Fetch and integrate the latest main safely.
- Positive: Reconcile upstream divergence through the permitted merge strategy.
- Negative: Explain divergence without changing the checkout. -> investigate
- Negative: Push and merge completed local work. -> push

## Additional boundaries

- `develop` routes to build; `reconcile` routes to fix with reconciliation intent.
- Ambiguous "publish my changes" requires establishing whether the requested
  effect is source delivery, a release, or explicit force publication.
- "Bypass required GitHub reviews and publish" routes to publish for classification,
  but the external bypass is prohibited, not a successful publication test.
- No project-specific skills are active. Add 3 positive and 2 negative cases for
  every future project skill and reject names colliding with the baseline.

An assessor should report case count, misroutes, and uncertainty. Static case
coverage is not a provider behavior benchmark; record actual evaluation method
and provider-discovery limitations in the task handoff.
