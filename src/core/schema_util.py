"""
Centralizes normalization logic and lookup tables (e.g. tax type maps).
"""

import pandas as pd

# ───────────────────────────────────────────────────────────────
# ENUM VALIDATION
# ───────────────────────────────────────────────────────────────

VALID_ENUMS = {
    'filing_status': {'single', 'married', 'head'},

    # Source types (source of funds)
    'source_type': {
        'inc_fers', 'inc_ord', 'inc_ssa',
        'ira', 'ira_inherited', 'tsp',
        'brokerage', 
        'roth', 'roth_inherited',
    },

    # Withdrawal event types (semantic classification)
    'wd_type': {
        'inc_ssa', 'inc_fers', 'inc_ord',
        'ira_rmd', 'ira_ord', 'ira_early',
        'brokerage_sale',
        'roth',
        'none', 'synthetic', 'rollover', 'transfer'
    },
}

VALID_FILING_STATUS = VALID_ENUMS['filing_status']
VALID_SOURCE_TYPE = VALID_ENUMS['source_type']
VALID_WD_TYPE = VALID_ENUMS['wd_type']

# ───────────────────────────────────────────────────────────────
# SOURCE → TAX CATEGORY LOOKUP
# (This is the only tax‑type lookup we keep)
# ───────────────────────────────────────────────────────────────

LKUP_SOURCE_TAX_TYPE = pd.DataFrame({
    'source_type': [
        'inc_fers', 'inc_ord', 'inc_ssa',
        'brokerage',
        'ira', 'ira_inherited', 'tsp',
        'roth', 'roth_inherited'
    ],
    'source_tax_type': [
        'taxable', 'taxable', 'taxable',
        'taxable',
        'deferred', 'deferred', 'deferred',
        'exempt', 'exempt'
    ]
})

SOURCE_TAX_TYPE_MAP = dict(zip(
    LKUP_SOURCE_TAX_TYPE['source_type'],
    LKUP_SOURCE_TAX_TYPE['source_tax_type']
))

# ───────────────────────────────────────────────────────────────
# SOURCE TYPE → DEFAULT WITHDRAWAL EVENT TYPE
# (wd_type is a semantic classifier, not a tax classifier)
# ───────────────────────────────────────────────────────────────

WD_TYPE_MAP = {
    # Income streams
    'inc_ssa': 'inc_ssa',
    'inc_fers': 'inc_fers',
    'inc_ord': 'inc_ord',

    # Taxable brokerage
    'brokerage': 'brokerage_sale',

    # Deferred accounts
    'ira_inherited': 'ira_rmd',   # Traditional inherited IRA → annual RMDs
    'ira': 'ira_ord',             # Traditional IRA
    'tsp': 'ira_ord',             # TSP behaves like IRA for withdrawals

    # Roth accounts
    'roth': 'roth',               # Roth IRA (no RMDs)
    'roth_inherited': 'roth',     # Inherited Roth IRA (10-year rule, no RMDs)

    # Synthetic/system-generated
    'synthetic': 'synthetic',
    'none': 'none',
    'rollover': 'rollover',
    'transfer': 'transfer',
}

# ───────────────────────────────────────────────────────────────
# ENUM NORMALIZATION
# ───────────────────────────────────────────────────────────────

def normalize_enum(value: str, column: str, default: str = 'unknown', label: str = 'DataFrame') -> str:
    """Normalize a string value to a valid enum, or return default if invalid."""
    valid_set = VALID_ENUMS.get(column)
    if not valid_set:
        raise ValueError(f"No valid set defined for column '{column}' in '{label}'")

    if pd.isna(value):
        return default

    normalized = str(value).strip().lower()
    return normalized if normalized in valid_set else default


def normalize_column(df: pd.DataFrame, column: str, default: str = 'unknown', label: str = 'DataFrame') -> pd.Series:
    return df[column].apply(lambda val: normalize_enum(val, column, default, label))


# ───────────────────────────────────────────────────────────────
# NUMERIC NORMALIZATION
# ───────────────────────────────────────────────────────────────

def normalize_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    return df


# ───────────────────────────────────────────────────────────────
# NULL HANDLING
# ───────────────────────────────────────────────────────────────

def fill_nulls_by_dtype(df: pd.DataFrame) -> pd.DataFrame:
    int_cols = df.select_dtypes(include='number').columns
    str_cols = df.select_dtypes(include='object').columns

    df[int_cols] = df[int_cols].fillna(0)
    df[str_cols] = df[str_cols].fillna('')

    return df


# ───────────────────────────────────────────────────────────────
# DTYPE ENFORCEMENT
# ───────────────────────────────────────────────────────────────

def enforce_dtypes(df: pd.DataFrame, dtype_map: dict[str, str]) -> pd.DataFrame:
    for col, dtype in dtype_map.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
    return df


# ───────────────────────────────────────────────────────────────
# COLUMN ORDER ENFORCEMENT
# ───────────────────────────────────────────────────────────────

def enforce_column_order(df: pd.DataFrame, expected_columns: list[str], strict: bool = True) -> pd.DataFrame:
    """Reorder DataFrame columns to match expected schema order."""
    missing = [col for col in expected_columns if col not in df.columns]
    if strict and missing:
        raise ValueError(f"❌ Missing columns for ordering: {missing}")

    return df[[col for col in expected_columns if col in df.columns]]
