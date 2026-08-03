# Private Finance Snapshot Area

This directory is reserved for the current personal financial snapshot. Its
contents are ignored by Git except for this safety guide.

Expected local files:

- `current-situation.json` - structured values that follow
  [the schema](../current-situation.schema.json).
- `current-situation.md` - narrative review, risks, decisions, and next actions.

To initialize a fresh checkout in PowerShell:

```powershell
Copy-Item finance/current-situation.example.json finance/private/current-situation.json
Copy-Item finance/current-situation.template.md finance/private/current-situation.md
```

After copying, change the JSON `$schema` value to
`../current-situation.schema.json` because the private file is one directory
deeper than the tracked example.

## Safety Rules

- Keep aggregate values here; do not copy transaction rows or account numbers.
- Do not add credentials, API keys, recovery information, or authentication
  data.
- Use `null` for unknown values and record missing coverage explicitly.
- Before any commit, confirm these files appear as ignored with
  `git status --ignored`.
- Do not link the private files from tracked reports or public documentation.

See [Finance Home](../../01_Finance_Home.md) and
[How it works](../how-it-works.md).

Tags: #finance/privacy #finance/snapshot #obsidian/local
