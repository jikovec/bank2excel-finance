# Scope semantics

Scope is not a universal override ladder. Authority depends on the data type:
source owns behavior, the registry owns configured identity/relationships,
canonical governance owns policy, live work systems own work state, and memory
is contextual. Conceptual containment does not let a deeper scope overrule them.

| Scope | Identity and lifetime | Read visibility | Write authority | Inheritance and promotion | Status |
| --- | --- | --- | --- | --- | --- |
| global | Established user/system context; cross-project lifetime | Configured permitted global context | Its governing explicit/standing grant | Supplies generic defaults; organization-to-global requires destination authority | Contextual memory; actual global governance retains its own authority |
| organization | Canonical organization ID; organization lifetime | Permitted organization/project readers | Organization governance | May constrain projects; project-to-organization requires adopted organizational relevance | Canonical organization policy/identity authoritative in its domain |
| project | Stable project ID; may span repositories | Permitted project participants | Project governance and assigned scope | Inherits applicable policy, not unrelated data; task-to-project requires accepted durable evidence | Accepted decisions/registry identity authoritative; memory contextual |
| repository | Canonical host/owner/name binding; repository lifetime | Permitted repository readers; public source does not expose private data | Repository governance and scoped task grant | Refines generic execution; cross-repo propagation requires destination authority | Current source/config/Git authoritative in their domains |
| agent | Actual agent assignment; assignment lifetime | Only context/tools allowed for its assignment | Delegated rights, never broader than delegator | No identity-based grants; findings promote through task/project review | Working context, not new canonical authority |
| task | Assigned objective and boundaries; objective lifetime | Task-relevant permitted context | Current task plus applicable standing grants | Can narrow scope; session-to-task requires relevant verified evidence | Intent may authorize actions within governance; findings contextual |
| session | Runtime conversation instance; session lifetime | Currently permitted context | Allowed task operations only | Ephemeral by default; no automatic persistence | Observations/hypotheses contextual |

## Invariants

A lower scope cannot silently rewrite higher-scope identity. An agent cannot
create a competing project ID; a session cannot change organization ownership.
Project/task/session memory cannot override current technical truth.
Lower scopes may narrow organization/repository policy, never silently widen
prohibited permissions. Task intent can grant actions only within the valid
authorization model. Scope nesting, memory, and session state create no grant.
Task/session findings remain ephemeral unless explicitly promoted.

## Promotion

For session -> task, task -> project, project -> organization, or organization
-> global, verify all of: destination permits writes; information belongs at
that scope; explicit/standing mutation authority exists; canonical repository
or registry truth is updated first where applicable; the mechanism supports
the write. These transitions are examples, not automatic propagation.

Normally adopt/commit durable technical decisions to `docs/decisions.md` before
or with an authorized memory pointer. Reject promotion of unverified facts,
secrets, or private financial evidence into public or broader contexts. No
external scopes are instantiated here; do not invent IDs for missing bindings.
