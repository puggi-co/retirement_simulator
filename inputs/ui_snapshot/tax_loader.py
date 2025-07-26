# input/tax_loader.py

import pandas as pd
from pathlib import Path
from simulation.tax.registry import TAX_TABS, TAX_REQUIRED_COLUMNS
from simulation.tax.cleaning import clean_tax_sheet
from simulation.tax.registry import register_tax_accessors

def load_all_tax_tabs(file_path: Path) -> dict:
    """
    Load and clean all tax reference tabs using centralized schema and cleaning logic.
    Args:
        file_path (Path): Path to the Excel file with tax data.
    Returns:
        dict: Dictionary of cleaned DataFrames keyed by tab name.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Tax file not found at: {file_path}")

    # Load and clean all registered tax tabs
    raw_dfs = {
        tab: pd.read_excel(file_path, sheet_name=tab)
        for tab in TAX_TABS
    }

    cleaned_dfs = {
        tab: clean_tax_sheet(raw_dfs[tab], TAX_REQUIRED_COLUMNS[tab], sheet_name=tab)
        for tab in TAX_TABS
    }

    return cleaned_dfs
