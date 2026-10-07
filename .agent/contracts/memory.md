# Persistent memory contract

> Memory is contextual state, not repository truth.

Memory never overrides current source, repository configuration, tests, schemas,
manifests, Git/GitHub state, runtime evidence, or accepted repository decisions.
Durable technical decisions belong in the repository first.

## Reading

Determine the configured backend, readable scopes, applicable tool permissions,
and provenance before reading. Consult [scopes](scopes.md) for boundaries.
Use memory to find decisions, retain approved context, discover relationships,
or understand historical work. Reconcile mutable claims against their current
owning sources. When evidence conflicts, use the current authoritative source
and label memory stale/contextual; do not silently rewrite it.

This repository uses tracked documentation for decisions/navigation and has no
configured external memory backend or scope IDs. Global assistant memory, if
available, is contextual and governed by its own permissions. Do not infer a
Mind-Seed/MemPalace grant or binding from access, directory names, or identity.

## Writing and promotion

A write requires a writable destination scope, explicit or valid standing
mutation authority, appropriate information, and a supported persistence
mechanism. Tool availability is not permission. No external memory write or
promotion authority is granted by this toolkit.

Do not automatically promote observations, task hypotheses, temporary failures,
or unverified interpretations. Promote only under [scope rules](scopes.md).
Record durable technical decisions in accepted repository state first or
atomically with their adoption; then persist an authorized pointer/summary,
not a second canonical decision. Preserve ADR/spec/Issue/PR references.

Never store credentials, private keys, tokens, transient secrets, or unnecessary
sensitive runtime data. Do not write memory merely to record routine activity.
Live mutable memory stays in a configured external store, not Git. Enabling a
future binding is separately authorized enrollment; record stable bindings
only, not conversations or invented registry records.
