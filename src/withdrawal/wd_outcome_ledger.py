import pandas as pd
from typing import Literal

from withdrawal.wd_schema import (
    WD_OUTCOME_SCHEMA_COLUMNS,
    WD_OUTCOME_SCHEMA_DTYPES,
    WD_OUTCOME_SCHEMA_VERSION,
)
from core.schema_frame import SchemaFrame
from core.spending_util import SpendingModel
from context.context import SimulationContext
from withdrawal.wd_ledger import WithdrawalLedger


class OutcomeLedger:
    """Base class for simulation-wide outcomes."""

    def __init__(self):
        empty_df = pd.DataFrame({
            col: pd.Series(dtype=WD_OUTCOME_SCHEMA_DTYPES[col])
            for col in WD_OUTCOME_SCHEMA_COLUMNS
        })
        self.frame = SchemaFrame(
            df=empty_df,
            columns=WD_OUTCOME_SCHEMA_COLUMNS,
            dtypes=WD_OUTCOME_SCHEMA_DTYPES,
            label="WD Outcome Ledger",
        )

    def filter_by_type(self, sim_type: Literal["wd", "mc"]) -> pd.DataFrame:
        return self.frame.df[self.frame.df["sim_type"] == sim_type]

    def add_row(self, row: dict):
        casted_row = {
            col: pd.Series([row.get(col, pd.NA)], dtype=self.frame.dtypes[col])
            for col in self.frame.columns
        }
        self.frame.df = pd.concat([self.frame.df, pd.DataFrame(casted_row)], ignore_index=True)
        self.frame.validate(strict=False)

    def validate_schema(self):
        self.frame.validate(strict=True)

    def export(self) -> pd.DataFrame:
        self.frame.enforce_order()
        self.frame.validate(strict=True)
        return self.frame.df


class WDOutcomeLedger(OutcomeLedger):
    """Specialized ledger for withdrawal simulations."""

    def add_year(
        self, *,
        year: int,
        age: int,
        base_balance: float,
        end_balance: float,
        income_amount: float,
        portfolio_amount: float,
        portfolio_rate: float,
        spending_target: float,
        portfolio_funding_total: float,
        portfolio_funding_delta: float,
        goal_met: bool,
        closure_met: bool,
        rmd_met: bool,
        strategy_id: str,
        sim_mode: str,
        sim_rate: float,
    ):
        self.add_row({
            'year': year,
            'age': age,

            'base_balance': round(base_balance, 2),
            'end_balance': round(end_balance, 2),

            'income_amount': round(income_amount, 2),
            'portfolio_amount': round(portfolio_amount, 2),
            'portfolio_rate': round(portfolio_rate, 4),

            'spending_target': round(spending_target, 2),
            'portfolio_funding_total': round(portfolio_funding_total, 2),
            'portfolio_funding_delta': round(portfolio_funding_delta, 2),

            'goal_met': goal_met,
            'closure_met': closure_met,
            'rmd_met': rmd_met,

            'sim_type': 'wd',
            'strategy_id': strategy_id,
            'sim_mode': sim_mode,
            'sim_rate': sim_rate,
            'schema_version': WD_OUTCOME_SCHEMA_VERSION,
        })

    def validate_consistency(self, wd_ledger_df: pd.DataFrame) -> None:
        self._validate_consistency(self.frame.df, wd_ledger_df)

    @staticmethod
    def _validate_consistency(outcome_df: pd.DataFrame, wd_ledger_df: pd.DataFrame):
        for _, row in outcome_df.iterrows():
            year = row['year']
            ledger_year = wd_ledger_df[wd_ledger_df['year'] == year]

            assert abs(row['portfolio_amount'] - ledger_year['portfolio_amount'].sum()) < 1e-6
            assert abs(
                row['income_amount']
                - ledger_year[ledger_year['wd_type'].str.startswith('inc_')]['portfolio_amount'].sum()
            ) < 1e-6
            assert abs(row['base_balance'] - ledger_year['base_balance'].sum()) < 1e-6
            assert abs(row['portfolio_funding_total'] - (row['income_amount'] + row['portfolio_amount'])) < 1e-6
            assert abs(row['portfolio_funding_delta'] - (row['portfolio_funding_total'] - row['spending_target'])) < 1e-6
            assert row['goal_met'] == (row['portfolio_funding_total'] >= row['spending_target'])

            rmd_triggered = ledger_year['wd_type'].str.contains('ira_rmd', case=False, na=False).any()
            assert row['rmd_met'] == rmd_triggered

    def final_balance(self) -> float:
        df = self.frame.df
        if df.empty:
            return 0.0
        return float(df['end_balance'].iloc[-1])
