# Local Configuration

Files without `.example` in this folder are private and ignored by Git.

Copy the example files before the first local build:

```powershell
Copy-Item config/accounts.example.csv config/accounts.csv
Copy-Item config/categories.example.csv config/categories.csv
Copy-Item config/currency_rates.example.csv config/currency_rates.csv
Copy-Item config/settings.example.yaml config/settings.yaml
```

Or run:

```powershell
.\scripts\setup_local.ps1
```

Private files:

- `accounts.csv` - own account identifiers, aliases, ownership flags, and transfer hints.
- `categories.csv` - local category, subcategory, confidence, keyword, and recurring rules.
- `currency_rates.csv` - manual dated FX rates.
- `settings.yaml` - local default paths and FX options.

Tracked `.example` files use fake placeholders only.

Keep merchant-specific rules, real account identifiers, and personal notes in private files, not in tracked examples or source code.

Related docs:

- [Development setup](../docs/setup/development.md)
- [Maintenance](../docs/setup/maintenance.md)
- [Data privacy](../docs/security/data-privacy.md)
