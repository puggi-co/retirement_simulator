import pandas as pd

from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime as dt

from src.io.export_util import debug_view

class ExcelSchemaLoader:
    """
    Mixin for consistently cleaning and validating Excel worksheets.

    Usage:
    - Clean column names
    - Enforce required fields and types
    - Apply conditional field rules based on logical dependencies
    """

    @staticmethod
    def clean_sheet(df: pd.DataFrame, required: Dict[str, str], sheet_name: str) -> pd.DataFrame:
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
        ExcelSchemaLoader.validate_columns(df, required, sheet_name)
        return df

    @staticmethod
    def validate_columns(df: pd.DataFrame, required: Dict[str, str], sheet_name: str):
        missing = set(required.keys()) - set(df.columns)
        if missing:
            raise ValueError(f"❌ Sheet '{sheet_name}' is missing required columns: {missing}")

    @staticmethod
    def enforce_column_types(df: pd.DataFrame, column_types: Dict[str, str], sheet_name: str) -> pd.DataFrame:
        for col, dtype in column_types.items():
            if col in df.columns:
                try:
                    df[col] = df[col].astype(dtype)
                except Exception as e:
                    raise TypeError(f"❌ Failed to cast column '{col}' in '{sheet_name}' to {dtype}: {e}")
        return df

    @staticmethod
    def validate_conditionals(df: pd.DataFrame, rules: List[Dict[str, Dict[str, str]]], sheet_name: str):
        for rule in rules:
            if_clause = rule["if"]
            then_fields = rule["then"]

            # 🧩 Ensure all conditional fields exist with correct dtypes
            for col, dtype in then_fields.items():
                if col not in df.columns:
                    df[col] = pd.Series(dtype=dtype)
                    print(f"🧩 Added missing conditional column '{col}' to '{sheet_name}' with dtype '{dtype}'")

            # 🧠 Apply conditional logic
            mask = pd.Series([True] * len(df))
            for col, val in if_clause.items():
                mask &= df[col] == val

            missing_mask = df[mask][list(then_fields)].isnull()
            if missing_mask.any().any():
                offending_rows = df[mask][missing_mask.any(axis=1)]
                raise ValueError(
                    f"{sheet_name} rows matching {if_clause} are missing required fields {list(then_fields)}:\n{offending_rows}"
                )

    @staticmethod
    def load_and_clean(
        file_path: Path,
        tabs: List[str],
        required_columns: Dict[str, Dict[str, str]],
        conditional_columns: Optional[Dict[str, List[Dict[str, Dict[str, str]]]]] = None
    ) -> Dict[str, pd.DataFrame]:

        raw = {tab: pd.read_excel(file_path, sheet_name=tab) for tab in tabs}
        ExcelSchemaLoader.validate_tabs(raw, tabs)

        cleaned = {}
        for tab in tabs:
            df_raw = raw[tab]
            required = required_columns.get(tab, {})
            df_clean = ExcelSchemaLoader.clean_sheet(df_raw, required, tab)

            # 🧩 Apply conditional validation before enforcing types
            if conditional_columns and tab in conditional_columns:
                ExcelSchemaLoader.validate_conditionals(df_clean, conditional_columns[tab], tab)

            # ✅ Enforce types for required and conditional fields
            df_typed = ExcelSchemaLoader.enforce_column_types(df_clean, required, tab)
            cleaned[tab] = df_typed

        return cleaned

    @staticmethod
    def load_workbook(
        workbook_path: Path,
        tabs: List[str],
        required_columns: Dict[str, Dict[str, str]],
        conditional_columns: Optional[Dict[str, List[Dict[str, Dict[str, str]]]]] = None
    ) -> Dict[str, pd.DataFrame]:
        return ExcelSchemaLoader.load_and_clean(
            workbook_path,
            tabs,
            required_columns,
            conditional_columns
        )

    @staticmethod
    def validate_tabs(sheets: Dict[str, pd.DataFrame], expected_tabs: List[str]):
        missing = set(expected_tabs) - set(sheets.keys())
        if missing:
            raise ValueError(f"❌ Workbook is missing expected tabs: {missing}")

    @staticmethod
    def check_iso_format(date_value) -> str:
        """Ensures date is stored as a string in 'YYYY-MM-DD' ISO format."""
        if isinstance(date_value, str):
            try:
                # Validate format
                parsed = dt.strptime(date_value, '%Y-%m-%d')
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                raise ValueError('Invalid date string. Expected format: "YYYY-MM-DD".')
        elif isinstance(date_value, dt):
            return date_value.strftime('%Y-%m-%d')
        else:
            raise TypeError('Expected a string or datetime object.')