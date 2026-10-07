---
name: investigate
description: Inspect repository, runtime, or work state to establish current behaviour, root cause, or required work without changing implementation by default.
---

# Investigate

## Shared contracts

Read `AGENTS.md`, then the workflow's contracts:

- [core](../../.agent/contracts/core.md)
- [handoff](../../.agent/contracts/handoff.md)

## Project context

Use `.agent/project.yaml` for discovery and the existing `00_Index.md` routing.
Consult task-relevant source, commands, and accepted decisions; resolve paths
from the repository root. Follow scoped instructions without loading unrelated
contracts or private finance content.

## Workflow

1. Define the question and relevant evidence: source behavior, reproducible
   symptom, runtime observation, work-management state, or inconsistency.
2. Inspect the smallest useful source/config examples and current facts. Read
   Git/GitHub contract only for repository/work-state investigation; load scope
   and memory contracts only for persistent context or identity questions.
3. Form competing explanations and check discriminating evidence. Use safe
   read-only diagnostics; seek explicit scope before accessing private finance
   inputs or causing writes. Do not run a workbook build as a generic probe.
4. Trace the likely cause to its source and identify what remains unproven.
   Use external `research` only when the repository cannot answer the question.

## Decision rules

Default to investigation only. Do not silently fix code, synchronize branches,
change settings, create Issues, or publish conclusions. A request to understand
upstream divergence is investigation; a request to integrate it is `pull`.

Prior handoffs are hypotheses/evidence to recheck, not proof of present truth.
Do not claim a runtime reproduction from source inspection alone.

## Completion and handoff

Distinguish observed, supported, inferred, and unknown findings. Provide source
locations, causal chain, any safe diagnostic results, and the smallest justified
next step. State which missing evidence prevents a conclusion.
