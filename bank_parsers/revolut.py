from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .common import (
    first_existing,
    infer_currency,
    normalize_text,
    normalized_blank_row,
    parse_amount,
    parse_date,
    read_tabular_file,
    stable_transaction_id,
)

DATE_ALIASES = ['Completed Date', 'Started Date', 'Date', 'Booking Date', 'Value Date']
DESC_ALIASES = ['Description', 'Reference', 'Type', 'Product', 'Notes']
COUNTERPARTY_ALIASES = ['Merchant', 'Counterparty', 'Description', 'Payer', 'Payee']
AMOUNT_ALIASES = ['Amount', 'Paid Out (EUR)', 'Paid In (EUR)', 'Money Out', 'Money In']
BALANCE_ALIASES = ['Balance', 'Balance After', 'Account Balance']
ACCOUNT_ALIASES = ['Account', 'Card', 'Product', 'Pocket']
REFERENCE_ALIASES = ['Reference', 'External Reference', 'Transaction ID', 'ID']


def parse_revolut_file(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sheet_name, df in read_tabular_file(path):
        if sheet_name == 'PDF':
            rows.append({'Parser_Warning': str(df.iloc[0, 0]), 'Source_File': path.name, 'Source_Bank': 'Revolut', 'Source_Sheet': 'PDF'})
            continue
        df = df.dropna(how='all')
        for idx, raw in df.iterrows():
            row = raw.to_dict()
            amount = parse_amount(first_existing(row, AMOUNT_ALIASES))
            money_in = parse_amount(first_existing(row, ['Money In', 'Paid In']))
            money_out = parse_amount(first_existing(row, ['Money Out', 'Paid Out']))
            if amount is None:
                if money_in is not None:
                    amount = abs(money_in)
                elif money_out is not None:
                    amount = -abs(money_out)
            if amount is None:
                continue
            booking_date = parse_date(first_existing(row, DATE_ALIASES))
            desc = normalize_text(first_existing(row, DESC_ALIASES))
            cp = normalize_text(first_existing(row, COUNTERPARTY_ALIASES))
            reference = normalize_text(first_existing(row, REFERENCE_ALIASES))
            out = normalized_blank_row()
            out.update({
                'Source_File': path.name,
                'Source_Bank': 'Revolut',
                'Source_Sheet': sheet_name,
                'Source_Row': int(idx) + 2,
                'Source_Account': normalize_text(first_existing(row, ACCOUNT_ALIASES)),
                'Account_Name': normalize_text(first_existing(row, ACCOUNT_ALIASES)) or 'Revolut Account',
                'Booking_Date': booking_date,
                'Value_Date': parse_date(first_existing(row, ['Value Date', 'Completed Date'])) or booking_date,
                'Counterparty_Name': cp,
                'Description': desc or cp,
                'Reference': reference,
                'Original_Amount': amount,
                'Original_Currency': infer_currency(row, 'EUR'),
                'Amount_EUR': amount if infer_currency(row, 'EUR') == 'EUR' else '',
                'Balance_After': parse_amount(first_existing(row, BALANCE_ALIASES)),
            })
            out['Transaction_ID'] = reference or stable_transaction_id([path.name, sheet_name, idx, booking_date, amount, cp, desc])
            rows.append(out)
    return rows
