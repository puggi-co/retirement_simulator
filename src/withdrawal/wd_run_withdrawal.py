from src.context.context import SimulationContext
from src.core.rmd_util import get_rmd_amount

from util_dev.debug_util import debug_view

def get_fers_cola(inflation: float) -> float:
    if inflation <= 0.02:
        return inflation
    elif inflation < 0.03:
        return 0.02
    else:
        return inflation - 0.01

def process_income_stream(context, account, wd_ledger, base_balance, age, year, years_since_start):
    """
    Process income streams for ordinary income, and inflation-adjusted social security and FERS income.
    """

    # Unpack context parameters
    config = context.config
    inflation_rate = config.inflation_rate
    tax_ssa_rate = config.tax_ssa_rate

    # Account-level variables
    account_type = account['account_type']
    distribution_age = account['distribution_age']
    wd_type = account['account_type']

    if account_type == 'inc_fers':

        # FERS income is adjusted for COLA and taxed as ordinary income when distributed
        growth_factor = (1 + get_fers_cola(inflation_rate)) ** years_since_start # growth is compounded, not linear
        current_balance = round(base_balance * growth_factor, 2)
        taxable_income = current_balance if age >= distribution_age else 0.0

    elif account_type == 'inc_ssa':

        # SSA income is adjusted for inflation and taxed at highest ssa rate when distributed
        growth_factor = (1 + inflation_rate) ** years_since_start # growth is compounded, not linear
        current_balance = round(base_balance * growth_factor, 2)
        taxable_income = min(current_balance * tax_ssa_rate, current_balance) if age >= distribution_age else 0.0

    else:

        # Other income is not adjusted for inflation and is taxed as ordinary income
        growth_factor = 1.0
        current_balance = base_balance # growth is neither compounded nor linear
        taxable_income = current_balance if age >= distribution_age else 0.0

    wd_amount = current_balance if age >= distribution_age else 0.0

    # Log the results in the withdrawal ledger
    wd_ledger.add_year(
        account=account,
        year=year,
        age=age,
        current_balance=current_balance,
        end_balance=current_balance,
        wd_amount=wd_amount,
        wd_type=wd_type if age >= distribution_age else 'none',
        taxable_income=taxable_income
    )

    return wd_amount, taxable_income

def apply_rate_based_withdrawal(context, schedule, df_lef,
    wd_ledger, account, year, age, current_balance, withdrawal_rate):

    """
    Withdraw a fixed percentage from each account. 
    For tax-deferred accounts, use the greater of fixed rate or RMD. 
    Guardrails adjust rate if portfolio deviates.
    """

    config = context.config

    wd_type = "none"
    wd_amount = 0.0
    taxable_income = 0.0
    taxable_gain = 0.0

    account_type = account['account_type']
    account_tax_type = account['account_tax_type']
    distribution_age = account['distribution_age']

    # RMD logic for deferred accounts
    if account_type in ['ira', 'ira_inherited', 'tsp']:
        wd_type = 'ira_ord'
        wd_amount = round(current_balance * withdrawal_rate) if context.sim_mode == 'fixed_rate' else 0.0

        if age >= distribution_age:
            wd_type = 'ira_rmd'
            rmd_amount = round(get_rmd_amount(current_balance, age, account, df_lef, schedule), 2)
            fixed_amount = round(current_balance * withdrawal_rate)
            wd_amount = max(rmd_amount, fixed_amount)

    # Brokerage logic
    elif account_type == 'brokerage' and age >= distribution_age:
        wd_type = 'ordinary'
        wd_amount = round(current_balance * withdrawal_rate)

    # Roth logic
    elif account_type == 'roth' and age >= distribution_age:
        wd_type = 'exempt'
        wd_amount = round(current_balance * withdrawal_rate)

    # Enforce minimum account balance logic
    if current_balance == 0:
        wd_type = 'none'
        wd_amount = current_balance
    elif current_balance <= config.account_closure_threshold * config.account_closure_amount:
        wd_type = 'ordinary' if account_tax_type == 'taxable' else 'ira_ord'
        wd_amount = current_balance

    # Apply withdrawal
    wd_amount = min(wd_amount, current_balance) # Guard against a negative balance
    end_balance = current_balance - wd_amount

    # Taxable tracking
    if account_tax_type == 'deferred':
        taxable_income = wd_amount
    elif account_tax_type == 'taxable':
        taxable_gain = wd_amount * config.tax_gain_rate

    # Withdrawal Ledger entry
    wd_ledger.add_year(
        account=account,
        year=year,
        age=age,
        current_balance=current_balance,
        end_balance=end_balance,
        wd_amount=wd_amount,
        wd_type=wd_type,
        taxable_income=taxable_income,
        taxable_gain=taxable_gain
    )

    return wd_amount, end_balance, taxable_income, taxable_gain

def apply_amount_based_withdrawals(context, schedule, df_lef, portfolio_df, 
                                   wd_ledger, account, year, age, current_balance, 
                                   draw_order, withdrawal_target
):
    """
    Processes withdrawals for investment accounts, including:

    - Mandatory distributions (e.g., RMDs for deferred accounts at distribution age)
    - Discretionary withdrawals based on remaining withdrawal targets and drawdown order
    - Post-withdrawal account closure if balance falls below configured threshold

    Returns a single ledger entry per account per year, consolidating all withdrawal activity 
    and associated tax impact for audit traceability.
    """

    config = context.config
    schedule = context.schedule

    taxable_income = 0.0
    taxable_gain = 0.0

    # ── Mandatory Withdrawal Logic ─────────────────────────────

    if account['account_type'] in ['ira', 'ira_inherited', 'tsp'] and age >= account['distribution_age']:
        # RMD applies to IRA-type accounts
        wd_type = 'ira_rmd'
        rmd_amount = get_rmd_amount(current_balance, age, account, df_lef, schedule)
        wd_amount = min(rmd_amount, current_balance)
        current_balance -= wd_amount
        withdrawal_target = max(0.0, withdrawal_target - wd_amount)

#    elif account['account_type'] == 'brokerage' and age >= account['distribution_age']:
#        # Optional fixed-rate logic for taxable investment accounts
#        wd_type = 'ordinary'
#        fixed_amount = current_balance * config.withdrawal_rate
#        wd_amount = min(fixed_amount, current_balance)
#        current_balance -= wd_amount
#        withdrawal_target = max(0.0, withdrawal_target - wd_amount)
#
    else:
        # No mandatory withdrawal for income streams or pre-distribution accounts
        wd_type = 'none'
        wd_amount = 0.0

    # Taxable tracking for mandatory withdrawal
    if account['account_tax_type'] == 'deferred':
        taxable_income += wd_amount
    elif account['account_tax_type'] == 'taxable':
        taxable_gain += wd_amount * config.tax_gain_rate

    # ── Discretionary Withdrawals ─────────────────────

    if withdrawal_target > 0:
        portfolio_df, discretionary_records = calculate_discretionary_withdrawals(
            context, portfolio_df, draw_order, withdrawal_target
        )

        # If this account received discretionary withdrawals, merge them
        acct_index = account.name  # assumes account is a Series from portfolio_df
        if acct_index in discretionary_records:
            record = discretionary_records[acct_index]
            current_balance = record['end_balance']
            wd_amount += record['wd_amount']
            taxable_income += record['taxable_income']
            taxable_gain += record['taxable_gain']
            wd_type = record['wd_type'] if wd_type == "none" else wd_type  # preserve RMD/closure if present

    # ── Post-Withdrawal Account Closure Check ─────────────────────
    if current_balance <= config.account_closure_threshold * config.account_closure_amount:
        # Add remaining balance to withdrawal amount
        wd_amount += current_balance
        current_balance = 0.0
        # Do not overwrite wd_type

    end_balance = current_balance

    # ── Single Ledger Entry for Mandatory and Discretionary Withdrawals ───────────────────

    wd_ledger.add_year(
        account=account,
        year=year,
        age=age,
        current_balance=current_balance,
        end_balance=end_balance,
        wd_type=wd_type,
        wd_amount=wd_amount,
        taxable_income=taxable_income,
        taxable_gain=taxable_gain
    )

    return wd_ledger, end_balance, portfolio_df, wd_amount, taxable_income, taxable_gain

def calculate_discretionary_withdrawals(context, portfolio_df, draw_order, withdrawal_target):
    """
    Calculates discretionary withdrawals across investment accounts 
    using tax-aware logic and drawdown priority.

    This function does not mutate the withdrawal ledger. Instead, it returns 
    a dictionary of per-account withdrawal records, allowing the calling routine 
    to handle ledger entries and simulation metadata (e.g., year, age).
    """

    config = context.config

    # Accumulate per-account withdrawal deltas
    discretionary_records = {}

    for account_tax_type in draw_order:
        draw_df = portfolio_df[portfolio_df['account_tax_type'] == account_tax_type]
        draw_df = draw_df.sort_values(by='current_balance', ascending=True)

        for adx, account in draw_df.iterrows():

            # Skip income streams
            if account['account_type'] in ['inc_fers', 'inc_ord', 'inc_ssa']:
                continue

            current_balance = account['current_balance']
            if withdrawal_target <= 0 or current_balance <= 0:
                break

            wd_amount = min(current_balance, withdrawal_target)
            pre_balance = current_balance
            current_balance -= wd_amount
            withdrawal_target -= wd_amount

            portfolio_df.at[adx, 'current_balance'] = current_balance

            # Determine wd_type and tax impact
            if account['account_tax_type'] == 'deferred':
                taxable_income_delta = wd_amount
                taxable_gain_delta = 0.0
                wd_type = 'conversion' if context.sim_id == 'wd_roth' else 'deferred'
            elif account['account_tax_type'] == 'taxable':
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
