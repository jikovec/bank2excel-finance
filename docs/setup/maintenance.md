# Maintenance

## Rebuild After New Data

Run a normal build after adding exports:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx
```

Run offline when you want to use only local manual/cache FX rates:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx --no-fx-download
```

## Accounts

Update `config/accounts.csv` when you open, close, rename, or migrate accounts.

Useful fields:

- `Account_Name` and `Bank` help match source text to your own account.
- `IBAN_or_Account_Number` is normalized for own-account detection.
- `Aliases` helps match alternate source labels.
- `Belongs_To_Me` controls whether the account participates in own-account transfer detection.
- `Transfer_Hints` adds local text hints for internal transfer detection.

Keep real identifiers in the ignored private file, not in tracked examples.

## Categories And Recurring Rules

Update `config/categories.csv` for local category and recurring-payment rules. Keep personal merchant names and counterparties out of tracked source and examples.

The tracked example uses generic placeholder rules only. Local category rows drive category, subcategory, category type, confidence, keyword, and recurring-hint behavior.

## Currency Rates

Manual rates live in `config/currency_rates.csv`. The generated workbook includes an editable `Currency_Rates` sheet. Downloaded rates are cached in `cache/currency_rates_cache.csv`.

Use `--no-fx-download` for offline builds. Missing rates are flagged in the validation report instead of being invented.

## New Banks

To add a transaction source:

1. Add parser code under `bank_parsers/`.
2. Normalize rows into the shared transaction model from `bank_parsers/common.py`.
3. Register the parser in `discover_transactions()` in `build_finance_workbook.py`.
4. Make sure skipped rows and parser assumptions appear in source import reports.
5. Rebuild and review `reports/validation_summary.md`.

To add an investment snapshot source:

1. Add parser code under `bank_parsers/`.
2. Normalize rows into the investment snapshot schema from `bank_parsers/investments.py`.
3. Register the parser in `discover_investment_snapshots()`.
4. Rebuild and review the investment snapshot import table.

## Validation Warnings

Validation warnings identify:

- Missing FX rates.
- Parser assumptions.
- Low-confidence categories.
- Possible duplicate rows.
- Missing source balances.
- Transfer-like rows left for manual review.
- Recurring-like groups left unflagged because cadence or category evidence is weak.
- Investment snapshot parser warnings.

Reports are written to `reports/validation_summary.md` and ignored by Git because they can contain private paths and transaction details.
