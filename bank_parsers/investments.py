from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from .common import (
    clean_col,
    first_existing,
    normalize_text,
    parse_amount,
    parse_date,
    read_tabular_file,
    stable_transaction_id,
)

SLSP_INVESTMENT_BANK_NAME = "Slovenská sporiteľňa"

INVESTMENT_SNAPSHOT_COLUMNS = [
    "Snapshot_ID",
    "Source_File",
    "Source_Bank",
    "Source_Sheet",
    "Source_Row",
    "Snapshot_Date",
    "Account_Name",
    "Account_IBAN_or_Number",
    "Product_Name",
    "Product_Type",
    "ISIN_or_Product_ID",
    "Quantity",
    "Unit_Price",
    "Market_Value_Original",
    "Original_Currency",
    "Market_Value_EUR",
    "FX_Rate_To_EUR",
    "FX_Rate_Date",
    "FX_Rate_Source",
    "FX_Conversion_Status",
    "Notes",
    "Parser_Warning",
]

INVESTMENT_IMPORT_REPORT_COLUMNS = [
    "Bank",
    "File_Path",
    "Detected_Format",
    "Source_Apparent_Snapshot_Rows",
    "Parsed_Rows",
    "Skipped_Rows",
    "Skipped_Reasons",
    "Date_Range",
    "Currencies",
    "Product_Count",
    "Products",
    "Parser_Warnings",
]

DATE_ALIASES = ["Dátum splatnosti", "Dátum", "Snapshot date", "Statement date", "Date"]
VALUE_ALIASES = ["Suma", "Čiastka", "Ciastka", "Market value", "Hodnota", "Value", "Amount"]
CURRENCY_ALIASES = ["Mena", "Currency", "CCY"]
PRODUCT_ALIASES = ["Partner", "Produkt", "Product", "Fond", "Nástroj", "Nastroj", "Cenný papier"]
ACCOUNT_ALIASES = ["Vlastný IBAN", "IBAN", "Majetkový účet", "Majetkovy ucet", "Účet", "Císlo účtu", "Číslo účtu", "Account"]
ACCOUNT_NAME_ALIASES = ["Vlastný názov účtu", "Názov účtu", "Account name"]
PRODUCT_TYPE_ALIASES = ["Typ transakcie", "Typ produktu", "Product type", "Druh"]
NOTES_ALIASES = ["Popis transakcie", "Popis", "Detail", "Poznámka", "Description", "Notes"]

_INVESTMENT_IMPORT_REPORTS: list[dict[str, Any]] = []


def clear_investment_import_reports() -> None:
    _INVESTMENT_IMPORT_REPORTS.clear()


def record_investment_import_report(report: dict[str, Any]) -> None:
    normalized = {col: "" for col in INVESTMENT_IMPORT_REPORT_COLUMNS}
    normalized.update(report)
    _INVESTMENT_IMPORT_REPORTS.append(normalized)


def get_investment_import_reports() -> list[dict[str, Any]]:
    return [r.copy() for r in _INVESTMENT_IMPORT_REPORTS]


def normalized_investment_blank_row() -> dict[str, Any]:
    return {c: "" for c in INVESTMENT_SNAPSHOT_COLUMNS}


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
        has_value = _row_has_alias(values, VALUE_ALIASES)
        has_product = _row_has_alias(values, PRODUCT_ALIASES)
        if not (has_date and has_value and has_product):
            continue
        score = 3
        for aliases in [CURRENCY_ALIASES, ACCOUNT_ALIASES, ACCOUNT_NAME_ALIASES, PRODUCT_TYPE_ALIASES, NOTES_ALIASES]:
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
        header = normalize_text(value) or f"Unnamed_{pos}"
        counts[header] += 1
        if counts[header] > 1:
            header = f"{header}_{counts[header]}"
        headers.append(header)
    return headers


def _metadata_text(raw_df: pd.DataFrame, header_idx: int | None) -> str:
    if header_idx is None or header_idx <= 0:
        return ""
    parts: list[str] = []
    for _, raw in raw_df.iloc[:header_idx].iterrows():
        values = [normalize_text(v) for v in raw.tolist() if normalize_text(v)]
        if values:
            parts.append(" | ".join(values))
    return "; ".join(parts)


def _table_from_header(raw_df: pd.DataFrame, header_idx: int) -> pd.DataFrame:
    headers = _unique_headers(raw_df.iloc[header_idx].tolist())
    table = raw_df.iloc[header_idx + 1 :].copy()
    table.columns = headers
    table["__source_row"] = table.index + 1
    return table.reset_index(drop=True)


def _read_slsp_investment_tables(path: Path) -> list[tuple[str, pd.DataFrame, int | None, str]]:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=object, engine=None)
        out: list[tuple[str, pd.DataFrame, int | None, str]] = []
        for sheet_name, raw_df in sheets.items():
            header_idx = _detect_header_row(raw_df)
            if header_idx is None:
                out.append((sheet_name, pd.DataFrame(), None, _metadata_text(raw_df, None)))
            else:
                out.append((sheet_name, _table_from_header(raw_df, header_idx), header_idx + 1, _metadata_text(raw_df, header_idx)))
        return out
    out = []
    for sheet_name, df in read_tabular_file(path):
        table = df.dropna(how="all").copy()
        table["__source_row"] = table.index + 2
        out.append((sheet_name, table.reset_index(drop=True), 1, ""))
    return out


def _format_counter(counter: Counter[str]) -> str:
    if not counter:
        return "None"
    return "; ".join(f"{reason} ({count})" for reason, count in sorted(counter.items()))


def _extract_isin(text: str) -> str:
    match = re.search(r"\b[A-Z]{2}[A-Z0-9]{10}\b", text.upper())
    return match.group(0) if match else ""


def _extract_quantity(text: str) -> float | None:
    match = re.search(r"\b(?:units|quantity|počet|pocet)\s*[:=]?\s*([+-]?\d+(?:[ .]\d{3})*(?:[,.]\d+)?)", text, re.I)
    if not match:
        return None
    return parse_amount(match.group(1))


def _extract_unit_price(text: str) -> float | None:
    match = re.search(r"\bunit\s+price\s*[:=]?\s*([+-]?\d+(?:[,.]\d+)?)", text, re.I)
    if not match:
        return None
    return parse_amount(match.group(1))


def _extract_source_reference(text: str) -> str:
    match = re.search(r"\bsource\s+([^;]+)", text, re.I)
    return normalize_text(match.group(1)) if match else ""


def _normalize_product_type(value: Any) -> str:
    text = normalize_text(value)
    lower = text.lower()
    if "finan" in lower or "invest" in lower or "nástroj" in lower or "nastroj" in lower:
        return "Investment / Financial Instruments"
    if "sporen" in lower or "savings" in lower:
        return "Savings"
    return text or "Investment / Savings"


def _record_report(
    path: Path,
    detected_formats: list[str],
    apparent_rows: int,
    parsed_rows: list[dict[str, Any]],
    skipped_reasons: Counter[str],
    parser_warnings: list[str],
) -> None:
    dates = pd.to_datetime([r.get("Snapshot_Date") for r in parsed_rows], errors="coerce")
    valid_dates = [d for d in dates if not pd.isna(d)]
    currencies = Counter(normalize_text(r.get("Original_Currency")).upper() for r in parsed_rows if normalize_text(r.get("Original_Currency")))
    product_labels: dict[str, str] = {}
    for r in parsed_rows:
        isin = normalize_text(r.get("ISIN_or_Product_ID"))
        product = normalize_text(r.get("Product_Name"))
        key = isin or product
        if not key or key in product_labels:
            continue
        product_labels[key] = f"{product} ({isin})" if product and isin else (product or isin)
    products = sorted(product_labels.values())
    record_investment_import_report({
        "Bank": SLSP_INVESTMENT_BANK_NAME,
        "File_Path": str(path),
        "Detected_Format": "; ".join(detected_formats) or f"SLSP investment {path.suffix.lower().lstrip('.').upper()}",
        "Source_Apparent_Snapshot_Rows": apparent_rows,
        "Parsed_Rows": len(parsed_rows),
        "Skipped_Rows": sum(skipped_reasons.values()),
        "Skipped_Reasons": _format_counter(skipped_reasons),
        "Date_Range": f"{min(valid_dates).date()} to {max(valid_dates).date()}" if valid_dates else "",
        "Currencies": ", ".join(f"{ccy}: {count}" for ccy, count in sorted(currencies.items())),
        "Product_Count": len(product_labels),
        "Products": ", ".join(products[:12]) + ("..." if len(products) > 12 else ""),
        "Parser_Warnings": "; ".join(parser_warnings),
    })


def parse_slsp_investment_snapshot_file(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    apparent_rows = 0
    skipped_reasons: Counter[str] = Counter()
    parser_warnings: list[str] = []
    detected_formats: list[str] = []

    for sheet_name, df, header_row, metadata in _read_slsp_investment_tables(path):
        if header_row is None:
            parser_warnings.append(f"{sheet_name}: no SLSP investment snapshot header row found.")
            continue
        detected_formats.append(f"{sheet_name}: header row {header_row}")
        for idx, raw in df.iterrows():
            row = raw.to_dict()
            source_row = int(row.get("__source_row") or idx + 2)
            content_values = {k: v for k, v in row.items() if not str(k).startswith("__")}
            if not any(normalize_text(v) for v in content_values.values()):
                skipped_reasons[f"{sheet_name}!{source_row}: blank row after header"] += 1
                continue
            apparent_rows += 1

            snapshot_date = parse_date(first_existing(row, DATE_ALIASES))
            market_value = parse_amount(first_existing(row, VALUE_ALIASES))
            currency = normalize_text(first_existing(row, CURRENCY_ALIASES)).upper()[:3]
            product_name = normalize_text(first_existing(row, PRODUCT_ALIASES))
            account_name = normalize_text(first_existing(row, ACCOUNT_NAME_ALIASES))
            account_number = normalize_text(first_existing(row, ACCOUNT_ALIASES))
            product_type_raw = first_existing(row, PRODUCT_TYPE_ALIASES)
            notes_text = normalize_text(first_existing(row, NOTES_ALIASES))

            reasons: list[str] = []
            if pd.isna(snapshot_date):
                reasons.append("missing/invalid snapshot date")
            if market_value is None:
                reasons.append("missing/invalid market value")
            if not currency:
                reasons.append("missing currency")
            if reasons:
                skipped_reasons[f"{sheet_name}!{source_row}: {', '.join(reasons)}"] += 1
                continue

            isin = _extract_isin(notes_text)
            quantity = _extract_quantity(notes_text)
            unit_price = _extract_unit_price(notes_text)
            source_ref = _extract_source_reference(notes_text)

            warning_parts: list[str] = []
            if not product_name:
                product_name = isin or "Unspecified investment product"
                warning_parts.append("Missing product name; used ISIN/product placeholder.")
            if quantity is not None and unit_price is not None and market_value is not None:
                calculated_value = quantity * unit_price
                if abs(calculated_value - market_value) > 0.05:
                    warning_parts.append(f"Quantity x unit price differs from market value by {calculated_value - market_value:.2f} {currency}.")

            notes_parts = []
            if source_ref:
                notes_parts.append(f"Source reference: {source_ref}")
            if notes_text:
                notes_parts.append(f"Source text: {notes_text}")
            if metadata:
                notes_parts.append(f"Workbook metadata: {metadata}")

            out = normalized_investment_blank_row()
            out.update({
                "Source_File": path.name,
                "Source_Bank": SLSP_INVESTMENT_BANK_NAME,
                "Source_Sheet": sheet_name,
                "Source_Row": source_row,
                "Snapshot_Date": snapshot_date,
                "Account_Name": account_name or "SLSP Investment / Savings",
                "Account_IBAN_or_Number": account_number,
                "Product_Name": product_name,
                "Product_Type": _normalize_product_type(product_type_raw),
                "ISIN_or_Product_ID": isin,
                "Quantity": quantity if quantity is not None else "",
                "Unit_Price": unit_price if unit_price is not None else "",
                "Market_Value_Original": market_value,
                "Original_Currency": currency,
                "Market_Value_EUR": market_value if currency == "EUR" else "",
                "Notes": "; ".join(notes_parts),
                "Parser_Warning": " ".join(warning_parts),
            })
            out["Snapshot_ID"] = "INV_" + stable_transaction_id([
                path.name,
                sheet_name,
                source_row,
                snapshot_date,
                account_name,
                account_number,
                product_name,
                isin,
                market_value,
                currency,
            ]).upper()
            rows.append(out)

    _record_report(path, detected_formats, apparent_rows, rows, skipped_reasons, parser_warnings)
    return rows
