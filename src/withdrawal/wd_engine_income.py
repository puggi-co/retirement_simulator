"""
This module implements the logic for processing income streams in the withdrawal engine. 
It calculates the current balance, taxable income, and marginal tax rate for each income stream 
based on its type (FERS COLA, Social Security, or ordinary income) and 
updates the withdrawal ledger accordingly.
"""

def get_fers_cola(inflation: float) -> float:
    if inflation <= 0.02:
        return inflation
    elif inflation < 0.03:
        return 0.02
    else:
        return inflation - 0.01

def log_income_stream(context, account, wd_ledger, base_balance, age, year):

    config = context.config
    inflation_rate = config.inflation_rate
    tax_ssa_rate = config.tax_ssa_rate

    source_type = account['source_type']
    distribution_age = account['distribution_age']

    # Income streams never close accounts
    closure_met = False

    # Income streams always use their source_type as wd_type
    wd_type = source_type

    # Years since income began
    years_since_start = max(0, age - distribution_age)

    # Compute current balance and taxable income
    if source_type == 'inc_fers':
        growth_factor = (1 + get_fers_cola(inflation_rate)) ** years_since_start
        current_balance = round(base_balance * growth_factor, 2)
        taxable_income = current_balance if age >= distribution_age else 0.0

    elif source_type == 'inc_ssa':
        growth_factor = (1 + inflation_rate) ** years_since_start
        current_balance = round(base_balance * growth_factor, 2)
        taxable_income = (
            min(current_balance * tax_ssa_rate, current_balance)
            if age >= distribution_age else 0.0
        )

    else:  # inc_ord
        current_balance = base_balance
        taxable_income = current_balance if age >= distribution_age else 0.0

    # Income streams do NOT use wd_amount for tax purposes
    wd_amount = current_balance if age >= distribution_age else 0.0

    # Compute marginal rate
    marginal_rate = context.tax_engine.get_marginal_rate(
        year=year,
        taxable_income=taxable_income,
        filing_status=account['filing_status']
    )

    # Log the results
    wd_ledger.add_year(
        account=account,
        year=year,
        age=age,
        current_balance=current_balance,
        end_balance=current_balance,
        wd_type=wd_type,
        wd_amount=wd_amount,
        taxable_income=taxable_income,
        taxable_gain=0.0,
        marginal_rate=marginal_rate,
        closure_met=closure_met
    )

    return wd_amount, taxable_income
