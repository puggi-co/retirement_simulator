############## Monte Carlo Simulations ###############

def simulate_montecarlo_withdrawals(context: SimulationContext, 
    config,
    df_accounts,
    rate,
    mode='target_amount',  # 'fixed_rate', 'target_amount', or 'guardrail_amount'
    num_simulations=1000
):
    """
    Simulate withdrawal strategy using Monte Carlo returns.
    Supports target-based withdrawals, rate-based, and guardrails on target amount.
    """

    config_years = config.years
    inflation_rate = config.inflation_rate
    withdrawal_rate = config.withdrawal_rate
    base_target_amount = config.withdrawal_amount
    guardrail_floor = getattr(config, 'guardrail_floor', 0.035)
    guardrail_ceiling = getattr(config, 'guardrail_ceiling', 0.055)
    seed = config.seed
    return_sampler = config.return_sampler or (lambda n: np.random.normal(loc=rate, scale=5, size=n))

    if seed is not None:
        np.random.seed(seed)

    # Initial balance from eligible accounts
    initial_balance = df_accounts.loc[
        df_accounts['account_tax_type'].isin(['taxable', 'deferred', 'tax_free']),
        'begin_balance'
    ].sum()

    all_results = []

    for sim in range(1, num_simulations + 1):
        returns = return_sampler(config_years)
        downturn_years = np.random.choice(range(1, config_years + 1), size=4, replace=False)

        balance = initial_balance
        withdrawal_target = base_target_amount

        sim_data = []

        for ydx in range(config_years):
            year = ydx + 1
            return_rate = returns[ydx]
            is_downturn = year in downturn_years

            # Portfolio grows first (withdraw-after-return)
            balance *= (1 + return_rate / 100)

            # Update withdrawal target based on strategy
            if mode == 'fixed_rate':
                withdrawal_amt = balance * withdrawal_rate

            elif mode == 'target_amount':
                withdrawal_amt = withdrawal_target * ((1 + inflation_rate) ** ydx)

            elif mode == 'guardrail_amount':
                actual_rate = withdrawal_target / balance if balance > 0 else 0
                if actual_rate > guardrail_ceiling:
                    withdrawal_target *= (1 - 0.10)
                elif actual_rate < guardrail_floor:
                    withdrawal_target *= (1 + 0.10)
                else:
                    withdrawal_target *= (1 + inflation_rate)
                withdrawal_amt = min(withdrawal_target, balance)

            else:
                raise ValueError(f"Unsupported mode: '{mode}'")

            withdrawal_amt = min(withdrawal_amt, balance)
            balance -= withdrawal_amt

            actual_withdrawal_rate = withdrawal_amt / balance if balance > 0 else np.nan

            sim_data.append({
                'simulation': sim,
                'strategy': mode,
                'year': year,
                'return_%': return_rate,
                'withdrawal': withdrawal_amt,
                'portfolio_balance': balance,
                'actual_rate': actual_withdrawal_rate,
                'downturn': is_downturn
            })

        all_results.append(pd.DataFrame(sim_data))

    return pd.concat(all_results, ignore_index=True)

def summarize_withdrawal_outcomes(
    df_sim_results,
    failure_thresholds=[0, 100_000, 250_000],
    export_excel_path=None,
    export_pdf_path=None
):
    """Summarize Monte Carlo portfolio outcomes from withdrawal simulations."""

    strategy_col = 'strategy' if 'strategy' in df_sim_results.columns else 'strategy_placeholder'
    df_sim_results[strategy_col] = df_sim_results.get(strategy_col, 'strategy_1')

    if 'simulation' in df_sim_results.columns:
        df_final = df_sim_results.groupby(['strategy', 'simulation']).tail(1).copy()
    else:
        df_sim_results['strategy'] = df_sim_results.get('strategy', 'strategy_1')
        df_sim_results['simulation'] = 1  # Placeholder for compatibility
        df_final = df_sim_results.tail(1).copy()

    def failure_table(df, thresholds):
        rows = []
        for strategy in df[strategy_col].unique():
            subset = df[df[strategy_col] == strategy]
            total = subset['simulation'].nunique()
            for t in thresholds:
                failed = (subset['portfolio_balance'] <= t).sum()
                rows.append({
                    'strategy': strategy,
                    'threshold': f'≤ ${t:,.0f}',
                    'failure_rate_(%)': round(100 * failed / total, 2)
                })
        return pd.DataFrame(rows)

    print("👀 df_final columns:", df_final.columns.tolist())

    df_failures = failure_table(df_final, failure_thresholds)

    df_summary = df_final.groupby(strategy_col)['portfolio_balance'].agg(
        Median='median', Mean='mean', Std='std', Min='min', Max='max'
    ).round(2)

    df_median = df_sim_results.groupby([strategy_col, 'year'])['portfolio_balance'].median().reset_index()
    df_percentiles = df_sim_results.groupby([strategy_col, 'year'])['portfolio_balance'].quantile(
        [0.1, 0.25, 0.75, 0.9]
    ).unstack().reset_index()
    df_percentiles.columns = [strategy_col, 'Year', '10th', '25th', '75th', '90th']

    # Plot: Median & Band
    plt.figure(figsize=(12, 6))
    for strategy in df_median[strategy_col].unique():
        med = df_median[df_median[strategy_col] == strategy]
        pctl = df_percentiles[df_percentiles[strategy_col] == strategy]
        plt.plot(med['year'], med['portfolio_balance'], label=f'{strategy} (Median)')
        plt.fill_between(pctl['year'], pctl['10th'], pctl['90th'], alpha=0.15)
    plt.title('Portfolio Median Trajectory with 10–90% Band')
    plt.xlabel('Year')
    plt.ylabel('portfolio_balance ($)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    if export_pdf_path:
        plt.savefig(export_pdf_path.replace('.pdf', '_trajectory.pdf'))

    # Plot: KDE of Final Balances
    plt.figure(figsize=(10, 5))
    sns.kdeplot(data=df_final, x='portfolio_balance', hue=strategy_col, fill=True, alpha=0.4)
    for t in failure_thresholds[1:]:
        plt.axvline(t, color='gray', linestyle='--', alpha=0.5)
    plt.axvline(0, color='black', linestyle='--')
    plt.title('Distribution of Ending Balances (Final Year)')
    plt.grid(True)
    plt.tight_layout()
    if export_pdf_path:
        plt.savefig(export_pdf_path.replace('.pdf', '_distribution.pdf'))

    # Export Excel
    if export_excel_path:
        with pd.ExcelWriter(export_excel_path, engine='xlsxwriter') as writer:
            df_sim_results.to_excel(writer, index=False, sheet_name='Sim Paths')
            df_final.to_excel(writer, index=False, sheet_name='Final Year Results')
            df_summary.to_excel(writer, sheet_name='Summary Stats')
            df_failures.to_excel(writer, index=False, sheet_name='Failure Rates')
            df_median.to_excel(writer, index=False, sheet_name='Median Paths')
            df_percentiles.to_excel(writer, index=False, sheet_name='Percentiles')

    print('\n📊 Portfolio Summary (Final Year)')
    print(df_summary)
    print('\n📉 Failure Rates by Threshold')
    print(df_failures)

    return df_summary, df_failures, df_median, df_percentiles

def diagnostic_dashboard(context: SimulationContext, 
                         sim_results, config, folder='.', export_excel_name='diagnostic_output.xlsx', export_pdf_name='diagnostic_charts.pdf'):
    excel_path = os.path.join(folder, export_excel_name)
    pdf_path = os.path.join(folder, export_pdf_name)

    # Perform your usual analysis and save files to the paths above
    analyze_montecarlo_rmd_timing(
        df_sim_results=sim_results,
        config=config,
        export_excel_path=excel_path,
        export_pdf_path=pdf_path
    )

    print(f'📁 Dashboard files saved to: {folder}')
