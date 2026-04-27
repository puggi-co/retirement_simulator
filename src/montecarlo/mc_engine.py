# ── 2. MONTE CARLO ENGINE ─────────────────────────────────────

import pandas as pd
import numpy as np

from typing import List, Any

from src.context.context import SimulationContext
from src.core.schedule import SimulationSchedule
from src.io.tax_loader import TaxTable
from src.montecarlo.mc_simulator import MonteCarloSimulator
from src.montecarlo.mc_summary_core import MonteCarloAnalyzer

class MonteCarloEngine:
    """
    Core Monte Carlo simulation engine - orchestrates the entire MC process
    """
    
    def __init__(self, context: SimulationContext, schedule: SimulationSchedule, tax_table: TaxTable = None,
                 failure_thresholds: List[int] = None):
        self.context = context
        self.schedule = schedule
        self.tax_table = tax_table
        self.failure_thresholds = failure_thresholds or [0, 100_000, 250_000]
        
        # Initialize components
        self.simulator = MonteCarloSimulator(context, schedule, tax_table, failure_thresholds=self.failure_thresholds)
        self.analyzer = MonteCarloAnalyzer(failure_thresholds=self.failure_thresholds)

    def simulate(self, portfolio_df: pd.DataFrame, 
                num_simulations: int = 1000) -> pd.DataFrame:
        """
        Execute Monte Carlo simulations
        
        Returns:
            DataFrame with all simulation results
        """
        
        # Validate inputs
        self._validate_inputs(portfolio_df, num_simulations)
        
        # Run simulations
        outcome_ledger = self.simulator.run_simulations(
            portfolio_df=portfolio_df,
            num_simulations=num_simulations
        )

        return outcome_ledger
    
    def analyze_results(self, results_df: pd.DataFrame) -> Any:
        """Analyze Monte Carlo results and return summary statistics"""
        return self.analyzer.analyze(results_df)
    
    def _validate_inputs(self, portfolio_df: pd.DataFrame, num_simulations: int) -> None:
        """Validate simulation inputs"""
        
        required_cols = ['account_tax_type', 'base_balance', 'account_type']
        missing_cols = [col for col in required_cols if col not in portfolio_df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required portfolio columns: {missing_cols}")
            
        if num_simulations < 1:
            raise ValueError("Number of simulations must be positive")
            
        if not self.schedule:
            raise ValueError("Context must have a valid schedule")
