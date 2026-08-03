# Finance Vault

This folder adds a personal-finance knowledge layer to the existing software
documentation. It provides a stable format for answering “where do my finances
stand now?” without mixing private values into tracked project files.

## Two-Layer Structure

| Layer | Files | Rule |
| --- | --- | --- |
| Tracked structure | `README.md`, `how-it-works.md`, the Markdown template, JSON example, and JSON schema | May describe fields and use `null` placeholders, but must not contain real personal values. |
| Private state | `private/current-situation.json` and `private/current-situation.md` | Contains current figures and personal interpretation; ignored by Git. |

Start from [Finance Home](../01_Finance_Home.md). Technical details remain in
the [documentation index](../docs/README.md) and
[pipeline architecture](../docs/architecture/pipeline.md).

## File Roles

- [How it works](how-it-works.md) explains the evidence flow, metric
  definitions, and refresh routine.
- [Current-situation Markdown template](current-situation.template.md) is the
  readable review format.
- [Current-situation JSON example](current-situation.example.json) is the safe
  machine-readable starting point.
- [Current-situation JSON schema](current-situation.schema.json) defines the
  fields and permitted states.
- [Private-area guide](private/README.md) explains how to initialize and handle
  the ignored local files.

## Source-Of-Truth Order

1. Original exports and investment snapshots are source evidence.
2. The generated workbook is the computed analysis.
3. The validation report describes data-quality limitations.
4. The private JSON file is the canonical point-in-time summary.
5. The private Markdown file explains context, priorities, and decisions.

If two layers disagree, do not silently choose one. Check the snapshot date and
coverage, inspect validation findings, then refresh the private snapshot from
verified workbook values.

## Snapshot Rules

- Use ISO dates (`YYYY-MM-DD`) and ISO date-times.
- Use one three-letter base currency, normally `EUR` for this project.
- Store liabilities as positive amounts; calculate net worth as assets minus
  liabilities.
- Use `null` for unknown or unverified values. Use `0` only for a known zero.
- Keep money as JSON numbers without currency symbols or thousands separators.
- Keep transaction-level details, account numbers, counterparties, and secrets
  out of the snapshot.
- Record excluded or missing data sources so a partial snapshot is not mistaken
  for a complete one.

Tags: #finance/snapshot #finance/net-worth #finance/cash-flow #finance/privacy
