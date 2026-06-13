from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from .common import (
    clean_col,
    first_existing,
    infer_currency,
    normalize_text,
    normalized_blank_row,
    parse_amount,
    parse_date,
    read_tabular_file,
    record_import_report,
    stable_transaction_id,
)

SLSP_BANK_NAME = 'Slovenská sporiteľňa'

DATE_ALIASES = ['Dátum splatnosti', 'Dátum zaúčtovania', 'Dátum spracovania', 'Date', 'Dátum']
VALUE_DATE_ALIASES = ['Dátum valuty', 'Value date', 'Valuta']
AMOUNT_ALIASES = ['Suma', 'Čiastka', 'Ciastka', 'Amount']
CURRENCY_ALIASES = ['Mena', 'Currency', 'CCY']
DESC_ALIASES = ['Popis transakcie', 'Typ transakcie', 'Popis', 'Detail', 'Poznámka', 'Správa', 'Description']
COUNTERPARTY_ALIASES = ['Partner', 'Obchodník', 'Názov protiúčtu', 'Príjemca', 'Odosielateľ', 'Counterparty']
COUNTERPARTY_ACCOUNT_ALIASES = ['IBAN partnera', 'IBAN protiúčtu', 'Číslo účtu partnera', 'Protiúčet', 'Číslo účtu', 'Counterparty account']
ACCOUNT_ALIASES = ['Vlastný IBAN', 'IBAN', 'Účet', 'Číslo účtu', 'Account']
ACCOUNT_NAME_ALIASES = ['Vlastný názov účtu', 'Názov účtu', 'Account name']
REFERENCE_ALIASES = [
    'Referencia', 'Referenčné číslo', 'VS', 'KS', 'SS', 'ID transakcie',
    'Konštantný symbol', 'Špecifický symbol', 'Variabilný symbol',
]
BALANCE_ALIASES = ['Zostatok', 'Balance', 'Zostatok po transakcii']
DEBIT_ALIASES = ['Debit', 'Výdaj', 'Odchádzajúce']
CREDIT_ALIASES = ['Credit', 'Príjem', 'Prichádzajúce']


def _matches_alias(header: str, aliases: list[str]) -> bool:
    cleaned = clean_col(header)
    if not cleaned:
        return False
    for alias in aliases:
        ca = clean_col(alias)
        if cleaned == ca or ca in cleaned:
            return True
    return False


def _row_has_alias(headers: list[Any], aliases: list[str]) -> bool:
    return any(_matches_alias(str(h), aliases) for h in headers)


def _detect_header_row(df: pd.DataFrame) -> int | None:
    best_idx: int | None = None
    best_score = 0
    for idx, raw in df.iterrows():
        values = [normalize_text(v) for v in raw.tolist()]
        if not any(values):
            continue
        has_date = _row_has_alias(values, DATE_ALIASES)
        has_amount = _row_has_alias(values, AMOUNT_ALIASES)
        if not (has_date and has_amount):
            continue
        score = 2
        for aliases in [
            CURRENCY_ALIASES,
            DESC_ALIASES,
            COUNTERPARTY_ALIASES,
            COUNTERPARTY_ACCOUNT_ALIASES,
            ACCOUNT_ALIASES,
            ACCOUNT_NAME_ALIASES,
            REFERENCE_ALIASES,
            BALANCE_ALIASES,
        ]:
            if _row_has_alias(values, aliases):
                score += 1
        if score > best_score:
            best_score = score
            best_idx = int(idx)
    return best_idx


def _unique_headers(values: list[Any]) -> list[str]:
    counts: Counter[str] = Counter()
    headers: list[str] = []
    for pos, value in enumerate(values, start=1):
        header = normalize_text(value) or f'Unnamed_{pos}'
        counts[header] += 1
        if counts[header] > 1:
            header = f'{header}_{counts[header]}'
        headers.append(header)
    return headers


def _table_from_header(raw_df: pd.DataFrame, header_idx: int) -> pd.DataFrame:
    headers = _unique_headers(raw_df.iloc[header_idx].tolist())
    table = raw_df.iloc[header_idx + 1:].copy()
    table.columns = headers
    table['__source_row'] = table.index + 1
    return table.reset_index(drop=True)


def _read_slsp_tables(path: Path) -> list[tuple[str, pd.DataFrame, int | None]]:
    if path.suffix.lower() in {'.xlsx', '.xls'}:
        sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=object, engine=None)
        out: list[tuple[str, pd.DataFrame, int | None]] = []
        for sheet_name, raw_df in sheets.items():
            header_idx = _detect_header_row(raw_df)
            if header_idx is None:
                out.append((sheet_name, pd.DataFrame(), None))
            else:
                out.append((sheet_name, _table_from_header(raw_df, header_idx), header_idx + 1))
        return out
    return [(sheet_name, df.dropna(how='all'), 1) for sheet_name, df in read_tabular_file(path)]


def _join_existing(row: dict[str, Any], aliases: list[str]) -> str:
    parts: list[str] = []
    seen: set[str] = set()
    for alias in aliases:
        value = normalize_text(first_existing(row, [alias]))
        if value and value not in seen:
            parts.append(value)
            seen.add(value)
    return ' | '.join(parts)


def _build_reference(row: dict[str, Any]) -> str:
    labeled = [
        ('Referenčné číslo', 'Reference'),
        ('Referencia', 'Reference'),
        ('ID transakcie', 'Transaction ID'),
        ('Variabilný symbol', 'VS'),
        ('Špecifický symbol', 'SS'),
        ('Konštantný symbol', 'KS'),
        ('VS', 'VS'),
        ('SS', 'SS'),
        ('KS', 'KS'),
    ]
    parts: list[str] = []
    seen: set[str] = set()
    for alias, label in labeled:
        value = normalize_text(first_existing(row, [alias]))
        if not value:
            continue
        text = f'{label}: {value}'
        if text not in seen:
            parts.append(text)
            seen.add(text)
    return '; '.join(parts)


def _format_counter(counter: Counter[str]) -> str:
    if not counter:
        return 'None'
    return '; '.join(f'{reason} ({count})' for reason, count in sorted(counter.items()))


def _record_report(
    path: Path,
    detected_formats: list[str],
    apparent_rows: int,
    parsed_rows: list[dict[str, Any]],
    skipped_reasons: Counter[str],
    parser_warnings: list[str],
    old_zero_reason: str = '',
) -> None:
    amounts = [parse_amount(r.get('Original_Amount')) for r in parsed_rows]
    amounts = [a for a in amounts if a is not None]
    dates = pd.to_datetime([r.get('Booking_Date') for r in parsed_rows], errors='coerce')
    valid_dates = [d for d in dates if not pd.isna(d)]
    currencies = Counter(normalize_text(r.get('Original_Currency')).upper() for r in parsed_rows if normalize_text(r.get('Original_Currency')))
    warnings = list(parser_warnings)
    if old_zero_reason:
        warnings.append(old_zero_reason)
    record_import_report({
        'Bank': SLSP_BANK_NAME,
        'File_Path': str(path),
        'Detected_Format': '; '.join(detected_formats) or f'SLSP {path.suffix.lower().lstrip(".").upper()}',
        'Source_Apparent_Transaction_Rows': apparent_rows,
        'Parsed_Rows': len(parsed_rows),
        'Skipped_Rows': sum(skipped_reasons.values()),
        'Skipped_Reasons': _format_counter(skipped_reasons),
        'Date_Range': f'{min(valid_dates).date()} to {max(valid_dates).date()}' if valid_dates else '',
        'Currencies': ', '.join(f'{ccy}: {count}' for ccy, count in sorted(currencies.items())),
        'Incoming_Amount': round(sum(a for a in amounts if a > 0), 2),
        'Outgoing_Amount': round(sum(abs(a) for a in amounts if a < 0), 2),
        'Parser_Warnings': '; '.join(warnings),
    })


def parse_slsp_file(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    apparent_rows = 0
    skipped_reasons: Counter[str] = Counter()
    parser_warnings: list[str] = []
    detected_formats: list[str] = []
    old_zero_reason = ''

    for sheet_name, df, header_row in _read_slsp_tables(path):
        if sheet_name == 'PDF':
            warning = str(df.iloc[0, 0])
            parser_warnings.append(warning)
            rows.append({'Parser_Warning': warning, 'Source_File': path.name, 'Source_Bank': SLSP_BANK_NAME, 'Source_Sheet': 'PDF'})
            continue
        if header_row is None:
            parser_warnings.append(f'{sheet_name}: no SLSP transaction header row found.')
            continue
        detected_formats.append(f'{sheet_name}: header row {header_row}')
        if header_row > 1:
            old_zero_reason = (
                'Previously imported 0 rows because the XLSX has metadata rows before the transaction table; '
                f'the real header is on Excel row {header_row}.'
            )
        for idx, raw in df.iterrows():
            row = raw.to_dict()
            source_row = int(row.get('__source_row') or idx + 2)
            content_values = {k: v for k, v in row.items() if not str(k).startswith('__')}
            if not any(normalize_text(v) for v in content_values.values()):
                skipped_reasons[f'{sheet_name}!{source_row}: blank row after header'] += 1
                continue
            apparent_rows += 1

            amount = parse_amount(first_existing(row, AMOUNT_ALIASES))
            if amount is None:
                debit = parse_amount(first_existing(row, DEBIT_ALIASES))
                credit = parse_amount(first_existing(row, CREDIT_ALIASES))
                if credit is not None:
                    amount = abs(credit)
                elif debit is not None:
                    amount = -abs(debit)

            booking_date = parse_date(first_existing(row, DATE_ALIASES))
            currency_value = first_existing(row, CURRENCY_ALIASES)
            currency = normalize_text(currency_value).upper()[:3] if normalize_text(currency_value) else infer_currency(row, '')
            if currency:
                currency = currency.upper()[:3]

            reasons: list[str] = []
            if amount is None:
                reasons.append('missing/invalid amount')
            if pd.isna(booking_date):
                reasons.append('missing/invalid transaction date')
            if not currency:
                reasons.append('missing currency')
            if reasons:
                skipped_reasons[f'{sheet_name}!{source_row}: {", ".join(reasons)}'] += 1
                continue

            desc = _join_existing(row, ['Popis transakcie', 'Typ transakcie', 'Popis', 'Detail', 'Poznámka', 'Správa', 'Description'])
            cp = normalize_text(first_existing(row, COUNTERPARTY_ALIASES))
            cp_account = normalize_text(first_existing(row, COUNTERPARTY_ACCOUNT_ALIASES))
            reference = _build_reference(row) or normalize_text(first_existing(row, REFERENCE_ALIASES))
            account = normalize_text(first_existing(row, ACCOUNT_ALIASES))
            account_name = normalize_text(first_existing(row, ACCOUNT_NAME_ALIASES))
            value_date = parse_date(first_existing(row, VALUE_DATE_ALIASES))
            if pd.isna(value_date):
                value_date = ''
            out = normalized_blank_row()
            out.update({
                'Source_File': path.name,
                'Source_Bank': SLSP_BANK_NAME,
                'Source_Sheet': sheet_name,
                'Source_Row': source_row,
                'Source_Account': account,
                'Account_Name': account_name or account or 'Slovenská sporiteľňa Account',
                'Account_IBAN_or_Number': account,
                'Booking_Date': booking_date,
                'Value_Date': value_date,
                'Counterparty_Name': cp,
                'Counterparty_Account': cp_account,
                'Description': desc or cp,
                'Reference': reference,
                'Original_Amount': amount,
                'Original_Currency': currency,
                'Amount_EUR': amount if currency == 'EUR' else '',
                'Balance_After': parse_amount(first_existing(row, BALANCE_ALIASES)),
            })
            out['Transaction_ID'] = stable_transaction_id([path.name, sheet_name, source_row, booking_date, amount, account, cp, cp_account, desc, reference])
            rows.append(out)
    _record_report(path, detected_formats, apparent_rows, rows, skipped_reasons, parser_warnings, old_zero_reason)
    return rows
