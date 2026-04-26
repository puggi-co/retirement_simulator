# Withdrawal Analysis - Summary

from typing import Optional
import pandas as pd

from src.orchestration.outcome_ledger import OutcomeLedger
from orchestration.orch_entity import WDAnalyzeResults

from util_dev.debug_util import debug_view

def wd_summarize_outcomes(
    outcome_ledger: OutcomeLedger,
    failure_threshold: float = 0.0
) -> WDAnalyzeResults:
    """
    Summarize deterministic withdrawal outcomes from outcome_ledger.
    """

    df_outcome = outcome_ledger.frame.df

    # ── Validate Required Columns ─────────────────────────────
    required_cols = [
    'year', 'age', 'base_balance', 'income_amount', 'wd_amount', 'actual_rate', 
    'sim_type', 'sim_mode', 'sim_id', 'sim_rate', 
    'shortfall_amount', 'closure_met', 'goal_met', 'rmd_met', 'synthetic_flag'
    ]
    missing = [col for col in required_cols if col not in df_outcome.columns]
    if missing:
        raise ValueError(f"Missing required columns in df_outcome: {missing}")

    # ── Goal Success Summary ─────────────────────────────────
    goal_success = df_outcome.groupby(['sim_mode', 'year'])['goal_met'].mean().reset_index()
    goal_success.rename(columns={'goal_met': 'goal_success_rate'}, inplace=True)

    # ── RMD Trigger Mapping ──────────────────────────────────
    rmd_trigger_ages = df_outcome[df_outcome['rmd_met']].groupby('sim_id')['age'].min().reset_index()
    rmd_trigger_ages.rename(columns={'age': 'rmd_trigger_age'}, inplace=True)

    # ── Withdrawal Efficiency ────────────────────────────────
    withdrawal_efficiency = df_outcome.groupby(['sim_mode', 'year'])['actual_rate'].mean().reset_index()
    withdrawal_efficiency.rename(columns={'actual_rate': 'avg_actual_rate'}, inplace=True)

    # ── Balance Depletion Flags ──────────────────────────────
    df_depletion = df_outcome[df_outcome['base_balance'] <= failure_threshold]
    depletion_flags = df_depletion.groupby(['sim_mode', 'year']).size().reset_index(name='depletion_count')

    # ── Package Results ──────────────────────────────────────
    return WDAnalyzeResults(
        goal_success=goal_success,
        rmd_trigger_ages=rmd_trigger_ages,
        withdrawal_efficiency=withdrawal_efficiency,
        depletion_flags=depletion_flags
    )
