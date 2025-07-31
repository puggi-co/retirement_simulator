from pathlib import Path
import pandas as pd

from src.schema.tax_schema import TAX_TABS, TAX_REQUIRED_COLUMNS
from src.core.tax.tax_accessors import TaxTables
from src.core.tax.tax_registry import register_tax_accessors

DEFAULT_TAX_WB = Path("data/tax_tables.xlsx")  # Or inject via config

def load_tax_tables(workbook_path: str) -> TaxTables:
    tabs = {name: load_tab(name, workbook_path) for name in TAX_TABS}
    missing = [name for name, tab in tabs.items() if tab is None]
    if missing:
        raise ValueError(f"Workbook missing mandatory tax tabs: {missing}")
    return TaxTables(**tabs)

def ingest_tax_file(file_path: Path = DEFAULT_TAX_WB) -> tuple[TaxTables, dict[str, Callable]]:
    """Entry point for ingesting tax tables and returning structured access."""
    tables = load_tax_tables(file_path)
    registry = register_tax_accessors(tables)
    return TaxTables(tables), registry
