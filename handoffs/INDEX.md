# Handoff Index

This folder is for future-agent handoff notes that are safe to keep in the
repository.

No active handoff notes are present as of 2026-08-03.

## When To Add A Handoff

Add a handoff when:

- Work is intentionally incomplete.
- A future agent needs exact context that does not belong in permanent docs.
- Validation was blocked or deferred.
- A docs/report/source relationship needs follow-up.

Do not add a handoff just to restate stable documentation that already belongs
in [docs](../docs/README.md), [current state](../docs/current-state.md), or
[decisions](../docs/decisions.md).

## Handoff Format

Use a dated Markdown file name:

```text
YYYY-MM-DD-short-topic.md
```

Each handoff should include:

- Scope.
- Files inspected or changed.
- Commands run.
- Current status.
- Remaining work.
- Risks or blockers.
- Private-data boundaries observed.

## Safety Rules

- Do not copy private report contents, bank export data, account identifiers,
  merchant examples, local absolute paths, or `.env` values.
- Link to scrubbed tracked reports under `docs/reports/` when possible.
- Mention ignored root `reports/` evidence only by path and only when the user
  has explicitly requested that local evidence.

Tags: #agent/handoff #agent/orientation
