# Repository agent toolkit

Read [AGENTS.md](../AGENTS.md) first. [Project metadata](project.yaml) provides
stable identity; [the existing index](../00_Index.md) routes product context.
Paths written as code in skills are relative to the repository root.

## Workflows

| Request | Canonical skill |
| --- | --- |
| Substantial implementation; develop | [build](../skills/build/SKILL.md) |
| Establish current behavior or cause without repairs | [investigate](../skills/investigate/SKILL.md) |
| External technical evidence or alternatives | [research](../skills/research/SKILL.md) |
| Independently check a claim | [verify](../skills/verify/SKILL.md) |
| Find material defects in a change | [review](../skills/review/SKILL.md) |
| Repair a known defect or reconcile states | [fix](../skills/fix/SKILL.md) |
| Versioned source milestone | [release](../skills/release/SKILL.md) |
| Normal governed live deployment | [deploy](../skills/deploy/SKILL.md) |
| Explicit force publication | [publish](../skills/publish/SKILL.md) |
| Deliver already completed local changes | [push](../skills/push/SKILL.md) |
| Synchronize with upstream | [pull](../skills/pull/SKILL.md) |

Invoke the discovered skill by name (for example `$build` in Codex or `/build`
in Claude), or explicitly ask the agent to read its canonical path if a client
has a built-in command or another skill with the same name. Provider command
menus do not redefine repository semantics.

No project-specific skill is currently justified: private-safe validation is
shared workflow material. Add `skills/project/<unique-name>/SKILL.md` only for
complex recurring project reasoning, with matching adapters and routing cases.

## Contract ownership

- [Core](contracts/core.md): evidence, scope, preservation, implementation.
- [Authorization](contracts/authorization.md): mutation grants and boundaries.
- [Verification](contracts/verification.md): evidence categories and criteria.
- [Git/GitHub](contracts/git-github.md): repository delivery mechanics.
- [Deployment](contracts/deployment.md): release, deploy, and publish semantics.
- [Handoff](contracts/handoff.md): concise reporting.
- [Memory](contracts/memory.md): persistent context authority; load conditionally.
- [Scopes](contracts/scopes.md): identity, inheritance, and promotion; load conditionally.

[Workflows](workflows/README.md), [integrations](integrations/README.md), and
[hooks](hooks/README.md) specialize these contracts from real repository needs.
[Routing cases](evals/skill-routing.md) check neighboring workflow boundaries.

## Provider discovery

Canonical bodies exist only under `skills/`. Thin adapters at
`.agents/skills/<name>/SKILL.md` serve current Codex; `.claude/skills/` serves
Claude Code. `.codex/skills/` holds a compatibility pointer, not duplicate
adapters: the installed Codex scans both locations and would list each twice.
`CLAUDE.md` uses `@AGENTS.md`. No provider settings grant additional authority.
The Claude adapters for `release`, `deploy` and `publish` also set
`disable-model-invocation: true`, so Claude Code loads them only on an explicit
`/release`, `/deploy` or `/publish`. Canonical skills and Codex adapters keep the
portable name/description metadata, and the validator enforces both forms.

Discovery paths follow [Codex skills documentation](https://learn.chatgpt.com/docs/build-skills),
[Claude skills documentation](https://code.claude.com/docs/en/skills), and
[Claude imports](https://code.claude.com/docs/en/memory).
Runtime discovery evidence and limitations belong in the bootstrap handoff,
not stable metadata. Do not assume an existing session reloads new skills.

## Identity and memory

The remote-qualified project ID is local stable discovery identity, not an
invented registry ID. There is no configured organization, external registry,
or Mind-Seed/MemPalace binding. Obsidian/VaultGuard-style documentation does not
establish ownership by VaultGuard or enrollment in Mind-Seed. Keep
`mind_seed.enabled: false` until enrollment and canonical bindings are verified.
