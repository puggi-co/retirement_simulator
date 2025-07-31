import pandas as pd
from dataclasses import fields
from src.config.config import SimulationConfig

class ConfigInputXls:
    """Loads simulation config from a standalone Excel file."""

    def __init__(self, config_path='data/in_config.xlsx'):
        self.config_path = config_path
        self.df_raw = self.load_config_df()
        self.config, self.scenario_config, self.montecarlo_config = self.split_config(self.df_raw)

    def load_config_df(self):
        df = pd.read_excel(self.config_path, sheet_name=0)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        return df

    def split_config(self, df):
        df[['scenario_default', 'montecarlo_default']] = (
            df[['scenario_default', 'montecarlo_default']]
            .fillna('N')
            .astype(str)
            .apply(lambda s: s.str.strip().str.upper() == 'Y')
        )
        defaults = SimulationConfig()

        def to_config(df_filtered):
            cfg = dict(zip(df_filtered['parameter'], df_filtered['value']))

            def cast(key):
                val = cfg.get(key)
                if pd.isna(val):
                    return getattr(defaults, key)
                try:
                    ref = getattr(defaults, key)
                    if isinstance(ref, bool):
                        val = str(val).strip().lower()
                        return val in ['true', 'yes', '1', 'y']
                    return type(ref)(val)
                except Exception:
                    return getattr(defaults, key)

            return SimulationConfig(**{f.name: cast(f.name) for f in fields(SimulationConfig) if f.init})

        base = to_config(df)
        scenario = to_config(df[df['scenario_default']])
        montecarlo = to_config(df[df['montecarlo_default']])
        return base, scenario, montecarlo
