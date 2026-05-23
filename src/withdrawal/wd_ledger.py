# wd_ledger.py – Records withdrawal details: amounts, types, tax effects, closure flags

import pandas as pd
from typing import Any

from context.context import SimulationContext
from core.schema_frame import SchemaFrame
from withdrawal.wd_schema import (
    WD_LEDGER_SCHEMA_COLUMNS,
    WD_LEDGER_SCHEMA_DTYPES,
    WD_LEDGER_SCHEMA_VERSION
)

class WithdrawalLedger:
    """
    Tracks one account's year-by-year withdrawal ledger and 
    provides writer methods to record what happened.
    """

    def __init__(self, context: SimulationContext):

        # Strategy metadata
        self.strategy_id = context.strategy_id
        self.sim_mode = context.sim_mode
        self.sim_type = context.sim_type

        # Simulation parameters
        self.sim_rate = context.return_rate
        self.spending_target = context.config.spending_target
        self.withdrawal_rate = context.config.withdrawal_rate

        # Create empty schema‑aligned DataFrame
        empty_df = pd.DataFrame({
            col: pd.Series(dtype=WD_LEDGER_SCHEMA_DTYPES[col])
            for col in WD_LEDGER_SCHEMA_COLUMNS
        })

        self.frame = SchemaFrame(
            df=empty_df,
            columns=WD_LEDGER_SCHEMA_COLUMNS,
            dtypes=WD_LEDGER_SCHEMA_DTYPES,
            label="Withdrawal Ledger"
        )

    # ==================================================================
    # ADD YEAR — MAIN WRITER
    # ==================================================================
    def add_year(
        self,
        account: pd.Series,
        year: int,
        age: int,
        current_balance: float,
        end_balance: float,
        wd_type: str = 'none',
        wd_amount: float = 0.0,
        taxable_income: float = 0.0,
        taxable_gain: float = 0.0,
        marginal_rate: float = 0.0,
        closure_met: bool = False,
        guardrail_triggered=None,
        guardrail_direction=None
    ):

        row = {
            # Temporal
            'year': year,
            'age': age,

            # Balances
            'base_balance': account['base_balance'],
            'current_balance': round(current_balance, 2),
            'end_balance': round(end_balance, 2),

            # Withdrawal
            'wd_type': wd_type,
            'wd_amount': round(wd_amount, 2),

            # Taxation
            'taxable_income': round(taxable_income, 2),
            'taxable_gain': round(taxable_gain, 2),
            'marginal_rate': marginal_rate,

            # Account Attribution (static)
            'source_name': account['source_name'],
            'source_type': account['source_type'],
            'source_tax_type': account['source_tax_type'],
            'filing_status': account['filing_status'],

            # RMD / Distribution (static)
            'distribution_year': int(account['distribution_year']),
            'distribution_age': int(account['distribution_age']),
            'distribution_table': account.get('distribution_table', 'unknown'),

            # Simulation Outcomes (dynamic)
            'closure_met': closure_met,
            'guardrail_triggered': guardrail_triggered,
            'guardrail_direction': guardrail_direction,

            # Metadata
            'strategy_id': self.strategy_id,
            'sim_type': self.sim_type,
            'sim_mode': self.sim_mode,
            'return_rate': self.sim_rate,
            'spending_target': self.spending_target,
            'withdrawal_rate': self.withdrawal_rate,
            'schema_version': WD_LEDGER_SCHEMA_VERSION,
        }

        self.frame.df.loc[len(self.frame.df)] = row

    # ==================================================================
    # VALIDATION / EXPORT
    # ==================================================================
    def validate_schema(self):
        self.frame.validate(strict=True)

    def export(self) -> pd.DataFrame:
        return self.frame.export()
