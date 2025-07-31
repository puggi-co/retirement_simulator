# ╭─────────────────────────────────────────╮
# │          6. Simulation Engine           │
# ╰─────────────────────────────────────────╯

############## Withdrawal Simulations ###############

def simulate_scenario_withdrawals(
    context: WithdrawalContext, tax_tables: TaxTables, portfolio_df, return_rate, ledger, roth=False):
    """Simulate withdrawals, taxes, and income streams over time; sync with AccountLedger."""

    # Unpack withdrawal context
    config = context.config
    adjust_for_inflation = context.use_inflation()
 
#    account_closure_amount = config.account_closure_amount
    ssa_tax_rate = config.ssa_tax_rate
    config_withdrawal = config.withdrawal_amount
    config_years = context.config.years
    
    schedule = context.schedule
    withdrawal_mode = context.withdrawal_mode

    df_deduction = tax_tables.deduction
    df_bracket   = tax_tables.bracket
    df_lef       = tax_tables.lef

    # Unpack withdrawal config
    withdrawal_goal = context.config.withdrawal.goal_for_year(ydx)
    assumed_gain_rate = withdrawal_cfg.assumed_gain_rate
    withdrawal_rate = withdrawal_cfg.withdrawal_rate
    guardrail_floor = withdrawal_cfg.guardrail_floor
    guardrail_ceiling = withdrawal_cfg.guardrail_ceiling
    
    inflation_rate = schedule.inflation_rate

    # Set local variables used for computing values before confirming portfolio-level changes.
    current_balance = end_balance = 0.0
    withdrawal_amount = omd = rmd = 0.0
    ord_inc = ssa_inc = 0.0
    
    filing_status = portfolio_df['filing_status'].min()

    all_withdrawals = []
    
    for ydx in range(config_years):
        year = schedule.year(ydx)
        age = schedule.age(ydx)
        withdrawals_this_year = []

        withdrawal_goal = context.apply_guardrails(
            context.adjust_for_inflation(context.config.withdrawal.withdrawal_amount, ydx)
        )
        inflation_adjusted = context.adjust_for_inflation(withdrawal_goal, ydx)


        # Set year snapshot starting balances
        income_total = 0.0
        taxable_gain = 0.0
        taxable_income = 0.0
        taxable_ssa = 0.0
        tax_owed = 0.0
        effective_tax_rate = 0.0

        for pdx, account in portfolio_df.iterrows():

            account_type = account['account_type']
            rmd_age = account['rmd_age']

            # 📥 Income Streams - calculate growth and taxes for income sources at begin age
            if account_type in ['ordinary_income', 'ssa_income', 'fers_income'] and age >= rmd_age:
                
                # Update current_balance with growth
                yrs_since_start = age - rmd_age
                if account_type == 'fers_income':
                    growth_factor = (1 + get_fers_cola(inflation_rate)) ** yrs_since_start
                elif account_type == 'ssa_income':
                    growth_factor = (1 + inflation_rate) ** yrs_since_start  # SSA gets full CPI
                else:
                    growth_factor = 1.0
                
                current_balance = round(account['begin_balance'] * growth_factor, 2)
                portfolio_df.loc[pdx, 'current_balance'] = current_balance

                # Set defaults for current year calculation
                ord_inc = ssa_inc = taxable_income = taxable_ssa = 0.0
                end_balance = current_balance  # income accounts aren't depleted
            
                # Categorize income
                if account_type == 'ssa_income':
                    ssa_inc = current_balance
                    taxable_ssa = min(ssa_tax_rate * ssa_inc, ssa_inc)
                else:
                    ord_inc = current_balance
                    taxable_income = ord_inc

                # Write annotated income to ledger
                context.record_income_to_ledger(
                    ledger=ledger,
                    account=account,
                    year=year,
                    age=age,
                    growth_rate=growth_factor,
                    current_balance=current_balance,
                    taxable_income=taxable_income,
                    taxable_ssa=taxable_ssa
                )

                if account_type in ['ordinary_income', 'fers_income']:
                    end_balance = ord_inc
                    taxable_income += ord_inc
                elif account_type == 'ssa_income':
                    end_balance = ssa_inc
                    taxable_ssa += ssa_inc
                else:
                    print('Warning: Account type is not yet supported.', account_type)

                income_total += end_balance
            
            withdrawal_target = max(0, withdrawal_goal - income_total)

            # 📥 Account Streams - calculate growth and taxes for investment accounts
            
            # Fetch standard deduction
            base_deduction = tax_tables.get_deduction(start_year, filing_status)

            base_deduction = df_deduction.loc[
                df_deduction['year'] == start_year, filing_status
            ].values[0]
    #        print('base_deduction', base_deduction)
            
            # 📈 Account Growth
            if account_type in ['ordinary_income', 'ssa_income', 'fers_income']:
                continue  # skip income accounts
            
            return_rate = account['return_rate']
    
            # Update current_balance with growth
            current_balance = round(account['current_balance'] * (1 + return_rate), 2)
            portfolio_df.loc[pdx, 'current_balance'] = current_balance

            if withdrawal_mode == 'fixed_rate':

                ledger, end_balance, taxable_income, taxable_gain = apply_rate_based_withdrawals(WithdrawalContext,  
                    ledger=ledger, account=account, return_rate=return_rate, withdrawal_mode=withdrawal_mode, account_closure_amount=account_closure_amount,
                    year=year, age=age, current_balance=current_balance, ord_inc=ord_inc, ssa_inc=ssa_inc , withdrawal_rate=withdrawal_rate, assumed_gain_rate=assumed_gain_rate,
                    schedule=schedule, df_lef=df_lef
                )
                
                # Suppress Shortfall Logging and other drawdown logic                
                withdrawal_target = 0.0
            
            elif withdrawal_mode in ('target_amount', 'guardrail_amount'):

                portfolio_total = portfolio_df['current_balance'].sum()
                actual_rate = withdrawal_target / portfolio_total
                
                if withdrawal_mode == 'guardrail_amount':
                    if actual_rate > guardrail_ceiling:
                        withdrawal_target *= (1 - 0.10)
                    elif actual_rate < guardrail_floor:
                        withdrawal_target *= (1 + 0.10)
                    else:
                        withdrawal_target *= (1 + inflation_rate)
                
                    withdrawal_goal = withdrawal_target

                draw_order = ['deferred', 'taxable', 'tax_free'] if roth else ['taxable', 'deferred', 'tax_free']

                ledger, end_balance, portfolio_df, withdrawal_goal, taxable_income, taxable_gain = apply_amount_based_withdrawals(
                    ledger, account, portfolio_df, draw_order, withdrawal_mode,
                    year, age, current_balance, withdrawal_goal, income_total, roth, assumed_gain_rate, actual_rate, 
                    df_lef, schedule
                )

            # Update end_balance directly in DataFrame
            portfolio_df.loc[pdx, 'current_balance'] = end_balance
            portfolio_df.loc[pdx, 'end_balance'] = end_balance
                
        # 💸 Shortfall Logging
        if withdrawal_target > 0:
            portfolio_balance = portfolio_df['current_balance'].sum()
            withdrawals_this_year.append({
                'year': year,
                'owner_age': age,
                'account_name': 'Shortfall',
                'account_type': 'Unfunded',
                'account_tax_type': 'Unfunded',
                'withdrawal_amount': round(withdrawal_target, 2),
                'withdrawal_type': 'Unmet Need',
            })

        # Tax computation using inflation-adjusted standard deduction for current year
        years_since_start = max(0, year - start_year)
        inflation_rate = config.inflation_rate
        deduction = base_deduction * ((1 + inflation_rate) ** years_since_start)

        gross_income = taxable_income + taxable_gain + taxable_ssa
        adj_income = max(0, gross_income - deduction)
        tax_owed, eff_rate = calculate_tax(df_bracket, year, filing_status, adj_income)

        # 📊 Taxes & Spending Power
        total_withdrawn = sum(w['withdrawal_amount'] for w in withdrawals_this_year)
        total_cashflow = total_withdrawn + income_total
        net_spend = total_cashflow - tax_owed
        real_spend = net_spend / ((1 + inflation_rate) ** ydx)

        # 💾 Annotate Results
#        portfolio_balance = portfolio_df['current_balance'].sum()     # ← compute after all actions
        for entry in withdrawals_this_year:
            entry.update({
                'other_income': round(income_total, 2),
                'taxable_income_portion': round(taxable_income, 2),
                'gross_taxable_income': round(gross_income, 2),
                'deduction': round(deduction, 2),
                'taxable_income_after_deduction': round(adj_income, 2),
                'tax_owed': round(tax_owed, 2),
                'effective_tax_rate': round(eff_rate, 4),
                'net_spending_power': round(net_spend, 2),
                'real_spending_power': round(real_spend, 2),
                'portfolio_balance': round(portfolio_balance, 2)
            })

        # 📦 Store Results
        all_withdrawals.extend(withdrawals_this_year)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
#        display(ledger.df_ledger)
        display(ledger.df_ledger.query("account_type == 'fers_income'"))
        display(ledger.df_ledger.query("account_type == 'ssa_income'"))
        display(ledger.df_ledger.query("account_type == 'ira_inherited'"))
        display(ledger.df_ledger.query("account_type == 'ira'"))
        display(ledger.df_ledger.query("account_type == 'tsp'"))
        display(ledger.df_ledger.query("account_type == 'brokerage'"))
        display(withdrawals_this_year)
        
    return pd.DataFrame(all_withdrawals)

def get_fers_cola(inflation):
    if inflation <= 0.02:
        return inflation
    elif inflation < 0.03:
        return 0.02
    else:
        return inflation - 0.01

def apply_rate_based_withdrawals(context: withdrawalContext, 
    ledger, account, return_rate, 
    year, age, current_balance, ord_inc, ssa_inc, 
#    withdrawal_rate, assumed_gain_rate, withdrawal_mode, account_closure_amount, schedule, df_lef
):
    """Withdraw a fixed percentage from each account. For tax deferred accounts, withdraw the greater of the fixed rate or the RMD."""

    # Unpack simulation config elements
    schedule = context.schedule
    df_lef = workbook_inputs.lef
    
    account_closure_amount = config.account_closure_amount
    assumed_gain_rate = config.assumed_gain_rate
    withdrawal_rate = config.withdrawal_rate
    withdrawal_mode = context.withdrawal_mode

    
    config = context.config

    df_deduction = workbook_inputs.deduction
    df_bracket   = workbook_inputs.bracket

    adjust_for_inflation = config.adjust_for_inflation
    ssa_tax_rate = config.ssa_tax_rate
    config_withdrawal = config.withdrawal_amount
    config_years = int(config.years)
    guardrail_floor = getattr(config, 'guardrail_floor', 0.035)  # default: 3.5%
    guardrail_ceiling = getattr(config, 'guardrail_ceiling', 0.055)  # default: 5.5%
    


    taxable_income = 0.0
    taxable_gain = 0.0

    withdrawal_amount = omd = rmd = 0.0

    if account['account_type'] in ['ira', 'ira_inherited', 'tsp'] and age >= account['rmd_age']:
        factor = df_lef.loc[
            df_lef['age'] == min(age, schedule.end_age), account['rmd_table']
        ].iloc[0]
        rmd = round(current_balance / factor, 2)
        withdrawal_amount = rmd if current_balance > account_closure_amount else current_balance

    if account['account_type'] == 'brokerage':
        omd = round(current_balance * context.withdrawal_rate)
        withdrawal_amount = omd if current_balance > account_closure_amount else current_balance
        
    # Apply withdrawal
    end_balance = current_balance - withdrawal_amount
    
    # Track taxable portions
    if account['account_tax_type'] == 'deferred':
        taxable_income += withdrawal_amount
    elif account['account_tax_type'] == 'taxable':
        taxable_gain += withdrawal_amount * assumed_gain_rate
#    tax_owed = taxable_income + taxable_gain

    # Adds a year of account activity to the ledger with full annotation.
    ledger.add_year(
        year=year, age=age, return_rate=account['return_rate'], withdrawal_mode=withdrawal_mode, account_name=account['account_name'], 
        begin_balance=current_balance, current_balance=current_balance, end_balance=end_balance, 
        withdraw_amount=withdrawal_amount, omd=0.0, rmd=rmd, ord_inc=0.0, ssa_inc=0.0, 
        taxable_gain=taxable_gain, taxable_income=taxable_income, tax_owed=account['tax_owed'], effective_tax_rate=0.0, 
        roth_convert_amount=account['roth_convert_amount'], rmd_begin_year=account['rmd_begin_year'], rmd_age=account['rmd_age'], rmd_table=account['rmd_table'],
        account_type=account['account_type'], account_tax_type=account['account_tax_type'], filing_status=account['filing_status']
    )
    actual_withdrawal_rate = round(withdrawal_amount / current_balance, 4) if current_balance > 0 else 0.0

    return ledger, end_balance, taxable_income, taxable_gain

def apply_amount_based_withdrawals(context: SimulationContext, 
        ledger, account, portfolio_df, draw_order, withdrawal_mode,
        year, age, current_balance, withdrawal_goal, income_total, roth, assumed_gain_rate, actual_rate, 
        df_lef, schedule
):

    withdrawal_target = max(0, withdrawal_goal - income_total)
    taxable_income = 0
    taxable_gain = 0
    rmd = omd = 0
    withdrawal_amount = 0
    end_balance = current_balance

    # RMD logic
    if account['account_tax_type'] == 'deferred' and age >= account['rmd_age']:
        factor = df_lef.loc[
            df_lef['age'] == min(age, schedule.end_age),
            account['rmd_table']
        ].iloc[0]

        rmd = min(current_balance, round(current_balance / factor, 2))
        current_balance -= rmd
        withdrawal_target -= rmd
        taxable_income += rmd

    # Tax-smart withdrawals
    if withdrawal_target > 0:
        portfolio_df, taxable_income_extra, taxable_gain, withdrawals_this_year = apply_tax_smart_withdrawals(
            portfolio_df, draw_order, year, age, roth, assumed_gain_rate, withdrawal_target
        )
        taxable_income += taxable_income_extra

    end_balance = current_balance
    
    # Add to ledger
    ledger.add_year(
        year=year, age=age, return_rate=account['return_rate'], withdrawal_mode=withdrawal_mode, account_name=account['account_name'], 
        scenario_id = scenario_id, begin_balance=account['begin_balance'], current_balance=current_balance, end_balance=end_balance,
        withdraw_amount=withdrawal_amount, omd=omd, rmd=rmd, ord_inc=0.0, ssa_inc=0.0,
        taxable_gain=taxable_gain, taxable_income=taxable_income, taxable_ssa=taxable_ssa, tax_owed=account['tax_owed'], effective_tax_rate=0.0,
        roth_convert_amount=account['roth_convert_amount'], rmd_begin_year=account['rmd_begin_year'], rmd_age=account['rmd_age'], rmd_table=account['rmd_table'],
        account_type=account['account_type'], account_tax_type=account['account_tax_type'], filing_status=account['filing_status']
    )

    return ledger, end_balance, portfolio_df, withdrawal_goal, taxable_income, taxable_gain

def apply_tax_smart_withdrawals(portfolio_df, draw_order, year, age, roth, assumed_gain_rate, withdrawal_target):
    taxable_income = 0
    taxable_gain = 0
    withdrawals_this_year = []

    for account_tax_type in draw_order:
        draw_df = portfolio_df[portfolio_df['account_tax_type'] == account_tax_type]
        draw_df = draw_df.sort_values(by='current_balance', ascending=True)

        for adx, account in draw_df.iterrows():

            if account['account_type'] in ['fers_income', 'ordinary_income','ssa_income']:
                continue

            current_balance = account['current_balance']
            if withdrawal_target <= 0 or current_balance <= 0:
                break

            withdrawal = min(current_balance, withdrawal_target)
            current_balance -= withdrawal
            withdrawal_target -= withdrawal

            portfolio_df.at[adx, 'current_balance'] = current_balance

            if account_tax_type == 'deferred':
                taxable_income += withdrawal
                withdrawal_type = 'conversion' if roth else 'tax_smart'
            elif account_tax_type == 'taxable':
                taxable_gain += withdrawal * assumed_gain_rate
                withdrawal_type = 'tax_smart'
            else:
                withdrawal_type = 'tax_smart'

            withdrawals_this_year.append({
                'year': year,
                'owner_age': age,
                'account_name': account['account_name'],
                'account_type': account['account_type'],
                'account_tax_type': account_tax_type,
                'withdrawal_amount': round(withdrawal, 2),
                'withdrawal_type': withdrawal_type,
            })

    return portfolio_df, taxable_income, taxable_gain, withdrawals_this_year

def summarize_spending_sources(df_withdrawals: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize how each year's total spending was funded.
    Returns one row per year with spending by source type and relative share.
    """
    df = df_withdrawals.copy()

    df['income_flag'] = df['account_type'].str.endswith('_income')
    df['is_rmd'] = df['withdrawal_type'] == 'RMD'
    df['is_conversion'] = df['withdrawal_type'] == 'conversion'
    df['is_shortfall'] = df['withdrawal_type'].str.lower().str.startswith('unmet')
    
    group = df.groupby('year')

    records = []
    for year, g in group:
        total = g['withdrawal_amount'].sum()
        income = g[g['income_flag']]['withdrawal_amount'].sum()
        rmd = g[g['is_rmd']]['withdrawal_amount'].sum()
        roth = g[g['is_conversion']]['withdrawal_amount'].sum()
        shortfall = g[g['is_shortfall']]['withdrawal_amount'].sum()
        discretionary = total - income - rmd - roth - shortfall

        records.append({
            'year': year,
            'total_spending': round(total, 2),
            'income_streams': round(income, 2),
            'rmd': round(rmd, 2),
            'roth_conversions': round(roth, 2),
            'shortfall': round(shortfall, 2),
            'discretionary_draws': round(discretionary, 2),
            '% income': round(income / total * 100, 1) if total else 0.0,
            '% rmd': round(rmd / total * 100, 1) if total else 0.0,
            '% roth': round(roth / total * 100, 1) if total else 0.0,
            '% shortfall': round(shortfall / total * 100, 1) if total else 0.0,
            '% discretionary': round(discretionary / total * 100, 1) if total else 0.0,
        })

    return pd.DataFrame(records)
