# ── Workbook Interface ──────────────────────────
import pandas as pd
from src.core.schedule.schedule import SimulationSchedule
from src.interface.input.config_in_xlsx import ConfigInputXls
from pathlib import Path

WORKBOOK_TABS = ['My Account', 'My Income']

class SimInputXls:
    def __init__(self, workbook='RetirementPlan-Input.xlsx'):
        self.workbook = workbook
        self.tabs = WORKBOOK_TABS

        # Load external config
        config_loader = ConfigInputXls()
        self.config = config_loader.config
        self.scenario_config = config_loader.scenario_config
        self.montecarlo_config = config_loader.montecarlo_config

        # Remaining user data
        self.df_my_portfolio = None
        self.sim_schedule = None

        # Registry
        self._registry = {
            'portfolio': lambda: self.df_my_portfolio,
            'scenario': lambda: self.df_scenario,
            'scenario_config': lambda: self.scenario_config,
            'montecarlo_config': lambda: self.montecarlo_config,
            'schedule': lambda: self.sim_schedule
        }

    # ── Loaders ──────────────────────────────────
    def load_workbook(self):
        """Reads Excel sheets and builds structured DataFrames."""
        df_my_account = pd.read_excel(self.workbook, sheet_name='My Account')
        df_my_income = pd.read_excel(self.workbook, sheet_name='My Income')
        self.df_my_portfolio = merge_income_sources(df_my_account, df_my_income)

        self.df_scenario = self.load_scenarios()
        self.sim_schedule = self.compute_sim_schedule(df_my_account)

    def clean_sheet(self, df, required_cols=None, sheet_name=''):
        """Standardizes column names and validates required fields."""
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()

        if required_cols:
            missing = required_cols - set(df.columns)
            if missing:
                raise ValueError(f"❌ Sheet '{sheet_name}' is missing required column(s): {missing}")

        reserved = {'name', 'index', 'values', 'dtype', 'shape', 'size'}
        risky = set(df.columns) & reserved
        if risky:
            print(f"⚠️ Sheet '{sheet_name}': Column(s) {risky} may conflict with pandas attributes. Use row[...] syntax.")

        return df

    def compute_sim_schedule(self, df_my_account):
        """Compute simulation timing parameters based on birth year."""
        begin_year = df_my_account['begin_year'].min()
        begin_age = df_my_account['owner_age'].min()
        duration = self.config.max_age - begin_age
        end_year = begin_year + duration - 1
        end_age = begin_age + duration

        return SimulationSchedule(
            begin_age=int(begin_age),
            begin_year=int(begin_year),
            duration=int(duration),
            end_age=int(end_age),
            end_year=int(end_year)
        )

    def build_schedule(self, schedule_dict) -> SimulationSchedule:
        return SimulationSchedule(
            begin_age=schedule_dict['begin_age'],
            begin_year=schedule_dict['begin_year'],
            duration=schedule_dict['duration'],
            end_age=schedule_dict['end_age'],
            end_year=schedule_dict['end_year']
        )
