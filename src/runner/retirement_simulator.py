from pathlib import Path
from datetime import datetime
from src.interface.output.export.export_util import create_run_subfolder
from src.interface.input.sim_in_xlsx import SimInputXls
from src.interface.input.tax_loader import load_tax_tables
from src.runner.retirement_simulator import ScenarioRunner
from src.workstreams.scenarios.scenario_catalog import SCENARIO_CATALOG

# from src.config import 
# from core.adjustments import apply_adjustments
# from core.ledger import AccountLedger
# from tax_models import TaxCalculator
# from strategy_withdrawals import simulate_scenario_withdrawals
# from strategy_montecarlo import simulate_montecarlo_withdrawals
# from runner import ScenarioRunner
# from utils.folders import create_run_subfolder
# from utils.schedule import build_schedule


# simulation orchestrator
def run_single_scenario(context, portfolio_df, return_rate, scenario, wbi, run_folder):
    scenario_name = scenario['scenario_name']
    withdrawal_mode = scenario.get('withdrawal_mode', 'fixed_amount')
    include_dashboard = scenario.get('include_dashboard', True)

    print('=' * 60)
    print(f'\nSimulating: {scenario_name}, Return Rate: {return_rate}%')

    context.withdrawal_mode = withdrawal_mode
    runner = ScenarioRunner(context, portfolio_df, return_rate, wbi=wbi)
    runner.run_strategy()
    runner.export_all_to_folder(run_folder, include_summary=True, include_dashboard=include_dashboard)

def main():
    run_begin = datetime.now()
    run_folder = create_run_subfolder()

    # Load account inputs
    account_path = Path("data/in_account.xlsx")
    wbi = SimInputXls()
    wbi.load_workbook(account_path)  # Accepts path now

    # Load tax tables
    tax_path = Path("data/in_tax_table.xlsx")
    tax_tables = load_tax_tables(file_path=tax_path)

    portfolio_df = wbi.get('portfolio')
    config = wbi.get('config')
    schedule = build_schedule(wbi.get('schedule'))
    
    display(portfolio_df)
    display(config)
    display(schedule)

    apply_adjustments(config, schedule)

    for return_rate in config.get_return_rates():
        for scenario_id, scenario_cfg in SCENARIO_CATALOG.items():
            context = build_context_objects(config, scenario_cfg=scenario_cfg, schedule=schedule)

            run_single_scenario(context, portfolio_df, return_rate, scenario_cfg, wbi, run_folder)

            if scenario_cfg.montecarlo_id:
                mc_cfg = SCENARIO_CATALOG[scenario_cfg.montecarlo_id]
                mc_context = build_context_objects(config, scenario_cfg=mc_cfg, schedule=schedule)

                print(f'\n🎲 Running Monte Carlo Pair: {mc_cfg.scenario_id}, Return Rate: {return_rate}%')
                run_single_scenario(mc_context, portfolio_df, return_rate, mc_cfg, wbi, run_folder)

    print('Total run time:', datetime.now() - run_begin)

    run_end_date = datetime.now()
    print('Total run time: ', run_end_date - run_begin_date)

if __name__ == "__main__":
    main()
