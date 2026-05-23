# MONTE CARLO ENGINE 

import pandas as pd
from typing import Any, List

from context.context import SimulationContext
from loader.tax_loader import TaxTable
from montecarlo.mc_simulator import MonteCarloSimulator
from montecarlo.mc_summary_core import MonteCarloAnalyzer

class MonteCarloEngine:
    """
    Core Monte Carlo simulation engine - orchestrates the entire MC process
    """
    
    def __init__(self, context: SimulationContext, tax_table: TaxTable = None,
                 failure_thresholds: List[int] = None):

        self.context = context
        self.schedule = context.schedule                     # ✔ unified schedule source
        self.tax_table = tax_table
        self.failure_thresholds = failure_thresholds or [0, 100_000, 250_000]

        # Initialize components
        self.simulator = MonteCarloSimulator(
            context=context,
            tax_table=tax_table,
            failure_thresholds=self.failure_thresholds
        )

        self.analyzer = MonteCarloAnalyzer(
            failure_thresholds=self.failure_thresholds
        )

    def simulate(self, num_simulations: int = 1000) -> pd.DataFrame:
        """
        Execute Monte Carlo simulations
        
        Returns:
            DataFrame with all simulation results
        """
        
        # Validate inputs
        self._validate_inputs(num_simulations)
        
        # Run simulations
        outcome = self.simulator.run_simulations(
            num_simulations=num_simulations
        )

        return outcome
    
    def analyze_results(self, results_df: pd.DataFrame) -> Any:
        """Analyze Monte Carlo results and return summary statistics"""
        return self.analyzer.analyze(results_df)
    
    def _validate_inputs(self, num_simulations: int) -> None:
        """Validate simulation inputs"""

        portfolio_df = self.context.portfolio
            
        required_cols = ['source_tax_type', 'base_balance', 'source_type']
        missing_cols = [col for col in required_cols if col not in portfolio_df.columns]
            
        if missing_cols:
            raise ValueError(f"Missing required portfolio columns: {missing_cols}")
                
        if num_simulations < 1:
            raise ValueError("Number of simulations must be positive")
                
        if not self.schedule:
            raise ValueError("Context must have a valid schedule")
