# ================================================================================
# Roth conversion logic for withdrawals.
# ================================================================================

import pandas as pd

from loader.tax_loader import TaxTable
from withdrawal.wd_ledger import WithdrawalLedger

def perform_roth_conversion(
    tax_table: TaxTable,
    wd_ledger: WithdrawalLedger,
    portfolio_df: pd.DataFrame,
    year: int,
    age: int,
    filing_status: str,
    taxable_income_so_far: float,
    target_bracket_rate: float
    ) -> tuple[float, pd.DataFrame]:
    """
    Convert from deferred to Roth up to the remaining room in the target bracket.
    Returns updated taxable_income and portfolio_df.
    """

    df_bracket = tax_table.tax_bracket
    year_row = df_bracket[df_bracket['year'] == year]

    # This assumes a column naming convention like 'rate' and 'upper_limit'
    # Filter to the target bracket (e.g., 24%)
    bracket_row = year_row[year_row['rate'] == target_bracket_rate]
    if bracket_row.empty:
        return taxable_income_so_far, portfolio_df

    bracket_top = float(bracket_row[filing_status].iloc[0])
    remaining_room = max(0.0, bracket_top - taxable_income_so_far)
    if remaining_room <= 0:
        return taxable_income_so_far, portfolio_df

    # Find deferred accounts to convert from
    deferred_mask = portfolio_df['source_tax_type'] == 'deferred'
    deferred_accounts = portfolio_df[deferred_mask]

    remaining_to_convert = remaining_room

    for pdx, account in deferred_accounts.iterrows():
        if remaining_to_convert <= 0:
            break

        current_balance = account['current_balance']
        convert_amount = min(current_balance, remaining_to_convert)
        if convert_amount <= 0:
            continue

        # Reduce deferred
        portfolio_df.at[pdx, 'current_balance'] = current_balance - convert_amount

        # Increase Roth (exempt) – simple model: first exempt account
        exempt_mask = portfolio_df['source_tax_type'] == 'exempt'
        exempt_accounts = portfolio_df[exempt_mask]
        if not exempt_accounts.empty:
            ex_idx = exempt_accounts.index[0]
            ex_bal = portfolio_df.at[ex_idx, 'current_balance']
            portfolio_df.at[ex_idx, 'current_balance'] = ex_bal + convert_amount

        # Ledger entry
        wd_ledger.add_conversion(
            year=year,
            age=age,
            amount=convert_amount,
            source_account=account['source_type'],
            target_account='roth'
        )

        taxable_income_so_far += convert_amount
        remaining_to_convert -= convert_amount

    return taxable_income_so_far, portfolio_df
