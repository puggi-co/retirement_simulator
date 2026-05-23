"""
Executes Required Minimum Distributions (RMDs) for eligible accounts.
"""

from core.rmd_util import get_rmd_amount

def apply_rmd(
    context,
    account,
    wd_ledger,
    age,
    year
):
    source_type = account['source_type']

    # Only IRA-type accounts have RMDs
    if source_type not in ('ira', 'tsp', 'ira_inherited'):
        return 0

    current_balance = account['current_balance']
    dist_year = account['distribution_year']
    dist_age  = account['distribution_age']

    # --- 1. Skip RMD if not yet in RMD window ---
    if source_type != 'ira_inherited':
        if age < dist_age:
            return 0
        rmd_age = age
    else:
        # inherited IRA: single-life table, age advances each year
        rmd_age = dist_age + (year - dist_year)

    # --- 2. Compute RMD amount ---
    rmd_amount = get_rmd_amount(
        context=context,
        account=account,
        age=rmd_age
    )

    if rmd_amount <= 0:
        return 0

    base_balance = current_balance
    end_balance = current_balance - rmd_amount

    # --- 3. Closure Logic ---
    closure_met = False
    threshold = context.config.account_closure_amount * context.config.account_closure_threshold

    if end_balance <= threshold:
        rmd_amount += end_balance
        end_balance = 0.0
        closure_met = True

    # --- 4. Marginal rate ---
    marginal_rate = context.tax_engine.get_marginal_rate(
        year=year,
        taxable_income=rmd_amount,
        filing_status=account['filing_status']
    )

    # --- 5. Ledger entry (modernized) ---
    wd_ledger.add_year(
        account=account,
        year=year,
        age=age,
        current_balance=base_balance,
        end_balance=end_balance,
        wd_type='ira_rmd',          # keep your existing wd_type
        wd_amount=rmd_amount,
        taxable_income=rmd_amount,
        taxable_gain=0.0,
        marginal_rate=marginal_rate,
        closure_met=closure_met,
        guardrail_triggered=None,
        guardrail_direction=None
    )

    # --- 6. Update account balance ---
    account['current_balance'] = end_balance
    account['end_balance'] = end_balance

    return rmd_amount
