from datetime import datetime
from pathlib import Path
from typing import List

# Core imports
from core.strategy_catalog import STRATEGY_CATALOG, StrategyDefinition
#from src.context.context import SimulationContext

# Orchestrator imports
from src.withdrawal.wd_runner import WithdrawalRunner
from src.montecarlo.mc_runner import MonteCarloRunner
from orchestration.orch_entity import SimulationRun, BatchResults

from src.io.export_util import debug_view

def run_all_strategies(self, selected_strategies: List[str] = None) -> BatchResults:
    """
    Run all strategy simulations across return rate spectrum

    Args:
        selected_strategies: List of strategy IDs to run (None = all strategies)

    Returns:
        BatchResults containing all simulation outcomes
    """
    
    if not self._validate_initialization():
        raise RuntimeError("Orchestrator not properly initialized. Call initialize() first.")
    
    start_time = datetime.now()

    mc_simulations = self.config.mc_simulations

    # Filter strategies if specified
    strategies_to_run = self._get_strategies_to_run(selected_strategies)
    sim_types_per_strategy = [
        (1 if STRATEGY_CATALOG[sc].wd_id else 0) +
        (1 if STRATEGY_CATALOG[sc].mc_id else 0)
        for sc in strategies_to_run
    ]
    total_combinations = sum(sim_types_per_strategy) * len(self._get_return_rates())

    print(f"\n🚀 Running Retirement Simulations")
    print("=" * 60)
    print(f"Strategies: (2) Withdrawal, Monte Carlo - {mc_simulations:,} simulations per strategy")
    print(f"Strategies: ({len(strategies_to_run)}) - {strategies_to_run}")
    print(f"Return rates: ({len(self._get_return_rates())}) - {self._get_return_rates()}")
    print(f"Total combinations: ({total_combinations})")

    # Execute all simulation runs
    all_runs = []
    for strategy_id in strategies_to_run:
        strategy_runs = self._run_strategy_suite(
            strategy_id=strategy_id
        )
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

def run_single_strategy(self, strategy_id: str, return_rate: float) -> SimulationRun:
    """
    Run a single strategy at a specific return rate using dedicated runners.
    """

    # Validate preconditions
    if not self._validate_initialization():
        raise RuntimeError("Orchestrator not properly initialized. Call initialize() first.")
    
    if strategy_id not in STRATEGY_CATALOG:
        raise ValueError(f"Unknown strategy: {strategy_id}")

    # Create context
    strategy_config = STRATEGY_CATALOG[strategy_id]
    wd_context, mc_context, self.schedule = self._create_simulation_contexts(strategy_config, return_rate)

    # Inject shared components
    for ctx in [wd_context, mc_context]:
        ctx.portfolio = self.portfolio_df
        ctx.strategy_config = strategy_config
        ctx.tax_table = self.tax_table

    # Create run folder
    run_folder = self.run_folder / f"{strategy_id}_{return_rate:.2f}pct"
    run_folder.mkdir(parents=True, exist_ok=True)

    # Create simulation run container
    sim_run = SimulationRun(
        strategy_id=strategy_id,
        strategy_config=strategy_config,
        return_rate=return_rate,
        run_folder=run_folder,
        context=wd_context # Default to withdrawal context
    )

    try:
        # Run simulations
        start_time = datetime.now()

        if strategy_config.wd_id:
            debug_view(self.portfolio_df, "Portfolio DataFrame Before WD Run")
            wd_runner = WithdrawalRunner(wd_context, self.schedule, self.portfolio_df, self.tax_table)
            sim_run.wd_results = wd_runner.run()
            wd_runner.export(run_folder)

        if strategy_config.mc_id:
            mc_runner = MonteCarloRunner(mc_context, self.schedule, self.portfolio_df, self.tax_table)
            sim_run.mc_results = mc_runner.run(num_simulations=self.config.mc_simulations)
            mc_runner.export(run_folder)

        sim_run.execution_time = (datetime.now() - start_time).total_seconds()
        sim_run.success = True

        print(f"✅ Completed {strategy_id} at {return_rate:.1%} in {sim_run.execution_time:.1f}s")

    except Exception as e:
        import traceback
        traceback.print_exc()
        sim_run.error_message = str(e)
        print(f"❌ Failed {strategy_id} at {return_rate:.1%}: {e}")

    return sim_run

def _run_strategy_suite(self, strategy_id: str) -> List[SimulationRun]:
    """Run all return rates for a given strategy"""
    return_rates = self._get_return_rates()
    runs = []
    for rate in return_rates:
        run = self.run_single_strategy(strategy_id, rate)
        runs.append(run)
                
    return runs
