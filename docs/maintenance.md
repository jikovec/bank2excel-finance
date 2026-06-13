# Maintenance

## Rebuild

Run a normal build after adding exports:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx
```

Run offline when you want to use only local manual/cache FX rates:

```bash
python build_finance_workbook.py --input input --output output/Personal_Finance_Analysis.xlsx --no-fx-download
```

## Categories

Update `config/categories.csv` for local category and recurring-payment rules. Keep personal merchant names and counterparties out of tracked source and examples.

## New Banks

Add parser code under `bank_parsers/`, normalize rows into the shared transaction model, and register the parser in `discover_transactions`.

## Validation Warnings

Validation warnings identify missing FX rates, parser assumptions, low-confidence categories, possible duplicates, missing balances, or rows needing manual review. Reports are written to `reports/validation_summary.md` and ignored by Git.
