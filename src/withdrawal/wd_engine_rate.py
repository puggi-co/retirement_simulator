# ================================================================================
# Rate-Based Withdrawal Engine 
# ================================================================================

def apply_rate_withdrawal(
    context,
    wd_ledger,
    account,
    year,
    age,
    current_balance,
    withdrawal_rate
):
    """
    Rate-based withdrawal engine.
    - Withdraws a fixed percentage from each account.
    - RMDs are handled separately by the RMD engine.
    - No age-based logic belongs here.
    """

    config = context.config

    source_type = account['source_type']
    source_tax_type = account['source_tax_type']

    taxable_income = 0.0
    taxable_gain = 0.0

    # Base wd_type from account type
    wd_type = WD_TYPE_MAP.get(source_type, 'none')

    # --------------------------------------------------------------
    # Apply fixed-rate withdrawal
    # --------------------------------------------------------------
    wd_amount = round(current_balance * withdrawal_rate)

    # --------------------------------------------------------------
    # Closure Logic
    # --------------------------------------------------------------
    closure_met = False

    if current_balance <= config.account_closure_amount * config.account_closure_threshold:
        wd_amount += current_balance
        current_balance = 0.0
        closure_met = True

    end_balance = current_balance

    # --------------------------------------------------------------
    # No withdrawal if empty
    # --------------------------------------------------------------
    if current_balance == 0:
        wd_type = 'none'
        wd_amount = 0.0

    # Apply withdrawal
    wd_amount = min(wd_amount, current_balance)
    end_balance = current_balance - wd_amount

    # --------------------------------------------------------------
    # Taxable tracking
    # --------------------------------------------------------------
    if source_tax_type == 'deferred':
        taxable_income = wd_amount
    elif source_tax_type == 'taxable':
        taxable_gain = wd_amount * config.tax_gain_rate

    # --------------------------------------------------------------
    # Compute marginal rate
    # --------------------------------------------------------------
    marginal_rate = context.tax_engine.get_marginal_rate(
        year=year,
        taxable_income=taxable_income,
        filing_status=account['filing_status']
    )

    # --------------------------------------------------------------
    # Ledger entry
    # --------------------------------------------------------------
    wd_ledger.add_year(
        account=account,
        year=year,
        age=age,
        current_balance=current_balance,
        end_balance=end_balance,
        wd_amount=wd_amount,
        wd_type=wd_type,
        taxable_income=taxable_income,
        taxable_gain=taxable_gain,
        marginal_rate=marginal_rate,
        closure_met=closure_met
    )

    return wd_amount, end_balance, taxable_income, taxable_gain
