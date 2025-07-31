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
