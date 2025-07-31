"""
Manages tax-related reference data structures for the retirement simulator.
Defines supported tabs, required schema columns, and valid filing statuses.
"""

import pandas as pd
from typing import List, Dict, Set, Callable, Optional, Tuple

# define constants for tax filing status
class FilingStatus:
    SINGLE = 'single'
    MARRIED = 'married'
    HEAD = 'head'

VALID_STATUSES = {FilingStatus.SINGLE, FilingStatus.MARRIED, FilingStatus.HEAD}

TAX_TABS: List[str] = [
    'T_AMT', 'T_CapitalGain', 'T_TaxBracket',
    'T_StandardDeduction', 'T_LEF'
]

TAX_REQUIRED_COLUMNS: Dict[str, Set[str]] = {
    'T_AMT': {'year', 'tax_type', 'low_single', 'high_single', 'low_married', 'high_married'},
    'T_CapitalGain': {'year', 'tax_type', 'tax_rate', 'single', 'married', 'head'},
    'T_TaxBracket': {'year', 'tax_type', 'tax_rate', 'low_single', 'high_single', 'low_married', 'high_married', 'low_head', 'high_head'},
    'T_StandardDeduction': {'year', 'tax_type', 'single', 'married', 'head'},
    'T_LEF': {'age', 'lef_2001', 'uniform_2001', 'lef_2002_2020', 'uniform_2002_2020', 'lef_2021_present', 'uniform_2021_present'}
}

def load_all_tax_tabs(raw_dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    return {tab: raw_dfs.get(tab) for tab in TAX_TABS if tab in raw_dfs}

def register_tax_accessors(tables: Dict[str, pd.DataFrame]) -> Dict[str, Callable]:
    return {
        'amt': lambda: tables.get('T_AMT'),
        'capital_gain': lambda: tables.get('T_CapitalGain'),
        'standard_deduction': lambda: tables.get('T_StandardDeduction'),
        'tax_bracket': lambda: tables.get('T_TaxBracket'),
        'lef': lambda: tables.get('T_LEF')
    }