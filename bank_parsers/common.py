from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

SUPPORTED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
PDF_UNSUPPORTED_WARNING = 'PDF parsing is intentionally unsupported unless reliable extraction is added for a specific bank export layout.'

MONTHS_SK = {
    'január': 1, 'januar': 1, 'február': 2, 'februar': 2, 'marec': 3, 'apríl': 4, 'april': 4,
    'máj': 5, 'maj': 5, 'jún': 6, 'jun': 6, 'júl': 7, 'jul': 7, 'august': 8,
    'september': 9, 'október': 10, 'oktober': 10, 'november': 11, 'december': 12,
}

MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
    7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December',
}

NORMALIZED_COLUMNS = [
    'Transaction_ID', 'Source_File', 'Source_Bank', 'Source_Sheet', 'Source_Row', 'Source_Account',
    'Account_Name', 'Account_IBAN_or_Number', 'Booking_Date', 'Value_Date', 'Year', 'Month_Number',
    'Month_Name', 'Counterparty_Name', 'Counterparty_Account', 'Description', 'Reference',
    'Original_Amount', 'Original_Currency', 'Amount_EUR', 'FX_Rate_To_EUR', 'FX_Rate_Date',
    'FX_Rate_Source', 'FX_Conversion_Status', 'Direction', 'Income_Amount', 'Expense_Amount',
    'Balance_After', 'Category', 'Subcategory', 'Category_Type', 'Category_Confidence',
    'Is_Internal_Transfer', 'Transfer_Group_ID', 'Is_Savings_Investment', 'Savings_Investment_Type',
    'Is_Recurring', 'Recurring_Group_ID', 'Is_Ignored', 'Is_Duplicate_Suspect', 'Duplicate_Reason',
    'Parser_Warning', 'Notes',
]

SOURCE_IMPORT_REPORT_COLUMNS = [
    'Bank', 'File_Path', 'Detected_Format', 'Source_Apparent_Transaction_Rows',
    'Parsed_Rows', 'Skipped_Rows', 'Skipped_Reasons', 'Date_Range',
    'Currencies', 'Incoming_Amount', 'Outgoing_Amount', 'Parser_Warnings',
]

_SOURCE_IMPORT_REPORTS: list[dict[str, Any]] = []


def clear_import_reports() -> None:
    _SOURCE_IMPORT_REPORTS.clear()


def record_import_report(report: dict[str, Any]) -> None:
    normalized = {col: '' for col in SOURCE_IMPORT_REPORT_COLUMNS}
    normalized.update(report)
    _SOURCE_IMPORT_REPORTS.append(normalized)


def get_import_reports() -> list[dict[str, Any]]:
    return [r.copy() for r in _SOURCE_IMPORT_REPORTS]


def normalize_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ''
    return re.sub(r'\s+', ' ', str(value).strip())


def clean_col(name: Any) -> str:
    s = normalize_text(name).lower()
    s = s.replace('\ufeff', '')
    s = re.sub(r'[^a-z0-9áäčďéíĺľňóôŕšťúýž/ _.-]+', '', s)
    return s.strip()


def parse_amount(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    s = s.replace('\xa0', ' ')
    s = re.sub(r'[^0-9,.-]', '', s)
    if not s or s in {'-', '.', ',', '-.'}:
        return None
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def parse_date(value: Any, fallback_year: int | None = None, fallback_month: int | None = None) -> pd.Timestamp | pd.NaT:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        if fallback_year and fallback_month:
            return pd.Timestamp(year=fallback_year, month=fallback_month, day=1)
        return pd.NaT
    if isinstance(value, pd.Timestamp):
        return value
    if isinstance(value, datetime):
        return pd.Timestamp(value)
    s = normalize_text(value)
    if not s:
        if fallback_year and fallback_month:
            return pd.Timestamp(year=fallback_year, month=fallback_month, day=1)
        return pd.NaT
    candidates = [s]
    if fallback_year and re.fullmatch(r'\d{1,2}[./-]\d{1,2}\.?', s):
        candidates.append(f'{s}.{fallback_year}')
    for candidate in candidates:
        dt = pd.to_datetime(candidate, dayfirst=True, errors='coerce')
        if not pd.isna(dt):
            return pd.Timestamp(dt)
    if fallback_year and fallback_month:
        return pd.Timestamp(year=fallback_year, month=fallback_month, day=1)
    return pd.NaT


def infer_currency(row: dict[str, Any], default: str = 'EUR') -> str:
    for key, value in row.items():
        ck = clean_col(key)
        if 'currency' in ck or 'mena' in ck or ck == 'ccy':
            s = normalize_text(value).upper()
            if s:
                return s[:3]
    return default


def stable_transaction_id(parts: Iterable[Any]) -> str:
    joined = '|'.join(normalize_text(p).lower() for p in parts)
    return hashlib.sha256(joined.encode('utf-8')).hexdigest()[:20]


def read_tabular_file(path: Path) -> list[tuple[str, pd.DataFrame]]:
    ext = path.suffix.lower()
    if ext == '.csv':
        # Try common European and international separators/encodings.
        for encoding in ['utf-8-sig', 'utf-8', 'cp1250', 'latin1']:
            for sep in [None, ';', ',', '\t']:
                try:
                    df = pd.read_csv(path, sep=sep, engine='python', encoding=encoding)
                    if len(df.columns) >= 2:
                        return [('CSV', df)]
                except Exception:
                    pass
        raise ValueError(f'Could not parse CSV file: {path}')
    if ext in {'.xlsx', '.xls'}:
        sheets = pd.read_excel(path, sheet_name=None, dtype=object, engine=None)
        return list(sheets.items())
    if ext == '.pdf':
        return [('PDF', pd.DataFrame({'Parser_Warning': [PDF_UNSUPPORTED_WARNING]}))]
    return []


def first_existing(row: dict[str, Any], aliases: list[str]) -> Any:
    cleaned = {clean_col(k): v for k, v in row.items()}
    for alias in aliases:
        ca = clean_col(alias)
        if ca in cleaned and normalize_text(cleaned[ca]) != '':
            return cleaned[ca]
    for key, value in cleaned.items():
        for alias in aliases:
            if clean_col(alias) in key and normalize_text(value) != '':
                return value
    return None


def normalized_blank_row() -> dict[str, Any]:
    return {c: '' for c in NORMALIZED_COLUMNS}
