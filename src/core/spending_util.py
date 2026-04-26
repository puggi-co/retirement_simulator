from dataclasses import dataclass
from typing import Optional, Tuple
import pandas as pd

from src.config.config_schema import SimulationConfig
from src.context.context import SimulationContext
from src.core.schedule import SimulationSchedule
from src.core.tax_engine import calculate_tax

@dataclass
class SpendingModel:
    config: SimulationConfig
    context: SimulationContext
    schedule: SimulationSchedule

    # Public method: main entry point for spending logic
    def compute_spending_target(self, sim_mode: str, portfolio_df: pd.DataFrame, year_index: int) -> Tuple[float, dict]:
        portfolio_total = portfolio_df['current_balance'].sum()
        spending_target = self.get_adjusted_spending(year_index)

        guardrail_meta = {
            'guardrail_triggered': False,
            'guardrail_direction': 'none',
            'actual_rate': self.context.sim_rate
        }

        if sim_mode == 'fixed_rate':
            return self.config.withdrawal_rate, guardrail_meta

        if sim_mode in ('guardrail_amount', 'guardrail_amount_roth'):
            actual_rate = spending_target / portfolio_total if portfolio_total > 0 else 0.0
            guardrail_meta['actual_rate'] = actual_rate

            if actual_rate > self.config.guardrail_amount_high:
                guardrail_meta['guardrail_triggered'] = True
                guardrail_meta['guardrail_direction'] = 'down'
            elif actual_rate < self.config.guardrail_amount_low:
                guardrail_meta['guardrail_triggered'] = True
                guardrail_meta['guardrail_direction'] = 'up'

            spending_target = self._apply_amount_guardrail(spending_target, portfolio_total, year_index)

        return spending_target, guardrail_meta

    def evaluate_spending_power(self, df_bracket, year, filing_status,
                                taxable_income, taxable_gain, taxable_ssa,
                                base_deduction, ydx, income_total, total_withdrawn):
        '''Compute tax and spending metrics.'''

        # 🧾 Tax Computation
        deduction = self.adjust_for_inflation(base_deduction, ydx, reverse=False)

        taxable_gross_income = taxable_income + taxable_gain + taxable_ssa
        adj_income = max(0, taxable_gross_income - deduction)
        tax_owed, effective_tax_rate = calculate_tax(df_bracket, year, filing_status, adj_income)

        # 💰 Spending Power
        total_cashflow = total_withdrawn + income_total
        net_spend = total_cashflow - tax_owed
        real_spend = self.adjust_for_inflation(net_spend, ydx, reverse=True)

        return {
            "deduction": deduction,
            "taxable_gross_income": taxable_gross_income,
            "tax_owed": tax_owed,
            "effective_tax_rate": effective_tax_rate,
            "net_spending_power": net_spend,
            "real_spending_power": real_spend
        }

    def adjust_for_inflation(self, value: float, years: int, reverse: bool = False, rate: Optional[float] = None) -> float:
        r = rate if rate is not None else self.config.inflation_rate
        return value / ((1 + r) ** years) if reverse else value * ((1 + r) ** years)

    # Public method: inflation-adjusted accessor
    def adjust_for_inflation2(self, value: float, years: int, rate: Optional[float] = None) -> float:
        """Public wrapper for inflation adjustment."""
        return self._adjust_for_inflation(value, years, rate)

    # Public method: inflation-adjusted spending accessor
    def get_adjusted_spending(self, year_index: int) -> float:
        age = self.schedule.age(year_index)
        return self._get_adjusted_spending(year_index, age)

    # Public method: convert net spend to real spending power
    def compute_real_spend2(self, net_spend: float, year_index: int) -> float:
        return self._adjust_for_real_spend(net_spend, year_index)

    # Public method: check if inflation adjustment is enabled
    def use_inflation(self) -> bool:
        return getattr(self.config, 'inflation_adjusted', False)

    # Static utility: clamp rate within configured bounds
    @staticmethod
    def apply_rate_guardrail(rate: float, config: SimulationConfig) -> float:
        return max(config.guardrail_rate_low, min(rate, config.guardrail_rate_high))

    # Private helper: inflation-adjusted spending logic
    def _get_adjusted_spending(self, year: int, age: int) -> float:
        base = self.config.spending_target
        inflation = self.config.inflation_rate

        adjusted = base * ((1 + inflation) ** year)

        if year < 15:
            adjusted *= 1.1
        if age > 85:
            adjusted *= 0.8
        if age in [75, 80, 85]:
            adjusted += 5000

        return adjusted

    # Private helper: apply amount-based guardrail logic
    def _apply_amount_guardrail(self, target: float, balance: float, year_index: int) -> float:
        actual_rate = target / balance if balance > 0 else 0.0
        inflation = self.config.inflation_rate

        if actual_rate > self.config.guardrail_amount_high:
            adjusted = target * 0.90
        elif actual_rate < self.config.guardrail_amount_low:
            adjusted = target * 1.10
        else:
            adjusted = target * (1 + inflation)

        return min(adjusted, balance)

    # Private helper: forward inflation adjustment
    def _adjust_for_inflation2(self, value: float, years: int, rate: Optional[float] = None) -> float:
        r = rate if rate is not None else self.config.inflation_rate
        return value * ((1 + r) ** years)

    # Private helper: reverse inflation adjustment
    def _adjust_for_real_spend2(self, value: float, years: int, rate: Optional[float] = None) -> float:
        r = rate if rate is not None else self.config.inflation_rate
        return value / ((1 + r) ** years)

    def adjust_for_real_spend2(self, nominal_spend: float, ydx: int) -> float:
        inflation_factors = [1.0, 0.98, 0.96, 0.94]
        factor = inflation_factors[ydx] if ydx < len(inflation_factors) else 1.0
        return round(nominal_spend * factor, 2)