from __future__ import annotations

from pathlib import Path
from typing import Any

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

DATE_ALIASES = ['Dátum spracovania', 'Dátum zaúčtovania', 'Datum zauctovania', 'Dátum účtovania', 'Booking date', 'Date', 'Dátum']
VALUE_DATE_ALIASES = ['Dátum zúčtovania', 'Dátum valuty', 'Value date', 'Valuta']
AMOUNT_ALIASES = ['Suma', 'Amount', 'Čiastka', 'Ciastka']
DESC_ALIASES = ['Popis transakcie', 'Popis', 'Detail', 'Správa pre prijímateľa', 'Informácia pre príjemcu', 'Poznámka', 'Description', 'Účel platby']
COUNTERPARTY_ALIASES = ['Názov protiúčtu', 'Názov druhého účtu', 'Protiúčet názov', 'Partner', 'Counterparty', 'Príjemca / Platiteľ', 'Obchodné miesto']
COUNTERPARTY_ACCOUNT_ALIASES = ['IBAN protiúčtu', 'Protiúčet', 'Counterparty account', 'Číslo účtu', 'Číslo účtu / IBAN']
ACCOUNT_ALIASES = ['Číslo účtu / IBAN', 'IBAN', 'Účet', 'Account', 'Číslo účtu platiteľa']
REFERENCE_ALIASES = ['Referencia platby', 'Referencia platiteľa', 'Variabilný symbol', 'Špecifický symbol', 'Konštantný symbol', 'VS', 'KS', 'SS', 'Referenčné číslo', 'Reference', 'ID transakcie']
BALANCE_ALIASES = ['Zostatok', 'Balance', 'Zostatok po transakcii']


def parse_tatrabanka_file(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sheet_name, df in read_tabular_file(path):
        if sheet_name == 'PDF':
            rows.append({'Parser_Warning': str(df.iloc[0, 0]), 'Source_File': path.name, 'Source_Bank': 'Tatra banka', 'Source_Sheet': 'PDF'})
            continue
        df = df.dropna(how='all')
        for idx, raw in df.iterrows():
            row = raw.to_dict()
            amount = parse_amount(first_existing(row, AMOUNT_ALIASES))
            if amount is None:
                debit = parse_amount(first_existing(row, ['Debit', 'Má dať', 'Odchádzajúce']))
                credit = parse_amount(first_existing(row, ['Credit', 'Dal', 'Prichádzajúce']))
                if credit is not None:
                    amount = abs(credit)
                elif debit is not None:
                    amount = -abs(debit)
            if amount is None:
                continue
            booking_date = parse_date(first_existing(row, DATE_ALIASES))
            desc = normalize_text(first_existing(row, DESC_ALIASES))
            raw_cp = normalize_text(first_existing(row, COUNTERPARTY_ALIASES[:-1]))
            merchant = normalize_text(first_existing(row, ['Obchodné miesto']))
            cp = raw_cp or merchant
            cp_account = normalize_text(first_existing(row, COUNTERPARTY_ACCOUNT_ALIASES))
            reference = normalize_text(first_existing(row, REFERENCE_ALIASES))
            account = normalize_text(first_existing(row, ACCOUNT_ALIASES))
            currency = infer_currency(row, 'EUR')
            out = normalized_blank_row()
            out.update({
                'Source_File': path.name,
                'Source_Bank': 'Tatra banka',
                'Source_Sheet': sheet_name,
                'Source_Row': int(idx) + 2,
                'Source_Account': account,
                'Account_Name': account or 'Tatra banka Account',
                'Account_IBAN_or_Number': account,
                'Booking_Date': booking_date,
                'Value_Date': parse_date(first_existing(row, VALUE_DATE_ALIASES)) or booking_date,
                'Counterparty_Name': cp,
                'Counterparty_Account': cp_account,
                'Description': desc or cp,
                'Reference': reference,
                'Original_Amount': amount,
                'Original_Currency': currency,
                'Amount_EUR': amount if currency == 'EUR' else '',
                'Balance_After': parse_amount(first_existing(row, BALANCE_ALIASES)),
            })
            out['Transaction_ID'] = reference or stable_transaction_id([path.name, sheet_name, idx, booking_date, amount, raw_cp, cp_account, desc])
            rows.append(out)
    return rows
