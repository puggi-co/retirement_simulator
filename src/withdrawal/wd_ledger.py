# wd_ledger.py – Records withdrawal details: amounts, types, tax effects, closure flags

import pandas as pd
from typing import Any, Dict

from config.config_schema import SimulationConfig
from src.core.schema_frame import SchemaFrame
from src.core.schema_constants import (
    WD_LEDGER_SCHEMA_COLUMNS, WD_LEDGER_SCHEMA_DTYPES, WD_LEDGER_OVERRIDE_COLUMNS
)
from src.core.schema_util import WD_TAX_TYPE_MAP

class WithdrawalLedger:
    """
    Tracks one account's year-by-year withdrawal ledger and 
    provides writer methods to record what happened.
    """
    def __init__(self, config: SimulationConfig):
        metadata = self.extract_metadata(config)
        self.sim_id = metadata['sim_id']
        self.sim_type = metadata['sim_type']
        self.sim_mode = metadata['sim_mode']
        self.sim_rate = metadata['return_rate']
        self.inflation_rate = metadata['inflation_rate']
        self.spending_target = metadata['spending_target']
        self.withdrawal_rate = metadata['withdrawal_rate']
        self.config = config
        self.metadata = metadata

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

    def add_year(self, account: pd.Series, year: int, age: int,
                current_balance: float, end_balance: float,
                wd_type: str = 'none', wd_amount: float = 0.0,
                taxable_income: float = 0.0, taxable_gain: float = 0.0,
                overrides: dict[str, Any] = None):
        
        row = {
            # 📅 Temporal Alignment
            'year': year,
            'age': age,

            # 🧠 Simulation Metadata
            'sim_id': self.sim_id,
            'sim_type': self.sim_type,
            'sim_mode': self.sim_mode,
            'return_rate': self.sim_rate,
            'inflation_rate': self.inflation_rate,
            'spending_target': self.spending_target,
            'withdrawal_rate': self.withdrawal_rate,

            # 💰 Financial Metrics
            'base_balance': account['base_balance'],
            'current_balance': round(current_balance, 2),
            'end_balance': round(end_balance, 2),
            'wd_amount': round(wd_amount, 2),
            'wd_type': wd_type,
            'wd_tax_type': WD_TAX_TYPE_MAP.get(wd_type, 'unknown'),
            'wd_indicator': wd_amount > 0,
            'closure_met': wd_amount >= current_balance and wd_type not in ['inc_fers', 'inc_ssa', 'inc_ord'],
            'withdrawal_efficiency': 0.0,  # optional enrichment

            # 💰 Taxation
            'taxable_income': round(taxable_income, 2),
            'taxable_gain': round(taxable_gain, 2),

            # 🏦 Account Attribution
            'account_name': account['account_name'],
            'account_type': account['account_type'],
            'account_tax_type': account['account_tax_type'],
            'filing_status': account['filing_status'],
            'owner_age': account.get('owner_age', age),
            'distribution_year': int(account['distribution_year']),
            'distribution_age': int(account['distribution_age']),
            'distribution_table': account.get('distribution_table', 'unknown'),

            # 🛠 Overrides (defaults)
            'guardrail_triggered': False,
            'guardrail_direction': '',
            'guardrail_type': '',
            'guardrail_rate_high': 0.0,
            'guardrail_rate_low': 0.0,
            'guardrail_amount_high': 0.0,
            'guardrail_amount_low': 0.0,
            'synthetic_flag': False,
            'shortfall_flag': False,
            'shortfall_amount': 0.0
        }

        if overrides:
            for key, value in overrides.items():
                if key in WD_LEDGER_OVERRIDE_COLUMNS:
                    row[key] = value

        self.frame.df = pd.concat([self.frame.df, pd.DataFrame([row])], ignore_index=True)
 

    def add_shortfall(self, year: int, age: int, target: float, actual: float, filing_status: str):
        shortfall = max(0.0, target - actual)

        self.add_year(
            account=pd.Series({
                'account_name': 'shortfall',
                'account_type': 'synthetic',
                'account_tax_type': 'none',
                'filing_status': filing_status,
                'base_balance': 0.0,
                'distribution_year': year,
                'distribution_age': age
            }),
            year=year,
            age=age,
            current_balance=0.0,
            end_balance=0.0,
            wd_type='none',
            wd_amount=0.0,
            taxable_income=0.0,
            taxable_gain=0.0,
            overrides={
                'synthetic_flag': True,
                'shortfall_flag': True,
                'shortfall_amount': shortfall
            }
        )

    def add_guardrail(self, account: pd.Series, year: int, age: int,
                    current_balance: float, end_balance: float,
                    guardrail_type: str, direction: str,
                    rate_low: float = 0.0, rate_high: float = 0.0,
                    amount_low: float = 0.0, amount_high: float = 0.0):
        
        self.add_year(
            account=account,
            year=year,
            age=age,
            current_balance=current_balance,
            end_balance=end_balance,
            wd_type='none',
            wd_amount=0.0,
            taxable_income=0.0,
            taxable_gain=0.0,
            overrides={
                'guardrail_triggered': True,
                'guardrail_type': guardrail_type,
                'guardrail_direction': direction,
                'guardrail_rate_low': rate_low,
                'guardrail_rate_high': rate_high,
                'guardrail_amount_low': amount_low,
                'guardrail_amount_high': amount_high
            }
        )

    def initialize_from_portfolio(self, portfolio_df: pd.DataFrame):
        for _, account in portfolio_df.iterrows():
            self.add_year(
                account=account,
                year=account['distribution_year'],
                age=account['distribution_age'],
                current_balance=account['base_balance'],
                end_balance=account['base_balance']
            )

    def validate_schema(self):
        self.frame.validate(strict=True)

    def export(self) -> pd.DataFrame:
        return self.frame.export()

    @staticmethod
    def extract_metadata(config: SimulationConfig) -> Dict[str, Any]:
        return {
            # 🧠 Simulation Metadata
            'sim_id': 'wd_fixed_rate',
            'sim_type': 'wd',
            'sim_mode': 'fixed_rate',
            'return_rate': config.return_low_rate,
            'inflation_rate': config.inflation_rate,
            'spending_target': config.spending_target,
            'withdrawal_rate': config.withdrawal_rate,
            'guardrail_rate_high': config.guardrail_rate_high,
            'guardrail_rate_low': config.guardrail_rate_low,
            'guardrail_amount_high': config.guardrail_amount_high,
            'guardrail_amount_low': config.guardrail_amount_low
        }
