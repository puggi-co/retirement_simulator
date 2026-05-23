'''
Discretionary Withdrawal Engine
-------------------------------
Calculates discretionary withdrawals across investment accounts using tax-aware logic and drawdown priority.
'''
def calculate_discretionary_withdrawals(context, portfolio_df, draw_order, withdrawal_target):
    """
    This function does not mutate the withdrawal ledger. Instead, it returns 
    a dictionary of per-account withdrawal records, allowing the calling routine 
    to handle ledger entries and simulation metadata (e.g., year, age).
    """

    config = context.config

    # Accumulate per-account withdrawal deltas
    discretionary_records = {}

    for source_tax_type in draw_order:
        draw_df = portfolio_df[portfolio_df['source_tax_type'] == source_tax_type]
        draw_df = draw_df.sort_values(by='current_balance', ascending=True)

        # For deferred accounts, check if any non-inherited deferred accounts still have balance
        if source_tax_type == 'deferred':
            other_deferred_have_balance = (
                portfolio_df[
                    (portfolio_df['source_tax_type'] == 'deferred') &
                    (portfolio_df['source_type'] != 'ira_inherited')
                ]['current_balance'] > 0
            ).any()
        else:
            other_deferred_have_balance = False

        for adx, account in draw_df.iterrows():

            # Skip income streams
            if account['source_type'] in ['inc_fers', 'inc_ord', 'inc_ssa']:
                continue

            # Inherited IRA stretch rule: only use above RMD if no other deferred accounts remain
            if (
                account['source_type'] == 'ira_inherited'
                and other_deferred_have_balance
            ):
                continue

            current_balance = account['current_balance']
            if current_balance <= 0:
                continue

            if withdrawal_target <= 0:
                break

            wd_amount = min(current_balance, withdrawal_target)
            pre_balance = current_balance
            current_balance -= wd_amount
            withdrawal_target -= wd_amount

            portfolio_df.at[adx, 'current_balance'] = current_balance

            # Determine wd_type and tax impact
            if account['source_tax_type'] == 'deferred':
                taxable_income_delta = wd_amount
                taxable_gain_delta = 0.0
                wd_type = 'deferred'

            elif account['source_tax_type'] == 'taxable':
                taxable_income_delta = 0.0
                taxable_gain_delta = wd_amount * config.tax_gain_rate
                wd_type = 'ordinary'

            else:
                taxable_income_delta = 0.0
                taxable_gain_delta = 0.0
                wd_type = 'exempt'

            discretionary_records[adx] = {
                'wd_amount': wd_amount,
                'taxable_income': taxable_income_delta,
                'taxable_gain': taxable_gain_delta,
                'wd_type': wd_type,
                'pre_balance': pre_balance,
                'end_balance': current_balance,
            }

    return portfolio_df, discretionary_records
