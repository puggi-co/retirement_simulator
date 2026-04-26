# =================== MONTE CARLO (MC) SIMULATION RUNNER ===============
import pandas as pd
from pathlib import Path
from typing import Any, Optional, List

from src.context.context import SimulationContext
from src.core.schedule import SimulationSchedule
from src.montecarlo.mc_engine import MonteCarloEngine
from src.montecarlo.mc_exporter import MonteCarloExporter
from orchestration.orch_entity import (
    MCRunResults,
    MCAnalyzeResults,
    MCMetadata,
    MCStrategyResults
)

class MonteCarloRunner:
    '''Manages the Monte Carlo simulation process'''
    DEFAULT_FAILURE_THRESHOLDS = [0, 100_000, 250_000, 500_000]

    def __init__(self, context: SimulationContext, schedule: SimulationSchedule, portfolio_df: pd.DataFrame, tax_table: Any):
        self.context = context
        self.schedule = schedule
        self.portfolio_df = portfolio_df
        self.tax_table = tax_table
        self.results: Optional[MCStrategyResults] = None

    def run(self, num_simulations: int = 1000, failure_thresholds: Optional[List[int]] = None) -> MCStrategyResults:
        failure_thresholds = failure_thresholds or self.DEFAULT_FAILURE_THRESHOLDS

        print(f'🎲 Running Monte Carlo simulation [{self.context.sim_id}]...')
        print(f'   • Simulations: {num_simulations:,}')
        print(f'   • Mode: {self.context.sim_mode}')
        print(f'   • Duration: {self.schedule.duration} years')

        # 1. Execute core simulation
        engine = MonteCarloEngine(self.context, self.schedule, self.tax_table, failure_thresholds)
        raw_data = engine.simulate(self.portfolio_df, num_simulations)
        run_results = MCRunResults(raw_data=raw_data)

        # 2. Generate analysis
        analysis_data = engine.analyzer.analyze(raw_data)
        analyze_results = MCAnalyzeResults(
            summary=analysis_data.summary,
            failures=analysis_data.failures,
            median=analysis_data.median,
            percentiles=analysis_data.percentiles,
            extra=analysis_data.extra
)

        # 3. Store metadata
        metadata = MCMetadata(
            num_simulations=num_simulations,
            failure_thresholds=failure_thresholds,
            duration=self.schedule.duration,
            sim_mode=self.context.sim_mode,
            sim_id=self.context.sim_id,
            return_rate=self.context.return_rate,
            success=True
        )

        # 4. Package results
        self.results = MCStrategyResults(
            run=run_results,
            analysis=analyze_results,
            metadata=metadata
        )

        return self.results

    def export(self, output_folder: Path, include_charts: bool = True) -> None:
        """Export Monte Carlo simulation results"""

        if not self.results:
            raise ValueError("No Monte Carlo results to export.")

        exporter = MonteCarloExporter(self.results, self.context)
        exporter.export_all(str(output_folder), include_charts=include_charts)

        print(f"📦 Monte Carlo results exported to: {output_folder}")
