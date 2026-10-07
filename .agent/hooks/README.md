# Deterministic checks

Run the shared validator manually from the repository root:

```bash
python .agent/hooks/validate-toolkit.py
```

- Trigger: toolkit metadata, skills, adapter, or routing changes; manual before delivery.
- Purpose: parse metadata/frontmatter, check identity and adapter parity, required
  surfaces, contained local links, and routing coverage.
- Inputs: explicit toolkit paths and `git remote get-url origin`; no private paths.
- Side effects: none; no network requests, settings changes, or memory writes.
- Dependencies: Python and PyYAML (already declared in `requirements.txt`).
- Expected runtime: seconds for this small toolkit.
- Exit: 0 on structural success, 1 on invalid content, 2 on missing dependencies.
- Failure: repair the reported structural defect and rerun; missing dependencies
  remain unavailable, never silently passed.

No automatic Git or provider hook is installed. Providers can share this exact
implementation if automatic integration is separately requested. This check is
not an authorization engine, secret scanner, semantic reviewer, or completion
oracle. Review routing decisions and relevant runtime evidence separately.
