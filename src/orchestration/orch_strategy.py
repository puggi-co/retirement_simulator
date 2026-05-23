from datetime import datetime
from typing import List

# Core imports
from config.catalog import CATALOG
#from context.context import SimulationContext

# Orchestrator imports
from withdrawal.wd_runner import WithdrawalRunner
from montecarlo.mc_runner import MonteCarloRunner
from orchestration.orch_entity import SimulationRun, BatchResults

from loader.export_util import debug_view

def run_all_strategies(self, selected_strategies: List[str] = None) -> BatchResults:
    """
    This method orchestrates the execution of all strategies defined in the CATALOG.
    """

    if not self._validate_initialization():
        raise RuntimeError("Orchestrator not properly initialized. Call initialize() first.")

    start_time = datetime.now()

    # Global MC toggle
    run_mc = self.config.mc_simulations > 0

    # Filter strategies
    strategies_to_run = self._get_strategies_to_run(selected_strategies)

    # Number of simulation types per strategy
    sim_types_per_strategy = 1 + (1 if run_mc else 0)

    # Total combinations = (# strategies) × (# sim types) × (# return rates)
    total_combinations = (
        len(strategies_to_run) *
        sim_types_per_strategy *
        len(self._get_return_rates())
    )

    # Header
    print("\n🚀 Running Retirement Simulations")
    print("=" * 60)
    print(f"Strategies: {strategies_to_run}")
    print(f"Return rates: {self._get_return_rates()}")
    if run_mc:
        print(f"Monte Carlo: ENABLED — {self.config.mc_simulations:,} simulations per strategy")
    else:
        print("Monte Carlo: DISABLED")
    print(f"Total combinations: {total_combinations}")

    # Execute all simulation runs
    all_runs = []
    for strategy_id in strategies_to_run:
        strategy_runs = self._run_strategy_suite(strategy_id=strategy_id, run_mc=run_mc)
        all_runs.extend(strategy_runs)

    # Compile batch results
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()

    successful_runs = sum(1 for run in all_runs if run.success)
    failed_runs = len(all_runs) - successful_runs

    self.batch_results = BatchResults(
        runs=all_runs,
        total_execution_time=execution_time,
        successful_runs=successful_runs,
        failed_runs=failed_runs,
        run_metadata=self._create_run_metadata()
    )

    # Print summary
    self._print_batch_summary()

    # Export batch summary
    self._export_batch_summary()

    return self.batch_results

def run_single_strategy(self, strategy_id: str, return_rate: float, run_mc: bool) -> SimulationRun:
    """
    Run a single strategy at a specific deterministic return rate (WD),
    and optionally run Monte Carlo. MC ignores return_rate.
    """

    # Validate orchestrator state
    if not self._validate_initialization():
        raise RuntimeError("Orchestrator not properly initialized. Call initialize() first.")
    if strategy_id not in CATALOG:
        raise ValueError(f"Unknown strategy: {strategy_id}")

    # Create contexts for WD and MC
    catalog_config = CATALOG[strategy_id]
    wd_context, mc_context, self.schedule = self._create_simulation_contexts(
        catalog_config,
        return_rate
    )

    # WD context holds the authoritative deterministic return rate
    wd_return_rate = wd_context.return_rate

    # Inject shared components into both contexts
    for ctx in (wd_context, mc_context):
        ctx.portfolio = self.portfolio_df
        ctx.catalog_config = catalog_config
        ctx.tax_table = self.tax_table
        ctx.schedule = self.schedule

    # Create run folder using WD's deterministic return rate
    run_folder = self.run_folder / f"{strategy_id}_{wd_return_rate:.2f}pct"
    run_folder.mkdir(parents=True, exist_ok=True)

    # Create SimulationRun container (WD will assign return_rate later)
    sim_run = SimulationRun(
        strategy_id=strategy_id,
        catalog_config=catalog_config,
        return_rate=None,
        run_folder=run_folder,
        context=wd_context
    )

    try:
        start_time = datetime.now()

        # -------------------------
        # 1. WITHDRAWAL SIMULATION
        # -------------------------
        debug_view(self.portfolio_df, "Portfolio DataFrame Before WD Run")

        wd_runner = WithdrawalRunner(
            wd_context,
            self.portfolio_df,
            self.tax_table
        )

        sim_run.wd_results = wd_runner.run()

        # WD metadata contains the authoritative return_rate
        sim_run.return_rate = sim_run.wd_results.metadata.return_rate

        wd_runner.export(run_folder)

        # -------------------------
        # 2. OPTIONAL MONTE CARLO
        # -------------------------
        if run_mc:
            mc_runner = MonteCarloRunner(
                config=self.config,
                context=mc_context,
                tax_table=self.tax_table
            )

            sim_run.mc_results = mc_runner.run(
                num_simulations=self.config.mc_simulations
            )
            mc_runner.export(run_folder)

        # -------------------------
        # Finalize
        # -------------------------
        sim_run.execution_time = (datetime.now() - start_time).total_seconds()

        # Unified success flag
        sim_run.success = True
        if sim_run.wd_results:
            sim_run.success &= sim_run.wd_results.metadata.success
        if sim_run.mc_results:
            sim_run.success &= sim_run.mc_results.success

        print(f"✅ Completed {strategy_id} at {return_rate:.1%} in {sim_run.execution_time:.1f}s")

    except Exception as e:
        import traceback
        traceback.print_exc()
        sim_run.error_message = str(e)
        print(f"❌ Failed {strategy_id} at {return_rate:.1%}: {e}")

    return sim_run

def _run_strategy_suite(self, strategy_id: str, run_mc: bool) -> List[SimulationRun]:
    """
    Run all return rates for a given strategy.
    MC execution is controlled globally via run_mc.
    """

    return_rates = self._get_return_rates()
    runs = []

    for rate in return_rates:
        run = self.run_single_strategy(
            strategy_id=strategy_id,
            return_rate=rate,
            run_mc=run_mc
        )
        runs.append(run)

    return runs
