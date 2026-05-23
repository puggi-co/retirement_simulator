'''Performs dynamic enrichment, validation, and preparation of schema-compliant Portfolio DataFrames.'''

import json
import pandas as pd

from pathlib import Path
from typing import Dict, List

from config.config_schema import SimulationConfig
from core.rmd_util import enrich_portfolio_rmd

from core.schema_frame import SchemaFrame
from loader.loader_schema import (
    ACCOUNT_SHEET_COLUMNS, ACCOUNT_SHEET_DTYPES,
    INCOME_SHEET_COLUMNS, INCOME_SHEET_DTYPES,
    EXCEL_CONDITIONAL_COLUMNS,
    PORTFOLIO_SCHEMA_COLUMNS, PORTFOLIO_SCHEMA_DTYPES
)
from core.schema_util import (
    LKUP_SOURCE_TAX_TYPE,
    normalize_column, normalize_numeric_columns, fill_nulls_by_dtype
)

from loader.excel_loader import ExcelSchemaLoader
#from storage.export_util import debug_view

# Determine project root (src/ is one level below project root)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Default JSON location (adjust folder as needed)
DEFAULT_JSON = PROJECT_ROOT / "data" / "user" / "in_account.json"


# ── Tab and Schema Definitions ─────────────────

TABS: List[str] = ['My_Account', 'My_Income']

REQUIRED_COLUMNS: Dict[str, Dict[str, str]] = {
    'My_Account': {col: ACCOUNT_SHEET_DTYPES[col] for col in ACCOUNT_SHEET_COLUMNS},
    'My_Income': {col: INCOME_SHEET_DTYPES[col] for col in INCOME_SHEET_COLUMNS}
}

class PortfolioInputSource:
    def load(self) -> "SchemaFrame":
        raise NotImplementedError("Subclasses must implement load()")

# ── Excel Portfolio Loader ─────────────────────

class ExcelPortfolioLoader(PortfolioInputSource):
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def load(self):
        cleaned = ExcelSchemaLoader.load_and_clean(
            file_path=self.file_path,
            tabs=TABS,
            required_columns=REQUIRED_COLUMNS,
            conditional_columns=EXCEL_CONDITIONAL_COLUMNS
        )

        return cleaned['My_Account'], cleaned['My_Income']

# ── JSON Portfolio Loader ─────────────────────

class JSONPortfolioLoader(PortfolioInputSource):
    def __init__(self, json_path: Path):
        self.json_path = json_path

    def load(self) -> SchemaFrame:
        with open(self.json_path, "r") as f:
            records = json.load(f)

        df = pd.DataFrame(records)

        frame = SchemaFrame(
            df=df,
            columns=PORTFOLIO_SCHEMA_COLUMNS,
            dtypes=PORTFOLIO_SCHEMA_DTYPES,
            label="Portfolio Base (JSON)"
        )

        frame.validate(strict=True)
        return frame

# ── Streamlit Portfolio Loader ─────────────────────

class StreamlitPortfolioLoader(PortfolioInputSource):
    def __init__(self, form_data: dict):
        self.form_data = form_data

    def load(self) -> SchemaFrame:
        df = pd.DataFrame([self.form_data])

        frame = SchemaFrame(
            df=df,
            columns=PORTFOLIO_SCHEMA_COLUMNS,
            dtypes=PORTFOLIO_SCHEMA_DTYPES,
            label="Portfolio Base (Streamlit)"
        )

        frame.validate(strict=True)
        return frame

# ── Normalization of investment accounts and income streams ──────────────────────────────

def prepare_portfolio(config: SimulationConfig, df_my_account, df_my_income) -> pd.DataFrame:
    """
    Prepare and validate the portfolio DataFrame for simulation.
    Merges account and income sheets, enriches with metadata, and validates schema.
    """

    # Copy inputs to avoid mutation
    my_income_df = df_my_income.copy()
    my_account_df = df_my_account.copy()

    # Conform column names
    my_account_df = my_account_df.rename(columns={
    'account_name': 'source_name',
    'account_type': 'source_type',
    'account_balance': 'base_balance'
    })

    my_income_df = my_income_df.rename(columns={
        'income_name': 'source_name',
        'income_type': 'source_type',
        'income': 'base_balance',
        'begin_age': 'distribution_age'
    })

    # Combine account and income sheets
    merged_df = pd.concat([my_account_df, my_income_df], ignore_index=True)

    # Add lookup for account tax type
    merged_df = merged_df.merge(LKUP_SOURCE_TAX_TYPE, on='source_type', how='left')

    # Drop rows with non-positive balance
    merged_df = merged_df[merged_df['base_balance'] > 0]

    # Normalize numeric columns and fill nulls
    merged_df = normalize_numeric_columns(merged_df, ['prior_owner_death_year', 'beneficiary_birth_year'])
    merged_df = fill_nulls_by_dtype(merged_df)

    # Normalize Portfolio Columns
    merged_df['filing_status'] = normalize_column(merged_df, 'filing_status', 'unknown', 'Portfolio')
    merged_df['source_type'] = normalize_column(merged_df, 'source_type', 'unknown', 'Portfolio')

    # RMD Enrichment
    merged_df = enrich_portfolio_rmd(merged_df, config)

    # Remove columns used to enrich but not in final schema e.g., fields to enrich RMD data
    merged_df = merged_df.drop(columns=['owner_birth_date', 'prior_owner_birthdate_iso'], errors='ignore')

    # Enforce final schema column order and types
    merged_df = ExcelSchemaLoader.enforce_column_types(merged_df, PORTFOLIO_SCHEMA_DTYPES, sheet_name="Portfolio Base")

    # Validate final schema
    portfolio_frame = SchemaFrame(
        df=merged_df,
        columns=PORTFOLIO_SCHEMA_COLUMNS,
        dtypes=PORTFOLIO_SCHEMA_DTYPES,
        label="Portfolio Base"
    )

    portfolio_frame.validate(strict=True)
    enriched_df = portfolio_frame.export()

    return enriched_df

def get_portfolio_from_json(json_path: Path = Path("data/in_account.json"), config: SimulationConfig = None) -> pd.DataFrame:
    with open(json_path, "r") as f:
        records = json.load(f)

    df_raw = pd.DataFrame(records)

    if config:
        # Split if needed, then normalize
        df_account = df_raw[df_raw["source"] == "account"]
        df_income = df_raw[df_raw["source"] == "income"]
        return prepare_portfolio(config, df_account, df_income)
    else:
        # Assume already unified
        frame = SchemaFrame(
            df=df_raw,
            columns=PORTFOLIO_SCHEMA_COLUMNS,
            dtypes=PORTFOLIO_SCHEMA_DTYPES,
            label="Portfolio Base (JSON)"
        )
        frame.validate(strict=True)
        return frame.export()

# ── Public Entry Point ─────────────────────────

def get_portfolio_from_json(json_path: Path):
    loader = JSONPortfolioLoader(json_path)
    return loader.load().export()

def get_portfolio_from_streamlit(form_data: dict) -> pd.DataFrame:
    loader = StreamlitPortfolioLoader(form_data)
    return loader.load().export()

# ── Account Information Loader ───────────────────────────
class AccountExcel(ExcelSchemaLoader):

    def __init__(self, workbook='data/in_account.xlsx'):
        self.workbook = Path(workbook)
        self.tabs = TABS

        # Initialize DataFrames
        self.df_my_account = None
        self.df_my_income = None

        # Registry will be populated after loading
        self._registry = {
            'account': lambda: self.df_my_account.export(),  # returns validated, ordered DataFrame
            'account_raw': lambda: self.df_my_account.df,    # returns unvalidated raw DataFrame
            'income': lambda: self.df_my_income.export(),
            'income_raw': lambda: self.df_my_income.df
        }

    def get(self, key: str):
        if key not in self._registry:
            raise KeyError(f"Unknown key in AccountExcel registry: {key}")
        return self._registry[key]()

    def load_workbook(self) -> pd.DataFrame:
        cleaned = self.load_and_clean(
            self.workbook,
            self.tabs,
            REQUIRED_COLUMNS,
            EXCEL_CONDITIONAL_COLUMNS
        )
        
        self.df_my_account = SchemaFrame(
            df=cleaned['My_Account'],
            columns=list(REQUIRED_COLUMNS['My_Account'].keys()),
            dtypes=REQUIRED_COLUMNS['My_Account'],
            label="Raw Account Sheet"
        )
        
        self.df_my_income = SchemaFrame(
            df=cleaned['My_Income'],
            columns=list(REQUIRED_COLUMNS['My_Income'].keys()),
            dtypes=REQUIRED_COLUMNS['My_Income'],
            label="Income Stream"
        )
        return cleaned