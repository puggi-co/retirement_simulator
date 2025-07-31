"""
tax_engine.py

Handles centralized tax computations using reference tables.
Provides functions for standard deduction, tax bracket lookup, AMT logic, etc.
Designed to be consumed by simulation scenarios across withdrawal and Monte Carlo workstreams.
"""

from typing import Optional, Dict
import pandas as pd

from .tax_accessors import get_standard_deduction_table, get_tax_bracket_table
from .filing_status import FilingStatus  # if you separate it out

def get_standard_deduction(year: int, status: str) -> Optional[float]:
    table = get_standard_deduction_table()
    if table is None or status not in FilingStatus.ALL:
        return None
    row = table.loc[table['year'] == year]
    return row[f'deduction_{status}'].values[0] if not row.empty else None

def get_tax_bracket(year: int, status: str) -> pd.DataFrame:
    table = get_tax_bracket_table()
    if table is None or status not in FilingStatus.ALL:
        return pd.DataFrame()
    df = table[table['year'] == year].copy()
    return df[[f'low_{status}', f'high_{status}', 'rate']]

# Add more logic as needed (AMT calculations, capital gains, LEF)
