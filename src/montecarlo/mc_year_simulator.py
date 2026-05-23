# Monte Carlo Year Simulator

import pandas as pd
import numpy as np
from typing import Any, List, Dict

from context.context import SimulationContext
from core.rmd_util import get_rmd_amount
from core.schedule import SimulationSchedule
from core.spending_util import SpendingModel
from loader.tax_loader import TaxTable

#from storage.export_util import debug_view

class YearSimulator:
    """
    Handles simulation logic for a single year
    """
    
    def __init__(self, context: SimulationContext, schedule: SimulationSchedule,
                 tax_table: TaxTable = None, failure_thresholds: List[int] = None):
        self.context = context
        self.schedule = schedule
        self.config = context.config
        self.tax_table = tax_table
        self.failure_thresholds = failure_thresholds

    def simulate_year(self, year: int, age: int, year_index: int,
                     return_rate: float, portfolio_balance: float, withdrawal_target: float, 
                     downturn_years: List[int], sim_num: int) -> Dict[str, Any]:
        """
        Simulate portfolio evolution and withdrawals for a single year
        
        Returns:
            Dictionary with year results
        """
        
        start_balance = portfolio_balance
        is_downturn = year in downturn_years
        
        # Apply market returns
        end_balance_before_withdrawal = start_balance * (1 + return_rate / 100)
        
        # Calculate income sources
        income_amount = self.context.spending_model.get_income_for_age(age)
        net_withdrawal_target = max(0.0, withdrawal_target - income_amount)

        # Determine withdrawal amount and type
        withdrawal_result = self._calculate_withdrawal(
            age=age,
            year=year,
            year_index=year_index,
            balance=end_balance_before_withdrawal,
            target=net_withdrawal_target,
            is_downturn=is_downturn
        )
        
        # Final balance after withdrawal
        end_balance = end_balance_before_withdrawal - withdrawal_result['amount']
        
        # Determine next year's withdrawal target
        next_target = self._update_withdrawal_target(
            current_target=withdrawal_target,
            actual_withdrawal=withdrawal_result['amount'],
            balance=end_balance,
            year_index=year_index
        )
        
        return {
            'year': year,
            'age': age,
            'sim_num': sim_num,
            'year_index': year_index,

            # Balances
            'start_balance': start_balance,
            'end_balance': end_balance,

            # Returns and withdrawals
            'return_rate': return_rate,
            'mc_return_rate': return_rate,
            'wd_amount': withdrawal_result['amount'],

            # Income and targets
            'income_amount': income_amount,
            'withdrawal_target': withdrawal_target,
            'next_withdrawal_target': next_target,

            # Flags
            'is_downturn': is_downturn,
            'mc_failure_flag': any(end_balance <= threshold for threshold in self.failure_thresholds),
            'goal_met': withdrawal_result['amount'] >= net_withdrawal_target * 0.95,
            'rmd_met': withdrawal_result['type'] == 'ira_rmd'
        }


    def _calculate_withdrawal(self, age: int, year: int, year_index: int, balance: float,
                            target: float, is_downturn: bool) -> Dict[str, any]:
        """
        Calculate withdrawal amount and type based on strategy and constraints
        """

        mode = self.context.sim_mode
        withdrawal_rate = getattr(self.context, "withdrawal_rate", self.config.withdrawal_rate)

        # Map unsupported modes to fixed_rate for Monte Carlo
        if mode in ('taxable_first', 'deferred_first', 'roth_first', 'tsp_first'):
            mode = 'fixed_rate'

        # Check for RMD requirements first
        rmd_amount = self._calculate_rmd(age, balance, year)
        if rmd_amount > 0:
            return {
                'amount': min(rmd_amount, balance),
                'type': 'ira_rmd'
            }
        
        # Apply withdrawal strategy
        if mode == 'fixed_rate':
            amount = balance * withdrawal_rate / 100
            amount = min(amount, target)
            
        elif mode == 'fixed_amount':
            inflation_factor = (1 + self.config.inflation_rate) ** year_index
            amount = target * inflation_factor
            
        elif mode in ('guardrail', 'guardrail_roth'):
            amount = SpendingModel.apply_rate_guardrail(
                target=target,
                balance=balance,
                config=self.config,
                year_index=year_index
            )            

        else:
            raise ValueError(f"Unsupported withdrawal mode: {mode}")
        
        # Apply downturn adjustments if needed
        if is_downturn and hasattr(self.context, 'downturn_adjustment'):
            amount *= (1 - self.context.downturn_adjustment)
        
        # Ensure we don't withdraw more than available
        final_amount = min(amount, balance)
        
        return {
            'amount': final_amount,
            'type': 'strategy' if final_amount < balance else 'full_liquidation'
        }

    def _calculate_rmd(self, age: int, balance: float, year: int) -> float:
        """
        Monte Carlo RMD calculation aligned with the new deterministic RMD engine.
        """

        portfolio_df = self.context.portfolio

        # Select only accounts subject to RMD rules
        rmd_accounts = portfolio_df[
            portfolio_df['source_type'].isin(['ira', 'ira_inherited', 'tsp'])
        ]

        if rmd_accounts.empty:
            return 0.0

        total_rmd = 0.0

        for _, row in rmd_accounts.iterrows():

            source_type = row['source_type']
            dist_age    = row['distribution_age']
            dist_year   = row['distribution_year']

            # 1. Compute correct RMD age
            if source_type == 'ira_inherited':
                rmd_age = dist_age + (year - dist_year)
            else:
                if age < effective_distribution_age:
                    continue
                rmd_age = age

            # 2. Build the minimal account object expected by get_rmd_amount
            account = {
                "distribution_age": dist_age,
                "distribution_year": dist_year,
                "owner_birthdate": row.get("owner_birthdate"),
                "beneficiary_birth_year": row.get("beneficiary_birth_year"),
                "is_inherited": source_type == "ira_inherited",

                # MC uses the total portfolio balance for RMD calculations
                "current_balance": balance,
            }

            # 3. Compute RMD using the unified RMD engine
            try:
                rmd = get_rmd_amount(
                    context=self.context,
                    account=account,
                    age=rmd_age
                )
                total_rmd += rmd

            except Exception as e:
                print(f"⚠️ MC RMD failed for {source_type}: {e}")

        # 4. RMD cannot exceed the account balance
        return min(total_rmd, balance)


    def _update_withdrawal_target(self, current_target: float, 
                                 actual_withdrawal: float, balance: float,
                                 year_index: int) -> float:
        """Update withdrawal target for next year based on strategy"""
        
        mode = self.context.sim_mode
        inflation = self.config.inflation_rate
        
        if mode == 'fixed_amount':
            return current_target * (1 + inflation)
        
        elif mode == 'fixed_rate':
            return current_target * (1 + inflation)
        
        elif mode in ('guardrail', 'guardrail_roth'):
            return apply_rate_guardrail(
                target=current_target,
                balance=balance,
                config=self.config,
                year_index=year_index
            )
        
        else:
            return current_target * (1 + inflation)

def create_downturn_years(years: int, count: int = 4, seed: int = None) -> List[int]:
    """Randomly inject stochastic downturns for Monte Carlo simulation."""
    rng = np.random.default_rng(seed)
    return sorted(rng.choice(range(1, years + 1), size=count, replace=False).tolist())
