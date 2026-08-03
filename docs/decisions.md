# Decisions

This file records project-level decisions that future agents should preserve
unless the user explicitly changes direction.

## D-001: CLI-Only Product

Status: current

The repo is a local CLI workbook generator. Documentation should not describe a
web service, route table, OpenAPI API, frontend, deployment target, or hosted
runtime unless those files are added later and verified from source.

## D-002: Privacy Boundary

Status: current

Private financial data stays in ignored local paths:

- `input/`
- `output/`
- `cache/`
- `reports/`
- `.env`
- non-example config files under `config/`

Tracked docs may mention these paths, but should not copy private values,
account identifiers, merchant examples, local absolute paths, or raw report
content.

## D-003: Root Reports Are Local Evidence

Status: current

The root `reports/` folder is ignored. Use it for local validation output and
private evidence. Use `docs/reports/` only for scrubbed, shareable reports.

## D-004: Builds Are Not The Default Documentation Check

Status: current

Full builds read private exports and rewrite generated outputs. For
documentation or memory validation, prefer non-mutating checks such as CLI help,
source inspection, Git status, and Markdown link checks. Run builds only when
the user asks for build validation or when the task requires it.

## D-005: Parser Extensions Stay Explicit

Status: current

New transaction parsers should live under `bank_parsers/`, normalize into the
schema from `bank_parsers/common.py`, and be registered in
`discover_transactions()`.

New investment snapshot parsers should normalize into the schema from
`bank_parsers/investments.py` and be registered in
`discover_investment_snapshots()`.

## D-006: FX Rates Are Not Invented

Status: current

Manual rates come from `config/currency_rates.csv`. Downloaded rates come from
the configured Frankfurter flow and are cached under `cache/`. Missing FX rates
are validation findings, not values to guess.

## D-007: Current Financial State Is Local And Explicit

Status: current

The tracked `finance/` files define a shareable snapshot structure. Real
point-in-time values and personal interpretation belong only under ignored
`finance/private/` files.

The workbook and validation report remain the evidence for calculated values.
The private JSON snapshot is a manually maintained summary, and the private
Markdown note is its narrative interpretation. Unknown or unverified values use
`null`; zero is reserved for a known zero.

## Future Decision Template

Use this structure for new decisions. Do not add a decision unless it is backed
by a user instruction, existing repo documentation, or an implemented source
change.

```text
## D-XXX: Title

Status: proposed | current | superseded

Context:

Decision:

Consequences:
```
