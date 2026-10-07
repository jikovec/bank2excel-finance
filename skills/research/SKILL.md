---
name: research
description: Research external technical evidence, standards, APIs, libraries, or alternatives needed for a repository decision or implementation.
---

# Research

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

1. Establish the repository decision and constraints. Consult local source and
   accepted decisions for compatibility, privacy, runtime, and architecture.
2. Identify the external facts needed: API behavior, maintained documentation,
   technical standard, library compatibility, or viable alternatives.
3. Retrieve current primary sources. Record version/date and direct links;
   distinguish documented behavior from empirical evidence and inference.
4. Compare only alternatives relevant to the question, including integration
   effort and effects on local-only financial processing.
5. Give a supported recommendation or explain the remaining uncertainty.

## Decision rules

Research is not implementation, dependency installation, finance advice, or
permission to send private exports to a service. Use non-sensitive technical
queries. Investigation of current local code belongs to `investigate`.

Load memory/scopes only for cross-project persistent context or an explicitly
requested memory operation. A useful finding is not automatic permission to
persist it or adopt a new repository decision.

## Completion and handoff

Separate repository evidence, external evidence, inference, and recommendation.
Cite precise primary sources near supported claims. Identify material unknowns
and validation needed before adoption. Do not claim recommendations were built,
benchmarked, or accepted unless those effects were actually authorized and done.
