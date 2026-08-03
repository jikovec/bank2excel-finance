# API And CLI Surface

The current repository does not contain an HTTP API, web server, frontend app, or route definitions. The supported user-facing interface is the Python CLI in `build_finance_workbook.py`.

## CLI Entrypoint

```bash
python build_finance_workbook.py [options]
```

| Option | Purpose |
| --- | --- |
| `--input` | Input folder containing bank export subfolders. |
| `--output` | Output `.xlsx` workbook path. |
| `--accounts` | Private account config CSV path. |
| `--categories` | Private category rules CSV path. |
| `--currency-rates` | Manual currency-rate CSV or XLSX path. |
| `--cache` | FX cache CSV path. |
| `--report` | Validation report Markdown path. |
| `--settings` | Optional YAML settings path. Defaults to `config/settings.yaml`. |
| `--package-dir` | Deprecated; retained for CLI compatibility. |
| `--no-fx-download` | Disable external FX API calls and use only manual/cache rates. |
| `--fx-provider` | FX provider for automatic historical rates. Current choice: `frankfurter`. |
| `--fx-mode` | FX conversion mode. Current choices: `historical` and `latest`. |

## Internal Extension Points

These functions are the main internal surfaces for extension:

- `discover_transactions()` in `build_finance_workbook.py`.
- `discover_investment_snapshots()` in `build_finance_workbook.py`.
- `parse_revolut_file()` in `bank_parsers/revolut.py`.
- `parse_tatrabanka_file()` in `bank_parsers/tatrabanka.py`.
- `parse_slsp_file()` in `bank_parsers/slsp.py`.
- `parse_slsp_investment_snapshot_file()` in `bank_parsers/investments.py`.

Parser outputs should normalize into the transaction columns defined in `bank_parsers/common.py` or the investment snapshot columns defined in `bank_parsers/investments.py`.

## Route Status

No route table, OpenAPI document, controller layer, or server config was found during the 2026-07-07 documentation inventory. If a service layer is added later, document it here and link to the owning source files.
