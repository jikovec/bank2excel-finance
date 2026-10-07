# Documentation Index

This index is the main entry point for developer documentation. It reflects the
v0.0.2 vault and documentation structure reviewed on 2026-08-03 while keeping
private runtime evidence separate from tracked docs.

## Agent Toolkit

- [Workflow routing](../.agent/README.md) - portable skills and shared contracts.
- [Project identity](../.agent/project.yaml) - stable discovery metadata.
- [Toolkit decision](decisions.md) - D-008 policy adoption and provider boundaries.

## Project Overview

- [Personal finance home](../01_Finance_Home.md) - human-facing vault landing
  page for current situation and review cadence.
- [Finance vault guide](../finance/README.md) - tracked/private separation,
  snapshot contract, and update rules.
- [Codex project memory](../00_Index.md) - memory-first entry point for future agent work.
- [Agent operating rules](../AGENTS.md) - repo rules, privacy boundaries, and safe validation defaults.
- [Current state](current-state.md) - current repo shape, supported surfaces, and known gaps.
- [Decisions](decisions.md) - project-level decisions to preserve.
- [Project overview](project-overview.md) - purpose, supported sources, outputs, and current limits.
- [Root README](../README.md) - short start page and command reference.
- [Future-agent index](AGENT-INDEX.md) - start workflow, safety rules, and agent update obligations.
- [Machine-readable agent index](agent-index.json) - JSON index for tools and future agents.

## Setup And Development

- [Development setup](setup/development.md) - prerequisites, local config, first build, and dependency notes.
- [Bank export guide](setup/bank-export-guide.md) - where to place each supported export type.
- [Maintenance](setup/maintenance.md) - category rules, accounts, FX rates, parser extension, and recurring work.
- [Config README](../config/README.md) - local config file expectations.
- [Input README](../input/README.md) - private input folder expectations.

## Architecture

- [How the finance system works](../finance/how-it-works.md) - evidence layers,
  metric definitions, and snapshot refresh flow.
- [Pipeline architecture](architecture/pipeline.md) - data flow, parser map, FX handling, workbook sheets, and validation outputs.
- [Source map](SOURCE-MAP.md) - source, config, script, output, and docs ownership map.
- [Connection map](CONNECTIONS.md) - links between docs, source areas, verification, reports, and handoffs.

## Obsidian And Agent Orientation

- [Obsidian guide](OBSIDIAN.md) - local-first vault use, graph conventions, tags, and `.obsidian/` handling.
- [Current-situation Markdown template](../finance/current-situation.template.md)
  and [JSON example](../finance/current-situation.example.json) - safe tracked
  starting points for the ignored private snapshot.
- [Handoff index](../handoffs/INDEX.md) - safe handoff-note routing for future work.

## API And Routes

- [API and CLI surface](api/README.md) - current no-HTTP-API status, CLI arguments, and internal parser entrypoints.

## Security And Compliance

- [Data privacy](security/data-privacy.md) - ignored private data, commit checklist, report privacy, and network notes.

## Testing And Verification

- [Command reference](commands.md) - setup, CLI, build, validation, and privacy commands.
- [Testing memory](testing.md) - current validation strategy and known test gaps.
- [Verification workflow](testing/verification.md) - available checks, generated validation report, and known test-suite gaps.

## Security Model

- [Security model](security-model.md) - project privacy boundaries and handoff rules.

## Releases And Changelog

- [v0.0.2 release notes](releases/v0.0.2.md) - complete scope, privacy
  boundary, compatibility, and known limitations for the documentation/vault
  milestone.
- [Changelog](releases/changelog.md) - versioned change history and historical
  tag information.

## Reports, Handoffs, And Archive

- [Reports index](reports/README.md) - tracked report docs and private ignored report locations.
- [2026-07-07 documentation reorganization report](reports/2026-07-07-documentation-reorganization.md) - inventory, moves, extensions, validation, and intentional non-changes.
- [2026-07-09 Obsidian and agent indexing implementation report](reports/2026-07-09-obsidian-agent-indexing-implementation.md) - scrubbed summary of the indexing implementation.
- [2026-08-03 v0.0.2 release report](reports/2026-08-03-v0.0.2-release.md) -
  scrubbed full-file inventory, validation evidence, privacy review, and release
  boundaries.

## Documentation Inventory

Tracked documentation after reorganization:

- `AGENTS.md`
- `00_Index.md`
- `01_Finance_Home.md`
- `README.md`
- `finance/README.md`
- `finance/how-it-works.md`
- `finance/current-situation.template.md`
- `finance/current-situation.example.json`
- `finance/current-situation.schema.json`
- `finance/private/README.md`
- `docs/README.md`
- `docs/current-state.md`
- `docs/decisions.md`
- `docs/commands.md`
- `docs/testing.md`
- `docs/security-model.md`
- `docs/project-overview.md`
- `docs/AGENT-INDEX.md`
- `docs/OBSIDIAN.md`
- `docs/SOURCE-MAP.md`
- `docs/CONNECTIONS.md`
- `docs/agent-index.json`
- `docs/setup/development.md`
- `docs/setup/bank-export-guide.md`
- `docs/setup/maintenance.md`
- `docs/architecture/pipeline.md`
- `docs/api/README.md`
- `docs/security/data-privacy.md`
- `docs/testing/verification.md`
- `docs/releases/changelog.md`
- `docs/releases/v0.0.2.md`
- `docs/reports/README.md`
- `docs/reports/2026-07-07-documentation-reorganization.md`
- `docs/reports/2026-07-09-obsidian-agent-indexing-implementation.md`
- `docs/reports/2026-08-03-v0.0.2-release.md`
- `handoffs/INDEX.md`
- `config/README.md`
- `input/README.md`

Private generated reports remain under ignored `reports/` and are documented in [reports/README.md](reports/README.md).
