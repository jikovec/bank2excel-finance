# Codex discovery compatibility pointer

Active Codex adapters live in `.agents/skills/` at the repository root.
Do not copy them here: Codex versions scanning both directories would expose
each workflow twice. The canonical workflow bodies remain in root `skills/`.
For a client limited to this older discovery path, use an explicitly scoped
adapter relocation after testing that client; do not enable both copies.
