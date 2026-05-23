from dataclasses import dataclass
from typing import Optional, Tuple
import pandas as pd

from config.config_schema import SimulationConfig
from context.context import SimulationContext
import core.schedule as schedule

@dataclass
class SpendingModel:
    config: SimulationConfig
    context: SimulationContext
    schedule: schedule.SimulationSchedule

    # ==============================================================
    # MAIN ENTRY POINT — unified spending logic
    # ==============================================================
    def compute_spending_target(
        self,
        sim_mode: str,
        portfolio_df: pd.DataFrame,
        year_index: int
    ) -> Tuple[float, dict]:
        """
        Compute spending target for the year based on sim_mode.
        """

        portfolio_total = portfolio_df['current_balance'].sum()

        guardrail_meta = {
            'guardrail_triggered': False,
            'guardrail_direction': 'none'
        }

        # ----------------------------------------------------------
        # FIXED RATE (tax-efficient strategy)
        # ----------------------------------------------------------
        if sim_mode == 'fixed_rate_tax_efficient':
            spending_target = portfolio_total * self.config.withdrawal_rate
            return spending_target, guardrail_meta

        # ----------------------------------------------------------
        # AMOUNT-BASED MODES WITH GUARDRAILS
        # (taxable_first, deferred_first)
        # ----------------------------------------------------------
        if sim_mode in ('taxable_first', 'deferred_first'):
            base_target = self.get_adjusted_spending(year_index)

            # Implied withdrawal rate
            actual_rate = base_target / portfolio_total if portfolio_total > 0 else 0.0

            # Guardrail direction metadata
            if actual_rate > self.config.guardrail_amount_high:
                guardrail_meta['guardrail_triggered'] = True
                guardrail_meta['guardrail_direction'] = 'down'

            elif actual_rate < self.config.guardrail_amount_low:
                guardrail_meta['guardrail_triggered'] = True
                guardrail_meta['guardrail_direction'] = 'up'

            # Apply amount-based guardrail logic
            spending_target = self._apply_amount_guardrail(
                target=base_target,
                balance=portfolio_total,
                year_index=year_index
            )

            return spending_target, guardrail_meta

        # ----------------------------------------------------------
        # FALLBACK — inflation-adjusted spending (no guardrails)
        # ----------------------------------------------------------
        spending_target = self.get_adjusted_spending(year_index)
        return spending_target, guardrail_meta

    # ==============================================================
    # SUPPORTING METHODS (unchanged)
    # ==============================================================

    def evaluate_spending_power(self, year, filing_status,
                                taxable_income, taxable_gain, taxable_ssa,
                                base_deduction, ydx, income_total, total_withdrawn):
        deduction = self.adjust_for_inflation(base_deduction, ydx, reverse=False)
        taxable_gross_income = taxable_income + taxable_gain + taxable_ssa
        adj_income = max(0, taxable_gross_income - deduction)
        tax_owed, effective_tax_rate = self.context.tax_engine.calculate_tax(
            year, filing_status, adj_income)

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

    def get_adjusted_spending(self, year_index: int) -> float:
        age = self.schedule.age(year_index)
        return self._get_adjusted_spending(year_index, age)

    def compute_real_spend2(self, net_spend: float, year_index: int) -> float:
        return self._adjust_for_real_spend(net_spend, year_index)

    def get_income_for_age(self, age: int) -> float:
        return self._get_income_for_age(age)

    def use_inflation(self) -> bool:
        return getattr(self.config, 'inflation_adjusted', False)

    @staticmethod
    def apply_rate_guardrail(rate: float, config: SimulationConfig) -> float:
        return max(config.guardrail_rate_low, min(rate, config.guardrail_rate_high))

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

    def _apply_amount_guardrail(self, target: float, balance: float, year_index: int) -> float:
        wd_rate = target / balance if balance > 0 else 0.0
        inflation = self.config.inflation_rate

        if wd_rate > self.config.guardrail_amount_high:
            adjusted = target * 0.90
        elif wd_rate < self.config.guardrail_amount_low:
            adjusted = target * 1.10
        else:
            adjusted = target * (1 + inflation)

        return min(adjusted, balance)

    def _get_income_for_age(self, age: int) -> float:
        portfolio_df = self.context.portfolio
        income_mask = portfolio_df['source_type'].isin(['inc_ssa', 'inc_fers', 'inc_ord'])
        eligible_mask = portfolio_df['distribution_age'] <= age
        eligible_accounts = portfolio_df[income_mask & eligible_mask]
        return eligible_accounts['base_balance'].sum()
