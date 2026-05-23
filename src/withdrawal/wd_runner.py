# =================== WITHDRAWAL (WD) SIMULATION RUNNER ===================

import pandas as pd
from pathlib import Path
from typing import Any, Optional

from context.context import SimulationContext
from orchestration.orch_entity import (
    WDRunResults,
    WDMetadata,
    WDStrategyResults
)

from core.spending_util import SpendingModel
from withdrawal.wd_outcome import build_outcome_from_ledger
from withdrawal.wd_engine_runner import run_withdrawal_simulation
from withdrawal.wd_ledger import WithdrawalLedger
from withdrawal.wd_util import summarize_spending_sources, wd_summarize_outcomes

from loader.export_util import debug_view

class WithdrawalRunner:
    '''Manages the withdrawal simulation process'''

    REQUIRED_PORTFOLIO_COLUMNS = [
        'base_balance', 'source_type', 'filing_status'
    ]

    REQUIRED_WITHDRAWAL_COLUMNS = [
        'strategy_id', 'sim_mode', 'sim_rate',
        'base_balance', 'wd_amount', 'wd_type', 'shortfall_amount',
        'source_name', 'source_type', 'year'
    ]

    def __init__(self, context: SimulationContext, portfolio_df: pd.DataFrame, tax_table: Any):
        
        self.context = context
        self.schedule = context.schedule
        self.portfolio_df = portfolio_df
        self.spending_model = SpendingModel(
            config=context.config,
            context=context,
            schedule=context.schedule
        )

        self.results: Optional[WDStrategyResults] = None
        self.spending_summary: Optional[pd.DataFrame] = None

    def run(self) -> WDStrategyResults:
        print(f'🎲 Running Withdrawal simulation [{self.context.strategy_id}]...')
        print(f'   • Mode: {self.context.sim_mode}')
        print(f'   • Duration: {self.schedule.duration} years')

        # Step 1: Prepare portfolio
        wd_portfolio_df = self._prepare_wd_portfolio(self.portfolio_df)
        self._validate_portfolio(wd_portfolio_df)
        self.context.portfolio = wd_portfolio_df
        debug_view(wd_portfolio_df, '1. WithdrawalRunner - Prepared Portfolio')

        # Step 2: Run simulation
        wd_ledger = WithdrawalLedger(context=self.context)

        raw_data = run_withdrawal_simulation(
            context=self.context,
            spending_model=self.spending_model,
            portfolio_df=wd_portfolio_df,
            wd_ledger=wd_ledger
        )
        debug_view(wd_ledger.frame.df, '2. WithdrawalRunner - Withdrawal Ledger')

        # Step 3: Wrap raw results
        wd_outcome = build_outcome_from_ledger(wd_ledger, self.context, self.spending_model)
        wd_outcome.validate_consistency(wd_ledger.frame.df)
    
        run_results = WDRunResults(
            dashboard_df=raw_data['df_dashboard'],
            annotations=raw_data['all_annotations'],
            total_withdrawn=raw_data['total_withdrawn'],
            wd_outcome=wd_outcome,
            wd_ledger=wd_ledger
        )
        debug_view(run_results.annotations, '3. WithdrawalRunner - Year Annotations')
        debug_view(run_results.dashboard_df, '3. WithdrawalRunner - Dashboard DataFrame')
        debug_view(run_results.wd_outcome.frame.df, '3. WithdrawalRunner - Outcome Ledger')

        # Step 4: Analyze results
        analysis = wd_summarize_outcomes(run_results.wd_outcome)

        # Step 5: Metadata
        metadata = WDMetadata(
            duration=self.schedule.duration,
            strategy_id=self.context.strategy_id,
            sim_mode=self.context.sim_mode,
            return_rate=self.context.return_rate,
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

        excel_path = output_folder / f"{self.context.strategy_id}_withdrawal.xlsx"
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            self.results.run.wd_ledger.frame.df.to_excel(writer, sheet_name='Withdrawal Ledger', index=False)
            self.results.run.wd_outcome.frame.df.to_excel(writer, sheet_name='Outcome Summary', index=False)
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

    def _prepare_wd_portfolio(self, portfolio_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare portfolio for withdrawal simulation.

        - Preserve enriched RMD fields (distribution_year, distribution_age, etc.)
        - DO NOT touch owner_age (belongs to portfolio enrichment)
        - Set simulation age from schedule
        - Set simulation year from schedule
        """

        schedule = self.context.schedule
        df = portfolio_df.copy()

        # ---------------------------------------------------------
        # 1. Simulation temporal fields
        # ---------------------------------------------------------
        df['year'] = schedule.base_year
        df['age'] = schedule.base_age   # simulation age (your age)

        # ---------------------------------------------------------
        # 2. Simulation metadata
        # ---------------------------------------------------------
        df['strategy_id'] = self.context.strategy_id
        df['sim_mode'] = self.context.sim_mode
        df['sim_rate'] = self.context.sim_rate

        # ---------------------------------------------------------
        # 3. Initialize balances
        # ---------------------------------------------------------
        df['current_balance'] = df['base_balance']
        df['end_balance'] = df['base_balance']

        # ---------------------------------------------------------
        # 4. Initialize withdrawal/tax fields
        # ---------------------------------------------------------
        df['withdraw_amount'] = 0.0
        df['withdraw_type'] = 'none'
        df['taxable_gain'] = 0.0
        df['taxable_income'] = 0.0
        df['tax_owed'] = 0.0
        df['effective_tax_rate'] = 0.0
        df['effective_distribution_age'] = df['distribution_age']
        df['effective_distribution_year'] = df['distribution_year']

        return df
