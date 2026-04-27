import pandas as pd

from withdrawal.wd_ledger import WithdrawalLedger
from src.io.export_util import debug_view

def summarize_spending_sources(wd_ledger: WithdrawalLedger) -> pd.DataFrame:
    """
    Summarize how each year's total spending was funded.
    Returns one row per year with spending by source type and relative share.
    """

    df = wd_ledger.frame.df.copy()

    df = df[df['wd_amount'] > 0]
    summary = df.groupby(['year', 'account_type'])['wd_amount'].sum().reset_index()
    summary = summary.pivot(index='year', columns='account_type', values='wd_amount').fillna(0)
    summary = summary.reset_index()
    return summary

def validate_wd_columns(df: pd.DataFrame, required_cols: list[str]):
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in df_outcome: {missing}")
