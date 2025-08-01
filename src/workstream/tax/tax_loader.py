"""Ingests and validates tax sheets"""


import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

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

# --- Cleaning Helper (Minimal) ---
def clean_tax_sheet(df: pd.DataFrame, required: set, sheet_name: str) -> pd.DataFrame:
    """Validates schema and performs basic cleaning."""
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{sheet_name} missing required columns: {missing}")
    return df.dropna(how="all")  # simple row pruning

# --- Ingestion Function ---
def load_tax_tables(file_path: Path) -> Dict[str, pd.DataFrame]:
    """Loads and cleans all tax tabs from Excel file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Tax file not found: {file_path}")

    raw_dfs = {
        tab: pd.read_excel(file_path, sheet_name=tab)
        for tab in TAX_TABS
    }

    cleaned_dfs = {
        tab: clean_tax_sheet(raw_dfs[tab], TAX_REQUIRED_COLUMNS[tab], sheet_name=tab)
        for tab in TAX_TABS
    }

    return cleaned_dfs

# --- Structured Access Layer ---
@dataclass
class TaxTables:
    amt: pd.DataFrame
    capital_gain: pd.DataFrame
    tax_bracket: pd.DataFrame
    standard_deduction: Optional[pd.DataFrame] = None
    lef: Optional[pd.DataFrame] = None

    @classmethod
    def from_cleaned(cls, dfs: Dict[str, pd.DataFrame]) -> "TaxTables":
        return cls(
            amt=dfs["T_AMT"],
            capital_gain=dfs["T_CapitalGain"],
            tax_bracket=dfs["T_TaxBracket"],
            standard_deduction=dfs.get("T_StandardDeduction"),
            lef=dfs.get("T_LEF"),
        )

    @classmethod
    def from_excel(cls, file_path: Path) -> "TaxTables":
        cleaned = load_tax_tables(file_path)
        return cls.from_cleaned(cleaned)

    
    def get(self, tab: str) -> Optional[pd.DataFrame]:
        """Access raw tab by key (for advanced workflows)."""
        return {
            "T_AMT": self.amt,
            "T_CapitalGain": self.capital_gain,
            "T_TaxBracket": self.tax_bracket,
            "T_StandardDeduction": self.standard_deduction,
            "T_LEF": self.lef
        }.get(tab)

    def summary(self) -> pd.DataFrame:
        return pd.DataFrame({
            "Tab": ["T_AMT", "T_CapitalGain", "T_TaxBracket", "T_StandardDeduction", "T_LEF"],
            "Rows": [len(df) if df is not None else 0 for df in [
                self.amt, self.capital_gain, self.tax_bracket,
                self.standard_deduction, self.lef
            ]]
        })
