# wd_run_simulation.py - Orchestration layer that loops through years, accounts, and coordinates simulation steps

import os
import pandas as pd

from context.context import SimulationContext
from core.spending_util import SpendingModel
from loader.tax_loader import TaxTable

from withdrawal.wd_ledger import WithdrawalLedger
from withdrawal.wd_util import YearAnnotation
from withdrawal.wd_run_withdrawal import (
    log_income_stream,
    apply_rate_based_withdrawal,
    apply_amount_based_withdrawals
)
from withdrawal.wd_roth_conversion import perform_roth_conversion
from withdrawal.wd_rmd_suppression import apply_rmd_suppression

def simulate_withdrawal(
    context: SimulationContext,
    tax_table: TaxTable,
    spending_model: SpendingModel,
    portfolio_df: pd.DataFrame,
    wd_ledger: WithdrawalLedger
) -> dict:
    """
    Simulate withdrawals, taxes, and income streams over time; sync with WithdrawalLedger.
    """

    config = context.config
    schedule = context.schedule
    sim_mode = context.sim_mode
    spending_model_name = context.catalog_config.spending_model
    draw_order = context.catalog_config.draw_order

    df_deduction = tax_table.standard_deduction
    df_bracket = tax_table.tax_bracket
    df_lef = tax_table.lef

    portfolio_df = context.portfolio

    # Validate filing status
    filing_statuses = (
        portfolio_df['filing_status']
        .dropna()
        .str.strip()
        .str.lower()
        .unique()
    )
    if len(filing_statuses) != 1:
        raise ValueError(f"Expected one filing status, found: {filing_statuses.tolist()}")
    filing_status = filing_statuses[0]

    # Base deduction
    base_year = df_deduction[df_deduction['year'] == schedule.base_year]
    if not base_year.empty and filing_status in base_year.columns:
        base_deduction = base_year[filing_status].iloc[0]
    else:
        raise ValueError(
            f"Missing deduction data for year {schedule.base_year} and status '{filing_status}'"
        )

    all_annotations = []

    # ============================================================
    # MAIN YEAR LOOP
    # ============================================================
    for ydx in range(config.retire_max_years):
        year = schedule.year(ydx)
        age = schedule.age(ydx)

        income_total = 0.0
        taxable_income = 0.0
        taxable_gain_total = 0.0
        taxable_ssa = 0.0
        total_withdrawn = 0.0

        # --------------------------------------------------------
        # 1) Process income streams first (SSA, pensions, etc.)
        # --------------------------------------------------------
        for pdx, account in portfolio_df.iterrows():
            source_type = account['source_type']
            if source_type not in ['inc_fers', 'inc_ord', 'inc_ssa']:
                continue

            current_balance = account['current_balance']
            base_balance = account.get('base_balance', current_balance)
            years_since_start = int(ydx)

            income, taxable = log_income_stream(
                context, account, wd_ledger,
                base_balance, age, year, years_since_start
            )

            portfolio_df.loc[pdx, ['current_balance', 'end_balance']] = income
            income_total += income
            taxable_income += taxable

        # --------------------------------------------------------
        # 2) Compute spending target (before conversions/suppression)
        # --------------------------------------------------------
        withdrawal_target, guardrail_meta = spending_model.compute_spending_target(
            spending_model_name,
            portfolio_df,
            year_index=ydx
        )

        # --------------------------------------------------------
        # 3) Roth conversion (ALWAYS before RMD suppression)
        # --------------------------------------------------------
        if sim_mode == 'roth_conversion':
            taxable_income, portfolio_df = perform_roth_conversion(
                tax_table=tax_table,
                wd_ledger=wd_ledger,
                portfolio_df=portfolio_df,
                year=year,
                age=age,
                filing_status=filing_status,
                taxable_income_so_far=taxable_income,
                target_bracket_rate=0.24  # 24% bracket top
            )

        # --------------------------------------------------------
        # 4) RMD suppression (may adjust target / behavior)
        # --------------------------------------------------------
        if sim_mode == 'rmd_suppression':
            withdrawal_target = apply_rmd_suppression(
                context=context,
                portfolio_df=portfolio_df,
                withdrawal_target=withdrawal_target,
                year=year,
                age=age
            )

        # --------------------------------------------------------
        # 5) Withdrawals from investment accounts in draw_order
        # --------------------------------------------------------
        for source_tax_type in draw_order:
            draw_df = portfolio_df[portfolio_df['source_tax_type'] == source_tax_type]

            for pdx, account in draw_df.iterrows():

                source_type = account['source_type']
                current_balance = account['current_balance']
                base_balance = account.get('base_balance', current_balance)
                end_balance = current_balance

                # Skip income accounts (already processed)
                if source_type in ['inc_fers', 'inc_ord', 'inc_ssa']:
                    continue

                # Growth
                sim_rate = context.sim_rate
                current_balance = round(current_balance * (1 + sim_rate), 2)
                portfolio_df.loc[pdx, 'current_balance'] = current_balance

                # Withdrawals
                if spending_model_name == 'fixed_rate':
                    wd_amount, end_balance, taxable_inc, taxable_gain_amt = apply_rate_based_withdrawal(
                        context, df_lef, wd_ledger,
                        account, year, age, current_balance,
                        withdrawal_target
                    )

                elif spending_model_name in ('fixed_amount', 'guardrails'):
                    wd_ledger, end_balance, portfolio_df, wd_amount, taxable_inc, taxable_gain_amt = (
                        apply_amount_based_withdrawals(
                            context, df_lef, portfolio_df, wd_ledger,
                            account, year, age, current_balance,
                            draw_order, withdrawal_target
                        )
                    )

                else:
                    raise ValueError(f"Unknown spending model: {spending_model_name}")

                taxable_income += taxable_inc
                taxable_gain_total += taxable_gain_amt
                total_withdrawn += wd_amount

                portfolio_df.loc[pdx, ['current_balance', 'end_balance']] = end_balance

                # Guardrail logging (if any)
                if guardrail_meta.get("triggered", False):
                    wd_ledger.add_guardrail(
                        account=account['source_type'],
                        year=year,
                        age=age,
                        current_balance=current_balance,
                        end_balance=end_balance,
                        guardrail_type=guardrail_meta.get('type'),
                        direction=guardrail_meta.get('direction'),
                        rate_low=guardrail_meta.get('rate_low', 0.0),
                        rate_high=guardrail_meta.get('rate_high', 0.0),
                        amount_low=guardrail_meta.get('amount_low', 0.0),
                        amount_high=guardrail_meta.get('amount_high', 0.0)
                    )

        # --------------------------------------------------------
        # 6) Shortfall logging
        # --------------------------------------------------------
        shortfall = max(0, withdrawal_target - (income_total + total_withdrawn))
        if shortfall > 0:
            wd_ledger.add_shortfall(
                year=year,
                age=age,
                target=withdrawal_target,
                actual=income_total + total_withdrawn,
                filing_status=filing_status
            )

        # Ledger truth for total withdrawn
        total_withdrawn = wd_ledger.frame.df.query("year == @year")["wd_amount"].sum()

        # --------------------------------------------------------
        # 7) Tax + spending power
        # --------------------------------------------------------
        tax_spending_metrics = spending_model.evaluate_spending_power(
            year, filing_status,
            taxable_income, taxable_gain_total, taxable_ssa,
            base_deduction, ydx,
            income_total, total_withdrawn
        )

        year_ann = YearAnnotation.create(
            year=year,
            **tax_spending_metrics,
            guardrail_triggered=guardrail_meta.get('triggered', False),
            guardrail_direction=guardrail_meta.get('direction'),
            actual_rate=guardrail_meta.get('actual_rate')
        )

        all_annotations.append(year_ann)

    df_dashboard = pd.DataFrame([ann.to_dict() for ann in all_annotations])

    return {
        "df_dashboard": df_dashboard,
        "all_annotations": all_annotations,
        "total_withdrawn": total_withdrawn
    }