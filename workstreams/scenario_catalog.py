SCENARIO_DATA = [
    {
    'scenario_id': 'withdrawal_rate',
    'scenario_name': 'All Account Types, Fixed Rate',
    'withdrawal_mode': 'fixed_rate',
    'montecarlo_id': 'mc_rate',
    'include_dashboard': True,
    'scenario_description': """Withdraws a fixed rate (e.g., 4%) from each account in each year regardless of account type.
            The fixed rate is used to determine the withdrawal amount in year 1.
            In each future year, the fixed rate is adjusted for inflation.
            The account is expected to depleted in about 30 years.
        Tax-Deferred Accounts: RMDs may force withdraws beyond the fixed rate % and all withdraws are taxable as ordinary income. 
        Taxable Accounts: Assists with optimization to stay in lower tax brackets such as:
            Distinguishes ordinary income from long-term capital gains and qualified dividends.
            Uses standard deduction, Alt Min Tax (AMT), and/or tax-loss harvesting to offset gains. 
        Tax-Free Accounts: Qualified Withdraws are tax free. No RMDs.
            Pros: Simple
            Cons: Does not leverage the mix of account types to optimize withdraws.
            Key Concepts: Taxes are paid from withdraw amount which reduces net spending amount."""
    }, 
    {
    'scenario_id': 'withdrawal_amount',
    'scenario_name': 'Tax Smart, Target Amount',
    'withdrawal_mode': 'fixed_amount',
    'montecarlo_id': 'mc_amount',
    'include_dashboard': True,
    'scenario_description': """Withdraws the target amount from Taxable accounts first, then Tax-Deferred accounts, and Tax-Free accounts last.
            Target amount is adjusted for inflation each year.
        Tax-Deferred Accounts: RMDs are delayed until RMD age and taxed as ordinary income.
        Taxable Accounts: Withdraws the target amount minus RMDs.
            Distinguishes ordinary income from long-term capital gains and qualified dividends.
            Uses standard deduction, Alt Min Tax (AMT), and/or tax-loss harvesting to offset gains. 
        Tax-Free Accounts: Withdraws are delayed until after Taxable and Tax-Deferred accounts are depleted. 
            Qualified withdraws are tax free. No RMDs.
        Pros: Leverage the mix of account types to optimize withdraws. 
        Cons: Triggers capital gains taxes and reduces annual compounding of interest/dividend in taxable accounts."""
    }, 
    {
    'scenario_id': 'withdrawal_guardrail',
    'scenario_name': 'Tax Smart, Target Amount w/Guardrails',
    'withdrawal_mode': 'guardrail',
    'montecarlo_id': 'mc_guardrail',
    'include_dashboard': True,
    'scenario_description': """Withdraws the target amount from Taxable accounts first, then Tax-Deferred accounts, and Tax-Free accounts last.
            Withdraws an adjusted target amount from each account in each year regardless of account type.
            Target amount is adjusted for guardrails and inflation each year.
        Tax-Deferred Accounts: RMDs are delayed until RMD age and taxed as ordinary income.
        Taxable Accounts: Withdraws the target amount minus RMDs.
            Distinguishes ordinary income from long-term capital gains and qualified dividends.
            Uses standard deduction, Alt Min Tax (AMT), and/or tax-loss harvesting to offset gains. 
        Tax-Free Accounts: Withdraws are delayed until after Taxable and Tax-Deferred accounts are depleted. 
            Qualified withdraws are tax free. No RMDs.
        Pros: Leverage the mix of account types to optimize withdraws. 
        Cons: Triggers capital gains taxes and reduces annual compounding of interest/dividend in taxable accounts."""
    }, 
    {
    'scenario_id': 'roth_conversion',
    'scenario_name': 'Tax Smart, Roth Conversion',
    'withdrawal_mode': 'fixed_amount',
    'montecarlo_id': 'mc_roth_conversion',
    'include_dashboard': True,
    'scenario_description': """Withdraw from Tax-Deferred accounts first, then Taxable accounts, and Tax-Free accounts last. 
            Withdrawals from Tax-Deferred accounts are converted to a Roth IRA.
        Tax-Deferred Accounts: Maximizes withdraws to stay under a given tax bracket or effective tax rate (e.g., 22%, 19%).
        Taxable Accounts: Withdraw includes the taxes due on the conversion amount + gap amount on tax bracket or effective tax rate.
        Tax-Free Accounts: Withdraws are delayed until after Taxable and Tax-Deferred accounts are depleted. 
            Qualified withdraws are tax free. No RMDs.
        Pros: Limits capital gains taxes and fully leverages annual compounding of interest/dividends in taxable accounts. 
        Cons: Roth conversion amount is taxed as ordinary income and conversion amount cannot be withdraws for five years.
        Tips: Convert before collecting social security or RMDs. Convert when market is down to pay less taxes.
            Offset conversion taxes with large deductions (business losses, charitable contributions, or medical expenses)"""
    }
]