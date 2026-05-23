# Wraps a DataFrame to enforce column order, validates schema, and supports layered/grouped operations (e.g. temporal, financial, metadata).
 
import pandas as pd

class SchemaFrame:
    def __init__(self, df: pd.DataFrame, columns: list[str], dtypes: dict[str, str], label: str = "DataFrame"):
        self.df = df.copy()
        self.columns = columns
        self.dtypes = dtypes
        self.label = label

    def normalize_dtypes(self):
        for col, expected_dtype in self.dtypes.items():
            if col in self.df.columns:
                try:
                    self.df[col] = self.df[col].astype(expected_dtype)
                except Exception as e:
                    print(f"❌ Failed to cast '{col}' to '{expected_dtype}': {e}")

    def validate(self, strict: bool = True):
        self.normalize_dtypes()  # ✅ Enforce dtypes
        missing_cols = set(self.columns) - set(self.df.columns)
        extra_cols = set(self.df.columns) - set(self.columns)

        if missing_cols:
            raise ValueError(f"❌ {self.label} missing required columns: {missing_cols}")
        if extra_cols:
            print(f"⚠️ {self.label} has unexpected columns: {extra_cols}")

        for col, expected_dtype in self.dtypes.items():
            if col in self.df.columns:
                actual_dtype = str(self.df[col].dtype)
                if expected_dtype not in actual_dtype:
                    print(f"⚠️ Column '{col}' in {self.label} has dtype '{actual_dtype}', expected '{expected_dtype}'")

        if strict and missing_cols:
            raise ValueError(f"❌ {self.label} failed strict validation. Missing: {missing_cols}")

    def enforce_order(self):
        from core.schema_util import enforce_column_order
        self.df = enforce_column_order(self.df, self.columns, strict=False)

    def get_group(self, group_name: str, group_map: dict[str, list[str]]) -> pd.DataFrame:
        if group_name not in group_map:
            raise ValueError(f"Unknown group '{group_name}' in {self.label}")
        return self.df[group_map[group_name]]

    def export(self) -> pd.DataFrame:
        self.enforce_order()
        self.validate(strict=True)
        return self.df.copy()

    @classmethod
    def from_records(cls, records: list[dict], columns: list[str], dtypes: dict[str, str], label: str = "DataFrame"):
        df = pd.DataFrame.from_records(records)
        return cls(df, columns, dtypes, label)
