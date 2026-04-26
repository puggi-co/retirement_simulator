from altair import param
import pandas as pd
from typing import Dict, Any
from src.config.config_schema import (
    TABS,
    REQUIRED_COLUMNS,
    SimulationConfig
)
from io_input.excel_loader import ExcelSchemaLoader

class SimulationConfigLoader(ExcelSchemaLoader):
    def __init__(self, workbook_path: str):
        self.workbook_path = workbook_path
        self.sheets: Dict[str, pd.DataFrame] = self.load_workbook(
            workbook_path,
            TABS,
            REQUIRED_COLUMNS
        )

    def load(self) -> SimulationConfig:
        df = self.sheets['My_Config']
        return self._cast_to_config(df)

    def _cast_to_config(self, df: pd.DataFrame) -> SimulationConfig:
        valid_fields = SimulationConfig.__annotations__.keys()
        config_kwargs: Dict[str, Any] = {}

        for _, row in df.iterrows():
            param = row['parameter']
            value = row['value']

            if param not in valid_fields:
                print(f"⚠️ Unknown config parameter: {param}")
            elif pd.isna(value):
                print(f"⚠️ Missing value for config parameter: {param}")

            # Optional: handle string-to-type conversion if Excel provides everything as strings
            config_kwargs[param] = self._convert_value(param, value)

        return SimulationConfig(**config_kwargs)

    def _convert_value(self, param: str, value: Any) -> Any:
        annotation = SimulationConfig.__annotations__.get(param)

        # Normalize string values
        def normalize_string(val: Any) -> str:
            return str(val).strip().strip('"').strip("'")

        if annotation == bool:
            val = str(value).strip().strip('"').strip("'").lower()
            if val not in ('true', '1', 'yes', 'false', '0', 'no'):
                print(f"⚠️ Ambiguous boolean for {param}: {value}")
            return val in ('true', '1', 'yes')

        if annotation == int:
            try:
                return int(float(value))
            except (ValueError, TypeError):
                print(f"⚠️ Invalid int for {param}: {value}")
                return 0

        if annotation == float:
            try:
                return float(value)
            except (ValueError, TypeError):
                print(f"⚠️ Invalid float for {param}: {value}")
                return 0.0

        if annotation == str:
            return normalize_string(value)

        # Handle Optional[str | Callable] like mc_return_sampler
        if param == "mc_return_sampler":
            if callable(value):
                return value
            return normalize_string(value)

        return value  # fallback for untyped or complex fields

def get_simulation_config(workbook_path: str) -> SimulationConfig:
    return SimulationConfigLoader(workbook_path).load()
