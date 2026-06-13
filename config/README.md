# Local Configuration

Files without `.example` in this folder are private and ignored by Git.

Copy the example files before the first local build:

```powershell
Copy-Item config/accounts.example.csv config/accounts.csv
Copy-Item config/categories.example.csv config/categories.csv
Copy-Item config/currency_rates.example.csv config/currency_rates.csv
Copy-Item config/settings.example.yaml config/settings.yaml
```

Fill `accounts.csv` with your own account identifiers and optional transfer hints. Keep merchant-specific or personal category rules in `categories.csv`, not in tracked source code.
