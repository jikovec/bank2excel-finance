# Security Model

This project handles personal financial data locally. The security model is
based on local-only processing, ignored private paths, and careful handoff
discipline.

## Data Classes

Private data:

- Bank exports and investment snapshots.
- Account identifiers, IBANs, aliases, and ownership hints.
- Merchant names, counterparties, descriptions, balances, and category rules.
- Generated Excel workbooks.
- Generated validation summaries and build logs.
- Current financial snapshot values and personal review notes.
- FX caches.
- `.env` values.
- Local absolute paths.

Shareable data:

- Source code.
- Documentation.
- Scripts.
- `.example` config files with fake placeholders.
- `.gitkeep` placeholders.

## Private Paths

Do not read or edit these unless the user explicitly asks:

- `.env`
- `config/accounts.csv`
- `config/categories.csv`
- `config/currency_rates.csv`
- `config/settings.yaml`
- `input/`
- `output/`
- `cache/`
- `reports/`
- `finance/private/`

The only routine exception is creating a requested local validation report in
root `reports/`, as this validation did.

## Ignore Coverage

Current `.gitignore` protects:

- `.env`
- private config files under `config/`
- `input/`
- `output/`
- `cache/`
- root `reports/`
- private financial snapshots under `finance/private/`
- generated workbook, spreadsheet, PDF, XML, and TXT artifacts by extension
- `.obsidian/` local vault metadata

Tracked exceptions include example files, documentation, `.gitkeep`
placeholders, `requirements.txt`, and `README.md`.

## Network Behavior

Normal builds may call the Frankfurter FX API to fetch missing rates. Use
`--no-fx-download` for offline validation. The pipeline does not upload bank
exports.

## Handoff Rules

- Keep private generated evidence in root `reports/`.
- Put only scrubbed, shareable summaries in `docs/reports/`.
- Do not copy transaction examples, private paths, or account identifiers into
  tracked docs.
- Keep real current-situation values under `finance/private/`; tracked finance
  templates must contain only structure, `null`, or clearly fake values.
- Do not commit or push without explicit user approval.

See also `docs/security/data-privacy.md`.
