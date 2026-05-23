"""
Withdrawal Engine Runner
------------------------
Coordinates the year-by-year withdrawal simulation.

This module:
- orchestrates the income, rate, amount, and RMD engines
- manages the simulation loop
- writes to the WithdrawalLedger
- reads from SimulationContext
- does NOT contain business logic
"""

from core.schema_util import WD_TYPE_MAP
from context.context import SimulationContext
from core.spending_util import SpendingModel
from withdrawal.wd_ledger import WithdrawalLedger
from withdrawal.wd_engine_discretionary import calculate_discretionary_withdrawals

from withdrawal.wd_engine_income import log_income_stream
from withdrawal.wd_engine_rate import apply_rate_withdrawal
from withdrawal.wd_engine_rmd import apply_rmd

def _validate_filing_status(portfolio_df):
    filing_statuses = (
        portfolio_df['filing_status']
        .dropna()
        .str.strip()
        .str.lower()
        .unique()
    )
    if len(filing_statuses) != 1:
        raise ValueError(f"Expected one filing status, found: {filing_statuses.tolist()}")
    return filing_statuses[0]

def run_withdrawal_simulation(
    context: SimulationContext,
    spending_model: SpendingModel,
    portfolio_df,
    wd_ledger: WithdrawalLedger
) -> dict:

    config = context.config
    schedule = context.schedule
    sim_mode = context.sim_mode

    # Validate filing status upfront (assumes all accounts have same filing status)
    _validate_filing_status(portfolio_df)

    # Initialize when each account becomes eligible for discretionary withdrawals
    portfolio_df['effective_distribution_age']  = portfolio_df['distribution_age']
    portfolio_df['effective_distribution_year'] = portfolio_df['distribution_year']

    # Adjust effective distribution ages/years based on which accounts are eligible first in the given simulation mode
    if sim_mode == 'deferred_first':
        mask = portfolio_df['source_type'].isin(['ira', 'tsp', 'ira_inherited'])
        portfolio_df.loc[mask, 'effective_distribution_age']  = schedule.base_age
        portfolio_df.loc[mask, 'effective_distribution_year'] = schedule.base_year

    elif sim_mode == 'taxable_first':
        mask = portfolio_df['source_type'] == 'brokerage'
        portfolio_df.loc[mask, 'effective_distribution_age']  = schedule.base_age
        portfolio_df.loc[mask, 'effective_distribution_year'] = schedule.base_year

    elif sim_mode == 'fixed_rate_tax_efficient':
        portfolio_df['effective_distribution_age']  = schedule.base_age
        portfolio_df['effective_distribution_year'] = schedule.base_year    

    # --------------------------------------------------
    # MAIN SIMULATION LOOP
    # --------------------------------------------------
    for year_idx in range(schedule.duration + 1):

        year = schedule.year(year_idx)
        age  = schedule.age(year_idx)

        # --------------------------------------------------
        # 1) INCOME STREAMS (SSA, FERS, ORDINARY)
        # --------------------------------------------------
        for _, account in portfolio_df.iterrows():
            if account['source_type'].startswith('inc_'):
                log_income_stream(
                    context=context,
                    account=account,
                    wd_ledger=wd_ledger,
                    base_balance=account['base_balance'],
                    age=age,
                    year=year
                )

        # --------------------------------------------------
        # 2) RMDs (IRA, TSP, INHERITED IRA)
        # --------------------------------------------------
        for idx, account in portfolio_df.iterrows():
            if account['source_type'] in ('ira', 'tsp', 'ira_inherited'):

                _ = apply_rmd(
                    context=context,
                    account=account,
                    wd_ledger=wd_ledger,
                    age=age,
                    year=year
                )

                portfolio_df.at[idx, 'current_balance'] = account['current_balance']

        # --------------------------------------------------
        # 3) DISCRETIONARY WITHDRAWALS
        # --------------------------------------------------
        spending_target, guardrail_meta = spending_model.compute_spending_target(
            sim_mode=sim_mode,
            portfolio_df=portfolio_df,
            year_index=year_idx
        )

        # ---- FIXED RATE (TAX-EFFICIENT) PATH -----------------
        if sim_mode == 'fixed_rate_tax_efficient':
            draw_order = context.catalog_config.draw_order

            # 3a) Compute income for this year from the ledger
            income_sources = ['inc_fers', 'inc_ssa', 'inc_ord']
            year_income = wd_ledger.frame.df[
                (wd_ledger.frame.df['year'] == year) &
                (wd_ledger.frame.df['source_type'].isin(income_sources))
            ]['wd_amount'].sum()

            # 3b) Compute RMDs for this year from the ledger
            year_rmd = wd_ledger.frame.df[
                (wd_ledger.frame.df['year'] == year) &
                (wd_ledger.frame.df['wd_type'].str.contains('ira_rmd', case=False, na=False))
            ]['wd_amount'].sum()

            # 3c) Net withdrawal need (after income and RMDs)
            withdrawal_target = max(0.0, spending_target - year_income - year_rmd)

            if withdrawal_target > 0:
                # 3d) Single coordinated discretionary pass
                portfolio_df, discretionary_records = calculate_discretionary_withdrawals(
                    context=context,
                    portfolio_df=portfolio_df,
                    draw_order=draw_order,
                    withdrawal_target=withdrawal_target
                )
            else:
                discretionary_records = {}

            # 3e) Write ledger entries for discretionary withdrawals
            for idx, account in portfolio_df.iterrows():
                if account['source_type'].startswith('inc_'):
                    continue  # income already logged

                record = discretionary_records.get(idx)
                if not record:
                    continue

                wd_amount = record['wd_amount']
                taxable_income = record['taxable_income']
                taxable_gain = record['taxable_gain']
                wd_type = record['wd_type']
                current_balance = record['end_balance']

                # Closure logic
                closure_met = False
                if current_balance <= config.account_closure_amount * config.account_closure_threshold:
                    wd_amount += current_balance
                    current_balance = 0.0
                    closure_met = True

                end_balance = current_balance
                portfolio_df.at[idx, 'current_balance'] = end_balance

                marginal_rate = context.tax_engine.get_marginal_rate(
                    year=year,
                    taxable_income=taxable_income,
                    filing_status=account['filing_status']
                )

                wd_ledger.add_year(
                    account=account,
                    year=year,
                    age=age,
                    current_balance=current_balance,
                    end_balance=end_balance,
                    wd_type=wd_type,
                    wd_amount=wd_amount,
                    taxable_income=taxable_income,
                    taxable_gain=taxable_gain,
                    marginal_rate=marginal_rate,
                    closure_met=closure_met,
                    guardrail_triggered=guardrail_meta.get('guardrail_triggered'),
                    guardrail_direction=guardrail_meta.get('guardrail_direction'),
                    )

        # ---- AMOUNT / ORDERED MODES ----------------------
        elif sim_mode in ('taxable_first', 'deferred_first'):
            draw_order = context.catalog_config.draw_order

            # 3a) Compute income for this year from the ledger
            income_sources = ['inc_fers', 'inc_ssa', 'inc_ord']
            year_income = wd_ledger.frame.df[
                (wd_ledger.frame.df['year'] == year) &
                (wd_ledger.frame.df['source_type'].isin(income_sources))
            ]['wd_amount'].sum()

            # 3b) Compute RMDs for this year from the ledger
            year_rmd = wd_ledger.frame.df[
                (wd_ledger.frame.df['year'] == year) &
                (wd_ledger.frame.df['wd_type'].str.contains('ira_rmd', case=False, na=False))
            ]['wd_amount'].sum()

            # 3c) Net withdrawal need (after income and RMDs)
            withdrawal_target = max(0.0, spending_target - year_income - year_rmd)

            if withdrawal_target > 0:
                # 3d) Single coordinated discretionary pass
                portfolio_df, discretionary_records = calculate_discretionary_withdrawals(
                    context=context,
                    portfolio_df=portfolio_df,
                    draw_order=draw_order,
                    withdrawal_target=withdrawal_target
                )
            else:
                discretionary_records = {}

            # 3e) Write ledger entries for discretionary withdrawals
            for idx, account in portfolio_df.iterrows():
                if account['source_type'].startswith('inc_'):
                    continue  # income already logged

                record = discretionary_records.get(idx)

                if not record:
                    # No discretionary withdrawal for this account this year → skip
                    continue

                wd_amount = record['wd_amount']
                taxable_income = record['taxable_income']
                taxable_gain = record['taxable_gain']
                wd_type = record['wd_type']
                current_balance = record['end_balance']
                
                # Closure logic for discretionary withdrawals (only, since RMDs have their own closure logic)
                closure_met = False
                if current_balance <= config.account_closure_amount * config.account_closure_threshold:
                    wd_amount += current_balance
                    current_balance = 0.0
                    closure_met = True

                end_balance = current_balance
                portfolio_df.at[idx, 'current_balance'] = end_balance

                # Marginal rate based on this account's taxable income
                marginal_rate = context.tax_engine.get_marginal_rate(
                    year=year,
                    taxable_income=taxable_income,
                    filing_status=account['filing_status']
                )

                wd_ledger.add_year(
                    account=account,
                    year=year,
                    age=age,
                    current_balance=current_balance,
                    end_balance=end_balance,
                    wd_type=wd_type,
                    wd_amount=wd_amount,
                    taxable_income=taxable_income,
                    taxable_gain=taxable_gain,
                    marginal_rate=marginal_rate,
                    closure_met=closure_met,
                    guardrail_triggered=guardrail_meta.get('guardrail_triggered'),
                    guardrail_direction=guardrail_meta.get('guardrail_direction'),
                    )

    # --------------------------------------------------
    # RETURN RESULTS
    # --------------------------------------------------
    return {
        "df_dashboard": wd_ledger.frame.df,
        "all_annotations": {},
        "total_withdrawn": wd_ledger.frame.df['wd_amount'].sum()
    }
