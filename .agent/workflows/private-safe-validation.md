# Private-safe repository validation

1. Classify the task as source/docs/toolkit work or explicitly requested private
   workbook validation. Read `docs/commands.md`, `docs/testing.md`, and
   `docs/security-model.md` before commands. Do not open protected paths to
   establish an ordinary source/toolkit baseline.
2. Inspect source/config examples and select checks proportionate to the change.
   For Python syntax use the documented compile command (it writes bytecode).
   CLI help checks importability without loading private inputs; report missing
   dependencies as unavailable and preserve the known matplotlib gap.
3. For toolkit changes run the [metadata validator](../hooks/README.md), check
   relative links, and review [routing cases](../evals/skill-routing.md).
   Native provider discovery is a separate result from static adapter validity.
4. Review `git diff --check` and the scoped diff. Before staging inspect
   `git status --ignored`; after allowlisted staging inspect `git diff --cached`.
   Do not open private contents as a shortcut to a privacy review.
5. Report check categories, exact relevant state, and material limitations.
   Never relabel missing dependencies or absent CI as a pass.

A full workbook run reads private input and writes output/cache/reports. It
requires explicit coverage of those private-data effects. Offline FX mode
prevents rate downloads, not private-data access or output writes. Do not run
setup wrappers for docs validation: they create private config copies.

Use synthetic data for focused input-independent source checks when warranted.
Do not publish bank exports, generated workbooks, root reports, or private
finance state as release artifacts, screenshots, test fixtures, or PR evidence.
