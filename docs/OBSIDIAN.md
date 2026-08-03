# Obsidian Local Graph Guide

This repository can be opened as a local Obsidian vault for documentation and
agent orientation. Obsidian is a local reading and navigation layer only.

## Local-First Rules

- Keep `.obsidian/` ignored. It can contain workspace state, plugin state, and
  local UI preferences.
- Do not add Obsidian cloud, sync, sharing, account coupling, encryption setup,
  or company integrations from this repo.
- Keep tracked notes as normal Markdown so GitHub, editors, and agents can read
  the same files.
- Keep personal figures only in ignored `finance/private/` notes. Tracked
  finance templates must remain free of real balances and account details.
- Use relative Markdown links as the canonical link format.
- Use tags sparingly to improve graph navigation, not to decorate every line.

## Graph Hubs

Use these files as the main graph entry points:

- [Project memory index](../00_Index.md)
- [Personal finance home](../01_Finance_Home.md)
- [Finance vault guide](../finance/README.md)
- [Agent operating rules](../AGENTS.md)
- [Documentation index](README.md)
- [Future-agent index](AGENT-INDEX.md)
- [Source map](SOURCE-MAP.md)
- [Connection map](CONNECTIONS.md)
- [Reports index](reports/README.md)
- [Handoff index](../handoffs/INDEX.md)

## Link Conventions

- Prefer normal Markdown links such as `[Source map](SOURCE-MAP.md)`.
- Avoid relying on wiki links as the only connection between notes.
- Link source files, docs, reports, and handoffs from the owning hub rather than
  duplicating long file lists in every note.
- Link to ignored root `reports/` paths only as plain code text unless the file
  is explicitly intended as local-only evidence.

## Tag Taxonomy

Global repo tags:

- `#repo/index`
- `#repo/architecture`
- `#repo/development`
- `#repo/testing`
- `#repo/security`
- `#repo/decision`
- `#repo/source-map`
- `#repo/connection-map`
- `#agent/orientation`
- `#agent/handoff`
- `#agent/report`
- `#obsidian/local`
- `#obsidian/graph`

Repo-specific tags:

- `#finance/workbook`
- `#finance/transactions`
- `#finance/investments`
- `#finance/fx`
- `#finance/config`
- `#finance/privacy`
- `#finance/validation`
- `#finance/snapshot`
- `#finance/net-worth`
- `#finance/cash-flow`
- `#python/cli`
- `#excel/output`
- `#bank/revolut`
- `#bank/tatrabanka`
- `#bank/slsp`

## Tag Rules

- Put tags near the top or bottom of a hub page.
- Use tags on hub pages, reports, handoffs, and decision notes.
- Do not tag every source-map row or every checklist item.
- Do not use tags that imply unsupported behavior, such as hosted deployment,
  HTTP API, financial advice, compliance certification, Obsidian sync, cloud
  account integration, or encryption setup.

Tags: #obsidian/local #obsidian/graph #repo/index #agent/orientation

<!-- local-graph-scope-2026-07-21:start -->
## Default Local Graph View

The local `.obsidian/graph.json` uses this knowledge-only Global Graph filter:

```text
path:docs OR path:finance OR path:handoffs OR file:00_Index OR file:01_Finance_Home OR file:AGENTS
```

| Control | Local default | Purpose |
| --- | --- | --- |
| Attachments | off | Removes source, media, generated, dependency, and evidence-file noise. |
| Tags | off | Keeps normal Markdown links as the visible relationship model. |
| Existing files only | on | Hides unresolved targets until a real note exists. |
| Orphans | on | Keeps genuine degree-zero Markdown notes visible for maintenance. |

The filter intentionally excludes the ignored root `reports/` area because it can contain private financial filenames and validation evidence. It includes `finance/` so the local private Markdown snapshot can connect to the tracked finance hub, while attachments remain hidden. Tracked docs, handoffs, finance notes, and stable root hubs remain visible.

A large outer ring of isolated colored nodes usually means attachments were enabled with an empty or overly broad filter; it does not by itself prove missing documentation backlinks. Keep Orphans enabled, classify each remaining Markdown orphan, and connect it through the narrowest real owner, archive, report, handoff, release, or specification index. Do not create decorative backlinks only to improve the metric.

The graph JSON is local UI state, not repository truth. If an old force layout remains visible after this setting changes, close and reopen Global Graph once so Obsidian reloads the filter. Re-run the Markdown link/component audit after adding or moving documentation.
<!-- local-graph-scope-2026-07-21:end -->
