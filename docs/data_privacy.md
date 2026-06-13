# Data Privacy

This project is designed so reusable code and examples can be committed while real financial data stays local.

Private data includes bank exports, investment snapshots, account identifiers, IBANs, transaction descriptions, counterparties, balances, generated workbooks, validation reports, downloaded FX caches, and local absolute paths.

Never commit:

- `input/` export files
- `output/` workbooks
- `cache/` FX cache files
- `reports/` validation reports
- `.env`
- `config/accounts.csv`
- `config/categories.csv`
- `config/currency_rates.csv`
- `config/settings.yaml`

The `.gitignore` keeps those locations ignored and allows only README, `.gitkeep`, and `.example` templates through.

Before pushing, run:

```bash
git status --ignored
git diff --cached
```

Check that only source, docs, scripts, and fake `.example` files are staged.
