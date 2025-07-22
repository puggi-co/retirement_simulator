from config_context import load_config_from_workbook, build_context_objects
from workbook_interface import load_workbook_inputs
from adjustments import apply_adjustments
from ledger import AccountLedger
from tax_models import TaxCalculator
from strategy_withdrawals import simulate_scenario_withdrawals
from strategy_montecarlo import simulate_montecarlo_withdrawals
from runner import ScenarioRunner

# simulation orchestrator
def run_single_scenario(context, portfolio_df, return_rate, scenario, wb=None, run_folder=None):
    run_begin_date = datetime.now()
    run_folder = create_run_subfolder()

    wb = WorkbookInterface()
    wb.load_workbook()

    df_scenario = wb.get('scenario')
    df_my_portfolio = wb.get('porfolio')
    config = wb.get('config')
    raw_schedule = wb.get('schedule')
    schedule = build_schedule(raw_schedule)

    display(config)
    display(schedule)
    display(df_scenario)
    display(df_my_portfolio)
    
    scenario_name = scenario['scenario_name']
    scenario_id = scenario['scenario_id']
    withdrawal_mode = scenario.get('withdrawal_mode', 'fixed_amount')  # default fallback
    include_dashboard = scenario.get('include_dashboard', True)

    print('=' * 60)
    print(f'\nSimulating: {scenario_name}, Return Rate: {return_rate}%')

    context.withdrawal_mode = withdrawal_mode
    runner = ScenarioRunner(context, portfolio_df, return_rate, wb=wb)
    runner.run_strategy()
    runner.export_all_to_folder(run_folder, include_summary=True, include_dashboard=include_dashboard)

def main():

    # 
    run_begin_date = datetime.now()
    run_folder = create_run_subfolder()

    wb = WorkbookInterface()
    wb.load_workbook()

    df_scenario = wb.get('scenario')
    df_my_portfolio = wb.get('porfolio')
    config = wb.get('config')
    raw_schedule = wb.get('schedule')
    schedule = build_schedule(raw_schedule)

    display(config)
    display(schedule)
    display(df_scenario)
    display(df_my_portfolio)
    

    for return_rate in config.get_return_rates():
        for sdx, scenario in df_scenario.iterrows():
            scenario_id = scenario['scenario_id']
            context = build_context(scenario_id, config=config, schedule=schedule)

            run_single_scenario(context, df_my_portfolio, return_rate, scenario, wb=wb, run_folder=run_folder)

            mc_id = scenario.get('montecarlo_id')
            if mc_id:
                mc_context = build_context(mc_id, config=config, schedule=schedule)
                print(f'\n🎲 Running Monte Carlo Pair: {mc_id}, for {scenario["scenario_name"]}, Return Rate: {return_rate}%')

                run_single_scenario(mc_context, df_my_portfolio, return_rate, scenario, wb=None, run_folder=run_folder)

    run_end_date = datetime.now()
    print('Total run time: ', run_end_date - run_begin_date)
    
    # Step 1: Load inputs from Excel workbook
    config = load_config_from_workbook("inputs.xlsx")
    context = build_context_objects(config)

    # Step 2: Apply financial adjustments (e.g. inflation, COLA)
    apply_adjustments(config, context)

    # Step 3: Initialize ledger and tax model
    ledger = AccountLedger(config)
    tax_model = TaxCalculator(config)

    # Step 4: Run deterministic scenarios
    runner = ScenarioRunner(config, context, ledger, tax_model)
    results_fixed = runner.run_scenario("withdrawal_rate")
    results_guardrail = runner.run_scenario("withdrawal_guardrail")

    # Step 5: Run Monte Carlo simulations
    mc_results = simulate_montecarlo_withdrawals(
        scenario_id="withdrawal_amount",
        config=config,
        num_simulations=1000
    )

    # Step 6: Export and visualize results
    runner.export_results(results_fixed, "fixed_rate")
    runner.export_results(results_guardrail, "guardrail")
    runner.export_results(mc_results, "montecarlo")

if __name__ == "__main__":
    main()
