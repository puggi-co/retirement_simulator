# =================== WITHDRAWAL (WD) SIMULATION RUNNER ===================

import pandas as pd
from pathlib import Path
from typing import Any, Optional

from orchestration import outcome_ledger
from src.context.context import SimulationContext
from orchestration.orch_entity import (
    WDRunResults,
    WDMetadata,
    WDStrategyResults
)

from src.core.schedule import SimulationSchedule
from src.core.spending_util import SpendingModel
from orchestration.outcome_ledger import build_outcome_from_ledger
from withdrawal.wd_run_simulation import simulate_withdrawal
from withdrawal.wd_ledger import WithdrawalLedger
from withdrawal.wd_analyze_summary import wd_summarize_outcomes
from withdrawal.wd_analyze_util import summarize_spending_sources

from src.io.export_util import debug_view

class WithdrawalRunner:
    '''Manages the withdrawal simulation process'''

    REQUIRED_PORTFOLIO_COLUMNS = [
        'base_balance', 'account_type', 'filing_status'
    ]

    REQUIRED_WITHDRAWAL_COLUMNS = [
        'sim_mode', 'sim_id', 'sim_rate',
        'base_balance', 'wd_amount', 'wd_type', 'shortfall_amount',
        'account_name', 'account_type', 'year'
    ]

    def __init__(self, context: SimulationContext, schedule: SimulationSchedule, portfolio_df: pd.DataFrame, tax_table: Any):
        self.context = context
        self.schedule = schedule
        self.portfolio_df = portfolio_df
        self.tax_table = tax_table
        self.spending_model = SpendingModel(
            config=context.config,
            context=context,
            schedule=schedule
        )   
        self.results: Optional[WDStrategyResults] = None
        self.spending_summary: Optional[pd.DataFrame] = None

    def run(self) -> WDStrategyResults:
        print(f'🎲 Running Withdrawal simulation [{self.context.sim_id}]...')
        print(f'   • Mode: {self.context.sim_mode}')
        print(f'   • Duration: {self.schedule.duration} years')

        # Step 1: Prepare portfolio
        wd_portfolio_df = self._prepare_wd_portfolio(self.portfolio_df)
        self._validate_portfolio(wd_portfolio_df)
        self.context.portfolio = wd_portfolio_df
        debug_view(wd_portfolio_df, '1. WithdrawalRunner - Prepared Portfolio')

        # Step 2: Run simulation
        wd_ledger = WithdrawalLedger(config=self.context.config)

        raw_data = simulate_withdrawal(
            context=self.context,
            schedule=self.schedule,
            tax_table=self.tax_table,
            spending_model=self.spending_model,
            portfolio_df=wd_portfolio_df,
            wd_ledger=wd_ledger
        )
        debug_view(wd_ledger.frame.df, '2. WithdrawalRunner - Withdrawal Ledger')

        # Step 3: Wrap raw results
        outcome_ledger = build_outcome_from_ledger(wd_ledger, self.context, self.schedule, self.spending_model)
        outcome_ledger.validate_consistency(wd_ledger.frame.df)
    
        run_results = WDRunResults(
            dashboard_df=raw_data['df_dashboard'],
            annotations=raw_data['all_annotations'],
            total_withdrawn=raw_data['total_withdrawn'],
            outcome_ledger=outcome_ledger,
            wd_ledger=wd_ledger
        )
#        debug_view(run_results.annotations, '3. WithdrawalRunner - Year Annotations')
#        debug_view(run_results.dashboard_df, '3. WithdrawalRunner - Dashboard DataFrame')
        debug_view(run_results.outcome_ledger.frame.df, '3. WithdrawalRunner - Outcome Ledger')

        # Step 4: Analyze results
        analysis = wd_summarize_outcomes(run_results.outcome_ledger)

        # Step 5: Metadata
        metadata = WDMetadata(
            sim_id=self.context.sim_id,
            return_rate=self.context.return_rate,
            duration=self.schedule.duration,
            sim_mode=self.context.sim_mode,
            success=True
        )

        # Step 6: Store results
        self.results = WDStrategyResults(
            run=run_results,
            analysis=analysis,
            metadata=metadata
        )

        self.spending_summary = summarize_spending_sources(wd_ledger)

        return self.results

    def export(self, output_folder: Path) -> None:
        """Export withdrawal simulation results"""
        if not self.results:
            raise RuntimeError("Withdrawal results not available.")

        excel_path = output_folder / f"{self.context.sim_id}_withdrawal.xlsx"
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            self.results.run.wd_ledger.frame.df.to_excel(writer, sheet_name='Withdrawal Ledger', index=False)
            self.results.run.outcome_ledger.frame.df.to_excel(writer, sheet_name='Withdrawals', index=False)
            if self.spending_summary is not None:
                self.spending_summary.to_excel(writer, sheet_name='Spending Summary', index=False)

        print(f"💾 Withdrawal results exported: {excel_path}")

    def preview_summary(self):
        if self.results and self.results.analysis:
            print('\n🧾 Goal Success:'); print(self.results.analysis.goal_success)
            print('\n🚧 Depletion Flags:'); print(self.results.analysis.depletion_flags)
            print('\n📈 Withdrawal Efficiency:'); print(self.results.analysis.withdrawal_efficiency)
            print('\n📅 RMD Trigger Ages:'); print(self.results.analysis.rmd_trigger_ages)
        else:
            print('No analysis available yet.')

    def _validate_portfolio(self, df: pd.DataFrame):
        missing = [col for col in self.REQUIRED_PORTFOLIO_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required portfolio columns: {missing}")

    def _prepare_wd_portfolio(self, df_portfolio: pd.DataFrame) -> pd.DataFrame:
        """Augments user portfolio with computed columns needed for simulation."""
        wd_portfolio_df = df_portfolio.copy()

        wd_portfolio_df['year'] = None
        wd_portfolio_df['age'] = None

        base_balance = wd_portfolio_df['base_balance']
        wd_portfolio_df['current_balance'] = base_balance
        wd_portfolio_df['end_balance'] = base_balance

        wd_portfolio_df['sim_mode'] = self.context.sim_mode
        wd_portfolio_df['sim_id'] = self.context.sim_id
        wd_portfolio_df['sim_rate'] = self.context.sim_rate

        wd_portfolio_df['withdraw_type'] = 'none'
        wd_portfolio_df[['withdraw_amount', 'taxable_gain', 'taxable_income', 'tax_owed', 'effective_tax_rate']] = 0.0

        wd_portfolio_df = wd_portfolio_df[[  # column ordering
            'year', 'age', 'sim_mode', 'sim_id', 'sim_rate',
            'current_balance', 'end_balance', 'withdraw_amount', 'withdraw_type',
            'taxable_gain', 'taxable_income', 'tax_owed', 'effective_tax_rate',
            'base_balance', 'distribution_year', 'distribution_age', 'distribution_table',
            'account_name', 'account_type', 'account_tax_type', 'filing_status'
        ]]

        return wd_portfolio_df
