from typing import Dict, Optional
import pandas as pd
from .registry import TAX_TABS

class TaxTables:
    """Provides a uniform interface to tax tables across simulation workstreams."""

    def __init__(self, tables: Dict[str, pd.DataFrame]):
        self.tables = tables
        self.registry = register_tax_accessors(tables)

    def _get(self, tab_name: str) -> Optional[pd.DataFrame]:
        return self.tables.get(tab_name)

    @property
    def amt(self) -> Optional[pd.DataFrame]:
        return self._get('T_AMT')

    @property
    def capital_gain(self) -> Optional[pd.DataFrame]:
        return self._get('T_CapitalGain')

    @property
    def standard_deduction(self) -> Optional[pd.DataFrame]:
        return self._get('T_StandardDeduction')

    @property
    def tax_bracket(self) -> Optional[pd.DataFrame]:
        return self._get('T_TaxBracket')

    @property
    def lef(self) -> Optional[pd.DataFrame]:
        return self._get('T_LEF')

    def summary(self) -> pd.DataFrame:
        return pd.DataFrame({
            'Tab': TAX_TABS,
            'Present': [tab in self.tables for tab in TAX_TABS]
        })

def get_tax_tables(self, workbook: dict[str, pd.DataFrame]) -> "TaxTables":
    """
    Initializes a TaxTables instance from a workbook-like dictionary
    using expected registry keys.
    """
    tables = {
        'T_StandardDeduction': workbook.get('standard_deduction'),
        'T_TaxBracket': workbook.get('tax_bracket'),
        'T_LEF': workbook.get('lef'),
        'T_AMT': workbook.get('amt'),  # optional if workbook includes it
        'T_CapitalGain': workbook.get('capital_gain')  # optional
    }

    # Filter out any None values in case some tabs are missing
    tables = {k: v for k, v in tables.items() if v is not None}
    return TaxTables(tables)
