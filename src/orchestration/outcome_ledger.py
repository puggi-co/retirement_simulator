import pandas as pd
from typing import Literal, Optional

from src.core.schema_constants import (
    OUTCOME_SCHEMA_COLUMNS,
    OUTCOME_SCHEMA_DTYPES,
    OUTCOME_SCHEMA_GROUPS
)
from src.core.schema_frame import SchemaFrame
from src.core.schedule import SimulationSchedule
from src.core.spending_util import SpendingModel
from src.context.context import SimulationContext
from src.withdrawal.wd_ledger import WithdrawalLedger

class OutcomeLedger:
    """Base class for simulation-wide outcomes. Subclasses specialize per simulation type."""
    def __init__(self):
        empty_df = pd.DataFrame({
            col: pd.Series(dtype=OUTCOME_SCHEMA_DTYPES[col])
            for col in OUTCOME_SCHEMA_COLUMNS
        })
        self.frame = SchemaFrame(
            df=empty_df,
            columns=OUTCOME_SCHEMA_COLUMNS,
            dtypes=OUTCOME_SCHEMA_DTYPES,
            label="Outcome Ledger"
        )

    def filter_by_type(self, sim_type: Literal["wd", "mc"]) -> pd.DataFrame:
        return self.frame.df[self.frame.df["sim_type"] == sim_type]

    def add_row(self, row: dict):
        # Cast row values to expected dtypes
        casted_row = {
            col: pd.Series([row.get(col, pd.NA)], dtype=self.frame.dtypes[col])
            for col in self.frame.columns
        }
        self.frame.df = pd.concat([self.frame.df, pd.DataFrame(casted_row)], ignore_index=True)
        self.frame.validate(strict=False)

    def validate_schema(self):
        self.frame.validate(strict=True)

    def export(self) -> pd.DataFrame:
        self.enforce_order()
        self.validate(strict=True)
        return self.df

class WDOutcomeLedger(OutcomeLedger):
    """Specialized ledger for withdrawal simulations."""

    def add_year(self, *, year: int, age: int, base_balance: float, income_amount: float, wd_amount: float, actual_rate: float, 
                spending_target: float, funding_delta: float, funding_total: float, 
                shortfall_amount: float, goal_met: Optional[bool], rmd_met: Optional[bool], synthetic_flag: bool,
                sim_mode: str, sim_id: str, sim_rate: float):
        
        self.add_row({
            'year': year,
            'age': age,
            'base_balance': round(base_balance, 2),
            'income_amount': round(income_amount, 2),
            'wd_amount': round(wd_amount, 2),
            'actual_rate': round(actual_rate, 4),

            'spending_target': round(spending_target, 2),
            'funding_total': round(funding_total, 2),
            'funding_delta': round(funding_delta, 2),

            'shortfall_amount': round(shortfall_amount, 2),
            'closure_met': (wd_amount >= base_balance),
            'goal_met': goal_met,
            'rmd_met': rmd_met,
            'synthetic_flag': synthetic_flag,

            'sim_type': 'wd',
            'sim_mode': sim_mode,
            'sim_id': sim_id,
            'sim_rate': sim_rate,
            'mc_failure_flag': False,
            'mc_percentile': None
        })

    def validate_consistency(self, wd_ledger_df: pd.DataFrame):
        """Public method for orchestration to validate outcome consistency."""
        self._validate_consistency(self.frame.df, wd_ledger_df)

    @staticmethod
    def _validate_consistency(outcome_df: pd.DataFrame, wd_ledger_df: pd.DataFrame):
        for _, row in outcome_df.iterrows():
            year = row['year']
            ledger_year = wd_ledger_df[wd_ledger_df['year'] == year]

            assert abs(row['wd_amount'] - ledger_year['wd_amount'].sum()) < 1e-6
            assert abs(row['income_amount'] - ledger_year[ledger_year['account_type'].isin(['inc_fers', 'inc_ssa', 'inc_ord'])]['wd_amount'].sum()) < 1e-6
            assert abs(row['base_balance'] - ledger_year['base_balance'].sum()) < 1e-6
            assert abs(row['funding_total'] - (row['income_amount'] + row['wd_amount'])) < 1e-6
            assert abs(row['funding_delta'] - (row['spending_target'] - row['funding_total'])) < 1e-6
            assert row['goal_met'] == (row['funding_delta'] <= 0)

            rmd_triggered = ledger_year['wd_type'].str.contains('ira_rmd', case=False, na=False).any()
            assert row['rmd_met'] == rmd_triggered

class MCOutcomeLedger(OutcomeLedger):
    """Specialized ledger for Monte Carlo simulations."""
    def add_year(self, *, year: int, age: int, base_balance: float, income_amount: float, wd_amount: float, actual_rate: float, 
                 shortfall_amount: float, goal_met: Optional[bool], rmd_met: Optional[bool], synthetic_flag: bool,
                 sim_mode: str, sim_id: str, sim_rate: float,
                 mc_failure_flag: bool, mc_percentile: Optional[float]):

        self.add_row({
            'year': year,
            'age': age,
            'base_balance': round(base_balance, 2),
            'income_amount': round(income_amount, 2),
            'wd_amount': round(wd_amount, 2),
            'actual_rate': round(actual_rate, 4),

            'spending_target': None,
            'funding_total': None,
            'funding_delta': None,

            'shortfall_amount': round(shortfall_amount, 2),
            'closure_met': (wd_amount >= base_balance),
            'goal_met': goal_met,
            'rmd_met': rmd_met,
            'synthetic_flag': synthetic_flag,

            'sim_type': 'mc',
            'sim_mode': sim_mode,
            'sim_id': sim_id,
            'sim_rate': sim_rate,
            'mc_failure_flag': mc_failure_flag,
            'mc_percentile': mc_percentile
        })

def build_outcome_from_ledger(
    wd_ledger: WithdrawalLedger,
    context: SimulationContext,
    schedule: SimulationSchedule,
    spending_model: SpendingModel
) -> WDOutcomeLedger:
    """Builds a WDOutcomeLedger from the WithdrawalLedger and simulation context."""
    wd_ledger_df = wd_ledger.frame.df
    outcome_ledger = WDOutcomeLedger()
    
    for year in sorted(wd_ledger_df['year'].unique()):
        year_df = wd_ledger_df[wd_ledger_df['year'] == year]

        base_balance = year_df['base_balance'].sum()
        wd_amount = year_df['wd_amount'].sum()
        actual_rate = wd_amount / base_balance if base_balance > 0 else 0.0

        income_sources = ['inc_fers', 'inc_ssa', 'inc_ord']
        income_amount = year_df[year_df['account_type'].isin(income_sources)]['wd_amount'].sum()

        shortfall_amount = year_df['shortfall_amount'].sum()
        synthetic_flag = year_df['synthetic_flag'].any()
        
        year_index = year - schedule.base_year
        spending_target = spending_model.get_adjusted_spending(year_index)

        funding_total = income_amount + wd_amount
        funding_delta = spending_target - funding_total
        goal_met = funding_delta <= 0
        rmd_met = year_df['wd_type'].str.contains('ira_rmd', case=False, na=False).any()

        outcome_ledger.add_year(
            year=year,
            age=int(year_df['age'].max()),
            base_balance=base_balance,
            income_amount=income_amount,
            wd_amount=wd_amount,
            actual_rate=actual_rate,
            spending_target=spending_target,
            funding_delta=funding_delta,
            funding_total=funding_total,
            shortfall_amount=shortfall_amount,
            goal_met=goal_met,
            rmd_met=rmd_met,
            synthetic_flag=synthetic_flag,
            sim_mode=context.sim_mode,
            sim_id=context.sim_id,
            sim_rate=context.sim_rate
        )

    outcome_ledger.validate_schema()
    return outcome_ledger
