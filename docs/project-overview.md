# Project Overview

Finance Workbook Generator builds a local Excel workbook from private bank exports. It is designed for repeatable personal finance analysis while keeping real account data, exports, caches, reports, and generated workbooks out of Git.

## What It Does

The pipeline:

- Discovers bank export files under `input/`.
- Parses supported transaction exports into one normalized schema.
- Parses SLSP investment and savings valuation snapshots separately from transactions.
- Loads private account, category, manual FX-rate, and settings config from `config/`.
- Converts non-EUR rows to EUR using manual rates and the local FX cache, with optional Frankfurter downloads.
- Detects internal transfers, duplicate suspects, recurring groups, savings or investment transfers, and manual-review rows.
- Builds a styled workbook in `output/`.
- Writes a validation report in `reports/`.

## Supported Sources

Current transaction parsers are registered for:

- `input/revolut/`
- `input/tatrabanka/`
- `input/tatra/`, if created locally
- `input/slsp/`
- `input/slovenska_sporitelna/`, if created locally
- `input/legacy/`, if created locally

Current investment snapshot parsing is registered for SLSP-style investment or savings valuation snapshots under `input/investments/slsp/` and equivalent locally created Slovenska sporitelna folder names.

The shared parser helper recognizes `.csv`, `.xlsx`, and `.xls`. PDF discovery exists, but PDF parsing is intentionally unsupported unless a reliable extraction path is added for a specific bank layout.

## Generated Workbook

The workbook builder creates these major sheets:

- `Dashboard`
- `Raw_Transactions`
- `Investment_Snapshots`
- `Investment_Dashboard`
- `Accounts`
- `Categories`
- `Currency_Rates`
- `Recurring`
- One sheet per detected year
- `Validation`
- `Chart_Data`, hidden and used for workbook charts

## Private Runtime Data

The following paths are private runtime locations and are ignored by Git:

- `input/`
- `output/`
- `cache/`
- `reports/`
- `finance/private/`
- `.env`
- non-example config files under `config/`

Tracked `.example` files are fake placeholders. See [data privacy](security/data-privacy.md) before staging changes.

## Current Limits

- This repo is a CLI workbook generator, not a hosted service.
- No HTTP API, web routes, or frontend app are present.
- No dedicated automated test suite or CI config was found during the 2026-07-07 documentation inventory.
- No license file is included yet.
