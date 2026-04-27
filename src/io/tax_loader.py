import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Set, List

from io.excel_loader import ExcelSchemaLoader

# ── Tax Filing Status Enum ─────────────────────
class FilingStatus:
    SINGLE = 'single'
    MARRIED = 'married'
    HEAD = 'head'

    VALID = {SINGLE, MARRIED, HEAD}

# ── Tab and Schema Definitions ─────────────────
TABS: List[str] = [
    'T_AMT', 'T_CapitalGain', 'T_TaxBracket',
    'T_StandardDeduction', 'T_LEF'
]

REQUIRED_COLUMNS: Dict[str, Dict[str, str]] = {
    'T_AMT': {
        'year': 'Int64',
        'tax_type': 'string', 
        'low_single': 'float',
        'high_single': 'float',
        'low_married': 'float',
        'high_married': 'float'
    },
    'T_CapitalGain': {
        'year': 'Int64',
        'tax_type': 'string',
        'tax_rate': 'float',
        'single': 'float',
        'married': 'float',
        'head': 'float'
    },
    'T_TaxBracket': {
        'year': 'Int64',
        'tax_type': 'string',
        'tax_rate': 'float',
        'low_single': 'float',
        'high_single': 'float',
        'low_married': 'float',
        'high_married': 'float',
        'low_head': 'float',
        'high_head': 'float'
    },
    'T_StandardDeduction': {
        'year': 'Int64',
        'tax_type': 'string',
        'single': 'float',
        'married': 'float',
        'head': 'float'
    },
    'T_LEF': {
        'age': 'Int64',
        'lef_2001': 'float',
        'uniform_2001': 'float',
        'lef_2002_2020': 'float',
        'uniform_2002_2020': 'float',
        'lef_2021_present': 'float',
        'uniform_2021_present': 'float'
    }
}
CONDITIONAL_COLUMNS: Dict[str, List[Dict[str, Dict[str, str]]]] = {
    'T_AMT': [],
    'T_CapitalGain': [],
    'T_TaxBracket': [],
    'T_StandardDeduction': [],
    'T_LEF': []
}

# ── Tax Table Loader ───────────────────────────
@dataclass
class TaxTable(ExcelSchemaLoader):
    amt: pd.DataFrame
    capital_gain: pd.DataFrame
    tax_bracket: pd.DataFrame
    standard_deduction: Optional[pd.DataFrame] = None
    lef: Optional[pd.DataFrame] = None

    @classmethod
    def from_excel(cls, file_path: Path) -> "TaxTable":
        cleaned = ExcelSchemaLoader.load_and_clean(
            file_path=file_path,
            tabs=TABS,
            required_columns=REQUIRED_COLUMNS,
            conditional_columns=CONDITIONAL_COLUMNS
        )
        return cls.from_cleaned(cleaned)

    @classmethod
    def from_cleaned(cls, dfs: Dict[str, pd.DataFrame]) -> "TaxTable":
        return cls(
            amt=dfs["T_AMT"],
            capital_gain=dfs["T_CapitalGain"],
            tax_bracket=dfs["T_TaxBracket"],
            standard_deduction=dfs.get("T_StandardDeduction"),
            lef=dfs.get("T_LEF")
        )

    def get(self, tab: str) -> Optional[pd.DataFrame]:
        return {
            "T_AMT": self.amt,
            "T_CapitalGain": self.capital_gain,
            "T_TaxBracket": self.tax_bracket,
            "T_StandardDeduction": self.standard_deduction,
            "T_LEF": self.lef
        }.get(tab)

    def summary(self) -> pd.DataFrame:
        return pd.DataFrame({
            "Tab": TABS,
            "Rows": [len(self.get(tab)) if self.get(tab) is not None else 0 for tab in TABS]
        })

# ── Public Entry Point ─────────────────────────
def get_tax_table(file_path: Path) -> TaxTable:
    return TaxTable.from_excel(file_path)
