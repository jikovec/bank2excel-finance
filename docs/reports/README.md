# Reports, Handoffs, And Archive

This folder is for tracked documentation reports, handoffs, and scrubbed summaries.

Generated runtime reports belong in the root `reports/` folder. Root `reports/` is ignored because it can contain private financial data, local paths, transaction examples, and build logs.

## Private Generated Reports

The 2026-07-07 documentation inventory found these ignored private report artifacts in root `reports/`:

- `reports/validation_summary.md`
- `reports/normal_build.log`
- `reports/offline_build.log`
- `reports/build_consistency_summary.json`
- `reports/privacy_scan_summary.json`
- `reports/git_status_ignored.txt`
- `reports/git_init.log`

They were intentionally left in place. Do not move generated private reports into tracked docs unless they have been scrubbed.

A local project-memory validation report may exist at `reports/project-memory-validation-2026-07-07.md`. It is also in ignored root `reports/` because the user requested the report there.

## Tracked Reports

- [2026-07-07 documentation reorganization report](2026-07-07-documentation-reorganization.md)
- [2026-07-09 Obsidian and agent indexing implementation report](2026-07-09-obsidian-agent-indexing-implementation.md)
- [2026-08-03 v0.0.2 release report](2026-08-03-v0.0.2-release.md)

## Local Planning Reports

An ignored local planning report may exist at `reports/obsidian-agent-indexing-plan.md`.
It is not linked as a tracked artifact because root `reports/` is intentionally
local-only and can contain private evidence.

## Archive Guidance

Use this folder for:

- Documentation cleanup reports.
- Handoffs that are safe to commit.
- Scrubbed validation summaries.
- Historical notes that explain repository state without exposing private data.

Use root `reports/` for:

- Generated validation summaries.
- Build logs.
- Privacy scans that include local paths.
- Any report created from real input data.
