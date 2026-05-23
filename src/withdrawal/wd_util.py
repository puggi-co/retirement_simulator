"""
Withdrawal analysis utilities:
- Row-level analytics (withdrawal efficiency)
- Year-level aggregation
- Simulation-level summary
- Spending source summaries
"""

import pandas as pd

from dataclasses import dataclass
from typing import Optional

from withdrawal.wd_schema import WD_OUTCOME_SCHEMA_COLUMNS


# ───────────────────────────────────────────────────────────────
# YEAR ANNOTATION (Outcome-level)
# ───────────────────────────────────────────────────────────────

@dataclass
class YearAnnotation:
    year: int
    deduction: float
    taxable_gross_income: float
    tax_owed: float
    effective_tax_rate: float
    net_spending_power: float
    real_spending_power: float
    guardrail_triggered: bool = False
    guardrail_direction: str = 'none'
    wd_rate: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            'year': self.year,
            'deduction': round(self.deduction, 2),
            'taxable_gross_income': round(self.taxable_gross_income, 2),
            'tax_owed': round(self.tax_owed, 2),
            'effective_tax_rate': round(self.effective_tax_rate, 4),
            'net_spending_power': round(self.net_spending_power, 2),
            'real_spending_power': round(self.real_spending_power, 2),
            'guardrail_triggered': self.guardrail_triggered,
            'guardrail_direction': self.guardrail_direction,
            'wd_rate': self.wd_rate
        }

    def emoji_overlay(self) -> str:
        """Quick visual cue based on real spending power."""
        if self.real_spending_power >= self.net_spending_power:
            return "🟢💰"
        elif self.real_spending_power >= 0.75 * self.net_spending_power:
            return "🟡📉"
        else:
            return "🔴⚠️"

    @staticmethod
    def create(year: int, deduction: float, taxable_gross_income: float, tax_owed: float,
               effective_tax_rate: float, net_spending_power: float, real_spending_power: float,
               guardrail_triggered: bool = False, guardrail_direction: str = 'none',
               wd_rate: Optional[float] = None) -> "YearAnnotation":
        return YearAnnotation(
            year=year,
            deduction=deduction,
            taxable_gross_income=taxable_gross_income,
            tax_owed=tax_owed,
            effective_tax_rate=effective_tax_rate,
            net_spending_power=net_spending_power,
            real_spending_power=real_spending_power,
            guardrail_triggered=guardrail_triggered,
            guardrail_direction=guardrail_direction,
            wd_rate=wd_rate
        )


# ───────────────────────────────────────────────────────────────
# WITHDRAWAL EFFICIENCY
# ───────────────────────────────────────────────────────────────

def compute_withdrawal_efficiency(wd_type, wd_amount, taxable_income, taxable_gain, marginal_rate):
    """
    Spending power per dollar withdrawn.
    """

    # No withdrawal → no efficiency
    if wd_amount <= 0:
        return 0.0

    # Roth withdrawals → fully efficient
    if wd_type == 'roth':
        return 1.0

    # Brokerage sale → basis is efficient, gains are not
    if wd_type == 'brokerage_sale':
        eff = (wd_amount - taxable_gain) / wd_amount
        return max(0.0, eff)

    # IRA / TSP / income streams → taxed at marginal rate
    if wd_type in ('ira_rmd', 'ira_ord', 'ira_early',
                   'inc_fers', 'inc_ssa', 'inc_ord',
                   'conversion'):
        return max(0.0, 1.0 - marginal_rate)

    # Synthetic / rollover / transfer → no spending power
    if wd_type in ('synthetic', 'rollover', 'transfer'):
        return 0.0

    # Default fallback
    return 0.0

# ───────────────────────────────────────────────────────────────
# SPENDING SOURCE SUMMARY
# ───────────────────────────────────────────────────────────────

def summarize_spending_sources(wd_ledger) -> pd.DataFrame:
    """
    Summarize each year's withdrawals by source_name,
    and compute total portfolio withdrawals and total income.
    """

    df = wd_ledger.frame.df.copy()
    df = df[df['wd_amount'] > 0]

    # Pivot by source_name (matches Spending Summary tab)
    summary = (
        df.groupby(['year', 'source_name'])['wd_amount']
        .sum()
        .reset_index()
        .pivot(index='year', columns='source_name', values='wd_amount')
        .fillna(0)
    )

    # Identify income sources
    income_sources = ['Social Security', 'FERS Annuity']

    # Compute total income
    summary['total_income'] = summary[income_sources].sum(axis=1)

    # Compute total portfolio withdrawals (everything except income)
    summary['total_portfolio_withdrawals'] = (
        summary.sum(axis=1) - summary['total_income']
    )

    summary = summary.reset_index()

    return summary

# ───────────────────────────────────────────────────────────────
# VALIDATION
# ───────────────────────────────────────────────────────────────

def validate_wd_columns(df: pd.DataFrame, required_cols: list[str]):
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


# ───────────────────────────────────────────────────────────────
# OUTCOME SUMMARY (Simulation-level)
# ───────────────────────────────────────────────────────────────

@dataclass
class WDAnalyzeResults:
    goal_success: pd.DataFrame
    rmd_trigger_ages: pd.DataFrame
    withdrawal_efficiency: pd.DataFrame
    depletion_flags: pd.DataFrame


def wd_summarize_outcomes(wd_outcome, failure_threshold: float = 0.0) -> WDAnalyzeResults:
    """
    Summarize deterministic withdrawal outcomes from outcome.
    """

    df = wd_outcome.frame.df

    validate_wd_columns(df, WD_OUTCOME_SCHEMA_COLUMNS)  # Ensure all expected columns are present

    # Goal success
    goal_success = df.groupby(['sim_mode', 'year'])['goal_met'].mean().reset_index()
    goal_success.rename(columns={'goal_met': 'goal_success_rate'}, inplace=True)

    # RMD trigger ages
    rmd_trigger_ages = df[df['rmd_met']].groupby('strategy_id')['age'].min().reset_index()
    rmd_trigger_ages.rename(columns={'age': 'rmd_trigger_age'}, inplace=True)

    # Withdrawal efficiency (portfolio_rate is year-level efficiency)
    withdrawal_efficiency = df.groupby(['sim_mode', 'year'])['portfolio_rate'].mean().reset_index()
    withdrawal_efficiency.rename(columns={'portfolio_rate': 'avg_portfolio_rate'}, inplace=True)

    # Depletion flags
    df_depletion = df[df['base_balance'] <= failure_threshold]
    depletion_flags = df_depletion.groupby(['sim_mode', 'year']).size().reset_index(name='depletion_count')

    return WDAnalyzeResults(
        goal_success=goal_success,
        rmd_trigger_ages=rmd_trigger_ages,
        withdrawal_efficiency=withdrawal_efficiency,
        depletion_flags=depletion_flags
    )
