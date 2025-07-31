# simulation/ledger_writer.py

from dataclasses import dataclass
import pandas as pd
from typing import Optional

@dataclass
class LedgerWriterMixin:
    """
    Mixin that encapsulates methods for writing structured financial entries 
    to the simulation ledger.
    """

    def record_income_to_ledger(
        self,
        ledger,
        account: pd.Series,
        year: int,
        age: int,
        growth_rate: float,
        current_balance: float,
        end_balance: Optional[float] = None,
        taxable_income: float = 0.0,
        taxable_ssa: float = 0.0
    ) -> None:
        """Records income stream details to the ledger for a given account/year."""
        if end_balance is None:
            end_balance = current_balance

        ledger.add_year(
            year=year,
            age=age,
            return_rate=growth_rate,
            withdrawal_mode=account['account_type'],
            account_name=account['account_name'],
            account_type=account['account_type'],
            account_tax_type=account['account_tax_type'],
            filing_status=account['filing_status'],
            begin_balance=account['begin_balance'],
            current_balance=round(current_balance, 2),
            end_balance=round(end_balance, 2),
            withdraw_amount=round(current_balance, 2),
            omd=0.0,
            rmd=0.0,
            ord_inc=round(current_balance if account['account_type'] != 'ssa_income' else 0.0, 2),
            ssa_inc=round(current_balance if account['account_type'] == 'ssa_income' else 0.0, 2),
            roth_convert_amount=0.0,
            taxable_income=round(taxable_income, 2),
            taxable_gain=0.0,
            taxable_ssa=round(taxable_ssa, 2),
            tax_owed=0.0,
            effective_tax_rate=0.0,
            rmd_begin_year=account.get('rmd_begin_year', 0),
            rmd_age=account['rmd_age'],
            rmd_table=account['rmd_table']
        )

    def record_withdrawal_to_ledger(
        self,
        ledger,
        account: pd.Series,
        year: int,
        age: int,
        withdraw_amount: float,
        begin_balance: float,
        end_balance: float,
        growth_rate: float = 0.0,
        taxable_income: float = 0.0
    ) -> None:
        """Records withdrawal details to the ledger for a given account/year."""
        ledger.add_year(
            year=year,
            age=age,
            return_rate=growth_rate,
            withdrawal_mode=self.withdrawal_mode,
            account_name=account['account_name'],
            account_type=account['account_type'],
            account_tax_type=account['account_tax_type'],
            filing_status=account['filing_status'],
            begin_balance=begin_balance,
            current_balance=begin_balance,
            end_balance=end_balance,
            withdraw_amount=withdraw_amount,
            ord_inc=round(withdraw_amount, 2),
            roth_convert_amount=0.0,
            rmd=0.0,
            omd=0.0,
            taxable_income=round(taxable_income, 2),
            effective_tax_rate=0.0,
            tax_owed=0.0,
            ssa_inc=0.0,
            taxable_ssa=0.0,
            rmd_begin_year=account.get('rmd_begin_year', 0),
            rmd_age=account['rmd_age'],
            rmd_table=account['rmd_table']
        )

    def record_real_spend_to_ledger(
        self,
        ledger,
        account: pd.Series,
        year: int,
        age: int,
        nominal_spend: float,
        ydx: int,
        growth_rate: float = 0.0
    ) -> None:
        """Records inflation-adjusted spend to the ledger for a given account/year."""
        real_spend = self.adjust_for_real_spend(nominal_spend, ydx)

        ledger.add_year(
            year=year,
            age=age,
            return_rate=growth_rate,
            withdrawal_mode=self.withdrawal_mode,
            account_name=account['account_name'],
            account_type=account['account_type'],
            account_tax_type=account['account_tax_type'],
            filing_status=account['filing_status'],
            begin_balance=nominal_spend,
            current_balance=nominal_spend,
            end_balance=0.0,
            withdraw_amount=round(nominal_spend, 2),
            ord_inc=round(real_spend, 2),
            ssa_inc=0.0,
            roth_convert_amount=0.0,
            rmd=0.0,
            omd=0.0,
            taxable_income=round(real_spend, 2),
            taxable_gain=0.0,
            taxable_ssa=0.0,
            tax_owed=0.0,
            effective_tax_rate=0.0,
            rmd_begin_year=account.get('rmd_begin_year', 0),
            rmd_age=account['rmd_age'],
            rmd_table=account['rmd_table']
        )
