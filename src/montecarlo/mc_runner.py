# MONTE CARLO RUNNER

import pandas as pd
from pathlib import Path
from typing import Any, Optional, List

from context.context import SimulationContext
from montecarlo.mc_engine import MonteCarloEngine
from montecarlo.mc_exporter import MonteCarloExporter
from orchestration.orch_entity import (
    MCRunResults,
    MCAnalyzeResults,
    MCMetadata,
    MCStrategyResults
)

class MonteCarloRunner:
    '''Manages the Monte Carlo simulation process'''
    DEFAULT_FAILURE_THRESHOLDS = [0, 100_000, 250_000, 500_000]

    def __init__(self, config, context: SimulationContext, tax_table: Any):
        # Unified architecture: schedule always comes from context
        self.config = config
        self.context = context
        self.schedule = context.schedule
        self.tax_table = tax_table
        self.results: Optional[MCStrategyResults] = None

    def run(self, num_simulations: int = 1000, failure_thresholds: Optional[List[int]] = None) -> MCStrategyResults:
        failure_thresholds = failure_thresholds or self.DEFAULT_FAILURE_THRESHOLDS

        print(f'🎲 Running Monte Carlo simulation [{self.context.strategy_id}]...')
        print(f'   • Simulations: {num_simulations:,}')
        print(f'   • Mode: {self.context.sim_mode}')
        print(f'   • Duration: {self.schedule.duration} years')

        # 1. Execute core simulation
        engine = MonteCarloEngine(
            context=self.context,
            tax_table=self.tax_table,
            failure_thresholds=failure_thresholds
        )

        raw_data = engine.simulate(num_simulations)
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

        # 3. Store metadata (new grouped structure)
        metadata = MCMetadata(
            simulation={
                "strategy_id": self.context.strategy_id,
                "sim_mode": self.context.sim_mode,
                "sim_type": "mc",
                "num_simulations": num_simulations,
                "duration_years": self.schedule.duration,
            },
            portfolio={
                "start_balance": float(self.context.portfolio["base_balance"].sum())
            },
            spending={
                "spending_model_type": self.context.sim_mode,
                "withdrawal_rate": getattr(self.config, "withdrawal_rate", None),
                "guardrail_amount_high": getattr(self.config, "guardrail_amount_high", None),
                "guardrail_amount_low": getattr(self.config, "guardrail_amount_low", None),
                "sim_rate": getattr(self.context, "sim_rate", None),
            },
            tax={
                # You can fill this later once you confirm your tax_table attributes
            },
            failure={
                "failure_thresholds": failure_thresholds,
                "success_rate_%": analyze_results.summary.get("success_rate_%"),
                "goal_achievement_%": analyze_results.summary.get("goal_achievement_%"),
                "rmd_trigger_rate_%": analyze_results.summary.get("rmd_trigger_rate_%"),
            },
            derived={
                "median_final_balance": analyze_results.summary.get("median_final_balance"),
                "percentile_5_final_balance": analyze_results.summary.get("percentile_5_final_balance"),
                "percentile_95_final_balance": analyze_results.summary.get("percentile_95_final_balance"),
            }
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
