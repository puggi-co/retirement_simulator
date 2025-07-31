def simulate_montecarlo_withdrawals(context: MonteCarloContext,
                                    df_accounts: pd.DataFrame,
                                    num_simulations: int = 1000) -> pd.DataFrame:
    from .year_logic import simulate_one_year, create_downturn_years

    config = context.config
    initial_balance = df_accounts.loc[
        df_accounts['account_tax_type'].isin(['taxable', 'deferred', 'tax_free']),
        'begin_balance'
    ].sum()

    all_results = []

    for sim in range(1, num_simulations + 1):
        returns = [context.sample_return(ydx) for ydx in range(config.years)]
        downturn_years = create_downturn_years(config.years, seed=config.montecarlo.seed)

        balance = initial_balance
        withdrawal_target = config.withdrawal_amount
        sim_data = []

        for ydx in range(config.years):
            result = simulate_one_year(
                balance, withdrawal_target, returns[ydx], ydx, downturn_years,
                context.config.withdrawal, context.config.inflation_rate
            )
            sim_data.append(result)
            balance = result['portfolio_balance']
            withdrawal_target = result['withdrawal_target']

        df_sim = pd.DataFrame(sim_data)
        df_sim['simulation'] = sim
        df_sim['strategy'] = config.withdrawal.withdrawal_mode
        all_results.append(df_sim)

    return pd.concat(all_results, ignore_index=True)
