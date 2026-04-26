"""Performs computations using reference tax tables"""

from typing import Optional, Dict
import pandas as pd

from src.io_input.tax_loader import FilingStatus

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

def calculate_tax(brackets, year, filing_status, taxable_income):
    
    # Calculate tax owed and effective tax rate on taxable income
    bracket_rate = effective_tax_rate = tax_owed = 0.0
    taxable_balance = taxable_income

    # loop through income brackets
    for bracket in brackets[brackets['year'] == year].itertuples():

        if filing_status == FilingStatus.SINGLE:
            # retrieve tax bracket and low/high amounts
            bracket_rate = bracket[3]
            bracket_low = bracket[4]
            bracket_high = bracket[5]
        elif filing_status == FilingStatus.MARRIED:
            # retrieve tax bracket and low/high amounts
            bracket_rate = bracket[3]
            bracket_low = bracket[6]
            bracket_high = bracket[7]
        elif filing_status == FilingStatus.HEAD:
            # retrieve tax bracket and low/high amounts
            bracket_rate = bracket[3]
            bracket_low = bracket[8]
            bracket_high = bracket[9]

        if taxable_balance == 0.0:
            return tax_owed, effective_tax_rate

        taxable_portion = min(taxable_balance, bracket_high) - bracket_low if taxable_balance >= bracket_low else taxable_balance
        tax_owed += (taxable_portion * bracket_rate)
        taxable_balance -= taxable_portion
        
        effective_tax_rate = tax_owed / taxable_income if taxable_income > 0 else 0.0
                    
    return tax_owed, effective_tax_rate

# Add more logic as needed (AMT calculations, capital gains, LEF)
