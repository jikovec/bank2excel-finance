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

## D-008: Portable Agent Toolkit And Scoped Repository Delivery

Status: current

Context: the user explicitly requested the Repository Agent Toolkit Bootstrap,
including policy adoption and ordinary user-owned delivery through merge.

Decision: `AGENTS.md` is the always-on contract; `.agent/project.yaml` owns stable
identity; `.agent/contracts/` owns shared policy; `skills/` owns canonical
workflows. Provider adapters remain thin. `.agents/skills/` is the current Codex
discovery path, `.codex/skills/` supplies a compatibility pointer to avoid
duplicate discovery on clients scanning both locations, and
`.claude/skills/` plus the `CLAUDE.md` import serve Claude Code.

The user's bootstrap instruction adopts the standing task-related repository
grant in [.agent/contracts/authorization.md](../.agent/contracts/authorization.md).
It supersedes the earlier blanket requirement to ask separately for every
commit/push/PR/merge. Narrower task restrictions, private-data boundaries,
external protections, and separate release/deployment/publication scope remain
binding. Ordinary build/fix delivery may continue through verified merge.

The project ID is `github:jikovec/bank2excel-finance`, derived from the verified
remote. No organization or canonical external registry binding is configured;
Mind-Seed remains disabled. Local Obsidian/VaultGuard-style documentation does
not establish external ownership, enrollment, or memory mutation authority.

Consequences: existing product/finance documentation remains authoritative in
its domain. Memory is contextual; durable decisions are repository-first.
Deployment/publication skills expose honest absent-target boundaries for the
local CLI. No hosted runtime, CI, private-data access, or external memory writes
are introduced. Historical reports retain their original dated observations.

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
