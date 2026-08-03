# Data Privacy

This project is designed so reusable code, examples, and documentation can be committed while real financial data stays local.

## Private Data

Private data includes:

- Bank transaction exports.
- Investment and savings valuation snapshots.
- Account identifiers and IBANs.
- Merchant names, counterparties, transaction descriptions, balances, and local category rules.
- Generated workbooks.
- Validation reports and build logs.
- Current financial snapshot values and personal review notes.
- Downloaded FX caches.
- Local absolute paths.
- `.env` values and local automation settings.

## Never Commit

Never commit real files from:

- `input/` export files.
- `output/` workbooks.
- `cache/` FX cache files.
- `reports/` validation reports and logs.
- `finance/private/` current-situation JSON and Markdown files.
- `.env`.
- `config/accounts.csv`.
- `config/categories.csv`.
- `config/currency_rates.csv`.
- `config/settings.yaml`.

The `.gitignore` keeps these locations ignored and allows only README, `.gitkeep`, and `.example` templates through.

## Commit Checklist

Before committing or pushing, run:

```bash
git status --ignored
git diff --cached
```

Check that only source, docs, scripts, `.gitignore`, `requirements.txt`, `.env.example`, `.gitkeep`, and fake `.example` files are staged.

Do not stage generated workbooks, raw exports, caches, private config, private
finance snapshots, or report files copied from `reports/`.

## Report Privacy

`reports/validation_summary.md` is useful evidence, but it can include:

- Absolute local paths.
- Source file names.
- Transaction counts and date ranges.
- Counterparty examples.
- Manual-review transaction groups.
- FX cache paths.

Keep generated reports under ignored `reports/`. If a report must be shared, scrub it first and store the scrubbed version under `docs/reports/` with a clear note that private values were removed.

## Network Behavior

Normal builds may download missing FX rates from the configured provider. The current source supports the Frankfurter provider. Use `--no-fx-download` for offline builds that rely only on manual and cached rates.

The pipeline does not upload bank exports. Generated workbook and report files are local outputs.
