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


class BaseOutcome:
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


class WDOutcome(BaseOutcome):
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
        """
        Validate that the outcome ledger is consistent with the WD ledger.
        No asserts. Raises ValueError with detailed diagnostics if mismatches occur.
        """

        errors = []

        for _, row in outcome_df.iterrows():
            year = row['year']
            ledger_year = wd_ledger_df[wd_ledger_df['year'] == year]

            # --- Compute ledger-based income ---
            ledger_income = ledger_year[
                ledger_year['wd_type'].str.startswith('inc_')
            ]['wd_amount'].sum()

            # --- Compute ledger-based total withdrawals ---
            ledger_total_wd = ledger_year['wd_amount'].sum()

            # --- Compute ledger-based portfolio withdrawals ---
            ledger_portfolio_amount = ledger_total_wd - ledger_income

            # --- Compare portfolio_amount ---
            if abs(row['portfolio_amount'] - ledger_portfolio_amount) > 1e-6:
                errors.append(
                    f"[Year {year}] portfolio_amount mismatch: "
                    f"outcome={row['portfolio_amount']}, "
                    f"ledger={ledger_portfolio_amount}"
                )

            # --- Compare income_amount ---
            if abs(row['income_amount'] - ledger_income) > 1e-6:
                errors.append(
                    f"[Year {year}] income_amount mismatch: "
                    f"outcome={row['income_amount']}, "
                    f"ledger={ledger_income}"
                )

            # --- Compare base_balance ---
            ledger_base_balance = ledger_year['base_balance'].sum()
            if abs(row['base_balance'] - ledger_base_balance) > 1e-6:
                errors.append(
                    f"[Year {year}] base_balance mismatch: "
                    f"outcome={row['base_balance']}, "
                    f"ledger={ledger_base_balance}"
                )

            # --- Compare end_balance ---
            ledger_end_balance = ledger_year['end_balance'].sum()
            if abs(row['end_balance'] - ledger_end_balance) > 1e-6:
                errors.append(
                    f"[Year {year}] end_balance mismatch: "
                    f"outcome={row['end_balance']}, "
                    f"ledger={ledger_end_balance}"
                )

            # --- Funding math ---
            expected_total = row['income_amount'] + row['portfolio_amount']
            if abs(row['portfolio_funding_total'] - expected_total) > 1e-6:
                errors.append(
                    f"[Year {year}] portfolio_funding_total mismatch: "
                    f"outcome={row['portfolio_funding_total']}, "
                    f"expected={expected_total}"
                )

            expected_delta = row['portfolio_funding_total'] - row['spending_target']
            if abs(row['portfolio_funding_delta'] - expected_delta) > 1e-6:
                errors.append(
                    f"[Year {year}] portfolio_funding_delta mismatch: "
                    f"outcome={row['portfolio_funding_delta']}, "
                    f"expected={expected_delta}"
                )

            expected_goal = row['portfolio_funding_total'] >= row['spending_target']
            if row['goal_met'] != expected_goal:
                errors.append(
                    f"[Year {year}] goal_met mismatch: "
                    f"outcome={row['goal_met']}, "
                    f"expected={expected_goal}"
                )

            # --- RMD flag ---
            rmd_triggered = ledger_year['wd_type'].str.contains('ira_rmd', case=False, na=False).any()
            if row['rmd_met'] != rmd_triggered:
                errors.append(
                    f"[Year {year}] rmd_met mismatch: "
                    f"outcome={row['rmd_met']}, "
                    f"expected={rmd_triggered}"
                )

        # --- Final error reporting ---
        if errors:
            message = "Outcome ledger consistency check failed:\n" + "\n".join(errors)
            raise ValueError(message)

def build_outcome_from_ledger(
    wd_ledger: WithdrawalLedger,
    context: SimulationContext,
    spending_model: SpendingModel,
) -> WDOutcome:

    schedule = context.schedule
    wd_ledger_df = wd_ledger.frame.df
    wd_outcome = WDOutcome()

    for year in sorted(wd_ledger_df['year'].unique()):
        year_df = wd_ledger_df[wd_ledger_df['year'] == year]

        base_balance = year_df['base_balance'].sum()
        end_balance = year_df['end_balance'].sum()

        # Income (SSA, FERS, pensions)
        income_amount = year_df[
            year_df['wd_type'].str.startswith('inc_')
        ]['wd_amount'].sum()

        # Total withdrawals from all accounts
        total_wd = year_df['wd_amount'].sum()

        # Portfolio withdrawals = total withdrawals minus income
        portfolio_amount = total_wd - income_amount

        # Portfolio withdrawal rate
        portfolio_rate = (
            portfolio_amount / base_balance
            if base_balance > 0 else 0.0
        )

        year_index = year - schedule.base_year
        spending_target = spending_model.get_adjusted_spending(year_index)

        portfolio_funding_total = income_amount + portfolio_amount
        portfolio_funding_delta = portfolio_funding_total - spending_target
        goal_met = portfolio_funding_total >= spending_target

        closure_met = year_df['closure_met'].any()
        rmd_met = year_df['wd_type'].str.contains('ira_rmd', case=False, na=False).any()

        wd_outcome.add_year(
            year=year,
            age=int(year_df['age'].max()),
            base_balance=base_balance,
            end_balance=end_balance,
            income_amount=income_amount,
            portfolio_amount=portfolio_amount,
            portfolio_rate=portfolio_rate,
            spending_target=spending_target,
            portfolio_funding_total=portfolio_funding_total,
            portfolio_funding_delta=portfolio_funding_delta,
            goal_met=goal_met,
            closure_met=closure_met,
            rmd_met=rmd_met,
            strategy_id=context.strategy_id,
            sim_mode=context.sim_mode,
            sim_rate=context.sim_rate,
        )

    wd_outcome.validate_schema()
    return wd_outcome
