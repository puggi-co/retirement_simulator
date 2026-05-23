import pandas as pd
from typing import Literal, Optional

from montecarlo.mc_schema import (
    MC_OUTCOME_SCHEMA_COLUMNS,
    MC_OUTCOME_SCHEMA_DTYPES,
    MC_OUTCOME_SCHEMA_VERSION
)
from core.schema_frame import SchemaFrame

class BaseOutcome:
    """Base class for simulation-wide outcomes."""

    def __init__(self):
        empty_df = pd.DataFrame({
            col: pd.Series(dtype=MC_OUTCOME_SCHEMA_DTYPES[col])
            for col in MC_OUTCOME_SCHEMA_COLUMNS
        })
        self.frame = SchemaFrame(
            df=empty_df,
            columns=MC_OUTCOME_SCHEMA_COLUMNS,
            dtypes=MC_OUTCOME_SCHEMA_DTYPES,
            label="MC Outcome Ledger"
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

    def final_balance(self) -> float:
        df = self.frame.df
        if df.empty:
            return 0.0
        return float(df['end_balance'].iloc[-1])


class MCOutcome(BaseOutcome):
    """Ledger for Monte Carlo simulation results."""

    def add_year(
        self, *,
        year: int,
        age: int,
        sim_num: int,
        base_balance: float,
        end_balance: float,
        income_amount: float,
        mc_amount: float,
        mc_return_rate: float,
        strategy_id: str,
        sim_mode: str,
        sim_rate: float,
        shortfall_amount: float,
        goal_met: Optional[bool],
        rmd_met: Optional[bool],
        synthetic_flag: bool,
        mc_failure_flag: bool,
        mc_percentile: float
    ):
        self.add_row({
            'year': year,
            'age': age,
            'sim_num': sim_num,

            'base_balance': round(base_balance, 2),
            'end_balance': round(end_balance, 2),
            'income_amount': round(income_amount, 2),
            'mc_amount': round(mc_amount, 2),
            'mc_return_rate': round(mc_return_rate, 4),

            'shortfall_amount': round(shortfall_amount, 2),
            'goal_met': goal_met,
            'rmd_met': rmd_met,
            'synthetic_flag': synthetic_flag,

            'sim_type': 'mc',
            'strategy_id': strategy_id,
            'sim_mode': sim_mode,
            'sim_rate': sim_rate,
            'mc_failure_flag': mc_failure_flag,
            'mc_percentile': mc_percentile,
            'schema_version': MC_OUTCOME_SCHEMA_VERSION
        })
