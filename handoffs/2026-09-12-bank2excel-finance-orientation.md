# 2026-09-12 Bank2Excel Finance Orientation

## Scope And Status

Historical snapshot: the observations and limitations below are from
2026-09-12. The later [agent toolkit bootstrap](2026-10-07-agent-toolkit-bootstrap.md)
and current [repository contract](../AGENTS.md) supersede its workflow and
tooling inventory where they differ. Retrieve current Git and GitHub state
before relying on its remote, runtime, or release observations.

This is a documentation-only local orientation handoff. It supplements the
existing workflow in [AGENTS.md](../AGENTS.md),
[00_Index.md](../00_Index.md), [future-agent index](../docs/AGENT-INDEX.md),
and [machine-readable agent index](../docs/agent-index.json). No separate
docs/agent-workflow.md is needed or created.

No bank exports, private config, .env, generated workbooks, caches, root
reports, or finance/private content were opened. No files were moved, deleted,
staged, committed, pushed, published, or sent to an external service.

## Project Card

| Field | Current local evidence | Status |
| --- | --- | --- |
| Purpose | Local Python CLI that imports private bank exports and investment snapshots, normalizes and enriches them, applies FX handling, and writes a personal-finance Excel workbook plus validation evidence. | Implemented. |
| Product shape | CLI-only; no web server, HTTP API, frontend, hosted runtime, or deployment target is present in tracked source. | Local workflow only. |
| Working source | Current worktree is on main at b7c28b35e9fb; its cached local origin/main ref points to the same commit. | Locally observed only. |
| Remote / owner candidate | origin resolves for both fetch and push to https://github.com/jikovec/bank2excel-finance.git; main tracks origin/main. The jikovec namespace is a candidate owner identity, not a locally verified owner. | Reachability, authority, visibility, protection, and access are unverified. |
| Canonical source | Local Git metadata does not establish whether this checkout or origin is canonical. Treat the checked worktree as the inspected working source and the configured remote as a candidate until a separately authorized remote check confirms authority. | Unresolved. |
| Lifecycle | b7c28b3 is the local documentation milestone described as v0.0.2. The only local Git tag is v0.0.1, which peels to 67d02c4; no local v0.0.2 tag was found. | Local history only; no remote release or publication verified. |

## Code, Data, And Evidence Boundary

| Location | Role | Handling |
| --- | --- | --- |
| build_finance_workbook.py, bank_parsers/, scripts/ | CLI orchestration, parsers, and PowerShell helpers. | Tracked source. |
| config/*.example.*, .env.example | Fake configuration and optional wrapper-environment templates. | Tracked examples only. |
| docs/, handoffs/, finance/ | Documentation, agent navigation, finance-vault structure, templates, and schema. | Track only scrubbed material without real financial values. |
| .env, non-example config/ files | Account identifiers, category rules, manual FX rates, local settings, and optional local automation values. | Private and ignored. |
| input/, output/, cache/, reports/, finance/private/ | Bank exports, generated workbooks, FX cache, local evidence, and current-finance snapshots. | Private and ignored; do not inspect without explicit authorization. |
| docs/reports/ | Scrubbed, shareable historical reports. | Tracked documentation only; never raw local reports. |

The implementation supports Revolut, Tatra banka, Slovenska sporitelna, and
legacy transaction inputs, plus SLSP investment or savings snapshots. It uses
manual/cached FX rates and can obtain missing rates from Frankfurter. PDF
discovery is intentional, but PDF parsing is unsupported. The workbook contains
dashboard, raw transactions, investment, accounts, categories, FX, recurring,
yearly, validation, and hidden chart-data sheets. See
[pipeline architecture](../docs/architecture/pipeline.md) and
[API and CLI surface](../docs/api/README.md) for the source-owned details.

## Agent Workflow

1. Read [AGENTS.md](../AGENTS.md), [00_Index.md](../00_Index.md),
   [current state](../docs/current-state.md), and
   [decisions](../docs/decisions.md) before meaningful work.
2. Read [commands](../docs/commands.md), [testing](../docs/testing.md), and
   [security model](../docs/security-model.md) before running a command.
3. Use [source map](../docs/SOURCE-MAP.md) and
   [connection map](../docs/CONNECTIONS.md) to find the owning source and
   supporting documentation.
4. Preserve dirty work. Before staging a separately authorized change, run
   git status --ignored and git diff --cached and verify that private paths are
   not staged.
5. Record unresolved, time-sensitive, or privacy-limited work in handoffs/
   rather than duplicating stable guidance in permanent docs.

At review time, the worktree had 16 unstaged changes, no staged changes, and no
untracked files. git diff --ignore-space-at-eol was empty, so the existing
unstaged differences appear to be line-ending conversion only. Leave them
unchanged unless their owner explicitly asks for normalization or another
scoped edit. A plain git diff --check reports those inherited CRLF endings as
trailing whitespace; the authored handoff/index checks passed, and the global
check passes with core.whitespace=cr-at-eol.

## Exact Supported Commands

Run commands from the repository root. They come from current source, scripts,
and command documentation; they were not all runnable on the review host.

Create a Python environment and install declared dependencies:

~~~bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
~~~

On macOS or Linux, activate the environment with:

~~~bash
source .venv/bin/activate
~~~

Prepare missing private folders and example copies without overwriting an
existing private file:

~~~powershell
.\scripts\setup_local.ps1
~~~

Run the normal build only with authorized private data:

~~~bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx
~~~

Use the offline form when a build is authorized but external FX downloads must
be disabled:

~~~bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx --no-fx-download
~~~

The equivalent PowerShell wrappers are:

~~~powershell
.\scripts\run_build.ps1
.\scripts\run_build_offline.ps1
~~~

Safe documented source checks are:

~~~bash
python build_finance_workbook.py --help
python -m py_compile build_finance_workbook.py bank_parsers/common.py bank_parsers/investments.py bank_parsers/revolut.py bank_parsers/slsp.py bank_parsers/tatrabanka.py
git status --ignored
git diff --cached
git diff --check
~~~

python, python3, py, pwsh, and powershell were absent from the review host on
2026-09-12, so neither CLI-help/compile checks nor PowerShell wrappers could be
run there. A full workbook build was intentionally not run: it would read
private input and rewrite ignored output, cache, and report data.

## Dependencies, Tools, And Connectors

requirements.txt declares pandas, openpyxl, xlsxwriter, xlrd, and PyYAML. The
CLI also imports matplotlib unconditionally, but that package is not declared;
a clean-environment dependency decision is still needed.

No repository-local SKILL.md, plugin manifest, MCP configuration, CI config,
container definition, Python project-manager file, or PowerShell environment
definition was found. The existing agent setup is the Markdown and JSON index
listed above. On the review host, git, node, and jq were callable; that is host
capability, not a project dependency contract.

The only implemented external application surface found in code is the optional
Frankfurter FX request via Python standard-library urllib. A normal build may
use it for missing rates; --no-fx-download disables that request. The pipeline
does not upload bank exports. The configured Git remote is transport metadata,
not evidence of an authenticated GitHub connector or remote access. No
project-defined connector exists for a bank, spreadsheet SaaS, GitHub API, CI,
deployment service, or other plugin. Any recommended but uninstalled Codex
plugins remain proposed, not callable, and were not installed or enabled.

## Publication And Deployment Boundary

No tracked .github/ directory, CI workflow, deployment manifest, package-publish
configuration, hosted endpoint, or local automatic-deployment trigger was found.
A separately authorized git push could publish a chosen commit to the configured
remote, but it is not a verified deployment and does not establish a live
workbook, CI run, remote tag, GitHub Release, or hosted acceptance. Remote-side
Actions, webhooks, branch protection, Pages, releases, and visibility were not
queried and remain distinct unverified states.

The dated GitHub guidance in [AGENTS.md](../AGENTS.md) is historical local
memory, not current remote evidence. It must not be used as authorization for
remote changes.

## Remaining Gaps And Exact Decisions

1. Confirm, in a separately authorized read-only remote check, whether origin
   is canonical; who owns it; its visibility, branch protection, remote
   release/tag state, and whether any remote automation exists.
2. Decide whether matplotlib belongs in requirements.txt or is intentionally
   supplied outside the project. Do not change dependencies until that scope is
   approved.
3. Decide whether input-independent tests and optional CI are worth adding.
   Current docs correctly prohibit treating a private-data build as public CI.
4. Reconcile the documented v0.0.2 milestone with the absence of a local v0.0.2
   Git tag only when release/tag work is explicitly authorized.
5. Provide an approved Python and, if needed, PowerShell runtime before asking
   this host to run the project CLI, setup, or compile commands.
6. Obtain explicit authorization before inspecting or rebuilding from private
   financial inputs; this handoff does not prove private-data correctness,
   remote publication, CI, deployment, or live acceptance.

## Files Inspected And Checks Run

Inspected safe project instructions, documentation, tracked examples, source
entrypoint/CLI declarations, helper scripts, ignore behavior using nonexistent
probe paths, and local Git metadata. No protected data was read.

Completed checks include Git worktree/topology inspection, safe ignore-rule
probes, local workflow/configuration inventory, source/CLI declaration
inspection, and git diff --ignore-space-at-eol. Run git diff --check and a
tracked-document link check after an edit to this handoff or its index.

Tags: #agent/handoff #agent/orientation #finance/privacy #python/cli
