from dataclasses import dataclass
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from .registry import TAX_TABS, TAX_REQUIRED_COLUMNS
from .cleaning import clean_tax_sheet

def load_tax_tables(file_path: Path) -> Dict[str, pd.DataFrame]:
   """Handles raw ingestion and cleaning of tax data from Excel."""
    if not file_path.exists():
        raise FileNotFoundError(f"Tax file not found: {file_path}")

    raw_dfs = {
        tab: pd.read_excel(file_path, sheet_name=tab)
        for tab in TAX_TABS
    }

    cleaned_dfs = {
        tab: clean_tax_sheet(raw_dfs[tab], TAX_REQUIRED_COLUMNS.get(tab, set()), sheet_name=tab)
        for tab in TAX_TABS
    }

    return cleaned_dfs

def load_all_tax_tabs(raw_dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    return {tab: raw_dfs.get(tab) for tab in TAX_TABS if tab in raw_dfs}

# --- New structured access layer ---
@dataclass
class TaxTables:
    amt: pd.DataFrame
    capital_gain: pd.DataFrame
    ordinary_income: pd.DataFrame
    standard_deduction: Optional[pd.DataFrame] = None
    lef: Optional[pd.DataFrame] = None  # Optional tab

    @classmethod
    def from_cleaned(cls, dfs: Dict[str, pd.DataFrame]) -> "TaxTables":
        return cls(
            amt=dfs["AMT"],
            capital_gain=dfs["Capital Gain"],
            ordinary_income=dfs["Ordinary Income"],
            standard_deduction=dfs.get("T_StandardDeduction")
            lef=dfs.get("LEF")
        )

    @classmethod
    def from_excel(cls, file_path: Path) -> "TaxTables":
        cleaned = load_tax_tables(file_path)
        return cls.from_cleaned(cleaned)

    def bracket_for_income(self, year: int, income: float) -> Dict:
        df = self.ordinary_income[self.ordinary_income["Year"] == year]
        match = df[(df["Min"] <= income) & (income <= df["Max"])]
        if match.empty:
            raise ValueError(f"No bracket found for income {income} in year {year}")
        return match.squeeze().to_dict()
