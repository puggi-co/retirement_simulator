'''Centralizes normalization logic and lookup tables (e.g. tax type maps).'''

import pandas as pd

# ── Validate Enumerations ─────────────────────────────

VALID_ENUMS = {
    'filing_status': {'single', 'married', 'head'},
    'account_type': {
        'brokerage', 'ira', 'ira_inherited', 'tsp', 'roth_ira', 'roth_ira_inherited',
        'inc_fers', 'inc_ord', 'inc_ssa'
    },
    # Add more as needed
}

VALID_FILING_STATUS = VALID_ENUMS['filing_status']
VALID_ACCOUNT_TYPE = VALID_ENUMS['account_type']

# ── Lookups for Withdrawal Tax Classification ─────────────────────────────

LKUP_ACCOUNT_TAX_TYPE = pd.DataFrame({
    'account_type': [
        'inc_fers', 'inc_ord', 'inc_ssa', 
        'brokerage', 'ira', 'ira_inherited', 'tsp', 'roth', 'roth_inherited'
    ],
    'account_tax_type': [
        'taxable', 'taxable', 'taxable',
        'taxable', 'deferred', 'deferred', 'deferred', 'exempt', 'exempt'
    ]
})

# WITHDRAWAL LOOKUPS
LKUP_WD_TAX_TYPE = pd.DataFrame({
    'wd_type': [
        # Withdrawals taxed as ordinary income
        'cap_short',     # Taxed as ordinary income (held ≤ 1 year)
        'conversion',    # Roth conversion
        'inc_ord',       # Other ordinary (ORD) income
        'ira_rmd',       # IRA Required Minimum Distribution
        'ira_ord',       # IRA ordinary withdrawal; may supersede RMD
        'ira_early',     # IRA early withdrawal with penalty
        'ordinary',      # Ordinary withdrawals from taxable accounts

        # Withdrawals taxed at preferential rates
        'cap_long',      # Taxed at preferential rates (held > 1 year)
        'charitable',    # QCDs reduce RMD and taxable income
        'dividend-q',    # Taxed at long-term capital gains rates (0–20%)
        'dividend-nq',   # Taxed as ordinary income
        'inc_fers',      # Federal Employee Retirement System (FERS) income
        'inc_ssa',       # Social Security Administration (SSA) income
        'interest',      # Taxed as ordinary income

        # Withdrawals exempt from tax
        'roth',          # Tax-exempt withdrawal (Roth, QCD, etc.)

        # Transactions not subject to tax
        'none',          # No withdrawal
        'rollover',      # Trustee-to-trustee rollover
        'synthetic',     # Synthetic reclassification
        'transfer'       # Internal account transfer
    ],
    'wd_tax_type': [
        'taxable', 'taxable', 'taxable', 'taxable', 'taxable', 'taxable', 'taxable', 
        'preferred', 'preferred', 'preferred', 'preferred', 'preferred','preferred', 'preferred',
        'exempt',
        'none', 'none', 'none', 'none'
    ]})

WD_TAX_TYPE_MAP = dict(zip(
    LKUP_WD_TAX_TYPE['wd_type'],
    LKUP_WD_TAX_TYPE['wd_tax_type']
))

# ── Enumeration and Normalization Functions ────────────────────────────────

def normalize_enum(value: str, column: str, default: str = 'unknown', label: str = 'DataFrame') -> str:
    """Normalize a string value to a valid enum, or return default if invalid."""
    valid_set = VALID_ENUMS.get(column)
    if not valid_set:
        print(f"⚠️ VALID_ENUMS keys: {list(VALID_ENUMS.keys())}")
        raise ValueError(f"No valid set defined for column '{column}' in '{label}'")
    if pd.isna(value):
        return default

    normalized = str(value).strip().lower()

    return normalized if normalized in valid_set else default

def normalize_column(df: pd.DataFrame, column: str, default: str = 'unknown', label: str = 'DataFrame') -> pd.Series:
    return df[column].apply(lambda val: normalize_enum(val, column, default, label))

def normalize_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    return df

def fill_nulls_by_dtype(df: pd.DataFrame) -> pd.DataFrame:
    int_cols = df.select_dtypes(include='number').columns
    str_cols = df.select_dtypes(include='object').columns
    df[int_cols] = df[int_cols].fillna(0)
    df[str_cols] = df[str_cols].fillna('')
    return df

def enforce_dtypes(df: pd.DataFrame, dtype_map: dict[str, str]) -> pd.DataFrame:
    for col, dtype in dtype_map.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
    return df

def enforce_column_order(df: pd.DataFrame, expected_columns: list[str], strict: bool = True) -> pd.DataFrame:
    """Reorder DataFrame columns to match expected schema order."""
    missing = [col for col in expected_columns if col not in df.columns]
    if strict and missing:
        raise ValueError(f"❌ Missing columns for ordering: {missing}")
    return df[[col for col in expected_columns if col in df.columns]]
