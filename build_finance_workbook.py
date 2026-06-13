from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from openpyxl import load_workbook
except Exception as exc:  # pragma: no cover
    load_workbook = None

from bank_parsers import (
    INVESTMENT_IMPORT_REPORT_COLUMNS,
    INVESTMENT_SNAPSHOT_COLUMNS,
    clear_investment_import_reports,
    get_investment_import_reports,
    parse_revolut_file,
    parse_slsp_file,
    parse_slsp_investment_snapshot_file,
    parse_tatrabanka_file,
)
from bank_parsers.common import (
    MONTH_NAMES,
    MONTHS_SK,
    NORMALIZED_COLUMNS,
    PDF_UNSUPPORTED_WARNING,
    SOURCE_IMPORT_REPORT_COLUMNS,
    clear_import_reports,
    get_import_reports,
    normalize_text,
    normalized_blank_row,
    parse_amount,
    parse_date,
    stable_transaction_id,
)

# =========================
# Centralized color palette
# =========================
COLOR_BG = "000000"
COLOR_PANEL = "111111"
COLOR_PANEL_2 = "181818"
COLOR_PRIMARY = "B51E02"
COLOR_SECONDARY = "B57602"
COLOR_PRIMARY_DARK = "611B08"
COLOR_PRIMARY_LIGHT = "FC2803"
COLOR_COMPLEMENT = "029AB5"
COLOR_TEXT = "F2F2F2"
COLOR_TEXT_MUTED = "BFBFBF"
COLOR_GRID = "333333"
COLOR_WARNING = "FC2803"
COLOR_GOOD = "029AB5"

FINAL_CLEANUP_BASELINE = {
    "uncategorized_rows": 0,
    "duplicate_suspects": 0,
}

ACCOUNT_CONFIG_COLUMNS = [
    "Account_Name",
    "Bank",
    "Currency",
    "IBAN_or_Account_Number",
    "Aliases",
    "Belongs_To_Me",
    "Detected_Row_Count",
    "Notes",
    "Transfer_Hints",
]

CONFIGURED_OWN_ACCOUNTS: list[dict[str, Any]] = []
OWN_ACCOUNT_IDENTIFIER_SET: set[str] = set()
OWN_TRANSFER_HINTS: list[str] = []


def normalize_account_identifier(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", normalize_text(value).upper())


def parse_bool(value: Any, default: bool = False) -> bool:
    text = normalize_text(value).lower()
    if not text:
        return default
    if text in {"1", "true", "yes", "y", "t", "me", "mine"}:
        return True
    if text in {"0", "false", "no", "n", "f"}:
        return False
    return default


def split_config_list(value: Any) -> list[str]:
    text = normalize_text(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"[;\n]+", text) if part.strip()]


def set_configured_own_accounts(accounts: list[dict[str, Any]]) -> None:
    global CONFIGURED_OWN_ACCOUNTS, OWN_ACCOUNT_IDENTIFIER_SET, OWN_TRANSFER_HINTS
    normalized_accounts: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    transfer_hints: set[str] = set()
    for raw in accounts:
        row = {col: normalize_text(raw.get(col, "")) for col in ACCOUNT_CONFIG_COLUMNS}
        row["Belongs_To_Me"] = parse_bool(raw.get("Belongs_To_Me"), True)
        row["Detected_Row_Count"] = int(parse_amount(raw.get("Detected_Row_Count")) or 0)
        normalized_accounts.append(row)
        if row["Belongs_To_Me"]:
            identifier = normalize_account_identifier(row.get("IBAN_or_Account_Number"))
            if identifier:
                identifiers.add(identifier)
            for hint in split_config_list(row.get("Transfer_Hints")):
                clean_hint = normalize_text(hint).lower()
                if len(clean_hint) >= 4:
                    transfer_hints.add(clean_hint)
    CONFIGURED_OWN_ACCOUNTS = normalized_accounts
    OWN_ACCOUNT_IDENTIFIER_SET = identifiers
    OWN_TRANSFER_HINTS = sorted(transfer_hints, key=len, reverse=True)


def read_csv_config(path: Path) -> tuple[pd.DataFrame | None, str | None]:
    for encoding in ["utf-8-sig", "utf-8", "cp1250", "latin1"]:
        try:
            return pd.read_csv(path, dtype=object, encoding=encoding), None
        except Exception as exc:
            last_error = str(exc)
    return None, last_error if "last_error" in locals() else "unknown CSV read error"


def load_accounts_config(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], [
            f"Private account config not found: {path}. Copy config/accounts.example.csv to config/accounts.csv and fill your local account identifiers."
        ]
    raw, error = read_csv_config(path)
    if raw is None:
        return [], [f"Private account config could not be read from {path}: {error}"]
    for col in ACCOUNT_CONFIG_COLUMNS:
        if col not in raw.columns:
            raw[col] = ""
    rows = raw[ACCOUNT_CONFIG_COLUMNS].fillna("").to_dict("records")
    if not rows:
        return [], [f"Private account config has no rows: {path}"]
    return rows, []


def account_matches_bank_text(account: dict[str, Any], bank: Any, account_name: Any = "") -> bool:
    text = f"{normalize_text(bank)} {normalize_text(account_name)}".lower().strip()
    if not text:
        return False
    candidates = [account.get("Bank"), account.get("Account_Name")]
    candidates.extend(split_config_list(account.get("Aliases")))
    for candidate in candidates:
        value = normalize_text(candidate).lower()
        if len(value) < 3:
            continue
        if value in text or text in value:
            return True
    return False


def default_own_iban_for_bank(bank: Any, account_name: Any = "") -> str:
    for account in CONFIGURED_OWN_ACCOUNTS:
        if not parse_bool(account.get("Belongs_To_Me"), True):
            continue
        if account_matches_bank_text(account, bank, account_name):
            return normalize_text(account.get("IBAN_or_Account_Number"))
    return ""


def is_configured_own_iban(value: Any) -> bool:
    identifier = normalize_account_identifier(value)
    return bool(identifier and identifier in OWN_ACCOUNT_IDENTIFIER_SET)


def has_configured_transfer_hint(text: Any) -> bool:
    haystack = normalize_text(text).lower()
    return bool(haystack and any(hint in haystack for hint in OWN_TRANSFER_HINTS))


def append_note(existing: Any, note: str) -> str:
    existing_text = normalize_text(existing)
    if not existing_text:
        return note
    if note in existing_text:
        return existing_text
    return f"{existing_text} {note}"


CHART_DIR = Path(tempfile.mkdtemp(prefix="finance_workbook_charts_"))

def chart_palette(n: int) -> list[str]:
    base = [f"#{COLOR_PRIMARY}", f"#{COLOR_SECONDARY}", f"#{COLOR_COMPLEMENT}", f"#{COLOR_PRIMARY_LIGHT}", f"#{COLOR_PRIMARY_DARK}", "#7A7A7A", "#D64A1F", "#0D7C91", "#E07A2F", "#8A2D12"]
    return [base[i % len(base)] for i in range(max(n, 1))]

def _finish_chart(fig, path: Path):
    fig.savefig(path, dpi=120, facecolor=f"#{COLOR_BG}", edgecolor=f"#{COLOR_BG}")
    plt.close(fig)
    return str(path)

def save_pie_image(df: pd.DataFrame, label_col: str, value_col: str, title: str, filename: str, width: float = 3.5, height: float = 2.2) -> str:
    path = CHART_DIR / f"{filename}.png"
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(f"#{COLOR_BG}")
    ax.set_facecolor(f"#{COLOR_PANEL}")
    ax.set_title(title, color=f"#{COLOR_TEXT}", fontsize=10, fontweight="bold", pad=8)
    if df is None or df.empty or label_col not in df.columns or value_col not in df.columns:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", color=f"#{COLOR_TEXT_MUTED}", fontsize=11)
        ax.set_axis_off()
        return _finish_chart(fig, path)
    tmp = df[[label_col, value_col]].copy()
    tmp[value_col] = pd.to_numeric(tmp[value_col], errors="coerce").fillna(0)
    tmp = tmp[tmp[value_col] > 0].head(10)
    if tmp.empty:
        ax.text(0.5, 0.5, "No data detected", ha="center", va="center", color=f"#{COLOR_TEXT_MUTED}", fontsize=10)
        ax.set_axis_off()
        return _finish_chart(fig, path)
    labels = tmp[label_col].astype(str).tolist()
    values = tmp[value_col].astype(float).tolist()
    wedges, _texts, autotexts = ax.pie(
        values,
        startangle=90,
        colors=chart_palette(len(values)),
        autopct=lambda pct: f"{pct:.0f}%" if pct >= 6 else "",
        pctdistance=0.72,
        wedgeprops={"linewidth": 0.8, "edgecolor": f"#{COLOR_BG}"},
        textprops={"color": f"#{COLOR_TEXT}", "fontsize": 7},
    )
    for t in autotexts:
        t.set_color(f"#{COLOR_TEXT}")
        t.set_fontweight("bold")
    ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=6, frameon=False, labelcolor=f"#{COLOR_TEXT_MUTED}")
    ax.axis("equal")
    return _finish_chart(fig, path)

def save_line_image(df: pd.DataFrame, x_col: str, series: list[tuple[str, str, str]], title: str, filename: str, width: float = 4.8, height: float = 2.3) -> str:
    path = CHART_DIR / f"{filename}.png"
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(f"#{COLOR_BG}")
    ax.set_facecolor(f"#{COLOR_PANEL}")
    ax.set_title(title, color=f"#{COLOR_TEXT}", fontsize=10, fontweight="bold", pad=8)
    if df is None or df.empty or x_col not in df.columns:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", color=f"#{COLOR_TEXT_MUTED}")
    else:
        x = df[x_col].astype(str).tolist()
        for label, y_col, color in series:
            y = pd.to_numeric(df[y_col], errors="coerce").fillna(0).tolist() if y_col in df.columns else [0] * len(x)
            ax.plot(x, y, marker="o", linewidth=2.2, markersize=3, label=label, color=f"#{color}")
        ax.tick_params(axis="x", colors=f"#{COLOR_TEXT_MUTED}", labelsize=7, rotation=45)
        ax.tick_params(axis="y", colors=f"#{COLOR_TEXT_MUTED}", labelsize=7)
        ax.grid(True, color=f"#{COLOR_GRID}", linewidth=0.5, alpha=0.7)
        ax.legend(loc="upper left", fontsize=7, frameon=False, labelcolor=f"#{COLOR_TEXT}")
    for spine in ax.spines.values():
        spine.set_color(f"#{COLOR_PRIMARY}")
    return _finish_chart(fig, path)

def save_column_image(df: pd.DataFrame, x_col: str, y_cols: list[tuple[str, str, str]], title: str, filename: str, width: float = 4.8, height: float = 2.3) -> str:
    path = CHART_DIR / f"{filename}.png"
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(f"#{COLOR_BG}")
    ax.set_facecolor(f"#{COLOR_PANEL}")
    ax.set_title(title, color=f"#{COLOR_TEXT}", fontsize=10, fontweight="bold", pad=8)
    if df is None or df.empty or x_col not in df.columns:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", color=f"#{COLOR_TEXT_MUTED}")
    else:
        x = list(range(len(df)))
        width_bar = 0.36 if len(y_cols) > 1 else 0.55
        offset_base = -width_bar * (len(y_cols) - 1) / 2
        for i, (label, y_col, color) in enumerate(y_cols):
            y = pd.to_numeric(df[y_col], errors="coerce").fillna(0).tolist() if y_col in df.columns else [0] * len(x)
            ax.bar([v + offset_base + i * width_bar for v in x], y, width_bar, label=label, color=f"#{color}", edgecolor=f"#{COLOR_BG}")
        ax.set_xticks(x)
        ax.set_xticklabels(df[x_col].astype(str).tolist(), rotation=45, ha="right")
        ax.tick_params(axis="x", colors=f"#{COLOR_TEXT_MUTED}", labelsize=7)
        ax.tick_params(axis="y", colors=f"#{COLOR_TEXT_MUTED}", labelsize=7)
        ax.grid(True, axis="y", color=f"#{COLOR_GRID}", linewidth=0.5, alpha=0.7)
        ax.legend(loc="upper left", fontsize=7, frameon=False, labelcolor=f"#{COLOR_TEXT}")
    for spine in ax.spines.values():
        spine.set_color(f"#{COLOR_PRIMARY}")
    return _finish_chart(fig, path)

def insert_chart_image(ws: Any, cell: str, image_path: str):
    ws.insert_image(cell, image_path, {"x_offset": 4, "y_offset": 4})

CATEGORY_CONFIG_COLUMNS = [
    "Pattern",
    "Category",
    "Subcategory",
    "Category_Type",
    "Confidence",
    "Keywords",
    "Notes",
    "Recurring_Hint",
]

GENERIC_CATEGORY_RULES = [
    (r"salary|wage|payroll|income|mzda|vyplata", "Salary", "Main Work", "income", 0.90),
    (r"invoice|freelance|client payment", "Freelance / Work", "Client Work", "income", 0.80),
    (r"refund|cashback|reversal|return", "Refunds", "Refund", "income", 0.80),
    (r"interest|urok", "Interest", "Bank Interest", "income", 0.80),
    (r"grocery|supermarket|market|potraviny", "Food & Groceries", "Groceries", "food", 0.80),
    (r"restaurant|cafe|coffee|pizza|burger|food delivery", "Restaurants & Cafes", "Eating Out", "food", 0.78),
    (r"rent|utilities|electric|energy|gas|water|housing", "Housing", "Rent / Utilities", "housing", 0.80),
    (r"mobile|internet|telecom|phone", "Utilities", "Mobile / Internet", "utilities", 0.78),
    (r"transport|train|bus|taxi|ride|fuel|parking", "Transport", "Public Transport / Mobility", "transport", 0.78),
    (r"subscription|streaming|cloud|software", "Subscriptions", "Digital Subscription", "subscription", 0.78),
    (r"investment|broker|trading|etf|savings", "Investments", "Investments", "savings/investment", 0.78),
    (r"cash|atm|withdrawal", "Cash Withdrawal", "Cash Movement", "cash withdrawal", 0.78),
    (r"fee|bank fee|poplatok", "Bank Fees", "Bank Fee", "fee", 0.80),
    (r"tax|dan", "Taxes", "Taxes", "expense", 0.78),
    (r"insurance|poistenie", "Insurance", "Insurance", "expense", 0.78),
    (r"loan|debt|uver", "Debt / Loans", "Debt / Loan", "debt", 0.78),
]

GENERIC_DEFAULT_CATEGORIES = [
    ["Salary", "Main Work", "income", "salary; wage; payroll", "Work income"],
    ["Freelance / Work", "Client Work", "income", "invoice; freelance; client payment", "Other work income"],
    ["Refunds", "Refund", "income", "refund; cashback; reversal", "Refunds and corrections"],
    ["Interest", "Bank Interest", "income", "interest", "Interest income"],
    ["Other Income", "Other Income", "income", "", "Fallback income category"],
    ["Other Expense", "Other Expense", "expense", "", "Fallback expense category"],
    ["Food & Groceries", "Groceries", "food", "grocery; supermarket", "Food purchases"],
    ["Restaurants & Cafes", "Eating Out", "food", "restaurant; cafe; coffee", "Eating out"],
    ["Housing", "Rent / Utilities", "housing", "rent; utilities; energy", "Rent and housing costs"],
    ["Utilities", "Mobile / Internet", "utilities", "mobile; internet; telecom", "Utilities and phone"],
    ["Transport", "Public Transport / Mobility", "transport", "transport; train; bus; taxi", "Transport"],
    ["Subscriptions", "Digital Subscription", "subscription", "subscription; software; cloud", "Recurring digital services"],
    ["Shopping", "Shopping", "expense", "shop; shopping", "General shopping"],
    ["Health", "Health / Fitness", "health", "doctor; pharmacy; health", "Health spending"],
    ["Education", "Education", "education", "school; university; course", "Education spending"],
    ["Entertainment", "Entertainment", "entertainment", "game; cinema; event", "Entertainment"],
    ["Travel", "Travel", "expense", "hotel; flight; travel", "Travel"],
    ["Cash Withdrawal", "Cash Movement", "cash withdrawal", "cash; atm; withdrawal", "Cash movements"],
    ["Bank Fees", "Bank Fee", "fee", "fee; bank fee", "Bank fees"],
    ["Taxes", "Taxes", "expense", "tax", "Taxes"],
    ["Insurance", "Insurance", "expense", "insurance", "Insurance"],
    ["Debt / Loans", "Debt / Loan", "debt", "loan; debt", "Debt and loans"],
    ["Investments", "Investments", "savings/investment", "investment; broker; savings", "Investment contributions"],
    ["Internal Transfer", "Internal Transfer", "internal transfer", "own account; transfer", "Movement between own accounts"],
    ["Ignored", "Ignored", "ignored", "template; note", "Rows intentionally excluded"],
    ["Uncategorized", "Needs Review", "other", "", "Fallback category; review manually"],
]

CATEGORY_RULES = list(GENERIC_CATEGORY_RULES)
DEFAULT_CATEGORIES = list(GENERIC_DEFAULT_CATEGORIES)
RECURRING_HINT_CATEGORIES = {"Salary", "Freelance / Work", "Interest", "Subscriptions", "Bank Fees", "Utilities", "Housing", "Investments"}
RECURRING_HINT_PATTERNS = [pattern for pattern, category, *_ in CATEGORY_RULES if category in RECURRING_HINT_CATEGORIES]


MONTH_SHEET_NAMES = set(MONTHS_SK.keys())


def package_path(*parts: str) -> Path:
    return Path(__file__).resolve().parent.joinpath(*parts)


PROJECT_ROOT = Path(__file__).resolve().parent

DEFAULT_SETTINGS = {
    "paths": {
        "input": "input",
        "output": "output/Personal_Finance_Analysis.xlsx",
        "accounts": "config/accounts.csv",
        "categories": "config/categories.csv",
        "currency_rates": "config/currency_rates.csv",
        "cache": "cache/currency_rates_cache.csv",
        "report": "reports/validation_summary.md",
    },
    "fx": {
        "provider": "frankfurter",
        "mode": "historical",
        "no_download": False,
    },
}


def load_settings_file(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, []
    if yaml is None:
        return {}, [f"Settings file exists but PyYAML is not installed, so it was ignored: {path}"]
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return {}, [f"Settings file could not be read from {path}: {exc}"]
    if not isinstance(data, dict):
        return {}, [f"Settings file must contain a YAML mapping: {path}"]
    return data, []


def settings_get(settings: dict[str, Any], section: str, key: str, default: Any) -> Any:
    section_value = settings.get(section, {}) if isinstance(settings, dict) else {}
    if isinstance(section_value, dict) and key in section_value and section_value[key] not in (None, ""):
        return section_value[key]
    default_section = DEFAULT_SETTINGS.get(section, {})
    if isinstance(default_section, dict):
        return default_section.get(key, default)
    return default


def resolve_configured_path(value: Any, *, from_cli: bool = False) -> Path:
    raw = normalize_text(value)
    path = Path(raw) if raw else Path(".")
    if path.is_absolute():
        return path.resolve()
    base = Path.cwd() if from_cli else PROJECT_ROOT
    return (base / path).resolve()


def resolve_arg_path(args: argparse.Namespace, settings: dict[str, Any], attr: str, settings_key: str) -> Path:
    cli_value = getattr(args, attr, None)
    if cli_value not in (None, ""):
        return resolve_configured_path(cli_value, from_cli=True)
    return resolve_configured_path(settings_get(settings, "paths", settings_key, DEFAULT_SETTINGS["paths"][settings_key]))


def resolve_arg_value(args: argparse.Namespace, settings: dict[str, Any], attr: str, section: str, key: str, default: Any) -> Any:
    cli_value = getattr(args, attr, None)
    if cli_value not in (None, ""):
        return cli_value
    return settings_get(settings, section, key, default)


def category_rows_to_display(rows: list[dict[str, Any]]) -> list[list[Any]]:
    seen: set[tuple[str, str]] = set()
    display_rows: list[list[Any]] = []
    for row in rows:
        category = normalize_text(row.get("Category"))
        subcategory = normalize_text(row.get("Subcategory"))
        if not category:
            continue
        key = (category, subcategory)
        if key in seen:
            continue
        seen.add(key)
        display_rows.append([
            category,
            subcategory,
            normalize_text(row.get("Category_Type")) or "expense",
            normalize_text(row.get("Keywords")),
            normalize_text(row.get("Notes")),
        ])
    for fallback in GENERIC_DEFAULT_CATEGORIES:
        key = (fallback[0], fallback[1])
        if key not in seen:
            display_rows.append(fallback)
            seen.add(key)
    return display_rows


def set_category_rules(rows: list[dict[str, Any]]) -> None:
    global CATEGORY_RULES, DEFAULT_CATEGORIES, RECURRING_HINT_CATEGORIES, RECURRING_HINT_PATTERNS
    rules: list[tuple[str, str, str, str, float]] = []
    recurring_categories: set[str] = set()
    recurring_patterns: list[str] = []
    for row in rows:
        pattern = normalize_text(row.get("Pattern"))
        category = normalize_text(row.get("Category"))
        subcategory = normalize_text(row.get("Subcategory"))
        category_type = normalize_text(row.get("Category_Type")) or "expense"
        confidence = parse_amount(row.get("Confidence"))
        if not pattern or not category:
            continue
        confidence = 0.75 if confidence is None else float(confidence)
        rules.append((pattern, category, subcategory, category_type, confidence))
        if parse_bool(row.get("Recurring_Hint"), False):
            recurring_categories.add(category)
            recurring_patterns.append(pattern)
    if rules:
        CATEGORY_RULES = rules
        DEFAULT_CATEGORIES = category_rows_to_display(rows)
        RECURRING_HINT_CATEGORIES = recurring_categories
        RECURRING_HINT_PATTERNS = recurring_patterns


def load_categories_config(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], [
            f"Private category config not found: {path}. Copy config/categories.example.csv to config/categories.csv if you want custom categorization rules."
        ]
    raw, error = read_csv_config(path)
    if raw is None:
        return [], [f"Category config could not be read from {path}: {error}"]
    for col in CATEGORY_CONFIG_COLUMNS:
        if col not in raw.columns:
            raw[col] = ""
    rows = raw[CATEGORY_CONFIG_COLUMNS].fillna("").to_dict("records")
    return rows, []


def parse_year_from_filename(path: Path) -> int | None:
    m = re.search(r"(20\d{2})", path.name)
    if m:
        return int(m.group(1))
    return None


def parse_legacy_prototype(path: Path) -> list[dict[str, Any]]:
    """Parse the user's old manual workbook structure. These rows are not bank-native statements.

    Blocks used in the old files:
    - D:F recurring payments
    - H:J one-time payments
    - L:N expected payments
    - P:Q notes/write-offs without amount; these are preserved as validation notes but not emitted as transactions.
    """
    if load_workbook is None:
        return [{"Parser_Warning": "openpyxl is required to parse legacy prototype files", "Source_File": path.name, "Source_Bank": "Legacy Prototype"}]
    wb = load_workbook(path, data_only=True)
    rows: list[dict[str, Any]] = []
    file_year = parse_year_from_filename(path)
    for ws in wb.worksheets:
        sheet_key = ws.title.lower().strip()
        month = MONTHS_SK.get(sheet_key)
        if not month:
            continue
        year = file_year or 2024
        blocks = [
            (4, 5, 6, "Recurring payments", False),  # D/E/F 1-based
            (8, 9, 10, "One-time payments", False),   # H/I/J
            (12, 13, 14, "Expected payments", True),   # L/M/N
        ]
        for date_col, desc_col, amount_col, section, ignored in blocks:
            for ridx in range(2, ws.max_row + 1):
                desc = normalize_text(ws.cell(ridx, desc_col).value)
                amount = parse_amount(ws.cell(ridx, amount_col).value)
                if not desc and amount is None:
                    continue
                if amount is None:
                    continue
                raw_date = ws.cell(ridx, date_col).value
                booking_date = parse_date(raw_date, year, month)
                if pd.isna(booking_date):
                    booking_date = pd.Timestamp(year=year, month=month, day=1)
                out = normalized_blank_row()
                out.update({
                    "Source_File": path.name,
                    "Source_Bank": "Legacy Prototype",
                    "Source_Sheet": ws.title,
                    "Source_Row": ridx,
                    "Source_Account": "Legacy Manual Tracking",
                    "Account_Name": "Legacy Manual Tracking",
                    "Booking_Date": booking_date,
                    "Value_Date": booking_date,
                    "Counterparty_Name": desc,
                    "Description": desc,
                    "Reference": section,
                    "Original_Amount": amount,
                    "Original_Currency": "EUR",
                    "Amount_EUR": amount,
                    "Is_Ignored": bool(ignored),
                    "Parser_Warning": "Parsed from old manual prototype, not a bank-native export." + (" Expected-payment block; excluded from real totals." if ignored else ""),
                    "Notes": section,
                })
                out["Transaction_ID"] = stable_transaction_id([path.name, ws.title, ridx, section, booking_date, desc, amount])
                rows.append(out)
    return rows


def build_source_import_report(path: Path, bank: str, detected_format: str, parsed_rows: list[dict[str, Any]], parser_warning: str = "") -> dict[str, Any]:
    amounts = [parse_amount(r.get("Original_Amount")) for r in parsed_rows]
    amounts = [a for a in amounts if a is not None]
    dates = pd.to_datetime([r.get("Booking_Date") for r in parsed_rows], errors="coerce")
    valid_dates = [d for d in dates if not pd.isna(d)]
    currencies = Counter(normalize_text(r.get("Original_Currency")).upper() for r in parsed_rows if normalize_text(r.get("Original_Currency")))
    return {
        "Bank": bank,
        "File_Path": str(path),
        "Detected_Format": detected_format,
        "Source_Apparent_Transaction_Rows": len(parsed_rows),
        "Parsed_Rows": len(parsed_rows),
        "Skipped_Rows": 0,
        "Skipped_Reasons": "None" if parsed_rows else "",
        "Date_Range": f"{min(valid_dates).date()} to {max(valid_dates).date()}" if valid_dates else "",
        "Currencies": ", ".join(f"{ccy}: {count}" for ccy, count in sorted(currencies.items())),
        "Incoming_Amount": round(sum(a for a in amounts if a > 0), 2),
        "Outgoing_Amount": round(sum(abs(a) for a in amounts if a < 0), 2),
        "Parser_Warnings": parser_warning,
    }


def normalize_source_import_report(report: dict[str, Any]) -> dict[str, Any]:
    normalized = {col: "" for col in SOURCE_IMPORT_REPORT_COLUMNS}
    normalized.update(report)
    return normalized


def normalize_investment_import_report(report: dict[str, Any]) -> dict[str, Any]:
    normalized = {col: "" for col in INVESTMENT_IMPORT_REPORT_COLUMNS}
    normalized.update(report)
    return normalized


def discover_transactions(input_root: Path) -> tuple[pd.DataFrame, list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    source_reports: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    bank_dirs = {
        "revolut": ("Revolut", "Revolut tabular export", parse_revolut_file),
        "tatrabanka": ("Tatra banka", "Tatra banka tabular export", parse_tatrabanka_file),
        "tatra": ("Tatra banka", "Tatra banka tabular export", parse_tatrabanka_file),
        "slsp": ("Slovenská sporiteľňa", "SLSP tabular export", parse_slsp_file),
        "slovenska_sporitelna": ("Slovenská sporiteľňa", "SLSP tabular export", parse_slsp_file),
        "slovenská sporiteľňa": ("Slovenská sporiteľňa", "SLSP tabular export", parse_slsp_file),
        "legacy": ("Legacy Prototype", "Legacy manual prototype", parse_legacy_prototype),
    }
    if not input_root.exists():
        input_root.mkdir(parents=True, exist_ok=True)
        warnings.append(f"Input folder was created but contained no files: {input_root}")
    files_seen = 0
    clear_import_reports()
    for child in sorted(input_root.rglob("*")):
        if not child.is_file():
            continue
        if child.name.startswith("~$"):
            continue
        relative_parts = [p.lower() for p in child.relative_to(input_root).parts] if input_root in child.parents or child.parent == input_root else []
        if "investments" in relative_parts:
            continue
        if child.name.lower().startswith("currency_rates") or "currency_rates" in relative_parts:
            continue
        ext = child.suffix.lower()
        if ext not in {".csv", ".xlsx", ".xls", ".pdf"}:
            continue
        files_seen += 1
        parser = None
        bank_name = ""
        detected_format = ""
        parts = [p.name.lower() for p in child.parents if p != child.anchor]
        name_lower = child.name.lower()
        for key, (bank_label, format_label, func) in bank_dirs.items():
            if key in name_lower or any(key == part or key in part for part in parts):
                parser = func
                bank_name = bank_label
                detected_format = format_label
                break
        if parser is None:
            warnings.append(f"Skipped unsupported/unidentified file: {child}")
            source_reports.append(normalize_source_import_report(build_source_import_report(child, "Unknown", "Unsupported/unidentified", [], "Skipped unsupported/unidentified file.")))
            continue
        try:
            report_start = len(get_import_reports())
            parsed = parser(child)
            if not parsed:
                warnings.append(f"Parser produced 0 transaction rows for {child}. The file is preserved in input; review its export layout before adding rows.")
            parser_reports = get_import_reports()[report_start:]
            if parser_reports:
                source_reports.extend(normalize_source_import_report(r) for r in parser_reports)
            else:
                source_reports.append(normalize_source_import_report(build_source_import_report(child, bank_name, detected_format, parsed)))
            all_rows.extend(parsed)
        except Exception as exc:
            warnings.append(f"Parser failed for {child}: {exc}")
            source_reports.append(normalize_source_import_report(build_source_import_report(child, bank_name, detected_format or "Parser failed", [], f"Parser failed: {exc}")))
    if files_seen == 0:
        warnings.append("No supported input files found. Place exports into input/revolut, input/tatrabanka, input/slsp, or input/legacy.")
    df = pd.DataFrame(all_rows)
    for col in NORMALIZED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    if df.empty:
        return pd.DataFrame(columns=NORMALIZED_COLUMNS), warnings, source_reports
    df = df[NORMALIZED_COLUMNS]
    return df, warnings, source_reports


def discover_investment_snapshots(input_root: Path) -> tuple[pd.DataFrame, list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    source_reports: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    investment_root = input_root / "investments"
    if not investment_root.exists():
        return pd.DataFrame(columns=INVESTMENT_SNAPSHOT_COLUMNS), warnings, source_reports

    parser_map = {
        "slsp": ("Slovenská sporiteľňa", "SLSP investment/savings valuation snapshots", parse_slsp_investment_snapshot_file),
        "slovenska_sporitelna": ("Slovenská sporiteľňa", "SLSP investment/savings valuation snapshots", parse_slsp_investment_snapshot_file),
        "slovenská sporiteľňa": ("Slovenská sporiteľňa", "SLSP investment/savings valuation snapshots", parse_slsp_investment_snapshot_file),
    }
    clear_investment_import_reports()
    files_seen = 0
    for child in sorted(investment_root.rglob("*")):
        if not child.is_file():
            continue
        if child.name.startswith("~$"):
            continue
        ext = child.suffix.lower()
        if ext not in {".csv", ".xlsx", ".xls", ".pdf"}:
            continue
        files_seen += 1
        parser = None
        parts = [p.name.lower() for p in child.parents if p != child.anchor]
        name_lower = child.name.lower()
        for key, (_, _, func) in parser_map.items():
            if key in name_lower or any(key == part or key in part for part in parts):
                parser = func
                break
        if parser is None:
            warning = f"Skipped unsupported/unidentified investment snapshot file: {child}"
            warnings.append(warning)
            source_reports.append(normalize_investment_import_report({
                "Bank": "Unknown",
                "File_Path": str(child),
                "Detected_Format": "Unsupported/unidentified investment snapshot",
                "Source_Apparent_Snapshot_Rows": 0,
                "Parsed_Rows": 0,
                "Skipped_Rows": 0,
                "Skipped_Reasons": "Skipped unsupported/unidentified file.",
                "Parser_Warnings": warning,
            }))
            continue
        try:
            report_start = len(get_investment_import_reports())
            parsed = parser(child)
            if not parsed:
                warnings.append(f"Investment parser produced 0 snapshot rows for {child}.")
            parser_reports = get_investment_import_reports()[report_start:]
            if parser_reports:
                source_reports.extend(normalize_investment_import_report(r) for r in parser_reports)
            all_rows.extend(parsed)
        except Exception as exc:
            warning = f"Investment parser failed for {child}: {exc}"
            warnings.append(warning)
            source_reports.append(normalize_investment_import_report({
                "Bank": "Unknown",
                "File_Path": str(child),
                "Detected_Format": "Parser failed",
                "Source_Apparent_Snapshot_Rows": 0,
                "Parsed_Rows": 0,
                "Skipped_Rows": 0,
                "Skipped_Reasons": "",
                "Parser_Warnings": warning,
            }))
    if files_seen == 0:
        return pd.DataFrame(columns=INVESTMENT_SNAPSHOT_COLUMNS), warnings, source_reports
    df = pd.DataFrame(all_rows)
    for col in INVESTMENT_SNAPSHOT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    if df.empty:
        return pd.DataFrame(columns=INVESTMENT_SNAPSHOT_COLUMNS), warnings, source_reports
    return df[INVESTMENT_SNAPSHOT_COLUMNS], warnings, source_reports


def transaction_text(row: pd.Series | dict[str, Any]) -> str:
    return " ".join(
        normalize_text(row.get(col))
        for col in ["Counterparty_Name", "Description", "Reference", "Notes", "Counterparty_Account"]
    ).strip()


def transaction_text_lower(row: pd.Series | dict[str, Any]) -> str:
    return transaction_text(row).lower()


def stable_group_id(prefix: str, parts: list[Any]) -> str:
    return f"{prefix}_{stable_transaction_id(parts)[:10].upper()}"


SAVINGS_INVESTMENT_HINT_RE = re.compile(
    r"revolut vault|savings vault|vault topup|pocket|instant access savings|flexible cash funds|"
    r"investment account|margin trading|digital assets|broker|brokerage|trading|crypto|bitcoin|"
    r"kraken|blockchain|etf|sporenie|finančné nástroje|financne nastroje",
    re.I,
)


def has_savings_investment_hint(row: pd.Series | dict[str, Any]) -> bool:
    return bool(SAVINGS_INVESTMENT_HINT_RE.search(transaction_text_lower(row)))


def has_currency_exchange_hint(row: pd.Series | dict[str, Any]) -> bool:
    text = transaction_text_lower(row)
    return bool(re.search(r"\bexchanged to\b|\bcurrency exchange\b|zmenáreň|zmenaren", text, re.I))


def has_direct_own_account(row: pd.Series | dict[str, Any]) -> bool:
    return is_configured_own_iban(row.get("Counterparty_Account"))


def has_internal_transfer_hint(row: pd.Series | dict[str, Any]) -> bool:
    text = transaction_text_lower(row)
    source_bank = normalize_text(row.get("Source_Bank")).lower()
    if has_direct_own_account(row):
        return True
    if has_savings_investment_hint(row):
        return False
    if has_currency_exchange_hint(row):
        return True
    own_phrase = re.search(r"own account|to myself|from myself|between accounts|internal transfer|preúčt|preuct|vlastn", text, re.I)
    if own_phrase:
        return True
    if re.search(r"\btop[- ]?up\b|google pay top[- ]?up|card top[- ]?up|payment from myself|to myself", text, re.I):
        return True
    if has_configured_transfer_hint(text):
        return True
    # Card top-ups to Revolut from another configured bank appear as card merchants,
    # not as SEPA transfers, so they need a text hint plus opposite-amount matching.
    if source_bank != "revolut" and re.search(r"revolut\*\*|revolut", text, re.I):
        return True
    return False


def is_ambiguous_transfer_candidate(row: pd.Series | dict[str, Any]) -> bool:
    text = transaction_text_lower(row)
    if has_internal_transfer_hint(row) or has_savings_investment_hint(row):
        return False
    return bool(re.search(r"\btransfer (to|from)\b|odoslaná platba|odoslana platba|prijatá platba|prijata platba", text, re.I))


GENERIC_DUPLICATE_TEXT_RE = re.compile(
    r"^(gp |eur |ve |int |dom )?(nákup|nakup|pos|platba kartou|platba|vklad|výber|vyber|ccint|de\d+|tpp).*$",
    re.I,
)


def normalized_duplicate_text(row: pd.Series | dict[str, Any]) -> str:
    text = " ".join([
        normalize_text(row.get("Counterparty_Name")),
        normalize_text(row.get("Description")),
        normalize_text(row.get("Reference")),
        normalize_text(row.get("Counterparty_Account")),
    ]).lower()
    text = re.sub(r"\d{4,}", "#", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def duplicate_text_is_specific(row: pd.Series | dict[str, Any]) -> bool:
    cp = normalize_text(row.get("Counterparty_Name"))
    reference = normalize_text(row.get("Reference"))
    cp_account = normalize_text(row.get("Counterparty_Account"))
    desc = normalize_text(row.get("Description"))
    if reference or cp_account:
        return True
    if cp and not GENERIC_DUPLICATE_TEXT_RE.match(cp.lower()):
        return True
    if desc and not GENERIC_DUPLICATE_TEXT_RE.match(desc.lower()):
        return True
    return False


def normalized_recurring_key(row: pd.Series | dict[str, Any]) -> str:
    base = normalize_text(row.get("Counterparty_Name")) or normalize_text(row.get("Description"))
    key = base.lower()
    key = re.sub(r"\*+\d+|\d{2,}|[^\wáäčďéíĺľňóôŕšťúýž]+", " ", key, flags=re.I)
    key = re.sub(r"\b(payment|transfer|from|to|platba|nákup|nakup|pos|eur|gp|ve|int)\b", " ", key, flags=re.I)
    key = re.sub(r"\s+", " ", key).strip()
    return key[:70]


def group_amount_consistency(amounts: pd.Series) -> float:
    vals = amounts.dropna().astype(float).abs()
    if vals.empty:
        return 0.0
    median = float(vals.median())
    if median == 0:
        return 0.0
    tolerance = max(2.0, median * 0.20)
    return float(((vals - median).abs() <= tolerance).mean())


def group_monthly_cadence(dates: pd.Series) -> tuple[int, float, bool]:
    d = pd.to_datetime(dates, errors="coerce").dropna().sort_values()
    if d.empty:
        return 0, 0.0, False
    months = sorted(set(zip(d.dt.year.astype(int), d.dt.month.astype(int))))
    if len(d) < 2:
        return len(months), 0.0, False
    gaps = d.diff().dt.days.dropna()
    median_gap = float(gaps.median()) if not gaps.empty else 0.0
    monthly_like = 20 <= median_gap <= 45
    return len(months), median_gap, monthly_like


def categorize_transaction(row: pd.Series) -> tuple[str, str, str, float, bool, str]:
    amount = parse_amount(row.get("Amount_EUR")) or parse_amount(row.get("Original_Amount")) or 0.0
    text = transaction_text_lower(row)
    if bool(row.get("Is_Internal_Transfer")):
        return "Internal Transfer", "Internal Transfer", "internal transfer", 1.0, False, ""
    if bool(row.get("Is_Ignored")):
        return "Ignored", "Ignored", "ignored", 1.0, False, ""
    for pattern, category, subcategory, category_type, confidence in CATEGORY_RULES:
        if re.search(pattern, text, flags=re.IGNORECASE):
            is_savings = category_type == "savings/investment"
            si_type = subcategory if is_savings else ""
            if amount > 0 and category_type not in {"income", "cash withdrawal"}:
                # A positive amount from a merchant-like rule is more likely a refund or correction.
                if category_type in {"food", "expense", "transport", "housing", "subscription", "utilities"}:
                    return "Refunds", f"Refund / {category}", "income", min(confidence, 0.65), False, ""
            return category, subcategory, category_type, confidence, is_savings, si_type
    if amount > 0:
        return "Other Income", "Other Income", "income", 0.55, False, ""
    if amount < 0:
        return "Uncategorized", "Needs Review", "other", 0.25, False, ""
    return "Ignored", "Zero Amount", "ignored", 0.5, False, ""


def postprocess_transactions(df: pd.DataFrame, rates_df: pd.DataFrame | None = None, fx_mode: str = "historical") -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    warnings: list[str] = []
    if df.empty:
        return df, pd.DataFrame(), warnings
    df = df.copy()
    df["Booking_Date"] = pd.to_datetime(df["Booking_Date"], errors="coerce")
    df["Value_Date"] = pd.to_datetime(df["Value_Date"], errors="coerce")
    df["Original_Amount"] = df["Original_Amount"].apply(parse_amount)
    df["Amount_EUR"] = df["Amount_EUR"].apply(parse_amount)
    if rates_df is None:
        rates_df = pd.DataFrame(columns=CURRENCY_RATE_COLUMNS)
    df, fx_warnings = apply_currency_conversion(df, rates_df, fx_mode=fx_mode)
    warnings.extend(fx_warnings)
    df["Amount_EUR"] = df["Amount_EUR"].apply(parse_amount)
    df["Year"] = df["Booking_Date"].dt.year
    df["Month_Number"] = df["Booking_Date"].dt.month
    df["Month_Name"] = df["Month_Number"].map(MONTH_NAMES)
    df["Direction"] = df["Amount_EUR"].apply(lambda x: "Income" if pd.notna(x) and x > 0 else ("Expense" if pd.notna(x) and x < 0 else "Zero/Unknown"))
    df["Income_Amount"] = df["Amount_EUR"].apply(lambda x: float(x) if pd.notna(x) and x > 0 else 0.0)
    df["Expense_Amount"] = df["Amount_EUR"].apply(lambda x: abs(float(x)) if pd.notna(x) and x < 0 else 0.0)

    # Prefill source account IBANs from the user-provided own-account list where the bank is known.
    if "Account_IBAN_or_Number" not in df.columns:
        df["Account_IBAN_or_Number"] = ""
    df["Account_IBAN_or_Number"] = df.apply(
        lambda r: default_own_iban_for_bank(r.get("Source_Bank"), r.get("Account_Name")) or normalize_text(r.get("Account_IBAN_or_Number")),
        axis=1,
    )

    # Internal transfer detection by configured own IBANs, own-account hints,
    # Revolut top-up/card pairs, currency exchanges, and opposite amounts.
    df["Is_Internal_Transfer"] = df["Is_Internal_Transfer"].fillna(False).astype(bool)
    df["Transfer_Group_ID"] = df["Transfer_Group_ID"].fillna("")
    df["_Savings_Hint"] = df.apply(has_savings_investment_hint, axis=1)
    df["_Internal_Hint"] = df.apply(has_internal_transfer_hint, axis=1)
    df["_Currency_Exchange_Hint"] = df.apply(has_currency_exchange_hint, axis=1)
    df["_Ambiguous_Transfer"] = df.apply(is_ambiguous_transfer_candidate, axis=1)
    amount_round = pd.to_numeric(df["Amount_EUR"], errors="coerce").round(2)

    pair_candidates = df[
        df["_Internal_Hint"]
        & (~df["_Savings_Hint"])
        & amount_round.notna()
        & (amount_round != 0)
        & df["Booking_Date"].notna()
    ].copy()
    pair_candidates["_Amount_Round"] = amount_round.loc[pair_candidates.index]
    used: set[int] = set()
    for i, a in pair_candidates.sort_values(["Booking_Date", "_Amount_Round", "Transaction_ID"]).iterrows():
        if i in used:
            continue
        opposite = pair_candidates[
            (~pair_candidates.index.isin(used))
            & (pair_candidates.index != i)
            & (pair_candidates["_Amount_Round"] == round(-float(a["_Amount_Round"]), 2))
            & ((pair_candidates["Booking_Date"] - a["Booking_Date"]).abs().dt.days <= 3)
            & (
                (pair_candidates["Account_Name"].astype(str) != str(a.get("Account_Name")))
                | (pair_candidates["Source_Bank"].astype(str) != str(a.get("Source_Bank")))
            )
        ].copy()
        if opposite.empty:
            continue
        opposite["_Date_Diff"] = (opposite["Booking_Date"] - a["Booking_Date"]).abs().dt.days
        opposite["_Different_Bank"] = (opposite["Source_Bank"].astype(str) != str(a.get("Source_Bank"))).astype(int)
        opposite = opposite.sort_values(["_Date_Diff", "_Different_Bank", "Transaction_ID"], ascending=[True, False, True])
        j = int(opposite.index[0])
        gid = stable_group_id("TR_PAIR", sorted([df.at[i, "Transaction_ID"], df.at[j, "Transaction_ID"]]))
        df.loc[[i, j], "Is_Internal_Transfer"] = True
        df.loc[[i, j], "Transfer_Group_ID"] = gid
        for idx in [i, j]:
            df.at[idx, "Notes"] = append_note(df.at[idx, "Notes"], "Internal transfer pair: opposite amount on same/nearby date with own-account hint.")
        used.update({i, j})

    direct_mask = (
        (~df["Is_Internal_Transfer"])
        & df["_Internal_Hint"]
        & (~df["_Savings_Hint"])
        & amount_round.notna()
        & (amount_round != 0)
    )
    for idx, row in df[direct_mask].iterrows():
        prefix = "TR_EXCHANGE" if bool(row.get("_Currency_Exchange_Hint")) else "TR_OWN"
        df.at[idx, "Is_Internal_Transfer"] = True
        df.at[idx, "Transfer_Group_ID"] = stable_group_id(prefix, [row.get("Transaction_ID"), row.get("Booking_Date"), row.get("Amount_EUR")])
        if has_direct_own_account(row):
            reason = "Counterparty/source account matches one of the configured own IBANs."
        elif bool(row.get("_Currency_Exchange_Hint")):
            reason = "Currency exchange within own Revolut balances."
        else:
            reason = "Own-account transfer hint without a matching opposite statement row."
        df.at[idx, "Notes"] = append_note(row.get("Notes"), reason)

    ambiguous_transfer_mask = df["_Ambiguous_Transfer"] & (~df["Is_Internal_Transfer"])
    if ambiguous_transfer_mask.any():
        count = int(ambiguous_transfer_mask.sum())
        warnings.append(
            f"{count} transfer-like rows were left unclassified as internal transfers because own-account evidence was insufficient. "
            f"Examples: {format_review_examples(df, ambiguous_transfer_mask)}"
        )
        df.loc[ambiguous_transfer_mask, "Notes"] = df.loc[ambiguous_transfer_mask, "Notes"].apply(
            lambda x: append_note(x, "Transfer-like row left for manual review; no configured own-account or opposite-amount proof.")
        )

    # Category pass
    cat_results = df.apply(categorize_transaction, axis=1)
    df["Category"] = [x[0] for x in cat_results]
    df["Subcategory"] = [x[1] for x in cat_results]
    df["Category_Type"] = [x[2] for x in cat_results]
    df["Category_Confidence"] = [x[3] for x in cat_results]
    df["Is_Savings_Investment"] = [x[4] for x in cat_results]
    df["Savings_Investment_Type"] = [x[5] for x in cat_results]

    # Exclude ignored/internal rows from effective income/expense for summaries via helper fields used in formulas.
    df["Is_Ignored"] = df["Is_Ignored"].fillna(False).astype(bool)

    # Duplicate suspects: only strong evidence, with a reason kept in the raw sheet.
    df["Is_Duplicate_Suspect"] = False
    df["Duplicate_Reason"] = ""
    df["_Duplicate_Text"] = df.apply(normalized_duplicate_text, axis=1)
    df["_Duplicate_Specific"] = df.apply(duplicate_text_is_specific, axis=1)
    df["_Amount_Round"] = amount_round
    df["_Booking_Day"] = df["Booking_Date"].dt.date.astype(str)
    duplicate_signature = df.apply(
        lambda r: stable_transaction_id([
            r.get("_Booking_Day"),
            r.get("_Amount_Round"),
            normalize_text(r.get("Original_Currency")).upper(),
            normalize_text(r.get("Source_Bank")).lower(),
            normalize_text(r.get("Account_Name")).lower(),
            r.get("_Duplicate_Text"),
        ]),
        axis=1,
    )
    df["_Duplicate_Signature"] = duplicate_signature
    for _, g in df[df["_Amount_Round"].notna() & df["_Duplicate_Specific"]].groupby("_Duplicate_Signature"):
        if len(g) < 2:
            continue
        if g["Is_Internal_Transfer"].all():
            continue
        reason = ""
        non_empty_refs = g["Reference"].apply(normalize_text).replace("", pd.NA).dropna()
        balances = pd.to_numeric(g["Balance_After"], errors="coerce").dropna()
        if g["Source_File"].nunique() > 1:
            reason = "Same transaction signature appears in multiple source files; possible overlapping statement exports."
        elif len(non_empty_refs) >= 2 and non_empty_refs.nunique() == 1:
            reason = "Repeated non-empty bank reference with same date, amount, source bank, and counterparty text."
        elif len(balances) >= 2 and balances.nunique() == 1:
            reason = "Same date, amount, counterparty text, and post-transaction balance."
        if reason:
            df.loc[g.index, "Is_Duplicate_Suspect"] = True
            df.loc[g.index, "Duplicate_Reason"] = reason

    # Recurring detection. This intentionally ignores duplicate suspects and casual
    # repeated merchants such as daily food, vending, shopping, games, and transport.
    df["Is_Recurring"] = False
    df["Recurring_Group_ID"] = ""
    active = df[
        (~df["Is_Ignored"])
        & (~df["Is_Internal_Transfer"])
        & (~df["Is_Duplicate_Suspect"])
        & df["Amount_EUR"].notna()
    ].copy()
    active["Recurring_Key"] = active.apply(normalized_recurring_key, axis=1)
    recurring_rows: list[dict[str, Any]] = []
    low_confidence_recurring_candidates = 0
    low_confidence_recurring_examples: list[str] = []
    rgid = 1
    active["_Direction_Sign"] = active["Amount_EUR"].apply(lambda x: 1 if float(x) > 0 else (-1 if float(x) < 0 else 0)) if not active.empty else []
    for (key, sign, category), g in active.groupby(["Recurring_Key", "_Direction_Sign", "Category"], dropna=False):
        if not key or sign == 0:
            continue
        amounts = g["Amount_EUR"].dropna().astype(float)
        month_count, median_gap, monthly_like = group_monthly_cadence(g["Booking_Date"])
        if len(g) < 3 or month_count < 2:
            continue
        category_type = g["Category_Type"].mode().iat[0] if not g["Category_Type"].mode().empty else ""
        category_name = normalize_text(category)
        strong_named = any(re.search(pattern, str(key), re.I) for pattern in RECURRING_HINT_PATTERNS)
        named = strong_named or category_name in RECURRING_HINT_CATEGORIES
        casual_type = category_type in {"food", "transport", "entertainment", "expense", "health", "education", "other"}
        consistency = group_amount_consistency(amounts)
        detected = False
        if category_type == "subscription":
            detected = (strong_named and (monthly_like or consistency >= 0.60 or month_count >= 3)) or (monthly_like and consistency >= 0.75 and month_count >= 3)
        elif category_type in {"utilities", "housing", "fee"}:
            detected = (strong_named and (monthly_like or consistency >= 0.50)) or (monthly_like and consistency >= 0.75 and month_count >= 3)
        elif category_type == "income":
            recurring_income = category_name in {"Salary", "Freelance / Work", "Interest"} or bool(re.search(r"payroll|salary|mzda|wage", key, re.I))
            support_income = category_name == "Family"
            detected = (
                recurring_income and (monthly_like or consistency >= 0.60 or month_count >= 3)
            ) or (
                support_income and monthly_like and consistency >= 0.80 and month_count >= 3
            )
        elif category_type == "savings/investment":
            detected = month_count >= 2 and len(g) >= 3
        elif named and not casual_type:
            detected = monthly_like and consistency >= 0.75
        elif not casual_type and monthly_like and consistency >= 0.80 and month_count >= 3:
            detected = True
        if not detected:
            if named or (monthly_like and consistency >= 0.60):
                low_confidence_recurring_candidates += 1
                if len(low_confidence_recurring_examples) < 5:
                    low_confidence_recurring_examples.append(
                        f"{key.title()} / {category_name or 'Uncategorized'} "
                        f"({len(g)} rows, median gap {median_gap:.0f} days, amount consistency {consistency:.0%})"
                    )
            continue
        gid = f"RG_{rgid:04d}"
        df.loc[g.index, "Is_Recurring"] = True
        df.loc[g.index, "Recurring_Group_ID"] = gid
        confidence = min(0.95, 0.65 + (0.15 if monthly_like else 0) + (0.15 * consistency) + (0.05 if named else 0))
        usual_amount = float(amounts.abs().median()) if not amounts.empty else 0.0
        recurring_rows.append({
            "Recurring_Group_ID": gid,
            "Counterparty_or_Description": key.title(),
            "Category": category_name,
            "Category_Type": category_type,
            "Account": g["Account_Name"].mode().iat[0] if not g["Account_Name"].mode().empty else "",
            "Expected_Frequency": "Monthly" if monthly_like else "Repeated",
            "Usual_Amount_EUR": usual_amount,
            "Occurrences": int(len(g)),
            "First_Date": g["Booking_Date"].min(),
            "Last_Date": g["Booking_Date"].max(),
            "Confidence": round(float(confidence), 2),
            "Manually_Editable_Notes": f"Detected automatically; median gap {median_gap:.0f} days; amount consistency {consistency:.0%}.",
        })
        rgid += 1
    recurring_df = pd.DataFrame(recurring_rows)
    if low_confidence_recurring_candidates:
        example_text = "; ".join(low_confidence_recurring_examples) if low_confidence_recurring_examples else "None"
        warnings.append(
            f"{low_confidence_recurring_candidates} recurring-like groups were left unflagged because cadence/category evidence was weak. "
            f"Examples: {example_text}"
        )

    # Recalculate IDs if blank
    blank_ids = df["Transaction_ID"].isna() | (df["Transaction_ID"].astype(str).str.strip() == "")
    df.loc[blank_ids, "Transaction_ID"] = df[blank_ids].apply(lambda r: stable_transaction_id([r.get("Source_File"), r.get("Source_Sheet"), r.get("Source_Row"), r.get("Booking_Date"), r.get("Amount_EUR"), r.get("Description"), r.get("Counterparty_Name")]), axis=1)

    # Parser warning augmentation
    df.loc[df["Booking_Date"].isna(), "Parser_Warning"] = df["Parser_Warning"].astype(str) + " Missing/invalid booking date."
    if df["Amount_EUR"].isna().any():
        warnings.append("Some rows have no reliable EUR amount. Currency conversion was not invented.")
    if not df["Is_Savings_Investment"].any():
        warnings.append("No savings/investment transactions were detected in the parsed source rows.")

    # Final order and types
    df = df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")
    for col in NORMALIZED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[NORMALIZED_COLUMNS], recurring_df, warnings


def investment_fx_request_frame(investment_df: pd.DataFrame) -> pd.DataFrame:
    if investment_df is None or investment_df.empty:
        return pd.DataFrame(columns=["Booking_Date", "Original_Currency", "Original_Amount"])
    return pd.DataFrame({
        "Booking_Date": pd.to_datetime(investment_df.get("Snapshot_Date"), errors="coerce"),
        "Original_Currency": investment_df.get("Original_Currency", "").apply(lambda x: normalize_currency_code(x, "EUR")),
        "Original_Amount": investment_df.get("Market_Value_Original", "").apply(parse_amount),
    })


def combined_fx_request_frame(transactions_df: pd.DataFrame, investment_df: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    if transactions_df is not None and not transactions_df.empty:
        tx = transactions_df.copy()
        for col in ["Booking_Date", "Original_Currency", "Original_Amount"]:
            if col not in tx.columns:
                tx[col] = ""
        frames.append(tx[["Booking_Date", "Original_Currency", "Original_Amount"]])
    inv = investment_fx_request_frame(investment_df)
    if not inv.empty:
        frames.append(inv)
    if not frames:
        return pd.DataFrame(columns=["Booking_Date", "Original_Currency", "Original_Amount"])
    return pd.concat(frames, ignore_index=True)


def postprocess_investment_snapshots(investment_df: pd.DataFrame, rates_df: pd.DataFrame | None = None, fx_mode: str = "historical") -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    if investment_df is None or investment_df.empty:
        return pd.DataFrame(columns=INVESTMENT_SNAPSHOT_COLUMNS), warnings
    df = investment_df.copy()
    for col in INVESTMENT_SNAPSHOT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    if rates_df is None:
        rates_df = pd.DataFrame(columns=CURRENCY_RATE_COLUMNS)
    df["Snapshot_Date"] = pd.to_datetime(df["Snapshot_Date"], errors="coerce")
    df["Market_Value_Original"] = df["Market_Value_Original"].apply(parse_amount)
    df["Market_Value_EUR"] = df["Market_Value_EUR"].apply(parse_amount)
    df["Quantity"] = df["Quantity"].apply(parse_amount)
    df["Unit_Price"] = df["Unit_Price"].apply(parse_amount)
    df["FX_Rate_To_EUR"] = pd.to_numeric(df["FX_Rate_To_EUR"], errors="coerce")
    df["Original_Currency"] = df["Original_Currency"].apply(lambda x: normalize_currency_code(x, "EUR"))

    converted_count = 0
    missing_count = 0
    latest_count = 0
    for idx, row in df.iterrows():
        currency = normalize_currency_code(row.get("Original_Currency"), "EUR")
        market_value = parse_amount(row.get("Market_Value_Original"))
        if market_value is None:
            df.at[idx, "FX_Conversion_Status"] = "No market value"
            continue
        if currency == "EUR":
            df.at[idx, "Market_Value_EUR"] = market_value
            df.at[idx, "FX_Rate_To_EUR"] = 1.0
            df.at[idx, "FX_Rate_Date"] = ""
            df.at[idx, "FX_Rate_Source"] = "Base"
            df.at[idx, "FX_Conversion_Status"] = "Native EUR"
            continue
        rate, rate_date, source = get_rate_for_transaction(currency, row.get("Snapshot_Date"), rates_df, fx_mode=fx_mode)
        if rate is None:
            df.at[idx, "Market_Value_EUR"] = pd.NA
            df.at[idx, "FX_Conversion_Status"] = f"Missing FX rate for {currency}->EUR"
            existing_warning = normalize_text(row.get("Parser_Warning"))
            df.at[idx, "Parser_Warning"] = (existing_warning + " " if existing_warning else "") + f"Missing FX rate for {currency}->EUR."
            missing_count += 1
            continue
        df.at[idx, "Market_Value_EUR"] = market_value * rate
        df.at[idx, "FX_Rate_To_EUR"] = rate
        df.at[idx, "FX_Rate_Date"] = rate_date_to_string(rate_date)
        df.at[idx, "FX_Rate_Source"] = source or "Currency_Rates"
        if fx_mode == "latest":
            df.at[idx, "FX_Conversion_Status"] = "Latest rate used - not historical"
            latest_count += 1
        else:
            df.at[idx, "FX_Conversion_Status"] = "Converted using historical FX rate"
            converted_count += 1

    blank_ids = df["Snapshot_ID"].isna() | (df["Snapshot_ID"].astype(str).str.strip() == "")
    df.loc[blank_ids, "Snapshot_ID"] = df[blank_ids].apply(lambda r: "INV_" + stable_transaction_id([
        r.get("Source_File"),
        r.get("Source_Sheet"),
        r.get("Source_Row"),
        r.get("Snapshot_Date"),
        r.get("Account_Name"),
        r.get("Product_Name"),
        r.get("ISIN_or_Product_ID"),
        r.get("Market_Value_Original"),
        r.get("Original_Currency"),
    ]).upper(), axis=1)
    if converted_count:
        warnings.append(f"Converted {converted_count} non-EUR investment snapshot rows using historical FX rates.")
    if latest_count:
        warnings.append(f"Converted {latest_count} non-EUR investment snapshot rows using latest FX rates because --fx-mode latest was selected.")
    if missing_count:
        warnings.append(f"{missing_count} non-EUR investment snapshot rows could not be converted because no FX rate was available.")
    df = df.sort_values(["Snapshot_Date", "Product_Name", "Snapshot_ID"], na_position="last").reset_index(drop=True)
    return df[INVESTMENT_SNAPSHOT_COLUMNS], warnings


def effective_flags(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df.copy()
    tmp["Effective_Income"] = tmp.apply(lambda r: r["Income_Amount"] if (not r["Is_Internal_Transfer"] and not r["Is_Ignored"] and r["Category_Type"] != "savings/investment") else 0.0, axis=1)
    tmp["Effective_Expense"] = tmp.apply(lambda r: r["Expense_Amount"] if (not r["Is_Internal_Transfer"] and not r["Is_Ignored"] and r["Category_Type"] not in {"savings/investment", "income"}) else 0.0, axis=1)
    tmp["Savings_Investment_Amount"] = tmp.apply(lambda r: abs(r["Amount_EUR"]) if (not r["Is_Internal_Transfer"] and not r["Is_Ignored"] and r["Category_Type"] == "savings/investment" and pd.notna(r["Amount_EUR"])) else 0.0, axis=1)
    tmp["Internal_Transfer_Amount"] = tmp.apply(lambda r: abs(r["Amount_EUR"]) if (r["Is_Internal_Transfer"] and pd.notna(r["Amount_EUR"])) else 0.0, axis=1)
    tmp["Recurring_Income"] = tmp.apply(lambda r: r["Income_Amount"] if (r["Is_Recurring"] and not r["Is_Internal_Transfer"] and not r["Is_Ignored"] and r["Category_Type"] == "income") else 0.0, axis=1)
    tmp["Recurring_Expense"] = tmp.apply(lambda r: r["Expense_Amount"] if (r["Is_Recurring"] and not r["Is_Internal_Transfer"] and not r["Is_Ignored"] and r["Category_Type"] not in {"income", "savings/investment"}) else 0.0, axis=1)
    tmp["One_Time_Expense"] = tmp.apply(lambda r: r["Effective_Expense"] if (not r["Is_Recurring"]) else 0.0, axis=1)
    return tmp


def format_amount_range_for_review(values: pd.Series) -> str:
    nums = pd.to_numeric(values, errors="coerce").dropna()
    if nums.empty:
        return "amount unavailable"
    low = float(nums.min())
    high = float(nums.max())
    if abs(low - high) < 0.005:
        return f"{low:,.2f} EUR"
    return f"{low:,.2f} to {high:,.2f} EUR"


def review_text_key(row: pd.Series | dict[str, Any]) -> str:
    for col in ("Counterparty_Name", "Description", "Reference"):
        text = normalize_text(row.get(col))
        if text:
            return re.sub(r"\s+", " ", text)[:80]
    return "(blank text)"


def format_review_examples(df: pd.DataFrame, mask: pd.Series, limit: int = 5) -> str:
    if df.empty or not mask.any():
        return "None"
    review_df = df[mask].copy()
    review_df["_Review_Text_Key"] = review_df.apply(review_text_key, axis=1)
    grouped = (
        review_df.groupby(["Source_Bank", "_Review_Text_Key"], dropna=False)
        .agg(
            Rows=("Transaction_ID", "count"),
            Amount_Range=("Amount_EUR", format_amount_range_for_review),
            First_Date=("Booking_Date", "min"),
            Last_Date=("Booking_Date", "max"),
        )
        .reset_index()
        .sort_values(["Rows", "_Review_Text_Key"], ascending=[False, True])
    )
    examples: list[str] = []
    for _, r in grouped.head(limit).iterrows():
        first = pd.to_datetime(r["First_Date"], errors="coerce")
        last = pd.to_datetime(r["Last_Date"], errors="coerce")
        if pd.notna(first) and pd.notna(last):
            date_range = f"{first.date()} to {last.date()}" if first.date() != last.date() else str(first.date())
        else:
            date_range = "date unavailable"
        examples.append(f"{r['Source_Bank']} / {r['_Review_Text_Key']} ({int(r['Rows'])} rows, {r['Amount_Range']}, {date_range})")
    return "; ".join(examples)


def build_validation(
    df: pd.DataFrame,
    parser_warnings: list[str],
    input_root: Path,
    rates_df: pd.DataFrame | None = None,
    fx_report: dict[str, Any] | None = None,
    source_reports: list[dict[str, Any]] | None = None,
    investment_df: pd.DataFrame | None = None,
    investment_reports: list[dict[str, Any]] | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    def add(check: str, status: str, details: str, count: int | None = None):
        rows.append({"Check": check, "Status": status, "Count": count if count is not None else "", "Details": details})
    add("Input folder", "OK" if input_root.exists() else "Warning", str(input_root))
    add("Parsed rows", "OK" if len(df) else "Warning", "Rows normalized into Raw_Transactions", len(df))
    for report in source_reports or []:
        parsed_count = int(parse_amount(report.get("Parsed_Rows")) or 0)
        skipped_count = int(parse_amount(report.get("Skipped_Rows")) or 0)
        apparent_count = int(parse_amount(report.get("Source_Apparent_Transaction_Rows")) or 0)
        status = "OK" if parsed_count and skipped_count == 0 else ("Warning" if skipped_count or not parsed_count else "Manual")
        details = (
            f"{report.get('Bank')} | {report.get('File_Path')} | format: {report.get('Detected_Format')} | "
            f"apparent rows: {apparent_count}; parsed: {parsed_count}; skipped: {skipped_count}; "
            f"date range: {report.get('Date_Range')}; skipped reasons: {report.get('Skipped_Reasons')}; "
            f"warnings: {report.get('Parser_Warnings')}"
        )
        add("Source file import", status, details, parsed_count)
    investment_df = investment_df if investment_df is not None else pd.DataFrame(columns=INVESTMENT_SNAPSHOT_COLUMNS)
    add("Investment snapshots", "OK" if len(investment_df) else "Manual", "Rows normalized into Investment_Snapshots, separate from Raw_Transactions", len(investment_df))
    for report in investment_reports or []:
        parsed_count = int(parse_amount(report.get("Parsed_Rows")) or 0)
        skipped_count = int(parse_amount(report.get("Skipped_Rows")) or 0)
        apparent_count = int(parse_amount(report.get("Source_Apparent_Snapshot_Rows")) or 0)
        status = "OK" if parsed_count and skipped_count == 0 else ("Warning" if skipped_count or not parsed_count else "Manual")
        details = (
            f"{report.get('Bank')} | {report.get('File_Path')} | format: {report.get('Detected_Format')} | "
            f"apparent snapshots: {apparent_count}; parsed: {parsed_count}; skipped: {skipped_count}; "
            f"date range: {report.get('Date_Range')}; products: {report.get('Product_Count')}; "
            f"currencies: {report.get('Currencies')}; skipped reasons: {report.get('Skipped_Reasons')}; "
            f"warnings: {report.get('Parser_Warnings')}"
        )
        add("Investment source import", status, details, parsed_count)
    if not investment_df.empty:
        inv_summaries = make_investment_summary_data(investment_df)
        inv_metrics = latest_investment_metrics(investment_df, inv_summaries)
        inv_missing_fx = int(investment_df["FX_Conversion_Status"].astype(str).str.contains("Missing FX rate", na=False).sum())
        inv_warn_rows = int(investment_df["Parser_Warning"].astype(str).str.strip().ne("").sum())
        inv_currencies = ", ".join(sorted(set(investment_df["Original_Currency"].astype(str).str.upper()) - {"", "NAN"}))
        latest_date = inv_metrics.get("latest_date")
        latest_date_text = latest_date.strftime("%Y-%m-%d") if isinstance(latest_date, pd.Timestamp) and pd.notna(latest_date) else ""
        add("Investment latest value", "OK", f"Latest snapshot date {latest_date_text}; currencies: {inv_currencies}", round(float(inv_metrics.get("latest_total") or 0), 2))
        add("Investment products", "OK" if inv_metrics.get("product_count") else "Manual", "Distinct ISIN/product IDs or product names in investment snapshots", int(inv_metrics.get("product_count") or 0))
        add("Investment missing FX rates", "Warning" if inv_missing_fx else "OK", "Investment snapshot rows with no available rate to EUR", inv_missing_fx)
        add("Investment parser warnings", "Warning" if inv_warn_rows else "OK", "Rows in Investment_Snapshots with Parser_Warning populated", inv_warn_rows)
    uncategorized_mask = df["Category"] == "Uncategorized"
    add(
        "Missing categories",
        "Warning" if uncategorized_mask.any() else "OK",
        "Rows classified as Uncategorized. Top remaining groups: " + format_review_examples(df, uncategorized_mask),
        int(uncategorized_mask.sum()),
    )
    add("Duplicate suspects", "Warning" if df["Is_Duplicate_Suspect"].any() else "OK", "Strong duplicate evidence only: overlapping source files, repeated bank references, or identical post-transaction balances", int(df["Is_Duplicate_Suspect"].sum()))
    if "Duplicate_Reason" in df.columns:
        add("Duplicate reasons populated", "OK" if not df["Is_Duplicate_Suspect"].any() or df.loc[df["Is_Duplicate_Suspect"], "Duplicate_Reason"].astype(str).str.strip().ne("").all() else "Warning", "Duplicate suspects include a reason field in Raw_Transactions.", int(df["Duplicate_Reason"].astype(str).str.strip().ne("").sum()))
    add(
        "Duplicate review criteria",
        "OK",
        "Rows are strong duplicate suspects only with overlapping source files, at least two matching non-empty bank references, or at least two matching post-transaction balances. Same-day repeated merchant/card taps without those signals are preserved but not flagged.",
        int(df["Is_Duplicate_Suspect"].sum()),
    )
    add("Impossible dates", "Warning" if df["Booking_Date"].isna().any() else "OK", "Missing or invalid booking dates", int(df["Booking_Date"].isna().sum()))
    add("Suspicious balances", "Manual", "Balance_After is unavailable on rows where the source export or parser did not provide a reliable post-transaction balance.", int(df["Balance_After"].replace('', pd.NA).isna().sum()))
    add("Low-confidence categorization", "Warning" if (pd.to_numeric(df["Category_Confidence"], errors="coerce") < 0.5).any() else "OK", "Category confidence below 0.50", int((pd.to_numeric(df["Category_Confidence"], errors="coerce") < 0.5).sum()))
    add("Internal transfers", "OK", "Rows excluded from real income/expense totals", int(df["Is_Internal_Transfer"].sum()))
    transfer_groups = int(df.loc[df["Is_Internal_Transfer"], "Transfer_Group_ID"].replace("", pd.NA).dropna().nunique()) if "Transfer_Group_ID" in df.columns else 0
    add("Internal transfer groups", "OK", "Stable Transfer_Group_ID count for detected internal transfer rows", transfer_groups)
    ambiguous_transfer_mask = df["Notes"].astype(str).str.contains("Transfer-like row left for manual review", na=False) if "Notes" in df.columns else pd.Series(False, index=df.index)
    ambiguous_transfer_rows = int(ambiguous_transfer_mask.sum())
    add(
        "Ambiguous transfer candidates",
        "Manual" if ambiguous_transfer_rows else "OK",
        "Transfer-like rows not forced into Internal Transfer without own-account evidence. Examples: " + format_review_examples(df, ambiguous_transfer_mask),
        ambiguous_transfer_rows,
    )
    add("Savings/investments", "OK" if df["Is_Savings_Investment"].any() else "Manual", "Savings/investment rows detected separately from normal expenses", int(df["Is_Savings_Investment"].sum()))
    savings_types = int(df.loc[df["Is_Savings_Investment"], "Savings_Investment_Type"].replace("", pd.NA).dropna().nunique()) if "Savings_Investment_Type" in df.columns else 0
    add("Savings/investment types", "OK" if savings_types else "Manual", "Distinct savings/investment subtypes used", savings_types)
    recurring_groups = int(df.loc[df["Is_Recurring"], "Recurring_Group_ID"].replace("", pd.NA).dropna().nunique()) if "Recurring_Group_ID" in df.columns else 0
    add(
        "Recurring groups",
        "OK" if recurring_groups else "Manual",
        "Recurring groups after excluding duplicate suspects and casual repeated merchants. Strict monthly/repeated cadence and category evidence required.",
        recurring_groups,
    )
    non_eur = df[df["Original_Currency"].astype(str).str.upper().ne("EUR")]
    missing_fx = df["FX_Conversion_Status"].astype(str).str.contains("Missing FX rate", na=False) if "FX_Conversion_Status" in df.columns else pd.Series(False, index=df.index)
    converted_fx = df["FX_Conversion_Status"].astype(str).str.contains("Converted using historical FX rate|Latest rate used - not historical|Converted using Currency_Rates", regex=True, na=False) if "FX_Conversion_Status" in df.columns else pd.Series(False, index=df.index)
    rate_count = int(len(rates_df)) if rates_df is not None else 0
    add("Currency rates", "OK" if rate_count > 1 else "Manual", f"Editable rates loaded from config/currency_rates.csv. EUR identity rate is always included.", rate_count)
    add("Non-EUR rows", "OK" if len(non_eur) == 0 or not missing_fx.any() else "Warning", "Rows whose Original_Currency is not EUR.", int(len(non_eur)))
    add("Currency conversions", "OK" if converted_fx.any() or len(non_eur) == 0 else "Manual", "Non-EUR rows converted using transaction-date historical rates unless --fx-mode latest was selected.", int(converted_fx.sum()))
    add("Missing FX rates", "Warning" if missing_fx.any() else "OK", "Non-EUR rows with no available rate to EUR.", int(missing_fx.sum()))
    if fx_report:
        failures = fx_report.get("download_failures") or []
        add("FX provider", "OK", normalize_text(fx_report.get("provider")) or FX_PROVIDER_FRANKFURTER)
        add("FX mode", "Warning" if fx_report.get("mode") == "latest" else "OK", normalize_text(fx_report.get("mode")) or "historical")
        add("FX cache", "OK", normalize_text(fx_report.get("cache_path")), int(fx_report.get("cache_rows_after", 0) or 0))
        add("FX downloads", "Warning" if failures else "OK", f"Downloaded rates this run: {int(fx_report.get('downloaded_rates', 0) or 0)}; downloads enabled: {bool(fx_report.get('allow_download', False))}; failures: {len(failures)}", int(fx_report.get("downloaded_rates", 0) or 0))
    add("Ignored rows", "OK", "Rows preserved but excluded from real totals", int(df["Is_Ignored"].sum()))
    for w in parser_warnings:
        add("Parser warning", "Warning", w)
    warn_rows = df[df["Parser_Warning"].astype(str).str.strip() != ""]
    add("Rows with parser warnings", "Warning" if len(warn_rows) else "OK", "See Raw_Transactions.Parser_Warning", len(warn_rows))
    return pd.DataFrame(rows)


def sanitize_sheet_name(name: Any) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "", str(name))[:31]
    return s or "Sheet"


def excel_col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def format_date_for_excel(x: Any) -> Any:
    if pd.isna(x) or x == "":
        return ""
    if isinstance(x, pd.Timestamp):
        return x.to_pydatetime()
    return x


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


CURRENCY_RATE_COLUMNS = ["Rate_Date", "From_Currency", "To_Currency", "Rate_To_EUR", "Source", "Notes"]
FX_CACHE_COLUMNS = ["Currency", "Rate_Date", "Rate_To_EUR", "Source", "Retrieved_At", "Notes"]
FX_CACHE_FILENAME = "currency_rates_cache.csv"
FX_PROVIDER_FRANKFURTER = "frankfurter"
FRANKFURTER_SOURCE = "Frankfurter (ECB reference rates)"
FRANKFURTER_BASE_URL = "https://api.frankfurter.app"
FX_RATE_LOOKBACK_DAYS = 14
FX_WEEKEND_PRIOR_MAX_AGE_DAYS = 4

CURRENCY_RATE_COLUMN_ALIASES = {
    "Rate_Date": ["rate_date", "date", "datum", "dátum", "valid_from", "valid date", "exchange date"],
    "From_Currency": ["from_currency", "from", "currency", "mena", "source_currency", "original_currency", "ccy"],
    "To_Currency": ["to_currency", "to", "target_currency", "base_currency"],
    "Rate_To_EUR": ["rate_to_eur", "rate", "exchange_rate", "kurz", "fx_rate", "eur_rate", "value"],
    "Source": ["source", "zdroj", "provider", "rate_source"],
    "Notes": ["notes", "note", "poznamka", "poznámka"],
}


def normalize_currency_code(value: Any, default: str = "EUR") -> str:
    code = normalize_text(value).upper()[:3]
    return code or default


def rate_date_to_string(value: Any) -> str:
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return ""
    return ts.date().isoformat()


def clean_header_for_match(value: Any) -> str:
    return re.sub(r"[^a-z0-9áäčďéíĺľňóôŕšťúýž_ -]+", "", normalize_text(value).lower()).strip()


def header_alias_matches(cleaned: str, alias: str) -> bool:
    if len(alias) <= 3:
        return cleaned == alias
    return alias in cleaned


def first_rate_column(df: pd.DataFrame, canonical: str) -> str | None:
    aliases = [clean_header_for_match(x) for x in CURRENCY_RATE_COLUMN_ALIASES[canonical]]
    header_map = {clean_header_for_match(c): c for c in df.columns}
    for alias in aliases:
        if alias in header_map:
            return header_map[alias]
    for cleaned, original in header_map.items():
        if any(header_alias_matches(cleaned, alias) for alias in aliases):
            return original
    return None


def normalize_currency_rates(raw: pd.DataFrame, source_name: str) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame(columns=CURRENCY_RATE_COLUMNS)
    out = pd.DataFrame()
    for col in CURRENCY_RATE_COLUMNS:
        found = first_rate_column(raw, col)
        if found is not None:
            out[col] = raw[found]
        else:
            out[col] = ""
    out["Rate_Date"] = pd.to_datetime(out["Rate_Date"], dayfirst=True, errors="coerce")
    out["From_Currency"] = out["From_Currency"].apply(lambda x: normalize_currency_code(x, ""))
    out["To_Currency"] = out["To_Currency"].apply(lambda x: normalize_currency_code(x, "EUR"))
    out["Rate_To_EUR"] = out["Rate_To_EUR"].apply(parse_amount)
    out["Source"] = out["Source"].apply(lambda x: normalize_text(x) or source_name)
    out["Notes"] = out["Notes"].apply(normalize_text)
    out = out[(out["From_Currency"] != "") & (out["To_Currency"] == "EUR") & (out["Rate_To_EUR"].notna()) & (out["Rate_To_EUR"] > 0)].copy()
    if out.empty:
        return pd.DataFrame(columns=CURRENCY_RATE_COLUMNS)
    # Deterministic de-duplication: exact date/currency rows keep the last row in the file.
    out = out.drop_duplicates(subset=["Rate_Date", "From_Currency", "To_Currency"], keep="last")
    return out[CURRENCY_RATE_COLUMNS]


def discover_currency_rates(currency_rates_path: Path) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    frames: list[pd.DataFrame] = []
    candidates: list[Path] = []
    if currency_rates_path.exists() and currency_rates_path.is_file():
        candidates.append(currency_rates_path)
    elif currency_rates_path.exists() and currency_rates_path.is_dir():
        candidates.extend(sorted(p for p in currency_rates_path.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".xlsx", ".xls"}))
    else:
        warnings.append(
            f"Manual currency-rate config not found: {currency_rates_path}. Copy config/currency_rates.example.csv to config/currency_rates.csv or rely on downloaded cache."
        )
    for path in candidates:
        try:
            if path.suffix.lower() == ".csv":
                loaded = None
                for encoding in ["utf-8-sig", "utf-8", "cp1250", "latin1"]:
                    for sep in [None, ";", ",", "\t"]:
                        try:
                            loaded = pd.read_csv(path, sep=sep, engine="python", encoding=encoding, dtype=object)
                            if len(loaded.columns) >= 2:
                                break
                        except Exception:
                            loaded = None
                    if loaded is not None:
                        break
                if loaded is None:
                    warnings.append(f"Currency-rates file could not be parsed: {path}")
                    continue
                frames.append(normalize_currency_rates(loaded, path.name))
            else:
                sheets = pd.read_excel(path, sheet_name=None, dtype=object)
                for sheet_name, raw in sheets.items():
                    frames.append(normalize_currency_rates(raw, f"{path.name}:{sheet_name}"))
        except Exception as exc:
            warnings.append(f"Currency-rates parser failed for {path}: {exc}")
    if frames:
        rates = pd.concat(frames, ignore_index=True)
    else:
        rates = pd.DataFrame(columns=CURRENCY_RATE_COLUMNS)
    rates = rates[rates["From_Currency"] != "EUR"].copy() if "From_Currency" in rates.columns else pd.DataFrame(columns=CURRENCY_RATE_COLUMNS)
    eur_row = pd.DataFrame([{
        "Rate_Date": pd.NaT,
        "From_Currency": "EUR",
        "To_Currency": "EUR",
        "Rate_To_EUR": 1.0,
        "Source": "Base",
        "Notes": "Default identity conversion.",
    }])
    rates = pd.concat([eur_row, rates], ignore_index=True)
    rates = rates.sort_values(["From_Currency", "Rate_Date"], na_position="first").drop_duplicates(
        subset=["Rate_Date", "From_Currency", "To_Currency"], keep="last"
    ).reset_index(drop=True)
    return rates[CURRENCY_RATE_COLUMNS], warnings


FX_CACHE_COLUMN_ALIASES = {
    "Currency": ["currency", "from_currency", "from", "ccy", "source_currency", "original_currency"],
    "Rate_Date": ["rate_date", "date", "datum", "dátum", "valid_from", "exchange date"],
    "Rate_To_EUR": ["rate_to_eur", "rate", "exchange_rate", "kurz", "fx_rate", "eur_rate", "value"],
    "Source": ["source", "provider", "rate_source", "zdroj"],
    "Retrieved_At": ["retrieved_at", "retrieved", "downloaded_at", "created_at"],
    "Notes": ["notes", "note", "poznamka", "poznámka"],
    "To_Currency": ["to_currency", "to", "target_currency", "base_currency"],
}


def first_cache_column(df: pd.DataFrame, canonical: str) -> str | None:
    aliases = [clean_header_for_match(x) for x in FX_CACHE_COLUMN_ALIASES[canonical]]
    header_map = {clean_header_for_match(c): c for c in df.columns}
    for alias in aliases:
        if alias in header_map:
            return header_map[alias]
    for cleaned, original in header_map.items():
        if any(header_alias_matches(cleaned, alias) for alias in aliases):
            return original
    return None


def normalize_fx_cache(raw: pd.DataFrame | None) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame(columns=FX_CACHE_COLUMNS)
    out = pd.DataFrame()
    for col in FX_CACHE_COLUMNS:
        found = first_cache_column(raw, col)
        out[col] = raw[found] if found is not None else ""
    to_currency_col = first_cache_column(raw, "To_Currency")
    if to_currency_col is not None:
        to_currency = raw[to_currency_col].apply(lambda x: normalize_currency_code(x, "EUR"))
    else:
        to_currency = pd.Series(["EUR"] * len(raw), index=raw.index)
    out["Currency"] = out["Currency"].apply(lambda x: normalize_currency_code(x, ""))
    out["Rate_Date"] = out["Rate_Date"].apply(rate_date_to_string)
    out["Rate_To_EUR"] = out["Rate_To_EUR"].apply(parse_amount)
    out["Source"] = out["Source"].apply(lambda x: normalize_text(x) or FRANKFURTER_SOURCE)
    out["Retrieved_At"] = out["Retrieved_At"].apply(normalize_text)
    out["Notes"] = out["Notes"].apply(normalize_text)
    out = out[
        (out["Currency"] != "")
        & (out["Currency"] != "EUR")
        & (to_currency == "EUR")
        & (out["Rate_Date"] != "")
        & (out["Rate_To_EUR"].notna())
        & (out["Rate_To_EUR"] > 0)
    ].copy()
    if out.empty:
        return pd.DataFrame(columns=FX_CACHE_COLUMNS)
    out = out.drop_duplicates(subset=["Currency", "Rate_Date", "Source"], keep="last")
    out = out.sort_values(["Currency", "Rate_Date", "Source"]).reset_index(drop=True)
    return out[FX_CACHE_COLUMNS]


def load_fx_cache(cache_path: Path) -> tuple[pd.DataFrame, Path, list[str]]:
    warnings: list[str] = []
    if not cache_path.exists():
        return pd.DataFrame(columns=FX_CACHE_COLUMNS), cache_path, warnings
    try:
        raw = pd.read_csv(cache_path, dtype=object)
    except Exception as exc:
        warnings.append(f"FX cache could not be read from {cache_path}: {exc}")
        return pd.DataFrame(columns=FX_CACHE_COLUMNS), cache_path, warnings
    cache = normalize_fx_cache(raw)
    return cache, cache_path, warnings


def save_fx_cache(cache_df: pd.DataFrame, cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    out = normalize_fx_cache(cache_df)
    for col in FX_CACHE_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out = out[FX_CACHE_COLUMNS].copy()
    out["Rate_To_EUR"] = pd.to_numeric(out["Rate_To_EUR"], errors="coerce").round(12)
    out.to_csv(cache_path, index=False, encoding="utf-8")


def cache_rates_to_currency_rates(cache_df: pd.DataFrame) -> pd.DataFrame:
    cache = normalize_fx_cache(cache_df)
    if cache.empty:
        return pd.DataFrame(columns=CURRENCY_RATE_COLUMNS)
    out = pd.DataFrame({
        "Rate_Date": pd.to_datetime(cache["Rate_Date"], errors="coerce"),
        "From_Currency": cache["Currency"].apply(lambda x: normalize_currency_code(x, "")),
        "To_Currency": "EUR",
        "Rate_To_EUR": pd.to_numeric(cache["Rate_To_EUR"], errors="coerce"),
        "Source": cache["Source"].apply(normalize_text),
        "Notes": cache["Notes"].apply(normalize_text),
    })
    out = out[(out["From_Currency"] != "") & (out["Rate_Date"].notna()) & (out["Rate_To_EUR"].notna()) & (out["Rate_To_EUR"] > 0)].copy()
    return out[CURRENCY_RATE_COLUMNS]


def combine_currency_rates(manual_rates_df: pd.DataFrame | None, cache_df: pd.DataFrame | None = None) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    cache_rates = cache_rates_to_currency_rates(cache_df if cache_df is not None else pd.DataFrame(columns=FX_CACHE_COLUMNS))
    if not cache_rates.empty:
        tmp = cache_rates.copy()
        tmp["_Priority"] = 10
        frames.append(tmp)
    if manual_rates_df is not None and not manual_rates_df.empty:
        tmp = manual_rates_df.copy()
        tmp["_Priority"] = 20
        frames.append(tmp)
    if frames:
        rates = pd.concat(frames, ignore_index=True)
    else:
        rates = pd.DataFrame(columns=CURRENCY_RATE_COLUMNS + ["_Priority"])
    for col in CURRENCY_RATE_COLUMNS:
        if col not in rates.columns:
            rates[col] = ""
    rates["Rate_Date"] = pd.to_datetime(rates["Rate_Date"], errors="coerce")
    rates["From_Currency"] = rates["From_Currency"].apply(lambda x: normalize_currency_code(x, ""))
    rates["To_Currency"] = rates["To_Currency"].apply(lambda x: normalize_currency_code(x, "EUR"))
    rates["Rate_To_EUR"] = pd.to_numeric(rates["Rate_To_EUR"], errors="coerce")
    rates["Source"] = rates["Source"].apply(normalize_text)
    rates["Notes"] = rates["Notes"].apply(normalize_text)
    rates["_Priority"] = pd.to_numeric(rates.get("_Priority", 0), errors="coerce").fillna(0)
    rates = rates[
        (rates["From_Currency"] != "")
        & (rates["To_Currency"] == "EUR")
        & (rates["Rate_To_EUR"].notna())
        & (rates["Rate_To_EUR"] > 0)
    ].copy()
    rates = rates[rates["From_Currency"] != "EUR"].copy()
    if not rates.empty:
        rates = rates.sort_values(["From_Currency", "Rate_Date", "_Priority"], na_position="first")
        rates = rates.drop_duplicates(subset=["Rate_Date", "From_Currency", "To_Currency"], keep="last")
    eur_row = pd.DataFrame([{
        "Rate_Date": pd.NaT,
        "From_Currency": "EUR",
        "To_Currency": "EUR",
        "Rate_To_EUR": 1.0,
        "Source": "Base",
        "Notes": "Default identity conversion.",
    }])
    rates = pd.concat([eur_row, rates[CURRENCY_RATE_COLUMNS]], ignore_index=True)
    rates = rates.sort_values(["From_Currency", "Rate_Date"], na_position="first").reset_index(drop=True)
    return rates[CURRENCY_RATE_COLUMNS]


def fetch_frankfurter_rate(currency: str, conversion_date: Any, target: str = "EUR", fx_mode: str = "historical", timeout: int = 10) -> tuple[dict[str, Any] | None, str | None]:
    currency = normalize_currency_code(currency, "")
    target = normalize_currency_code(target, "EUR")
    if not currency or currency == target:
        return None, None
    query = urllib.parse.urlencode({"from": currency, "to": target})
    requested_date = pd.to_datetime(conversion_date, errors="coerce")
    if fx_mode == "latest":
        url = f"{FRANKFURTER_BASE_URL}/latest?{query}"
        note = "Fetched from Frankfurter latest endpoint; use only when --fx-mode latest is explicitly selected."
    else:
        if pd.isna(requested_date):
            return None, f"Cannot fetch historical FX for {currency}->{target}: missing booking date."
        end_date = requested_date.date()
        start_date = end_date - timedelta(days=FX_RATE_LOOKBACK_DAYS)
        url = f"{FRANKFURTER_BASE_URL}/{start_date.isoformat()}..{end_date.isoformat()}?{query}"
        note = f"Fetched for transaction date {end_date.isoformat()}; nearest previous published rate is used when exact date is unavailable."
    headers = {"User-Agent": "personal-finance-workbook-fx/1.0"}
    last_error = ""
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if fx_mode == "latest":
                rate_date = rate_date_to_string(payload.get("date"))
                rate = parse_amount((payload.get("rates") or {}).get(target))
            else:
                requested = requested_date.date()
                candidates: list[tuple[str, float]] = []
                for date_key, rates in (payload.get("rates") or {}).items():
                    rate_date = pd.to_datetime(date_key, errors="coerce")
                    rate = parse_amount((rates or {}).get(target))
                    if pd.isna(rate_date) or rate is None or rate <= 0:
                        continue
                    date_str = rate_date.date().isoformat()
                    if rate_date.date() <= requested:
                        candidates.append((date_str, rate))
                if not candidates:
                    return None, f"Frankfurter returned no previous {currency}->{target} rate for {rate_date_to_string(conversion_date)}."
                rate_date, rate = sorted(candidates, key=lambda x: x[0])[-1]
            if not rate_date or rate is None or rate <= 0:
                return None, f"Frankfurter returned no usable {currency}->{target} rate for {rate_date_to_string(conversion_date) or fx_mode}."
            return {
                "Currency": currency,
                "Rate_Date": rate_date,
                "Rate_To_EUR": float(rate),
                "Source": FRANKFURTER_SOURCE,
                "Retrieved_At": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                "Notes": note,
            }, None
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            last_error = str(exc)
            if attempt == 0:
                time.sleep(0.75)
    return None, f"Frankfurter fetch failed for {currency}->{target} {rate_date_to_string(conversion_date) or fx_mode}: {last_error}"


def requested_dates_from_notes(notes: Any) -> set[str]:
    return set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", normalize_text(notes)))


def merge_fx_cache_notes(existing_notes: Any, new_notes: Any, requested_date: Any = None) -> str:
    dates = requested_dates_from_notes(existing_notes) | requested_dates_from_notes(new_notes)
    requested = rate_date_to_string(requested_date)
    if requested:
        dates.add(requested)
    if dates:
        return f"Fetched for transaction dates: {', '.join(sorted(dates))}; nearest previous published rate is used when exact date is unavailable."
    return normalize_text(new_notes) or normalize_text(existing_notes)


def upsert_fx_cache_record(cache_df: pd.DataFrame, record: dict[str, Any], requested_date: Any = None) -> pd.DataFrame:
    cache = normalize_fx_cache(cache_df)
    row = normalize_fx_cache(pd.DataFrame([record]))
    if row.empty:
        return cache
    rec = row.iloc[0].to_dict()
    rec["Notes"] = merge_fx_cache_notes("", rec.get("Notes"), requested_date)
    if cache.empty:
        return normalize_fx_cache(pd.DataFrame([rec]))
    mask = (
        (cache["Currency"] == rec["Currency"])
        & (cache["Rate_Date"] == rec["Rate_Date"])
        & (cache["Source"] == rec["Source"])
    )
    if mask.any():
        idx = cache[mask].index[-1]
        cache.at[idx, "Rate_To_EUR"] = rec["Rate_To_EUR"]
        cache.at[idx, "Retrieved_At"] = rec["Retrieved_At"]
        cache.at[idx, "Notes"] = merge_fx_cache_notes(cache.at[idx, "Notes"], rec.get("Notes"), requested_date)
    else:
        cache = pd.concat([cache, pd.DataFrame([rec])], ignore_index=True)
    return normalize_fx_cache(cache)


def historical_rate_covers_booking(rate_row: pd.Series, booking_ts: pd.Timestamp) -> bool:
    rate_ts = pd.to_datetime(rate_row.get("Rate_Date"), errors="coerce")
    if pd.isna(rate_ts) or pd.isna(booking_ts):
        return False
    rate_date = rate_ts.date()
    booking_date = booking_ts.date()
    if rate_date > booking_date:
        return False
    age_days = (booking_date - rate_date).days
    if age_days == 0:
        return True
    if booking_date.isoformat() in requested_dates_from_notes(rate_row.get("Notes")):
        return True
    source = normalize_text(rate_row.get("Source")).lower()
    if "frankfurter" not in source and age_days <= FX_RATE_LOOKBACK_DAYS:
        return True
    if booking_ts.weekday() >= 5 and age_days <= FX_WEEKEND_PRIOR_MAX_AGE_DAYS:
        return True
    return False


def latest_rate_is_fresh(rates_df: pd.DataFrame, currency: str) -> bool:
    currency = normalize_currency_code(currency, "")
    if not currency:
        return False
    rates = rates_df[(rates_df["From_Currency"] == currency) & (rates_df["To_Currency"] == "EUR") & (rates_df["Rate_Date"].notna())].copy()
    if rates.empty:
        return False
    max_date = pd.to_datetime(rates["Rate_Date"], errors="coerce").max()
    if pd.isna(max_date):
        return False
    return max_date.date() >= (datetime.utcnow().date() - timedelta(days=7))


def fetch_missing_fx_rates(
    transactions_df: pd.DataFrame,
    manual_rates_df: pd.DataFrame,
    cache_df: pd.DataFrame,
    cache_path: Path,
    allow_download: bool = True,
    provider: str = FX_PROVIDER_FRANKFURTER,
    fx_mode: str = "historical",
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], list[str]]:
    warnings: list[str] = []
    report: dict[str, Any] = {
        "provider": provider,
        "mode": fx_mode,
        "allow_download": bool(allow_download),
        "cache_path": str(cache_path),
        "cache_rows_before": int(len(cache_df)) if cache_df is not None else 0,
        "cache_rows_after": int(len(cache_df)) if cache_df is not None else 0,
        "downloaded_rates": 0,
        "download_failures": [],
        "missing_rate_requests_before_download": 0,
    }
    if provider != FX_PROVIDER_FRANKFURTER:
        warnings.append(f"Unsupported FX provider requested: {provider}. No downloads attempted.")
        report["download_failures"].append(f"Unsupported FX provider: {provider}")
        return combine_currency_rates(manual_rates_df, cache_df), cache_df, report, warnings

    cache_df = normalize_fx_cache(cache_df)
    combined_rates = combine_currency_rates(manual_rates_df, cache_df)
    if transactions_df is None or transactions_df.empty:
        return combined_rates, cache_df, report, warnings

    tx = transactions_df.copy()
    tx["Booking_Date"] = pd.to_datetime(tx["Booking_Date"], errors="coerce")
    tx["Original_Currency"] = tx["Original_Currency"].apply(lambda x: normalize_currency_code(x, "EUR"))
    non_eur = tx[tx["Original_Currency"].ne("EUR")].copy()
    if non_eur.empty:
        return combined_rates, cache_df, report, warnings

    fetched_rows: list[dict[str, Any]] = []
    attempted: set[tuple[str, str]] = set()

    if fx_mode == "latest":
        for currency in sorted(non_eur["Original_Currency"].dropna().unique()):
            if not currency or currency == "EUR":
                continue
            if latest_rate_is_fresh(combined_rates, currency):
                continue
            if not allow_download:
                continue
            record, error = fetch_frankfurter_rate(currency, None, fx_mode="latest")
            if record:
                fetched_rows.append(record)
                cache_df = upsert_fx_cache_record(cache_df, record)
                combined_rates = combine_currency_rates(manual_rates_df, cache_df)
            elif error:
                report["download_failures"].append(error)
        if fetched_rows:
            save_fx_cache(cache_df, cache_path)
            combined_rates = combine_currency_rates(manual_rates_df, cache_df)
        report["downloaded_rates"] = int(len(fetched_rows))
        report["cache_rows_after"] = int(len(cache_df))
        if report["download_failures"]:
            warnings.append(f"{len(report['download_failures'])} FX download failures occurred.")
        elif fetched_rows:
            warnings.append(f"Downloaded {len(fetched_rows)} latest FX rates from Frankfurter.")
        return combined_rates, cache_df, report, warnings

    for _, row in non_eur.sort_values(["Original_Currency", "Booking_Date"]).iterrows():
        currency = normalize_currency_code(row.get("Original_Currency"), "")
        booking_date = pd.to_datetime(row.get("Booking_Date"), errors="coerce")
        if not currency or currency == "EUR" or pd.isna(booking_date):
            continue
        rate, _, _ = get_rate_for_transaction(currency, booking_date, combined_rates, fx_mode="historical")
        if rate is not None:
            continue
        report["missing_rate_requests_before_download"] += 1
        if not allow_download:
            continue
        key = (currency, booking_date.date().isoformat())
        if key in attempted:
            continue
        attempted.add(key)
        record, error = fetch_frankfurter_rate(currency, booking_date, fx_mode="historical")
        if record:
            fetched_rows.append(record)
            cache_df = upsert_fx_cache_record(cache_df, record, booking_date)
            combined_rates = combine_currency_rates(manual_rates_df, cache_df)
        elif error:
            report["download_failures"].append(error)

    if fetched_rows:
        save_fx_cache(cache_df, cache_path)
        combined_rates = combine_currency_rates(manual_rates_df, cache_df)
        warnings.append(f"Downloaded {len(fetched_rows)} historical FX rates from Frankfurter.")
    if report["download_failures"]:
        warnings.append(f"{len(report['download_failures'])} FX download failures occurred.")
    report["downloaded_rates"] = int(len(fetched_rows))
    report["cache_rows_after"] = int(len(cache_df))
    return combined_rates, cache_df, report, warnings


def find_fx_rate(rates_df: pd.DataFrame, currency: str, booking_date: Any, fx_mode: str = "historical") -> tuple[float | None, Any, str]:
    currency = normalize_currency_code(currency, "EUR")
    if currency == "EUR":
        return 1.0, pd.NaT, "Base"
    if rates_df is None or rates_df.empty:
        return None, "", ""
    rates = rates_df[(rates_df["From_Currency"] == currency) & (rates_df["To_Currency"] == "EUR") & (pd.to_numeric(rates_df["Rate_To_EUR"], errors="coerce") > 0)].copy()
    if rates.empty:
        return None, "", ""
    booking_ts = pd.to_datetime(booking_date, errors="coerce")
    dated = rates[rates["Rate_Date"].notna()].copy()
    if fx_mode == "latest":
        if not dated.empty:
            hit = dated.sort_values("Rate_Date").iloc[-1]
            return float(hit["Rate_To_EUR"]), hit["Rate_Date"], normalize_text(hit["Source"])
        undated = rates[rates["Rate_Date"].isna()]
        if not undated.empty:
            hit = undated.iloc[-1]
            return float(hit["Rate_To_EUR"]), hit["Rate_Date"], normalize_text(hit["Source"])
        return None, "", ""
    if pd.notna(booking_ts) and not dated.empty:
        prior = dated[dated["Rate_Date"] <= booking_ts].sort_values("Rate_Date")
        for _, hit in prior.iloc[::-1].iterrows():
            if historical_rate_covers_booking(hit, booking_ts):
                return float(hit["Rate_To_EUR"]), hit["Rate_Date"], normalize_text(hit["Source"])
    return None, "", ""


def get_rate_for_transaction(currency: str, booking_date: Any, rates_cache: pd.DataFrame, fx_mode: str = "historical") -> tuple[float | None, Any, str]:
    return find_fx_rate(rates_cache, currency, booking_date, fx_mode=fx_mode)


def apply_currency_conversion(df: pd.DataFrame, rates_df: pd.DataFrame, fx_mode: str = "historical") -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    if df.empty:
        for col in ["FX_Rate_To_EUR", "FX_Rate_Date", "FX_Rate_Source", "FX_Conversion_Status"]:
            if col not in df.columns:
                df[col] = ""
        return df, warnings
    df = df.copy()
    for col in ["FX_Rate_Date", "FX_Rate_Source", "FX_Conversion_Status"]:
        if col not in df.columns:
            df[col] = ""

    if "FX_Rate_To_EUR" not in df.columns:
        df["FX_Rate_To_EUR"] = pd.NA

    df["FX_Rate_To_EUR"] = pd.to_numeric(df["FX_Rate_To_EUR"], errors="coerce")

    if "Amount_EUR" in df.columns:
        df["Amount_EUR"] = pd.to_numeric(df["Amount_EUR"], errors="coerce")
    if "Original_Amount" in df.columns:
        df["Original_Amount"] = pd.to_numeric(df["Original_Amount"], errors="coerce")

    df["Original_Currency"] = df["Original_Currency"].apply(lambda x: normalize_currency_code(x, "EUR"))
    converted_count = 0
    missing_count = 0
    latest_count = 0
    for idx, row in df.iterrows():
        currency = normalize_currency_code(row.get("Original_Currency"), "EUR")
        original_amount = parse_amount(row.get("Original_Amount"))
        if original_amount is None:
            df.at[idx, "FX_Conversion_Status"] = "No original amount"
            continue
        if currency == "EUR":
            df.at[idx, "Amount_EUR"] = original_amount
            df.at[idx, "FX_Rate_To_EUR"] = 1.0
            df.at[idx, "FX_Rate_Date"] = ""
            df.at[idx, "FX_Rate_Source"] = "Base"
            df.at[idx, "FX_Conversion_Status"] = "Native EUR"
            continue
        df.at[idx, "Amount_EUR"] = pd.NA
        rate, rate_date, source = get_rate_for_transaction(currency, row.get("Booking_Date"), rates_df, fx_mode=fx_mode)
        if rate is None:
            df.at[idx, "FX_Conversion_Status"] = f"Missing FX rate for {currency}->EUR"
            existing_warning = normalize_text(row.get("Parser_Warning"))
            df.at[idx, "Parser_Warning"] = (existing_warning + " " if existing_warning else "") + f"Missing FX rate for {currency}->EUR."
            missing_count += 1
            continue
        df.at[idx, "Amount_EUR"] = original_amount * rate
        df.at[idx, "FX_Rate_To_EUR"] = rate
        df.at[idx, "FX_Rate_Date"] = rate_date_to_string(rate_date)
        df.at[idx, "FX_Rate_Source"] = source or "Currency_Rates"
        if fx_mode == "latest":
            df.at[idx, "FX_Conversion_Status"] = "Latest rate used - not historical"
            latest_count += 1
        else:
            df.at[idx, "FX_Conversion_Status"] = "Converted using historical FX rate"
            converted_count += 1
    if converted_count:
        warnings.append(f"Converted {converted_count} non-EUR rows using historical FX rates.")
    if latest_count:
        warnings.append(f"Converted {latest_count} non-EUR rows using latest FX rates because --fx-mode latest was selected.")
    if missing_count:
        warnings.append(f"{missing_count} non-EUR rows could not be converted because no FX rate was available.")
    return df, warnings


def write_currency_rate_template(target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    target.write_text(
        "Rate_Date,From_Currency,To_Currency,Rate_To_EUR,Source,Notes\n"
        ",EUR,EUR,1,Base,Default identity conversion\n",
        encoding="utf-8",
    )


def make_summary_data(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dfe = effective_flags(df)
    out: dict[str, pd.DataFrame] = {}
    active_expense = dfe[dfe["Effective_Expense"] > 0]
    active_income = dfe[dfe["Effective_Income"] > 0]
    out["expense_by_category"] = active_expense.groupby("Category", dropna=False)["Effective_Expense"].sum().reset_index().sort_values("Effective_Expense", ascending=False)
    out["income_by_category"] = active_income.groupby("Category", dropna=False)["Effective_Income"].sum().reset_index().sort_values("Effective_Income", ascending=False)
    out["expense_by_account"] = active_expense.groupby("Account_Name", dropna=False)["Effective_Expense"].sum().reset_index().sort_values("Effective_Expense", ascending=False)
    recur = pd.DataFrame({
        "Type": ["Recurring Expenses", "One-Time Expenses"],
        "Amount": [float(dfe["Recurring_Expense"].sum()), float(dfe["One_Time_Expense"].sum())],
    })
    out["recurring_vs_one_time"] = recur
    savings = dfe[dfe["Savings_Investment_Amount"] > 0].groupby("Savings_Investment_Type", dropna=False)["Savings_Investment_Amount"].sum().reset_index().sort_values("Savings_Investment_Amount", ascending=False)
    if savings.empty:
        savings = pd.DataFrame({"Savings_Investment_Type": ["No Savings / Investment Detected"], "Savings_Investment_Amount": [0]})
    out["savings_by_type"] = savings
    monthly = dfe.groupby(["Year", "Month_Number", "Month_Name"], dropna=False).agg(
        Income=("Effective_Income", "sum"),
        Expenses=("Effective_Expense", "sum"),
        Savings_Investment=("Savings_Investment_Amount", "sum"),
    ).reset_index().sort_values(["Year", "Month_Number"])
    monthly["Net_Cashflow"] = monthly["Income"] - monthly["Expenses"]
    monthly["Period"] = monthly.apply(lambda r: f"{int(r['Year'])}-{int(r['Month_Number']):02d}", axis=1) if not monthly.empty else []
    out["monthly"] = monthly
    return out


def investment_product_label(row: pd.Series | dict[str, Any]) -> str:
    product = normalize_text(row.get("Product_Name"))
    isin = normalize_text(row.get("ISIN_or_Product_ID"))
    if product and isin:
        return f"{product} ({isin})"
    return product or isin or "Unspecified product"


def make_investment_summary_data(investment_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    if investment_df is None or investment_df.empty:
        empty_by_date = pd.DataFrame(columns=["Snapshot_Date", "Snapshot_Label", "Total_Market_Value_EUR", "Snapshot_Row_Count", "Value_Change_EUR", "Value_Change_Pct"])
        out["by_date"] = empty_by_date
        out["latest_allocation"] = pd.DataFrame(columns=["Product", "Market_Value_EUR", "Allocation"])
        out["by_product"] = pd.DataFrame(columns=["Product", "Market_Value_EUR", "Latest_Market_Value_EUR", "Snapshots"])
        out["product_by_date"] = pd.DataFrame(columns=["Snapshot_Date", "Snapshot_Label", "Product", "Market_Value_EUR"])
        return out

    df = investment_df.copy()
    df["Snapshot_Date"] = pd.to_datetime(df["Snapshot_Date"], errors="coerce")
    df["Market_Value_EUR"] = pd.to_numeric(df["Market_Value_EUR"], errors="coerce")
    df = df[df["Snapshot_Date"].notna() & df["Market_Value_EUR"].notna()].copy()
    if df.empty:
        return make_investment_summary_data(pd.DataFrame(columns=INVESTMENT_SNAPSHOT_COLUMNS))

    df["_Product_Label"] = df.apply(investment_product_label, axis=1)
    by_date = df.groupby("Snapshot_Date", dropna=False).agg(
        Total_Market_Value_EUR=("Market_Value_EUR", "sum"),
        Snapshot_Row_Count=("Snapshot_ID", "count"),
    ).reset_index().sort_values("Snapshot_Date")
    by_date["Value_Change_EUR"] = by_date["Total_Market_Value_EUR"].diff()
    by_date["Value_Change_Pct"] = by_date["Total_Market_Value_EUR"].pct_change().replace([math.inf, -math.inf], pd.NA)
    by_date["Snapshot_Label"] = by_date["Snapshot_Date"].dt.strftime("%Y-%m-%d")
    out["by_date"] = by_date[["Snapshot_Date", "Snapshot_Label", "Total_Market_Value_EUR", "Snapshot_Row_Count", "Value_Change_EUR", "Value_Change_Pct"]]

    latest_date = by_date["Snapshot_Date"].max()
    latest = df[df["Snapshot_Date"] == latest_date].copy()
    latest_allocation = latest.groupby("_Product_Label", dropna=False)["Market_Value_EUR"].sum().reset_index()
    latest_allocation = latest_allocation.rename(columns={"_Product_Label": "Product"}).sort_values("Market_Value_EUR", ascending=False)
    total_latest = float(latest_allocation["Market_Value_EUR"].sum()) if not latest_allocation.empty else 0.0
    latest_allocation["Allocation"] = latest_allocation["Market_Value_EUR"].apply(lambda x: float(x) / total_latest if total_latest else 0.0)
    out["latest_allocation"] = latest_allocation

    by_product = df.groupby("_Product_Label", dropna=False).agg(
        Market_Value_EUR=("Market_Value_EUR", "sum"),
        Snapshots=("Snapshot_Date", "nunique"),
    ).reset_index().rename(columns={"_Product_Label": "Product"})
    latest_values = latest.groupby("_Product_Label", dropna=False)["Market_Value_EUR"].sum().rename("Latest_Market_Value_EUR")
    by_product = by_product.merge(latest_values, left_on="Product", right_index=True, how="left").fillna({"Latest_Market_Value_EUR": 0})
    by_product = by_product.sort_values("Latest_Market_Value_EUR", ascending=False)
    out["by_product"] = by_product[["Product", "Market_Value_EUR", "Latest_Market_Value_EUR", "Snapshots"]]

    product_by_date = df.groupby(["Snapshot_Date", "_Product_Label"], dropna=False)["Market_Value_EUR"].sum().reset_index()
    product_by_date = product_by_date.rename(columns={"_Product_Label": "Product"})
    product_by_date["Snapshot_Label"] = product_by_date["Snapshot_Date"].dt.strftime("%Y-%m-%d")
    out["product_by_date"] = product_by_date[["Snapshot_Date", "Snapshot_Label", "Product", "Market_Value_EUR"]].sort_values(["Snapshot_Date", "Product"])
    return out


def latest_investment_metrics(investment_df: pd.DataFrame, investment_summaries: dict[str, pd.DataFrame] | None = None) -> dict[str, Any]:
    summaries = investment_summaries or make_investment_summary_data(investment_df)
    by_date = summaries.get("by_date", pd.DataFrame())
    if by_date.empty:
        return {
            "latest_date": "",
            "latest_total": 0.0,
            "value_change": 0.0,
            "value_change_pct": 0.0,
            "product_count": 0,
            "snapshot_rows": 0,
        }
    latest = by_date.sort_values("Snapshot_Date").iloc[-1]
    value_change = parse_amount(latest.get("Value_Change_EUR")) or 0.0
    value_change_pct = parse_amount(latest.get("Value_Change_Pct")) or 0.0
    if investment_df is None or investment_df.empty:
        product_count = 0
        snapshot_rows = 0
    else:
        product_keys = investment_df.apply(lambda r: normalize_text(r.get("ISIN_or_Product_ID")) or normalize_text(r.get("Product_Name")), axis=1)
        product_count = int(product_keys.replace("", pd.NA).dropna().nunique())
        snapshot_rows = int(len(investment_df))
    return {
        "latest_date": latest.get("Snapshot_Date"),
        "latest_total": float(latest.get("Total_Market_Value_EUR") or 0.0),
        "value_change": float(value_change),
        "value_change_pct": float(value_change_pct),
        "product_count": product_count,
        "snapshot_rows": snapshot_rows,
    }


def calc_top_label_value(df: pd.DataFrame, group_col: str, value_col: str) -> str:
    g = df.groupby(group_col, dropna=False)[value_col].sum().sort_values(ascending=False)
    if g.empty:
        return "—"
    return f"{g.index[0]} ({g.iloc[0]:,.2f} €)"


def setup_workbook_formats(workbook: Any) -> dict[str, Any]:
    fmt = {}
    fmt["bg"] = workbook.add_format({"bg_color": f"#{COLOR_BG}", "font_color": f"#{COLOR_TEXT}"})
    fmt["title"] = workbook.add_format({"bold": True, "font_size": 22, "font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_PRIMARY_DARK}", "align": "center", "valign": "vcenter", "border": 2, "border_color": f"#{COLOR_PRIMARY_LIGHT}"})
    fmt["section"] = workbook.add_format({"bold": True, "font_size": 13, "font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_PRIMARY}", "align": "left", "valign": "vcenter", "border": 2, "border_color": f"#{COLOR_SECONDARY}"})
    fmt["card_label"] = workbook.add_format({"font_color": f"#{COLOR_TEXT_MUTED}", "font_size": 10, "bg_color": f"#{COLOR_PANEL}", "align": "center", "valign": "vcenter", "border": 2, "border_color": f"#{COLOR_PRIMARY}"})
    fmt["card_value"] = workbook.add_format({"bold": True, "font_size": 16, "font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_PANEL}", "align": "center", "valign": "vcenter", "border": 2, "border_color": f"#{COLOR_PRIMARY}"})
    fmt["card_value_good"] = workbook.add_format({"bold": True, "font_size": 16, "font_color": f"#{COLOR_COMPLEMENT}", "bg_color": f"#{COLOR_PANEL}", "align": "center", "valign": "vcenter", "border": 2, "border_color": f"#{COLOR_PRIMARY}"})
    fmt["card_value_bad"] = workbook.add_format({"bold": True, "font_size": 16, "font_color": f"#{COLOR_PRIMARY_LIGHT}", "bg_color": f"#{COLOR_PANEL}", "align": "center", "valign": "vcenter", "border": 2, "border_color": f"#{COLOR_PRIMARY}"})
    fmt["header"] = workbook.add_format({"bold": True, "font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_PRIMARY_DARK}", "border": 1, "border_color": f"#{COLOR_PRIMARY_LIGHT}", "align": "center", "valign": "vcenter", "text_wrap": True})
    fmt["table"] = workbook.add_format({"font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_PANEL}", "border": 1, "border_color": f"#{COLOR_GRID}", "valign": "top"})
    fmt["table_alt"] = workbook.add_format({"font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_PANEL_2}", "border": 1, "border_color": f"#{COLOR_GRID}", "valign": "top"})
    fmt["muted"] = workbook.add_format({"font_color": f"#{COLOR_TEXT_MUTED}", "bg_color": f"#{COLOR_PANEL}", "border": 1, "border_color": f"#{COLOR_GRID}"})
    fmt["money"] = workbook.add_format({"num_format": '#,##0.00 €;[Red]-#,##0.00 €;0.00 €', "font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_PANEL}", "border": 1, "border_color": f"#{COLOR_GRID}"})
    fmt["money_alt"] = workbook.add_format({"num_format": '#,##0.00 €;[Red]-#,##0.00 €;0.00 €', "font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_PANEL_2}", "border": 1, "border_color": f"#{COLOR_GRID}"})
    fmt["pct"] = workbook.add_format({"num_format": '0.0%', "font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_PANEL}", "border": 1, "border_color": f"#{COLOR_GRID}"})
    fmt["date"] = workbook.add_format({"num_format": 'yyyy-mm-dd', "font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_PANEL}", "border": 1, "border_color": f"#{COLOR_GRID}"})
    fmt["warning"] = workbook.add_format({"font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_PRIMARY_LIGHT}", "border": 1, "border_color": f"#{COLOR_SECONDARY}"})
    fmt["blue"] = workbook.add_format({"font_color": f"#{COLOR_TEXT}", "bg_color": f"#{COLOR_COMPLEMENT}", "border": 1, "border_color": f"#{COLOR_PRIMARY}"})
    fmt["note"] = workbook.add_format({"font_color": f"#{COLOR_TEXT_MUTED}", "bg_color": f"#{COLOR_BG}", "italic": True})
    return fmt


def fill_background(ws: Any, fmt: Any, rows: int = 120, cols: int = 26):
    # Paint a bounded visible area without bloating too much.
    for r in range(rows):
        ws.set_row(r, 18, fmt)
    for c in range(cols):
        ws.set_column(c, c, 12, fmt)


def write_df_table(
    ws: Any,
    df: pd.DataFrame,
    start_row: int,
    start_col: int,
    table_name: str,
    fmt: dict[str, Any],
    money_cols: set[str] | None = None,
    date_cols: set[str] | None = None,
    pct_cols: set[str] | None = None,
    width_overrides: dict[str, int] | None = None,
):
    money_cols = money_cols or set()
    date_cols = date_cols or set()
    pct_cols = pct_cols or set()
    width_overrides = width_overrides or {}
    nrows, ncols = df.shape
    for c, col in enumerate(df.columns):
        ws.write(start_row, start_col + c, col, fmt["header"])
    for r, (_, row) in enumerate(df.iterrows(), start=start_row + 1):
        row_fmt_base = fmt["table"] if (r - start_row) % 2 else fmt["table_alt"]
        money_fmt = fmt["money"] if (r - start_row) % 2 else fmt["money_alt"]
        for c, col in enumerate(df.columns):
            val = row[col]
            if isinstance(val, pd.Timestamp):
                val = val.to_pydatetime()
            if pd.isna(val):
                val = ""
            cell_fmt = fmt["date"] if col in date_cols else (fmt["pct"] if col in pct_cols else (money_fmt if col in money_cols else row_fmt_base))
            ws.write(r, start_col + c, val, cell_fmt)
    if nrows > 0 and ncols > 0:
        columns = [{"header": col} for col in df.columns]
        ws.add_table(start_row, start_col, start_row + nrows, start_col + ncols - 1, {"name": table_name, "style": None, "columns": columns})
    for c, col in enumerate(df.columns):
        width = width_overrides.get(col)
        if width is None:
            if nrows:
                safe_lengths = df[col].map(lambda v: 0 if pd.isna(v) else len(str(v)))
                width = min(max(len(str(col)) + 2, int(safe_lengths.quantile(0.9)) + 2), 38)
            else:
                width = min(max(len(str(col)) + 2, len(str(col)) + 2), 38)
        ws.set_column(start_col + c, start_col + c, width)


def configure_chart(chart: Any, title: str, chart_type: str = "generic"):
    chart.set_title({"name": title, "name_font": {"color": f"#{COLOR_TEXT}", "bold": True}})
    chart.set_chartarea({"fill": {"color": f"#{COLOR_BG}"}, "border": {"color": f"#{COLOR_PRIMARY}"}})
    chart.set_plotarea({"fill": {"color": f"#{COLOR_PANEL}"}, "border": {"color": f"#{COLOR_PRIMARY_DARK}"}})
    chart.set_legend({"position": "bottom", "font": {"color": f"#{COLOR_TEXT}", "size": 8}})
    if chart_type != "pie":
        chart.set_x_axis({"name_font": {"color": f"#{COLOR_TEXT}"}, "num_font": {"color": f"#{COLOR_TEXT_MUTED}", "size": 8}, "line": {"color": COLOR_PRIMARY}})
        chart.set_y_axis({"name_font": {"color": f"#{COLOR_TEXT}"}, "num_font": {"color": f"#{COLOR_TEXT_MUTED}", "size": 8}, "major_gridlines": {"visible": True, "line": {"color": COLOR_GRID}}, "line": {"color": COLOR_PRIMARY}})


def add_pie_chart(workbook: Any, ws: Any, chart_sheet_name: str, chart_data_range: tuple[int, int, int, int], title: str, anchor: str):
    first_row, first_col, last_row, last_col = chart_data_range
    chart = workbook.add_chart({"type": "pie"})
    configure_chart(chart, title, "pie")
    colors = [COLOR_PRIMARY, COLOR_SECONDARY, COLOR_COMPLEMENT, COLOR_PRIMARY_LIGHT, COLOR_PRIMARY_DARK, "7A7A7A", "D64A1F", "0D7C91"]
    chart.add_series({
        "categories": [chart_sheet_name, first_row + 1, first_col, last_row, first_col],
        "values": [chart_sheet_name, first_row + 1, first_col + 1, last_row, first_col + 1],
        "points": [{"fill": {"color": c}} for c in colors],
        "data_labels": {"percentage": True, "font": {"color": f"#{COLOR_TEXT}", "size": 8}},
    })
    chart.set_size({"width": 360, "height": 250})
    ws.insert_chart(anchor, chart)


def add_line_chart(workbook: Any, ws: Any, sheet_name: str, data_range: tuple[int, int, int, int], title: str, anchor: str, ycols: list[tuple[str, int, str]]):
    first_row, first_col, last_row, last_col = data_range
    chart = workbook.add_chart({"type": "line"})
    configure_chart(chart, title, "line")
    for name, col_offset, color in ycols:
        chart.add_series({
            "name": name,
            "categories": [sheet_name, first_row + 1, first_col, last_row, first_col],
            "values": [sheet_name, first_row + 1, first_col + col_offset, last_row, first_col + col_offset],
            "line": {"color": color, "width": 2.25},
        })
    chart.set_size({"width": 520, "height": 260})
    ws.insert_chart(anchor, chart)


def add_column_chart(workbook: Any, ws: Any, sheet_name: str, data_range: tuple[int, int, int, int], title: str, anchor: str):
    first_row, first_col, last_row, _ = data_range
    chart = workbook.add_chart({"type": "column"})
    configure_chart(chart, title, "column")
    chart.add_series({"name": "Income", "categories": [sheet_name, first_row + 1, first_col, last_row, first_col], "values": [sheet_name, first_row + 1, first_col + 1, last_row, first_col + 1], "fill": {"color": COLOR_COMPLEMENT}, "border": {"color": COLOR_COMPLEMENT}})
    chart.add_series({"name": "Expenses", "categories": [sheet_name, first_row + 1, first_col, last_row, first_col], "values": [sheet_name, first_row + 1, first_col + 2, last_row, first_col + 2], "fill": {"color": COLOR_PRIMARY}, "border": {"color": COLOR_PRIMARY_LIGHT}})
    chart.set_size({"width": 520, "height": 260})
    ws.insert_chart(anchor, chart)


def write_chart_data(workbook: Any, summaries: dict[str, pd.DataFrame]) -> dict[str, tuple[int, int, int, int]]:
    ws = workbook.add_worksheet("Chart_Data")
    ws.hide()
    fmt = setup_workbook_formats(workbook)
    ranges: dict[str, tuple[int, int, int, int]] = {}
    row = 0
    for key, df in summaries.items():
        if df.empty:
            continue
        df2 = df.copy()
        # Limit huge category lists for chart clarity.
        if key not in {"monthly"} and len(df2) > 10:
            value_col = df2.columns[-1]
            top = df2.head(9)
            other_val = df2.iloc[9:][value_col].sum()
            other = pd.DataFrame([{df2.columns[0]: "Other", value_col: other_val}])
            df2 = pd.concat([top, other], ignore_index=True)
        write_df_table(ws, df2, row, 0, f"Chart_{key[:18]}".replace('-', '_'), fmt)
        ranges[key] = (row, 0, row + len(df2), len(df2.columns) - 1)
        row += len(df2) + 3
    return ranges


def write_dashboard(
    workbook: Any,
    df: pd.DataFrame,
    validation_df: pd.DataFrame,
    summaries: dict[str, pd.DataFrame],
    chart_ranges: dict[str, tuple[int, int, int, int]],
    fmt: dict[str, Any],
    investment_df: pd.DataFrame | None = None,
    investment_summaries: dict[str, pd.DataFrame] | None = None,
):
    ws = workbook.add_worksheet("Dashboard")
    fill_background(ws, fmt["bg"], 112, 24)
    ws.freeze_panes(3, 0)
    ws.merge_range("A1:Q2", "Personal Finance Analysis", fmt["title"])
    ws.write("A3", "All-years combined overview. Internal transfers and ignored rows are excluded from real income/expense totals.", fmt["note"])
    dfe = effective_flags(df)
    months_count = max(len(summaries.get("monthly", pd.DataFrame())), 1)
    total_income = float(dfe["Effective_Income"].sum())
    total_expenses = float(dfe["Effective_Expense"].sum())
    total_savings = float(dfe["Savings_Investment_Amount"].sum())
    net = total_income - total_expenses
    monthly = summaries.get("monthly", pd.DataFrame())
    highest_category = calc_top_label_value(dfe[dfe["Effective_Expense"] > 0], "Category", "Effective_Expense")
    most_account = calc_top_label_value(dfe[dfe["Effective_Expense"] > 0], "Account_Name", "Effective_Expense")
    if not monthly.empty:
        best = monthly.loc[monthly["Net_Cashflow"].idxmax()]
        worst = monthly.loc[monthly["Net_Cashflow"].idxmin()]
        best_month = f"{best['Period']} ({best['Net_Cashflow']:,.2f} €)"
        worst_month = f"{worst['Period']} ({worst['Net_Cashflow']:,.2f} €)"
        if monthly["Savings_Investment"].max() > 0:
            hs = monthly.loc[monthly["Savings_Investment"].idxmax()]
            highest_savings_month = f"{hs['Period']} ({hs['Savings_Investment']:,.2f} €)"
        else:
            highest_savings_month = "None detected"
    else:
        best_month = worst_month = highest_savings_month = "—"
    cards = [
        ("Total income", total_income, "money"),
        ("Total expenses", total_expenses, "money_bad"),
        ("Net cashflow", net, "money_good" if net >= 0 else "money_bad"),
        ("Savings rate", total_savings / total_income if total_income else 0, "pct"),
        ("Savings / investments", total_savings, "money_good"),
        ("Investment rate", total_savings / total_income if total_income else 0, "pct"),
        ("Recurring income", float(dfe["Recurring_Income"].sum()), "money"),
        ("Recurring expenses", float(dfe["Recurring_Expense"].sum()), "money_bad"),
        ("One-time expenses", float(dfe["One_Time_Expense"].sum()), "money_bad"),
        ("Internal transfers", float(dfe["Internal_Transfer_Amount"].sum()), "money"),
        ("Non-EUR rows", int(df["Original_Currency"].astype(str).str.upper().ne("EUR").sum()), "int"),
        ("Converted FX rows", int(df["FX_Conversion_Status"].astype(str).str.contains("Converted using historical FX rate|Latest rate used - not historical|Converted using Currency_Rates", regex=True, na=False).sum()), "int"),
        ("Missing FX rates", int(df["FX_Conversion_Status"].astype(str).str.contains("Missing FX rate", na=False).sum()), "int"),
        ("Average monthly income", total_income / months_count, "money"),
        ("Average monthly expenses", total_expenses / months_count, "money_bad"),
        ("Best month", best_month, "text"),
        ("Worst month", worst_month, "text"),
        ("Highest spending category", highest_category, "text"),
        ("Highest savings month", highest_savings_month, "text"),
        ("Most used account", most_account, "text"),
        ("Uncategorized count", int((df["Category"] == "Uncategorized").sum()), "int"),
    ]
    start_row, start_col = 4, 0
    card_w = 3
    for i, (label, value, kind) in enumerate(cards):
        r = start_row + (i // 3) * 3
        c = start_col + (i % 3) * 5
        ws.merge_range(r, c, r, c + card_w, label, fmt["card_label"])
        val_fmt = fmt["card_value"]
        if kind.endswith("good"):
            val_fmt = fmt["card_value_good"]
        elif kind.endswith("bad"):
            val_fmt = fmt["card_value_bad"]
        if kind.startswith("money") and isinstance(value, (int, float)):
            display = f"{value:,.2f} €"
        elif kind == "pct" and isinstance(value, (int, float)):
            display = f"{value:.1%}"
        else:
            display = value
        ws.merge_range(r + 1, c, r + 2, c + card_w, display, val_fmt)
    # Formula-driven cards (hidden-ish area but visible as proof)
    ws.merge_range("A28:F28", "Formula-driven checks", fmt["section"])
    raw_end = len(df) + 1
    raw_headers = list(df.columns)
    def raw_col(name: str) -> str:
        return excel_col(raw_headers.index(name) + 1) if name in raw_headers else "A"
    income_col = raw_col("Income_Amount")
    expense_col = raw_col("Expense_Amount")
    transfer_col = raw_col("Is_Internal_Transfer")
    ignored_col = raw_col("Is_Ignored")
    cat_type_col = raw_col("Category_Type")
    category_col = raw_col("Category")
    currency_col = raw_col("Original_Currency")
    fx_status_col = raw_col("FX_Conversion_Status")
    formula_rows = [
        ["Total income formula", f'=SUMIFS(Raw_Transactions!${income_col}$2:${income_col}${raw_end},Raw_Transactions!${transfer_col}$2:${transfer_col}${raw_end},FALSE,Raw_Transactions!${ignored_col}$2:${ignored_col}${raw_end},FALSE,Raw_Transactions!${cat_type_col}$2:${cat_type_col}${raw_end},"<>savings/investment")', total_income],
        ["Total expenses formula", f'=SUMIFS(Raw_Transactions!${expense_col}$2:${expense_col}${raw_end},Raw_Transactions!${transfer_col}$2:${transfer_col}${raw_end},FALSE,Raw_Transactions!${ignored_col}$2:${ignored_col}${raw_end},FALSE,Raw_Transactions!${cat_type_col}$2:${cat_type_col}${raw_end},"<>savings/investment",Raw_Transactions!${cat_type_col}$2:${cat_type_col}${raw_end},"<>income")', total_expenses],
        ["Uncategorized formula", f'=COUNTIF(Raw_Transactions!${category_col}$2:${category_col}${raw_end},"Uncategorized")', int((df["Category"] == "Uncategorized").sum())],
        ["Internal transfer formula", f'=SUMIFS(Raw_Transactions!${expense_col}$2:${expense_col}${raw_end},Raw_Transactions!${transfer_col}$2:${transfer_col}${raw_end},TRUE)+SUMIFS(Raw_Transactions!${income_col}$2:${income_col}${raw_end},Raw_Transactions!${transfer_col}$2:${transfer_col}${raw_end},TRUE)', float(dfe["Internal_Transfer_Amount"].sum())],
        ["Non-EUR rows formula", f'=COUNTIF(Raw_Transactions!${currency_col}$2:${currency_col}${raw_end},"<>EUR")', int(df["Original_Currency"].astype(str).str.upper().ne("EUR").sum())],
        ["Missing FX formula", f'=COUNTIF(Raw_Transactions!${fx_status_col}$2:${fx_status_col}${raw_end},"Missing FX rate*")', int(df["FX_Conversion_Status"].astype(str).str.contains("Missing FX rate", na=False).sum())],
    ]
    for i, (label, formula, cached_value) in enumerate(formula_rows, start=29):
        ws.write(i - 1, 0, label, fmt["table"])
        ws.write_formula(i - 1, 1, formula, fmt["money"] if "formula" in label.lower() else fmt["table"], cached_value)
    for hidden_r in range(27, 36):
        ws.set_row(hidden_r, None, fmt["bg"], {"hidden": True})
    ws.set_column("A:A", 22)
    ws.set_column("B:B", 28)

    # Styled embedded chart images are generated by the pipeline to avoid default white Excel chart styling.
    if "expense_by_category" in summaries:
        insert_chart_image(ws, "A35", save_pie_image(summaries["expense_by_category"], "Category", "Effective_Expense", "Expenses by Category", "dashboard_expense_category"))
    if "income_by_category" in summaries:
        insert_chart_image(ws, "G35", save_pie_image(summaries["income_by_category"], "Category", "Effective_Income", "Income by Category / Source", "dashboard_income_category"))
    if "expense_by_account" in summaries:
        insert_chart_image(ws, "M35", save_pie_image(summaries["expense_by_account"], "Account_Name", "Effective_Expense", "Expenses by Account / Bank", "dashboard_expense_account"))
    if "recurring_vs_one_time" in summaries:
        insert_chart_image(ws, "A51", save_pie_image(summaries["recurring_vs_one_time"], "Type", "Amount", "Recurring vs One-Time Expenses", "dashboard_recurring_vs_one_time"))
    if "savings_by_type" in summaries:
        insert_chart_image(ws, "G51", save_pie_image(summaries["savings_by_type"], "Savings_Investment_Type", "Savings_Investment_Amount", "Savings / Investments by Type", "dashboard_savings_type"))
    if "monthly" in summaries:
        insert_chart_image(ws, "M51", save_column_image(summaries["monthly"], "Period", [("Income", "Income", COLOR_COMPLEMENT), ("Expenses", "Expenses", COLOR_PRIMARY)], "Monthly Income vs Expenses", "dashboard_income_expenses"))
        insert_chart_image(ws, "A67", save_line_image(summaries["monthly"], "Period", [("Net Cashflow", "Net_Cashflow", COLOR_COMPLEMENT)], "Monthly Net Cashflow", "dashboard_net_cashflow"))
        insert_chart_image(ws, "G67", save_line_image(summaries["monthly"], "Period", [("Savings / Investment", "Savings_Investment", COLOR_SECONDARY)], "Savings / Investment Contributions", "dashboard_savings_trend"))
    investment_summaries = investment_summaries or make_investment_summary_data(investment_df if investment_df is not None else pd.DataFrame(columns=INVESTMENT_SNAPSHOT_COLUMNS))
    inv_metrics = latest_investment_metrics(investment_df if investment_df is not None else pd.DataFrame(columns=INVESTMENT_SNAPSHOT_COLUMNS), investment_summaries)
    ws.merge_range("A84:Q84", "Investment Valuation Snapshots", fmt["section"])
    ws.write("A85", "Separate valuation snapshots only. These rows are not included in transaction income, expense, transfer, or contribution totals.", fmt["note"])
    latest_date = inv_metrics.get("latest_date")
    latest_date_text = latest_date.strftime("%Y-%m-%d") if isinstance(latest_date, pd.Timestamp) and pd.notna(latest_date) else "—"
    inv_cards = [
        ("Latest investment value", f"{float(inv_metrics.get('latest_total') or 0):,.2f} €", "good"),
        ("Latest snapshot date", latest_date_text, "text"),
        ("Products tracked", int(inv_metrics.get("product_count") or 0), "int"),
        ("Snapshot rows", int(inv_metrics.get("snapshot_rows") or 0), "int"),
        ("Change vs prior snapshot", f"{float(inv_metrics.get('value_change') or 0):,.2f} €", "good" if float(inv_metrics.get("value_change") or 0) >= 0 else "bad"),
        ("Change %", f"{float(inv_metrics.get('value_change_pct') or 0):.1%}", "good" if float(inv_metrics.get("value_change_pct") or 0) >= 0 else "bad"),
    ]
    for i, (label, value, kind) in enumerate(inv_cards):
        r = 87
        c = i * 3
        ws.merge_range(r, c, r, c + 1, label, fmt["card_label"])
        val_fmt = fmt["card_value_good"] if kind == "good" else (fmt["card_value_bad"] if kind == "bad" else fmt["card_value"])
        ws.merge_range(r + 1, c, r + 2, c + 1, value, val_fmt)
    by_date = investment_summaries.get("by_date", pd.DataFrame())
    latest_allocation = investment_summaries.get("latest_allocation", pd.DataFrame())
    if by_date is not None:
        insert_chart_image(ws, "A93", save_line_image(by_date, "Snapshot_Label", [("Total Investment Value", "Total_Market_Value_EUR", COLOR_COMPLEMENT)], "Investment Valuation Trend", "dashboard_investment_trend", width=5.5, height=2.5))
    if latest_allocation is not None:
        insert_chart_image(ws, "H93", save_pie_image(latest_allocation, "Product", "Market_Value_EUR", "Latest Investment Allocation", "dashboard_investment_allocation", width=4.2, height=2.5))
    ws.set_column("A:Q", 14)
    ws.set_row(0, 30)
    ws.set_row(1, 30)


def write_config_sheets(workbook: Any, df: pd.DataFrame, recurring_df: pd.DataFrame, validation_df: pd.DataFrame, rates_df: pd.DataFrame, fmt: dict[str, Any]):
    # Accounts
    ws = workbook.add_worksheet("Accounts")
    fill_background(ws, fmt["bg"], 50, 12)
    ws.merge_range("A1:I2", "Accounts Configuration", fmt["title"])
    configured_df = pd.DataFrame(CONFIGURED_OWN_ACCOUNTS, columns=ACCOUNT_CONFIG_COLUMNS)
    acc_df = configured_df.copy()
    if not df.empty:
        for idx, r in acc_df.iterrows():
            iban = normalize_text(r.get("IBAN_or_Account_Number"))
            matched = df.apply(lambda tx: default_own_iban_for_bank(tx.get("Source_Bank"), tx.get("Account_Name")) == iban, axis=1)
            acc_df.at[idx, "Detected_Row_Count"] = int(matched.sum())
    write_df_table(ws, acc_df, 4, 0, "AccountsTable", fmt, width_overrides={"Notes": 48, "Aliases": 32})
    ws.data_validation(5, 5, max(20, len(acc_df)+10), 5, {"validate": "list", "source": ["TRUE", "FALSE"]})

    # Categories
    ws = workbook.add_worksheet("Categories")
    fill_background(ws, fmt["bg"], 80, 10)
    ws.merge_range("A1:E2", "Editable Category Rules", fmt["title"])
    cats = pd.DataFrame(DEFAULT_CATEGORIES, columns=["Category", "Subcategory", "Category_Type", "Keywords", "Notes"])
    write_df_table(ws, cats, 4, 0, "CategoryRules", fmt, width_overrides={"Keywords": 42, "Notes": 48})

    # Currency rates
    ws = workbook.add_worksheet("Currency_Rates")
    fill_background(ws, fmt["bg"], 80, 10)
    ws.merge_range("A1:F2", "Currency Conversion Rates", fmt["title"])
    ws.write("A3", "Editable FX table. Manual rows override downloaded cache rows for the same currency/date. Rate_To_EUR = value of 1 From_Currency in EUR.", fmt["note"])
    rates_out = rates_df.copy() if rates_df is not None and not rates_df.empty else pd.DataFrame(columns=CURRENCY_RATE_COLUMNS)
    for col in CURRENCY_RATE_COLUMNS:
        if col not in rates_out.columns:
            rates_out[col] = ""
    rates_out = rates_out[CURRENCY_RATE_COLUMNS].copy()
    if rates_out.empty:
        rates_out = pd.DataFrame([{"Rate_Date": "", "From_Currency": "EUR", "To_Currency": "EUR", "Rate_To_EUR": 1.0, "Source": "Native EUR", "Notes": "Default identity conversion."}])
    used_rate_currencies = set(rates_out["From_Currency"].astype(str).str.upper())
    missing_currencies = sorted(set(df["Original_Currency"].astype(str).str.upper()) - {"EUR", "", "NAN"} - used_rate_currencies) if not df.empty else []
    if missing_currencies:
        placeholders = pd.DataFrame([{
            "Rate_Date": "",
            "From_Currency": cur,
            "To_Currency": "EUR",
            "Rate_To_EUR": "",
            "Source": "Manual input needed",
            "Notes": "Fill Rate_To_EUR and rebuild to convert existing non-EUR rows.",
        } for cur in missing_currencies])
        rates_out = pd.concat([rates_out, placeholders], ignore_index=True)
    write_df_table(ws, rates_out, 5, 0, "CurrencyRates", fmt, date_cols={"Rate_Date"}, width_overrides={"Source": 24, "Notes": 60})
    ws.data_validation(6, 1, 200, 1, {"validate": "list", "source": ["EUR", "USD", "CZK", "GBP", "HUF", "PLN", "CHF", "NOK", "SEK", "DKK"]})
    ws.data_validation(6, 2, 200, 2, {"validate": "list", "source": ["EUR"]})

    # Recurring
    ws = workbook.add_worksheet("Recurring")
    fill_background(ws, fmt["bg"], 80, 14)
    ws.merge_range("A1:L2", "Recurring Transactions", fmt["title"])
    if recurring_df.empty:
        recurring_df = pd.DataFrame([{c: "" for c in ["Recurring_Group_ID", "Counterparty_or_Description", "Category", "Category_Type", "Account", "Expected_Frequency", "Usual_Amount_EUR", "Occurrences", "First_Date", "Last_Date", "Confidence", "Manually_Editable_Notes"]}])
    write_df_table(ws, recurring_df, 4, 0, "RecurringTable", fmt, money_cols={"Usual_Amount_EUR"}, date_cols={"First_Date", "Last_Date"}, width_overrides={"Counterparty_or_Description": 28, "Manually_Editable_Notes": 42})

    # Validation
    ws = workbook.add_worksheet("Validation")
    fill_background(ws, fmt["bg"], 100, 8)
    ws.merge_range("A1:D2", "Validation Summary", fmt["title"])
    write_df_table(ws, validation_df, 4, 0, "ValidationTable", fmt, width_overrides={"Details": 80})
    # Conditional highlighting on Status column.
    ws.conditional_format(5, 1, len(validation_df) + 5, 1, {"type": "text", "criteria": "containing", "value": "Warning", "format": fmt["warning"]})
    ws.conditional_format(5, 1, len(validation_df) + 5, 1, {"type": "text", "criteria": "containing", "value": "Manual", "format": fmt["blue"]})


def write_raw_transactions(workbook: Any, df: pd.DataFrame, fmt: dict[str, Any]):
    ws = workbook.add_worksheet("Raw_Transactions")
    fill_background(ws, fmt["bg"], min(max(len(df) + 10, 40), 500), 42)
    ws.freeze_panes(1, 0)
    df_out = df.copy()
    for col in ["Booking_Date", "Value_Date"]:
        df_out[col] = pd.to_datetime(df_out[col], errors="coerce")
    money_cols = {"Original_Amount", "Amount_EUR", "Income_Amount", "Expense_Amount", "Balance_After"}
    date_cols = {"Booking_Date", "Value_Date", "FX_Rate_Date"}
    write_df_table(ws, df_out, 0, 0, "RawTransactions", fmt, money_cols=money_cols, date_cols=date_cols, width_overrides={"Description": 34, "Parser_Warning": 50, "Duplicate_Reason": 46, "Notes": 34, "Transaction_ID": 24, "FX_Conversion_Status": 28, "FX_Rate_Source": 24})
    # Conditional formatting for review columns.
    headers = list(df_out.columns)
    def col_idx(name):
        return headers.index(name) if name in headers else None
    for cname in ["Category", "Category_Confidence", "Is_Duplicate_Suspect", "Parser_Warning", "Is_Savings_Investment", "Is_Internal_Transfer"]:
        c = col_idx(cname)
        if c is not None:
            ws.conditional_format(1, c, len(df_out), c, {"type": "text", "criteria": "containing", "value": "Uncategorized", "format": fmt["warning"]})
            ws.conditional_format(1, c, len(df_out), c, {"type": "text", "criteria": "containing", "value": "True", "format": fmt["blue"]})
    c = col_idx("Category_Confidence")
    if c is not None:
        ws.conditional_format(1, c, len(df_out), c, {"type": "cell", "criteria": "<", "value": 0.5, "format": fmt["warning"]})


def write_investment_snapshots(workbook: Any, investment_df: pd.DataFrame, fmt: dict[str, Any]):
    ws = workbook.add_worksheet("Investment_Snapshots")
    fill_background(ws, fmt["bg"], min(max(len(investment_df) + 10, 40), 300), len(INVESTMENT_SNAPSHOT_COLUMNS) + 2)
    ws.freeze_panes(1, 0)
    df_out = investment_df.copy() if investment_df is not None else pd.DataFrame(columns=INVESTMENT_SNAPSHOT_COLUMNS)
    for col in INVESTMENT_SNAPSHOT_COLUMNS:
        if col not in df_out.columns:
            df_out[col] = ""
    df_out = df_out[INVESTMENT_SNAPSHOT_COLUMNS].copy()
    df_out["Snapshot_Date"] = pd.to_datetime(df_out["Snapshot_Date"], errors="coerce")
    money_cols = {"Market_Value_Original", "Market_Value_EUR", "Unit_Price"}
    date_cols = {"Snapshot_Date", "FX_Rate_Date"}
    write_df_table(
        ws,
        df_out,
        0,
        0,
        "InvestmentSnapshots",
        fmt,
        money_cols=money_cols,
        date_cols=date_cols,
        width_overrides={
            "Snapshot_ID": 24,
            "Source_File": 32,
            "Product_Name": 36,
            "Product_Type": 28,
            "ISIN_or_Product_ID": 18,
            "FX_Conversion_Status": 28,
            "FX_Rate_Source": 24,
            "Notes": 72,
            "Parser_Warning": 48,
        },
    )
    headers = list(df_out.columns)
    for cname in ["FX_Conversion_Status", "Parser_Warning"]:
        if cname in headers:
            c = headers.index(cname)
            ws.conditional_format(1, c, max(len(df_out), 1), c, {"type": "text", "criteria": "containing", "value": "Missing", "format": fmt["warning"]})
            ws.conditional_format(1, c, max(len(df_out), 1), c, {"type": "text", "criteria": "containing", "value": "differs", "format": fmt["warning"]})


def write_investment_dashboard(workbook: Any, investment_df: pd.DataFrame, investment_summaries: dict[str, pd.DataFrame], fmt: dict[str, Any]):
    ws = workbook.add_worksheet("Investment_Dashboard")
    fill_background(ws, fmt["bg"], 105, 20)
    ws.freeze_panes(4, 0)
    ws.merge_range("A1:Q2", "Investment / Savings Valuation Dashboard", fmt["title"])
    ws.write("A3", "Valuation snapshots are portfolio/holding values at a point in time. They are not transaction income, expenses, transfers, or savings contributions.", fmt["note"])

    metrics = latest_investment_metrics(investment_df, investment_summaries)
    latest_date = metrics.get("latest_date")
    latest_date_text = latest_date.strftime("%Y-%m-%d") if isinstance(latest_date, pd.Timestamp) and pd.notna(latest_date) else "—"
    missing_fx = int(investment_df["FX_Conversion_Status"].astype(str).str.contains("Missing FX rate", na=False).sum()) if investment_df is not None and not investment_df.empty else 0
    currencies = ", ".join(sorted(set(investment_df["Original_Currency"].astype(str).str.upper()) - {"", "NAN"})) if investment_df is not None and not investment_df.empty else "—"
    cards = [
        ("Latest total value", f"{float(metrics.get('latest_total') or 0):,.2f} €", "good"),
        ("Latest snapshot", latest_date_text, "text"),
        ("Products", int(metrics.get("product_count") or 0), "int"),
        ("Snapshot rows", int(metrics.get("snapshot_rows") or 0), "int"),
        ("Change vs prior", f"{float(metrics.get('value_change') or 0):,.2f} €", "good" if float(metrics.get("value_change") or 0) >= 0 else "bad"),
        ("FX missing", missing_fx, "bad" if missing_fx else "good"),
        ("Currencies", currencies, "text"),
    ]
    for i, (label, value, kind) in enumerate(cards):
        r = 5 + (i // 4) * 3
        c = (i % 4) * 4
        ws.merge_range(r, c, r, c + 2, label, fmt["card_label"])
        val_fmt = fmt["card_value_good"] if kind == "good" else (fmt["card_value_bad"] if kind == "bad" else fmt["card_value"])
        ws.merge_range(r + 1, c, r + 2, c + 2, value, val_fmt)

    by_date = investment_summaries.get("by_date", pd.DataFrame())
    latest_allocation = investment_summaries.get("latest_allocation", pd.DataFrame())
    by_product = investment_summaries.get("by_product", pd.DataFrame())
    product_by_date = investment_summaries.get("product_by_date", pd.DataFrame())

    insert_chart_image(ws, "A13", save_line_image(by_date, "Snapshot_Label", [("Total Investment Value", "Total_Market_Value_EUR", COLOR_COMPLEMENT)], "Total Investment Value Over Time", "investment_total_trend", width=5.8, height=2.7))
    insert_chart_image(ws, "I13", save_pie_image(latest_allocation, "Product", "Market_Value_EUR", "Latest Allocation by Product", "investment_latest_allocation", width=4.6, height=2.7))
    insert_chart_image(ws, "A31", save_column_image(latest_allocation, "Product", [("Market Value", "Market_Value_EUR", COLOR_SECONDARY)], "Latest Product Value", "investment_latest_product_value", width=5.8, height=2.6))

    ws.merge_range("A49:F49", "Investment Value by Snapshot Date", fmt["section"])
    by_date_table = by_date[["Snapshot_Label", "Total_Market_Value_EUR", "Value_Change_EUR", "Value_Change_Pct", "Snapshot_Row_Count"]].copy() if by_date is not None and not by_date.empty else pd.DataFrame(columns=["Snapshot_Label", "Total_Market_Value_EUR", "Value_Change_EUR", "Value_Change_Pct", "Snapshot_Row_Count"])
    write_df_table(
        ws,
        by_date_table,
        50,
        0,
        "InvestmentByDate",
        fmt,
        money_cols={"Total_Market_Value_EUR", "Value_Change_EUR"},
        pct_cols={"Value_Change_Pct"},
        width_overrides={"Snapshot_Label": 16, "Total_Market_Value_EUR": 20, "Value_Change_EUR": 18, "Value_Change_Pct": 16},
    )

    ws.merge_range("H49:M49", "Latest Product Allocation", fmt["section"])
    latest_table = latest_allocation.copy() if latest_allocation is not None and not latest_allocation.empty else pd.DataFrame(columns=["Product", "Market_Value_EUR", "Allocation"])
    write_df_table(
        ws,
        latest_table,
        50,
        7,
        "InvestmentLatestAllocation",
        fmt,
        money_cols={"Market_Value_EUR"},
        pct_cols={"Allocation"},
        width_overrides={"Product": 42, "Market_Value_EUR": 18, "Allocation": 14},
    )

    table_start = max(62 + len(by_date_table), 62 + len(latest_table), 68)
    ws.merge_range(table_start, 0, table_start, 6, "Product Value Summary", fmt["section"])
    product_table = by_product.copy() if by_product is not None and not by_product.empty else pd.DataFrame(columns=["Product", "Market_Value_EUR", "Latest_Market_Value_EUR", "Snapshots"])
    write_df_table(
        ws,
        product_table,
        table_start + 1,
        0,
        "InvestmentByProduct",
        fmt,
        money_cols={"Market_Value_EUR", "Latest_Market_Value_EUR"},
        width_overrides={"Product": 44, "Market_Value_EUR": 18, "Latest_Market_Value_EUR": 20},
    )

    ws.merge_range(table_start, 8, table_start, 14, "Product Value by Date", fmt["section"])
    product_date_table = product_by_date.copy() if product_by_date is not None and not product_by_date.empty else pd.DataFrame(columns=["Snapshot_Label", "Product", "Market_Value_EUR"])
    if "Snapshot_Date" in product_date_table.columns:
        product_date_table = product_date_table.drop(columns=["Snapshot_Date"])
    write_df_table(
        ws,
        product_date_table,
        table_start + 1,
        8,
        "InvestmentProductByDate",
        fmt,
        money_cols={"Market_Value_EUR"},
        width_overrides={"Snapshot_Label": 16, "Product": 42, "Market_Value_EUR": 18},
    )
    ws.set_column("A:Q", 14)


def year_month_summary(dfe: pd.DataFrame, year: int) -> pd.DataFrame:
    months = pd.DataFrame({"Month_Number": list(range(1, 13)), "Month_Name": [MONTH_NAMES[i] for i in range(1, 13)]})
    g = dfe[dfe["Year"] == year].groupby("Month_Number").agg(
        Income=("Effective_Income", "sum"),
        Expenses=("Effective_Expense", "sum"),
        Net_Cashflow=("Amount_EUR", lambda s: 0),
        Savings_Investment=("Savings_Investment_Amount", "sum"),
        Recurring_Expenses=("Recurring_Expense", "sum"),
        One_Time_Expenses=("One_Time_Expense", "sum"),
        Internal_Transfers=("Internal_Transfer_Amount", "sum"),
        Uncategorized=("Category", lambda s: int((s == "Uncategorized").sum())),
    ).reset_index()
    out = months.merge(g, on="Month_Number", how="left").fillna(0)
    out["Net_Cashflow"] = out["Income"] - out["Expenses"]
    out["Savings_Rate"] = out.apply(lambda r: r["Savings_Investment"] / r["Income"] if r["Income"] else 0, axis=1)
    out["Investment_Rate"] = out["Savings_Rate"]
    return out


def write_year_sheet(workbook: Any, df: pd.DataFrame, summaries: dict[str, pd.DataFrame], year: int, fmt: dict[str, Any]):
    ws = workbook.add_worksheet(str(year))
    fill_background(ws, fmt["bg"], 180, 22)
    ws.freeze_panes(24, 0)
    ws.merge_range("A1:Q2", f"{year} Finance Overview", fmt["title"])
    dfe = effective_flags(df)
    ydf = dfe[dfe["Year"] == year].copy()
    msum = year_month_summary(dfe, year)
    income = float(ydf["Effective_Income"].sum())
    expenses = float(ydf["Effective_Expense"].sum())
    savings = float(ydf["Savings_Investment_Amount"].sum())
    net = income - expenses
    month_count = 12
    biggest_category = calc_top_label_value(ydf[ydf["Effective_Expense"] > 0], "Category", "Effective_Expense")
    highest_exp_month = msum.loc[msum["Expenses"].idxmax()]
    highest_inc_month = msum.loc[msum["Income"].idxmax()]
    highest_sav_month = msum.loc[msum["Savings_Investment"].idxmax()]
    cards = [
        ("Yearly income", income, "money"),
        ("Yearly expenses", expenses, "money_bad"),
        ("Net cashflow", net, "money_good" if net >= 0 else "money_bad"),
        ("Savings rate", savings / income if income else 0, "pct"),
        ("Savings / investment", savings, "money_good"),
        ("Investment rate", savings / income if income else 0, "pct"),
        ("Average monthly income", income / month_count, "money"),
        ("Average monthly expenses", expenses / month_count, "money_bad"),
        ("Highest expense month", f"{highest_exp_month['Month_Name']} ({highest_exp_month['Expenses']:,.2f} €)", "text"),
        ("Highest income month", f"{highest_inc_month['Month_Name']} ({highest_inc_month['Income']:,.2f} €)", "text"),
        ("Highest savings month", f"{highest_sav_month['Month_Name']} ({highest_sav_month['Savings_Investment']:,.2f} €)", "text"),
        ("Biggest spending category", biggest_category, "text"),
        ("Recurring expenses", float(ydf["Recurring_Expense"].sum()), "money_bad"),
        ("One-time expenses", float(ydf["One_Time_Expense"].sum()), "money_bad"),
        ("Internal transfers", float(ydf["Internal_Transfer_Amount"].sum()), "money"),
        ("Uncategorized count", int((ydf["Category"] == "Uncategorized").sum()), "int"),
    ]
    for i, (label, value, kind) in enumerate(cards):
        r = 4 + (i // 4) * 3
        c = (i % 4) * 4
        ws.merge_range(r, c, r, c + 2, label, fmt["card_label"])
        val_fmt = fmt["card_value_good"] if kind.endswith("good") else (fmt["card_value_bad"] if kind.endswith("bad") else fmt["card_value"])
        display = f"{value:,.2f} €" if kind.startswith("money") and isinstance(value, (int, float)) else (f"{value:.1%}" if kind == "pct" else value)
        ws.merge_range(r + 1, c, r + 2, c + 2, display, val_fmt)

    # Year-local chart data placed far right; charts read from same sheet.
    data_col = 24
    row = 0
    chart_ranges = {}
    def local_table(name: str, dfx: pd.DataFrame):
        nonlocal row
        if dfx.empty:
            dfx = pd.DataFrame({dfx.columns[0] if len(dfx.columns) else "Label": ["None"], dfx.columns[1] if len(dfx.columns) > 1 else "Amount": [0]})
        write_df_table(ws, dfx, row, data_col, f"Y{year}_{name}"[:31], fmt)
        chart_ranges[name] = (row, data_col, row + len(dfx), data_col + len(dfx.columns) - 1)
        row += len(dfx) + 3
    local_table("ExpCat", ydf[ydf["Effective_Expense"] > 0].groupby("Category")["Effective_Expense"].sum().reset_index().sort_values("Effective_Expense", ascending=False).head(10))
    local_table("IncCat", ydf[ydf["Effective_Income"] > 0].groupby("Category")["Effective_Income"].sum().reset_index().sort_values("Effective_Income", ascending=False).head(10))
    local_table("ExpAcc", ydf[ydf["Effective_Expense"] > 0].groupby("Account_Name")["Effective_Expense"].sum().reset_index().sort_values("Effective_Expense", ascending=False).head(10))
    local_table("RecVs", pd.DataFrame({"Type": ["Recurring Expenses", "One-Time Expenses"], "Amount": [ydf["Recurring_Expense"].sum(), ydf["One_Time_Expense"].sum()]}))
    sav = ydf[ydf["Savings_Investment_Amount"] > 0].groupby("Savings_Investment_Type")["Savings_Investment_Amount"].sum().reset_index()
    if sav.empty:
        sav = pd.DataFrame({"Savings_Investment_Type": ["No Savings / Investment Detected"], "Savings_Investment_Amount": [0]})
    local_table("SavType", sav)
    mchart = msum[["Month_Name", "Income", "Expenses", "Savings_Investment", "Net_Cashflow"]].copy()
    local_table("Monthly", mchart)
    ws.set_column(data_col, data_col + 8, None, None, {"hidden": True})

    # Styled chart images for this year.
    insert_chart_image(ws, "A18", save_pie_image(ydf[ydf["Effective_Expense"] > 0].groupby("Category")["Effective_Expense"].sum().reset_index().sort_values("Effective_Expense", ascending=False).head(10), "Category", "Effective_Expense", "Yearly Expenses by Category", f"{year}_expense_category"))
    insert_chart_image(ws, "G18", save_pie_image(ydf[ydf["Effective_Income"] > 0].groupby("Category")["Effective_Income"].sum().reset_index().sort_values("Effective_Income", ascending=False).head(10), "Category", "Effective_Income", "Yearly Income by Category", f"{year}_income_category"))
    insert_chart_image(ws, "M18", save_pie_image(ydf[ydf["Effective_Expense"] > 0].groupby("Account_Name")["Effective_Expense"].sum().reset_index().sort_values("Effective_Expense", ascending=False).head(10), "Account_Name", "Effective_Expense", "Yearly Expenses by Account", f"{year}_expense_account"))
    insert_chart_image(ws, "A33", save_pie_image(pd.DataFrame({"Type": ["Recurring Expenses", "One-Time Expenses"], "Amount": [ydf["Recurring_Expense"].sum(), ydf["One_Time_Expense"].sum()]}), "Type", "Amount", "Recurring vs One-Time", f"{year}_recurring_vs_one_time"))
    insert_chart_image(ws, "G33", save_pie_image(sav, "Savings_Investment_Type", "Savings_Investment_Amount", "Savings / Investments", f"{year}_savings_type"))
    insert_chart_image(ws, "M33", save_column_image(mchart, "Month_Name", [("Income", "Income", COLOR_COMPLEMENT), ("Expenses", "Expenses", COLOR_PRIMARY)], "Monthly Income vs Expenses", f"{year}_income_expenses"))
    insert_chart_image(ws, "A49", save_line_image(mchart, "Month_Name", [("Net Cashflow", "Net_Cashflow", COLOR_COMPLEMENT)], "Monthly Net Cashflow", f"{year}_net_cashflow"))
    insert_chart_image(ws, "G49", save_line_image(mchart, "Month_Name", [("Savings / Investment", "Savings_Investment", COLOR_SECONDARY)], "Monthly Savings / Investment", f"{year}_savings_trend"))

    # Monthly summary block
    ws.merge_range("A65:L65", "Monthly Breakdown", fmt["section"])
    write_df_table(ws, msum[["Month_Name", "Income", "Expenses", "Net_Cashflow", "Savings_Investment", "Savings_Rate", "Recurring_Expenses", "One_Time_Expenses", "Internal_Transfers", "Uncategorized"]], 66, 0, f"Y{year}Monthly", fmt, money_cols={"Income", "Expenses", "Net_Cashflow", "Savings_Investment", "Recurring_Expenses", "One_Time_Expenses", "Internal_Transfers"})

    # Details per month, largest transactions and categories
    base = 82
    for m in range(1, 13):
        block_row = base + (m - 1) * 7
        month_name = MONTH_NAMES[m]
        ms = msum[msum["Month_Number"] == m].iloc[0]
        ws.merge_range(block_row, 0, block_row, 5, f"{month_name}: summary", fmt["section"])
        mini = [
            ["Income", ms["Income"], "Expenses", ms["Expenses"], "Net", ms["Net_Cashflow"]],
            ["Savings / Investment", ms["Savings_Investment"], "Savings Rate", ms["Savings_Rate"], "Uncategorized", ms["Uncategorized"]],
        ]
        for rr, values in enumerate(mini, start=block_row + 1):
            for cc, value in enumerate(values):
                ws.write(rr, cc, value, fmt["money"] if isinstance(value, (int, float)) and cc % 2 == 1 else fmt["table"])
        mt = ydf[ydf["Month_Number"] == m].copy()
        largest = mt.reindex(mt["Expense_Amount"].abs().sort_values(ascending=False).index).head(3)
        ws.merge_range(block_row, 7, block_row, 11, "Largest transactions", fmt["section"])
        if not largest.empty:
            for rr, (_, tr) in enumerate(largest.iterrows(), start=block_row + 1):
                ws.write(rr, 7, tr["Booking_Date"].strftime("%Y-%m-%d") if pd.notna(tr["Booking_Date"]) else "", fmt["table"])
                ws.write(rr, 8, tr["Description"], fmt["table"])
                ws.write(rr, 10, tr["Amount_EUR"], fmt["money"])
                ws.write(rr, 11, tr["Category"], fmt["table"])
        cat = mt[mt["Effective_Expense"] > 0].groupby("Category")["Effective_Expense"].sum().sort_values(ascending=False).head(3)
        ws.merge_range(block_row, 13, block_row, 16, "Top categories", fmt["section"])
        if not cat.empty:
            for rr, (cat_name, amount) in enumerate(cat.items(), start=block_row + 1):
                ws.write(rr, 13, cat_name, fmt["table"])
                ws.write(rr, 15, amount, fmt["money"])

    # Detailed transaction table
    detail_start = base + 12 * 7 + 4
    ws.merge_range(detail_start, 0, detail_start, 16, "Detailed Transactions", fmt["section"])
    cols = ["Transaction_ID", "Booking_Date", "Description", "Counterparty_Name", "Amount_EUR", "Direction", "Category", "Subcategory", "Category_Type", "Is_Recurring", "Is_Internal_Transfer", "Is_Ignored", "Parser_Warning"]
    detail_df = ydf[cols].sort_values(["Booking_Date", "Description"]).copy()
    write_df_table(ws, detail_df, detail_start + 1, 0, f"Y{year}Transactions", fmt, money_cols={"Amount_EUR"}, date_cols={"Booking_Date"}, width_overrides={"Description": 36, "Parser_Warning": 50})
    ws.set_column("A:Q", 14)


def define_names(workbook: Any):
    lambdas = {
        "TX_YEAR": "=LAMBDA(d,YEAR(d))",
        "TX_MONTH": "=LAMBDA(d,MONTH(d))",
        "TX_DIRECTION": '=LAMBDA(amount,IF(amount>0,"Income",IF(amount<0,"Expense","Zero/Unknown")))',
        "TX_IS_INCOME": '=LAMBDA(amount,is_transfer,is_ignored,category_type,AND(amount>0,NOT(is_transfer),NOT(is_ignored),category_type<>"savings/investment"))',
        "TX_IS_EXPENSE": '=LAMBDA(amount,is_transfer,is_ignored,category_type,AND(amount<0,NOT(is_transfer),NOT(is_ignored),category_type<>"savings/investment",category_type<>"income"))',
        "TX_IS_SAVINGS_INVESTMENT": '=LAMBDA(category_type,category_type="savings/investment")',
        "TX_NET": "=LAMBDA(amount,is_transfer,is_ignored,IF(OR(is_transfer,is_ignored),0,amount))",
        "TX_SAVINGS_RATE": "=LAMBDA(income,expenses,IFERROR((income-expenses)/income,0))",
        "TX_INVESTMENT_RATE": "=LAMBDA(income,savings_investments,IFERROR(savings_investments/income,0))",
        "TX_IS_SPIKE": "=LAMBDA(value,average,IFERROR(ABS(value)>ABS(average)*1.8,FALSE))",
        "TX_NORMALIZE_TEXT": "=LAMBDA(text,LOWER(TRIM(text)))",
    }
    for name, formula in lambdas.items():
        try:
            workbook.define_name(name, formula)
        except Exception:
            pass


def build_workbook(
    df: pd.DataFrame,
    recurring_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    rates_df: pd.DataFrame,
    output: Path,
    investment_df: pd.DataFrame | None = None,
):
    output.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="yyyy-mm-dd", date_format="yyyy-mm-dd") as writer:
        workbook = writer.book
        fmt = setup_workbook_formats(workbook)
        define_names(workbook)
        # We control sheet order by creating in required order.
        summaries = make_summary_data(df)
        investment_df = investment_df if investment_df is not None else pd.DataFrame(columns=INVESTMENT_SNAPSHOT_COLUMNS)
        investment_summaries = make_investment_summary_data(investment_df)
        chart_ranges = write_chart_data(workbook, summaries)
        # Need Dashboard first in final workbook, but Chart_Data was created first to get ranges. Move by creating Dashboard now and set tab order via workbook.worksheets_objs reorder unsupported in public? xlsxwriter stores worksheets_objs.
        write_dashboard(workbook, df, validation_df, summaries, chart_ranges, fmt, investment_df, investment_summaries)
        write_raw_transactions(workbook, df, fmt)
        write_investment_snapshots(workbook, investment_df, fmt)
        write_investment_dashboard(workbook, investment_df, investment_summaries, fmt)
        write_config_sheets(workbook, df, recurring_df, validation_df, rates_df, fmt)
        years = sorted([int(y) for y in pd.to_numeric(df["Year"], errors="coerce").dropna().unique()])
        for year in years:
            write_year_sheet(workbook, df, summaries, year, fmt)
        # Reorder sheets so Dashboard first and Chart_Data hidden last.
        try:
            names_order = ["Dashboard", "Raw_Transactions", "Investment_Snapshots", "Investment_Dashboard", "Accounts", "Categories", "Currency_Rates", "Recurring"] + [str(y) for y in years] + ["Validation", "Chart_Data"]
            obj_by_name = {ws.get_name(): ws for ws in workbook.worksheets_objs}
            workbook.worksheets_objs = [obj_by_name[n] for n in names_order if n in obj_by_name]
        except Exception:
            pass
        workbook.set_calc_mode("auto")
        workbook.set_properties({
            "title": "Personal Finance Analysis",
            "subject": "Reusable finance-analysis workbook generated from bank exports",
            "author": "GPT-5.5 Heavy Thinking / Codex pipeline",
            "comments": "Generated locally; no external financial data upload required.",
        })


def write_readme(package_dir: Path):
    # Retained for backward-compatible imports; project documentation is maintained as tracked files.
    return None


def write_requirements(package_dir: Path):
    # Retained for backward-compatible imports; requirements.txt is maintained as a tracked file.
    return None


def _format_investment_skips_for_summary(investment_reports: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for report in investment_reports:
        skipped = int(parse_amount(report.get("Skipped_Rows")) or 0)
        if skipped:
            parts.append(f"{Path(str(report.get('File_Path') or '')).name}: {report.get('Skipped_Reasons')}")
    return "; ".join(parts) if parts else "None"


def write_validation_summary(
    report_path: Path,
    df: pd.DataFrame,
    validation_df: pd.DataFrame,
    warnings: list[str],
    output: Path,
    rates_df: pd.DataFrame | None = None,
    fx_report: dict[str, Any] | None = None,
    source_reports: list[dict[str, Any]] | None = None,
    investment_df: pd.DataFrame | None = None,
    investment_reports: list[dict[str, Any]] | None = None,
):
    non_eur_count = int(df["Original_Currency"].astype(str).str.upper().ne("EUR").sum()) if not df.empty else 0
    converted_fx_count = int(df["FX_Conversion_Status"].astype(str).str.contains("Converted using historical FX rate|Latest rate used - not historical|Converted using Currency_Rates", regex=True, na=False).sum()) if not df.empty else 0
    missing_fx_count = int(df["FX_Conversion_Status"].astype(str).str.contains("Missing FX rate", na=False).sum()) if not df.empty else 0
    transfer_group_count = int(df.loc[df["Is_Internal_Transfer"], "Transfer_Group_ID"].replace("", pd.NA).dropna().nunique()) if not df.empty else 0
    recurring_group_count = int(df.loc[df["Is_Recurring"], "Recurring_Group_ID"].replace("", pd.NA).dropna().nunique()) if not df.empty else 0
    uncategorized_count = int((df["Category"] == "Uncategorized").sum()) if not df.empty else 0
    duplicate_suspect_count = int(df["Is_Duplicate_Suspect"].sum()) if not df.empty else 0
    internal_transfer_count = int(df["Is_Internal_Transfer"].sum()) if not df.empty else 0
    savings_investment_count = int(df["Is_Savings_Investment"].sum()) if not df.empty else 0
    duplicate_reason_count = int(df["Duplicate_Reason"].astype(str).str.strip().ne("").sum()) if not df.empty and "Duplicate_Reason" in df.columns else 0
    balance_warning_count = int(df["Balance_After"].replace('', pd.NA).isna().sum()) if not df.empty else 0
    ambiguous_transfer_mask = df["Notes"].astype(str).str.contains("Transfer-like row left for manual review", na=False) if not df.empty and "Notes" in df.columns else pd.Series(False, index=df.index)
    ambiguous_transfer_count = int(ambiguous_transfer_mask.sum())
    uncategorized_examples = format_review_examples(df, df["Category"] == "Uncategorized") if not df.empty else "None"
    transfer_examples = format_review_examples(df, ambiguous_transfer_mask) if not df.empty else "None"
    recurring_warning = next((w for w in warnings if "recurring-like groups were left unflagged" in w), "")
    fx_report = fx_report or {}
    download_failures = fx_report.get("download_failures") or []
    investment_df = investment_df if investment_df is not None else pd.DataFrame(columns=INVESTMENT_SNAPSHOT_COLUMNS)
    investment_reports = investment_reports or []
    inv_summaries = make_investment_summary_data(investment_df)
    inv_metrics = latest_investment_metrics(investment_df, inv_summaries)
    if investment_df.empty:
        inv_date_range = "none"
        inv_currencies = "none"
        inv_missing_fx = 0
        inv_warning_rows = 0
    else:
        inv_dates = pd.to_datetime(investment_df["Snapshot_Date"], errors="coerce").dropna()
        inv_date_range = f"{inv_dates.min().date()} to {inv_dates.max().date()}" if not inv_dates.empty else "none"
        inv_currencies = ", ".join(sorted(set(investment_df["Original_Currency"].astype(str).str.upper()) - {"", "NAN"})) or "none"
        inv_missing_fx = int(investment_df["FX_Conversion_Status"].astype(str).str.contains("Missing FX rate", na=False).sum())
        inv_warning_rows = int(investment_df["Parser_Warning"].astype(str).str.strip().ne("").sum())
    latest_inv_date = inv_metrics.get("latest_date")
    latest_inv_date_text = latest_inv_date.strftime("%Y-%m-%d") if isinstance(latest_inv_date, pd.Timestamp) and pd.notna(latest_inv_date) else "none"
    summary = [
        "# Validation Summary",
        "",
        f"Generated workbook: `{output.name}`",
        f"Parsed normalized rows: {len(df)}",
        f"Years found: {', '.join(str(int(y)) for y in sorted(pd.to_numeric(df['Year'], errors='coerce').dropna().unique())) if not df.empty else 'none'}",
        f"Uncategorized rows: {uncategorized_count}",
        f"Duplicate suspects: {duplicate_suspect_count}",
        f"Duplicate reasons populated: {duplicate_reason_count}",
        f"Internal transfers detected: {internal_transfer_count}",
        f"Internal transfer groups: {transfer_group_count}",
        f"Configured own accounts: {len(CONFIGURED_OWN_ACCOUNTS)}",
        f"Savings/investment rows detected: {savings_investment_count}",
        f"Recurring groups detected: {recurring_group_count}",
        f"Parser warnings: {len(warnings)}",
        f"Balance availability warnings: {balance_warning_count}",
        f"Currency rates loaded: {len(rates_df) if rates_df is not None else 0}",
        f"Total non-EUR rows: {non_eur_count}",
        f"Converted non-EUR rows: {converted_fx_count}",
        f"Missing FX rows: {missing_fx_count}",
        f"FX provider: {normalize_text(fx_report.get('provider')) or FX_PROVIDER_FRANKFURTER}",
        f"FX mode: {normalize_text(fx_report.get('mode')) or 'historical'}",
        f"FX cache path: `{normalize_text(fx_report.get('cache_path')) or str((Path('cache') / FX_CACHE_FILENAME))}`",
        f"FX downloaded rates this run: {int(fx_report.get('downloaded_rates', 0) or 0)}",
        f"FX download failures: {len(download_failures)}",
        f"Investment source files processed: {len(investment_reports)}",
        f"Investment snapshot rows parsed: {len(investment_df)}",
        f"Investment snapshot date range: {inv_date_range}",
        f"Investment product count: {int(inv_metrics.get('product_count') or 0)}",
        f"Latest investment value: {float(inv_metrics.get('latest_total') or 0):,.2f} EUR",
        f"Latest investment snapshot date: {latest_inv_date_text}",
        f"Investment currencies found: {inv_currencies}",
        f"Investment missing FX rows: {inv_missing_fx}",
        f"Investment parser warning rows: {inv_warning_rows}",
        "",
        "## Source file import table",
        "",
        "| Bank | File path | Detected format | Source apparent transaction rows | Parsed rows | Skipped rows | Skipped reasons | Date range | Currencies | Parser warnings |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    def md_cell(value: Any) -> str:
        text = normalize_text(value)
        return text.replace("|", "\\|") if text else ""

    for report in source_reports or []:
        summary.append(
            "| "
            + " | ".join([
                md_cell(report.get("Bank")),
                f"`{md_cell(report.get('File_Path'))}`",
                md_cell(report.get("Detected_Format")),
                md_cell(report.get("Source_Apparent_Transaction_Rows")),
                md_cell(report.get("Parsed_Rows")),
                md_cell(report.get("Skipped_Rows")),
                md_cell(report.get("Skipped_Reasons")),
                md_cell(report.get("Date_Range")),
                md_cell(report.get("Currencies")),
                md_cell(report.get("Parser_Warnings")),
            ])
            + " |"
        )
    summary += [
        "",
        "## Investment snapshot import table",
        "",
        "| Bank | File path | Detected format | Apparent snapshot rows | Parsed rows | Skipped rows | Skipped reasons | Date range | Products | Currencies | Parser warnings |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for report in investment_reports:
        summary.append(
            "| "
            + " | ".join([
                md_cell(report.get("Bank")),
                f"`{md_cell(report.get('File_Path'))}`",
                md_cell(report.get("Detected_Format")),
                md_cell(report.get("Source_Apparent_Snapshot_Rows")),
                md_cell(report.get("Parsed_Rows")),
                md_cell(report.get("Skipped_Rows")),
                md_cell(report.get("Skipped_Reasons")),
                md_cell(report.get("Date_Range")),
                f"{md_cell(report.get('Product_Count'))}: {md_cell(report.get('Products'))}",
                md_cell(report.get("Currencies")),
                md_cell(report.get("Parser_Warnings")),
            ])
            + " |"
        )
    if not investment_reports:
        summary.append("|  |  | No investment snapshot files processed | 0 | 0 | 0 |  |  |  |  |  |")
    summary += [
        "",
        "## Investment valuation summary",
        "",
        f"- Investment source files processed: {len(investment_reports)}",
        f"- Apparent snapshot rows: {sum(int(parse_amount(r.get('Source_Apparent_Snapshot_Rows')) or 0) for r in investment_reports)}",
        f"- Parsed snapshot rows: {len(investment_df)}",
        f"- Skipped rows and reasons: {_format_investment_skips_for_summary(investment_reports)}",
        f"- Snapshot date range: {inv_date_range}",
        f"- Product count: {int(inv_metrics.get('product_count') or 0)}",
        f"- Latest total investment value: {float(inv_metrics.get('latest_total') or 0):,.2f} EUR",
        f"- Latest snapshot date: {latest_inv_date_text}",
        f"- Currencies found: {inv_currencies}",
        f"- FX conversion status: missing FX rows {inv_missing_fx}; rates loaded {len(rates_df) if rates_df is not None else 0}",
        f"- Warning/manual-review items: {inv_warning_rows} parser-warning rows; review source PDF notes and any missing product identifiers.",
    ]
    summary += [
        "",
        "## Checks performed",
        "",
    ]
    for _, r in validation_df.iterrows():
        summary.append(f"- **{r['Check']}** — {r['Status']}; count: {r['Count']}; {r['Details']}")
    if warnings:
        summary += ["", "## Parser warnings / assumptions", ""]
        summary += [f"- {w}" for w in warnings]
    summary += [
        "",
        "## Final cleanup pass",
        "",
        f"- Transaction rows: {len(df)}",
        f"- Investment snapshot rows: {len(investment_df)}",
        f"- Uncategorized rows before/after: {FINAL_CLEANUP_BASELINE['uncategorized_rows']} -> {uncategorized_count}",
        f"- Duplicate suspects before/after: {FINAL_CLEANUP_BASELINE['duplicate_suspects']} -> {duplicate_suspect_count}",
        f"- Internal transfer rows/groups: {internal_transfer_count} rows / {transfer_group_count} groups",
        f"- Savings/investment transaction rows: {savings_investment_count}",
        f"- Recurring groups: {recurring_group_count}",
        f"- FX status: {missing_fx_count} missing FX rows; {converted_fx_count} converted non-EUR rows; provider {normalize_text(fx_report.get('provider')) or FX_PROVIDER_FRANKFURTER}; mode {normalize_text(fx_report.get('mode')) or 'historical'}",
        f"- Source-file imports: {sum(int(parse_amount(r.get('Parsed_Rows')) or 0) for r in source_reports or [])} parsed rows across {len(source_reports or [])} bank source files; see the source-file import table above.",
        f"- Investment snapshots: {len(investment_df)} rows, {inv_date_range}, latest value {float(inv_metrics.get('latest_total') or 0):,.2f} EUR on {latest_inv_date_text}; see the investment snapshot table above.",
        f"- Remaining uncategorized review: {uncategorized_count} rows. Main groups: {uncategorized_examples}",
        f"- Remaining transfer review: {ambiguous_transfer_count} transfer-like rows left manual. Main groups: {transfer_examples}",
        f"- Remaining recurring review: {recurring_warning or 'No recurring-like warning emitted.'}",
        f"- Balance availability warnings: {balance_warning_count}; balances are not backfilled when the source export does not provide reliable post-transaction balances.",
        "- Intentionally left unresolved: generic person-to-person transfers, generic payment processors without merchant detail, unclear bank-transfer references, and one-off merchants with weak context remain uncategorized/manual-review rather than receiving low-confidence categories.",
    ]
    summary += [
        "",
        "## Manual review still recommended",
        "",
        f"- Keep `Accounts` updated if you open or close accounts; the current configured own account list contains {len(CONFIGURED_OWN_ACCOUNTS)} rows.",
        "- Review any rows still marked `Missing FX rate`; add a dated manual rate in `config/currency_rates.csv` if the public provider has no rate.",
        "- Review rows categorized as `Uncategorized` or with `Category_Confidence < 0.50`.",
        "- Review duplicate suspects if any remain; identical card payments are not flagged without overlapping-file, repeated-reference, or repeated-balance evidence.",
        "- Balance availability depends on the source export layout; rows without `Balance_After` are preserved and flagged rather than backfilled.",
        "- Review `Investment_Snapshots.Parser_Warning` and source PDF references if a future snapshot has missing product identifiers, missing FX, or a value mismatch.",
    ]
    if download_failures:
        summary += ["", "## FX download failures", ""]
        summary += [f"- {failure}" for failure in download_failures]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(summary), encoding="utf-8")


def validate_workbook_file(path: Path) -> list[str]:
    warnings: list[str] = []
    if not path.exists():
        return [f"Workbook was not created: {path}"]
    if load_workbook is None:
        return ["openpyxl unavailable for workbook validation"]
    try:
        wb = load_workbook(path, data_only=False, read_only=True)
        required = ["Dashboard", "Raw_Transactions", "Investment_Snapshots", "Investment_Dashboard", "Accounts", "Categories", "Recurring", "Validation"]
        for s in required:
            if s not in wb.sheetnames:
                warnings.append(f"Missing required sheet: {s}")
        formula_errors = ["#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"]
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str) and any(err in cell.value for err in formula_errors):
                        warnings.append(f"Formula/error token found in {ws.title}!{cell.coordinate}: {cell.value}")
                        if len(warnings) > 50:
                            return warnings
    except Exception as exc:
        warnings.append(f"Workbook validation failed: {exc}")
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a styled personal finance analysis workbook from bank exports.")
    parser.add_argument("--input", default=None, help="Input folder containing bank export subfolders")
    parser.add_argument("--output", default=None, help="Output .xlsx workbook path")
    parser.add_argument("--accounts", default=None, help="Private account config CSV path")
    parser.add_argument("--categories", default=None, help="Private category rules CSV path")
    parser.add_argument("--currency-rates", default=None, help="Manual currency-rate CSV/XLSX path")
    parser.add_argument("--cache", default=None, help="FX cache CSV path")
    parser.add_argument("--report", default=None, help="Validation report markdown path")
    parser.add_argument("--settings", default="config/settings.yaml", help="Optional YAML settings path")
    parser.add_argument("--package-dir", default=None, help="Deprecated; retained for CLI compatibility")
    parser.add_argument("--no-fx-download", default=None, action="store_true", help="Disable external FX API calls and use only manual/cache rates")
    parser.add_argument("--fx-provider", default=None, choices=[FX_PROVIDER_FRANKFURTER], help="FX provider for automatic historical rates")
    parser.add_argument("--fx-mode", default=None, choices=["historical", "latest"], help="FX conversion mode. Historical uses transaction-date rates by default.")
    args = parser.parse_args(argv)

    settings_path = resolve_configured_path(args.settings, from_cli=True)
    settings, settings_warnings = load_settings_file(settings_path)

    input_root = resolve_arg_path(args, settings, "input", "input")
    output = resolve_arg_path(args, settings, "output", "output")
    accounts_path = resolve_arg_path(args, settings, "accounts", "accounts")
    categories_path = resolve_arg_path(args, settings, "categories", "categories")
    currency_rates_path = resolve_arg_path(args, settings, "currency_rates", "currency_rates")
    cache_path = resolve_arg_path(args, settings, "cache", "cache")
    report_path = resolve_arg_path(args, settings, "report", "report")
    fx_provider = normalize_text(resolve_arg_value(args, settings, "fx_provider", "fx", "provider", FX_PROVIDER_FRANKFURTER)) or FX_PROVIDER_FRANKFURTER
    fx_mode = normalize_text(resolve_arg_value(args, settings, "fx_mode", "fx", "mode", "historical")) or "historical"
    no_fx_download = args.no_fx_download if args.no_fx_download is not None else parse_bool(settings_get(settings, "fx", "no_download", False), False)

    accounts, account_warnings = load_accounts_config(accounts_path)
    set_configured_own_accounts(accounts)
    category_rows, category_warnings = load_categories_config(categories_path)
    if category_rows:
        set_category_rules(category_rows)

    manual_rates_df, rate_warnings = discover_currency_rates(currency_rates_path)
    cache_df, cache_path, cache_warnings = load_fx_cache(cache_path)
    df, parse_warnings, source_reports = discover_transactions(input_root)
    investment_df, investment_parse_warnings, investment_reports = discover_investment_snapshots(input_root)
    fx_request_df = combined_fx_request_frame(df, investment_df)
    rates_df, cache_df, fx_report, fx_warnings = fetch_missing_fx_rates(
        fx_request_df,
        manual_rates_df,
        cache_df,
        cache_path,
        allow_download=not no_fx_download,
        provider=fx_provider,
        fx_mode=fx_mode,
    )
    df, recurring_df, process_warnings = postprocess_transactions(df, rates_df, fx_mode=fx_mode)
    investment_df, investment_process_warnings = postprocess_investment_snapshots(investment_df, rates_df, fx_mode=fx_mode)
    warnings = (
        settings_warnings
        + account_warnings
        + category_warnings
        + rate_warnings
        + cache_warnings
        + fx_warnings
        + parse_warnings
        + investment_parse_warnings
        + process_warnings
        + investment_process_warnings
    )
    validation_df = build_validation(df, warnings, input_root, rates_df, fx_report, source_reports, investment_df, investment_reports)
    build_workbook(df, recurring_df, validation_df, rates_df, output, investment_df)
    workbook_warnings = validate_workbook_file(output)
    if workbook_warnings:
        warnings.extend(workbook_warnings)
        validation_df = build_validation(df, warnings, input_root, rates_df, fx_report, source_reports, investment_df, investment_reports)
    write_validation_summary(report_path, df, validation_df, warnings, output, rates_df, fx_report, source_reports, investment_df, investment_reports)
    investment_summaries = make_investment_summary_data(investment_df)
    investment_metrics = latest_investment_metrics(investment_df, investment_summaries)
    inv_dates = pd.to_datetime(investment_df["Snapshot_Date"], errors="coerce").dropna() if not investment_df.empty else pd.Series(dtype="datetime64[ns]")
    print(json.dumps({
        "output": str(output),
        "report": str(report_path),
        "rows": int(len(df)),
        "years": [int(y) for y in sorted(pd.to_numeric(df["Year"], errors="coerce").dropna().unique())] if not df.empty else [],
        "investment_snapshot_rows": int(len(investment_df)),
        "investment_snapshot_date_range": f"{inv_dates.min().date()} to {inv_dates.max().date()}" if not inv_dates.empty else "",
        "investment_latest_value_eur": round(float(investment_metrics.get("latest_total") or 0), 2),
        "investment_latest_snapshot_date": investment_metrics.get("latest_date").strftime("%Y-%m-%d") if isinstance(investment_metrics.get("latest_date"), pd.Timestamp) and pd.notna(investment_metrics.get("latest_date")) else "",
        "investment_product_count": int(investment_metrics.get("product_count") or 0),
        "investment_missing_fx_rates": int(investment_df["FX_Conversion_Status"].astype(str).str.contains("Missing FX rate", na=False).sum()) if not investment_df.empty else 0,
        "currency_rates": int(len(rates_df)),
        "non_eur_rows": int(df["Original_Currency"].astype(str).str.upper().ne("EUR").sum()) if not df.empty else 0,
        "missing_fx_rates": int(df["FX_Conversion_Status"].astype(str).str.contains("Missing FX rate", na=False).sum()) if not df.empty else 0,
        "converted_non_eur_rows": int(df["FX_Conversion_Status"].astype(str).str.contains("Converted using historical FX rate|Latest rate used - not historical|Converted using Currency_Rates", regex=True, na=False).sum()) if not df.empty else 0,
        "fx_provider": fx_provider,
        "fx_mode": fx_mode,
        "fx_cache": str(cache_path),
        "fx_downloaded_rates": int(fx_report.get("downloaded_rates", 0) or 0),
        "fx_download_failures": fx_report.get("download_failures", []),
        "warnings": warnings,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
