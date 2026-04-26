# wd_run_simulation.py - Orchestration layer that loops through years, accounts, and coordinates simulation steps

import os
import pandas as pd

from src.context.context import SimulationContext
from src.core.schedule import SimulationSchedule
from src.core.spending_util import SpendingModel
from src.core.tax_engine import calculate_tax
from src.io_input.tax_loader import TaxTable

from src.withdrawal.wd_ledger import WithdrawalLedger
from src.withdrawal.wd_analyze_year import YearAnnotation
from src.withdrawal.wd_run_withdrawal import (
    process_income_stream,
    apply_rate_based_withdrawal,
    apply_amount_based_withdrawals
)

from util_dev.debug_util import debug_view

def simulate_withdrawal(context: SimulationContext, schedule: SimulationSchedule, tax_table: TaxTable,
                        spending_model: SpendingModel, portfolio_df: pd.DataFrame, wd_ledger: WithdrawalLedger) -> dict:
    """
    Simulate withdrawals, taxes, and income streams over time; sync with WithdrawalLedger.
    """

    config = context.config
    withdrawal_target = config.spending_target

    df_deduction = tax_table.standard_deduction
    df_bracket = tax_table.tax_bracket
    df_lef = tax_table.lef

    portfolio_df = context.portfolio

#    strategy_id = context.strategy_config.strategy_id
    sim_mode = context.sim_mode

    # Establish and validate filing status
    filing_statuses = portfolio_df['filing_status'].dropna().str.strip().str.lower().unique()

    if len(filing_statuses) != 1:
        raise ValueError(f"Expected one filing status, found: {filing_statuses.tolist()}")

    filing_status = filing_statuses[0]

    # Establish and validate the base deduction which is used to calculate inflation-adjusted standard deduction
    base_year = df_deduction[df_deduction['year'] == schedule.base_year]

    if not base_year.empty and filing_status in base_year.columns:
        base_deduction = base_year[filing_status].iloc[0]
    else:
        raise ValueError(f"Missing deduction data for year {schedule.base_year} and status '{filing_status}'")

    all_annotations = []

    for ydx in range(config.retire_max_years):
        year = schedule.year(ydx)
        age = schedule.age(ydx)

        # 🎯 Initialize year-level variables
        income_total = taxable_income = taxable_gain = taxable_ssa = total_withdrawn = 0.0

        # 💸 Determine withdrawal need
        draw_order = context.strategy_config.determine_draw_order()

        # 🧠 Compute spending target once per year
        if sim_mode == 'fixed_rate':
            withdrawal_rate, guardrail_meta = spending_model.compute_spending_target(sim_mode, portfolio_df, year_index=ydx)
        else:
            withdrawal_target, guardrail_meta = strategy.compute_spending_target(sim_mode, portfolio_df, year_index=ydx)

        # 🛠 Log guardrail if triggered
        if guardrail_meta.get('triggered', False):
            wd_ledger.add_guardrail(
                account=account,
                year=year,
                age=age,
                current_balance=current_balance,
                end_balance=end_balance,
                guardrail_type=guardrail_meta['type'],
                direction=guardrail_meta['direction'],
                rate_low=guardrail_meta.get('rate_low', 0.0),
                rate_high=guardrail_meta.get('rate_high', 0.0),
                amount_low=guardrail_meta.get('amount_low', 0.0),
                amount_high=guardrail_meta.get('amount_high', 0.0)
            )

        # 🔁 Process each account in the preferred draw order
        for account_tax_type in draw_order:
            draw_df = portfolio_df[portfolio_df['account_tax_type'] == account_tax_type]
            for pdx, account in draw_df.iterrows():

                # Account-level variables
                account_type = account['account_type']
                current_balance = account['current_balance']
                end_balance = current_balance

                # Inflation adjustment are calculated off of the base balance (versus prior year balance)
                base_balance = account['base_balance']

                if account_type in ['inc_fers', 'inc_ord', 'inc_ssa']:

                    # Track years since start to calculate compound growth
                    years_since_start = int(ydx)

                    # Process an income stream
                    income, taxable = process_income_stream(
                        context, account, wd_ledger, base_balance, age, year, years_since_start
                    )
                    portfolio_df.loc[pdx, ['current_balance', 'end_balance']] = income
                    income_total += income
                    taxable_income += taxable

                    continue # skip investment accounts

                # ── Investment Account Growth ────────────────────
                sim_rate = context.sim_rate
                current_balance = round(current_balance * (1 + sim_rate), 2)
                portfolio_df.loc[pdx, 'current_balance'] = current_balance

                # ── Withdrawal Logic ─────────────────────────────
                if sim_mode == 'fixed_rate':

                    # Apply fixed rate withdrawal strategy
                    wd_amount, end_balance, taxable_inc, taxable_gain = apply_rate_based_withdrawal(
                        context, schedule, df_lef, wd_ledger, account, year, age, current_balance, withdrawal_rate
                    )

                elif sim_mode in ('fixed_amount', 'fixed_amount_roth', 'guardrail_amount', 'guardrail_amount_roth'):

                    wd_ledger, end_balance, portfolio_df, wd_amount, taxable_inc, taxable_gain = apply_amount_based_withdrawals(
                        context, schedule, df_lef, portfolio_df, wd_ledger, account, year, age, current_balance, 
                        draw_order, withdrawal_target
                    )

                taxable_income += taxable_inc
                taxable_gain += taxable_gain
                total_withdrawn += wd_amount

                # ── Final Balance Update for investment accounts ─────────────────────────
                portfolio_df.loc[pdx, ['current_balance', 'end_balance']] = end_balance

        # 💸 Log Shortfall if unmet 
        shortfall = max(0, withdrawal_target - (income_total + total_withdrawn))
        if shortfall > 0:
            wd_ledger.add_shortfall(
                year=year,
                age=age,
                target=withdrawal_target,
                actual=income_total + total_withdrawn,
                filing_status=filing_status
            )

        # ── Year-Level Logic ─────────────────────────────d

        # 📊 Compute total withdrawn
        total_withdrawn = wd_ledger.frame.df.query("year == @year")["wd_amount"].sum()

        # 🧾 Compute Tax and 💰 Spending Power
#        taxable_gross_income = taxable_income + taxable_gain + taxable_ssa
        tax_spending_metrics = spending_model.evaluate_spending_power(
            df_bracket, year, filing_status, taxable_income, taxable_gain, taxable_ssa,
            base_deduction, ydx, income_total, total_withdrawn
        )

        # 🧾 Annual Summary
        year_ann = YearAnnotation.create(
            year=year,
            **tax_spending_metrics,
            guardrail_triggered=guardrail_meta['guardrail_triggered'],
            guardrail_direction=guardrail_meta['guardrail_direction'],
            actual_rate=guardrail_meta['actual_rate']
        )

        all_annotations.append(year_ann)

    # 📊 Dashboard DataFrame
    df_dashboard = pd.DataFrame([ann.to_dict() for ann in all_annotations])

    return {
        "df_dashboard": df_dashboard,
        "all_annotations": all_annotations,
        "total_withdrawn": total_withdrawn
    }
