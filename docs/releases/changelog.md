# Changelog

## Unreleased

No changes are documented after v0.0.2.

## v0.0.2 - 2026-08-03

- Reorganized documentation into topic folders under `docs/`.
- Added memory-first Codex entry docs: `AGENTS.md`, `00_Index.md`,
  `docs/current-state.md`, `docs/decisions.md`, `docs/commands.md`,
  `docs/testing.md`, and `docs/security-model.md`.
- Added Obsidian and future-agent indexing docs: `docs/AGENT-INDEX.md`,
  `docs/OBSIDIAN.md`, `docs/SOURCE-MAP.md`, `docs/CONNECTIONS.md`,
  `docs/agent-index.json`, and `handoffs/INDEX.md`.
- Added a human-facing finance-vault home, snapshot guide, Markdown template,
  JSON example/schema, and ignored local current-situation files without
  populating private financial values.
- Added local-first Obsidian graph guidance while keeping `.obsidian/` metadata
  ignored and outside the release.
- Added repository-specific GitHub operating guidance without enabling CI,
  Pages, Packages, Codespaces, deployment, or other remote services.
- Added a documentation index, project overview, architecture notes, API/CLI status, verification workflow, reports index, and this changelog.
- Moved existing bank export, maintenance, and data privacy docs into the new hierarchy.
- Kept private generated reports in ignored `reports/` instead of moving them into tracked docs.
- Expanded `.gitignore` for private finance snapshots and local Obsidian state.
- Added complete v0.0.2 release notes and a scrubbed release-validation report.
- Removed machine-specific absolute checkout paths from the public
  documentation candidate.
- Made no application source, parser, dependency, build, or workbook-format
  changes.

See [the v0.0.2 release notes](v0.0.2.md) for the complete scope and known
limitations.

## v0.0.1

- Current Git tag found during the 2026-07-07 documentation inventory: `v0.0.1`.
- The tag points at commit `67d02c4`.
- No separate tracked release notes were found.

## Release Notes Policy

Use this file for future tracked release notes. Keep private validation evidence in ignored `reports/` unless a scrubbed, shareable report is intentionally created under `docs/reports/`.
