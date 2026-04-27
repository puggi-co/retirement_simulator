# ── 3. MONTE CARLO SIMULATOR ───────────────────────────────────────────

import pandas as pd
import numpy as np
from typing import Dict, List

from src.context.context import SimulationContext
from src.core.schedule import SimulationSchedule
from src.core.spending_util import SpendingModel
from src.io.tax_loader import TaxTable
from src.orchestration.outcome_ledger import MCOutcomeLedger
from src.montecarlo.mc_year_annotation import YearSimulator, create_downturn_years

from src.io.export_util import debug_view

class MonteCarloSimulator:
    """
    Handles the core Monte Carlo simulation logic
    """
    def __init__(self, context: SimulationContext, schedule: SimulationSchedule,
                 tax_table: TaxTable = None, failure_thresholds: List[int] = None):
        self.context = context
        self.schedule = schedule
        self.tax_table = tax_table
        self.failure_thresholds = failure_thresholds
        self.spending_model = SpendingModel(
            config=context.config,
            context=context,
            schedule=schedule
        )       
        self.year_simulator = YearSimulator(
            context=context,
            schedule=schedule,
            tax_table=tax_table,
            failure_thresholds=self.failure_thresholds
        )

#        print(f"✅ schedule type: {type(schedule)}")

        
    def run_simulations(self, portfolio_df: pd.DataFrame, 
                       num_simulations: int) -> pd.DataFrame:
        """
        Execute multiple Monte Carlo simulation runs
        
        Returns:
            Combined DataFrame with results from all simulations
        """
        
        # Calculate initial portfolio balance
        initial_balance = self._calculate_initial_balance(portfolio_df)
        
        # Initialize outcome tracking
        outcome_ledger = MCOutcomeLedger()

        # Progress tracking
        print(f"Running {num_simulations:,} simulations...")
        milestone = max(1, num_simulations // 10)  # 10% milestones
        
        for sim_num in range(1, num_simulations + 1):
            
            # Progress reporting
            if sim_num % milestone == 0:
                progress = (sim_num / num_simulations) * 100
                print(f"  Progress: {progress:.0f}% ({sim_num:,}/{num_simulations:,})")
            
            # Run single simulation
            sim_results = self._run_single_simulation(
                sim_num=sim_num,
                portfolio_df=portfolio_df,
                initial_balance=initial_balance
            )
            
            # Record results
            self._record_simulation_results(outcome_ledger, sim_results)
        
        return outcome_ledger
    
    def _run_single_simulation(self, sim_num: int, portfolio_df: pd.DataFrame, 
                              initial_balance: float) -> List[Dict]:
        """Run a single Monte Carlo simulation across all years"""
        
        returns = self._generate_return_sequence()
        downturn_years = self._generate_downturn_years()
        balance = initial_balance
        
        sim_results = []
        
        for ydx in range(self.schedule.duration):
            year = self.schedule.year(ydx)
            age = self.schedule.age(ydx)
            
            # Always compute the adjusted target for this year
            adjusted_spend = self.spending_model.get_adjusted_spending(ydx)
  
            # Simulate single year
            year_result = self.year_simulator.simulate_year(
                year=year,
                age=age,
                year_index=ydx,
                return_rate=returns[ydx],
                portfolio_balance=balance,
                withdrawal_target=adjusted_spend,
                portfolio_df=portfolio_df,
                downturn_years=downturn_years,
                sim_num=sim_num
            )
            
            # Update state for next year
            balance = year_result['end_balance']
            
            sim_results.append(year_result)
        
        return sim_results
    
    def _generate_return_sequence(self) -> List[float]:
        """Generate sequence of annual returns for simulation"""
        return [self.context.sample_return(ydx) 
                for ydx in range(self.schedule.duration)]
    
    def _generate_downturn_years(self) -> List[int]:
        """Generate random downturn years for this simulation"""
        return create_downturn_years(
            years=self.schedule.duration,
            seed=self.context.config.mc_seed
        )
    
    def _calculate_initial_balance(self, portfolio_df: pd.DataFrame) -> float:
        """Calculate total initial portfolio balance"""
        investment_accounts = portfolio_df['account_tax_type'].isin(
            ['taxable', 'deferred', 'exempt']
        )
        return portfolio_df.loc[investment_accounts, 'base_balance'].sum()
    
    def _record_simulation_results(self, outcome_ledger: MCOutcomeLedger, 
                                sim_results: List[Dict]) -> None:
        """Record results from a single simulation run"""
        
        for result in sim_results:
            outcome_ledger.add_year(
                # Temporal
                year=result['year'],
                age=result['age'],
                
                # Financial metrics
                base_balance=result['start_balance'],
                income_amount=result.get('income_amount', 0.0),
                wd_amount=result['wd_amount'],
                actual_rate=result.get('actual_rate'),
                
                # Simulation metadata
                sim_mode=self.context.sim_mode,
                sim_id=self.context.sim_id,
                sim_rate=self.context.sim_rate,
                
                # Monte Carlo specific
                shortfall_amount=result.get('shortfall_amount', 0.0),
                goal_met=result.get('goal_met', None),
                rmd_met=result.get('rmd_met', False),
                synthetic_flag=result.get('synthetic_flag', False),
                mc_failure_flag=result.get('mc_failure_flag', False),
                mc_percentile=result.get('mc_percentile', np.nan)
            )
