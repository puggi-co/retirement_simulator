# Monte Carlo Engine and Orchestrator

import pandas as pd
import numpy as np

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Core imports
from config.config_schema import SimulationConfig
from context.context import SimulationContext
from config.catalog import CatalogEntry, CATALOG
from core.schedule import SimulationSchedule
from core.tax_engine import TaxEngine

# Input/Output imports 
#from storage.tax_loader import get_tax_table

# Orchestrator imports
from orchestration.orch_entity import BatchResults

# Display settings
#from storage.export_util import debug_view
pd.options.display.float_format = '{:,.2f}'.format

# =================== DATA CLASSES ===================

class RetirementSimulationOrchestrator:
    """
    Main orchestrator for retirement simulations - coordinates the entire process
    """
    
    def __init__(self, config_path: Path = None, data_folder: Path = None):
        """
        Initialize the orchestrator with configuration and data paths
        """
        # Assumes this file is in project_root/src/orchestration/retirement_orchestrator.py
        # Going up 3 levels brings us perfectly to project_root/
        self.project_root = Path(__file__).resolve().parent.parent.parent
        
        # Fallback to the pristine new layout we designed earlier
        self.data_folder = data_folder or self.project_root / "data"
        self.config_path = config_path or self.data_folder / "user" / "config.xlsx"
        
        # Initialize core components
        self.config: Optional[SimulationConfig] = None
        self.tax_table = None
        self.portfolio_df: Optional[pd.DataFrame] = None
        self.schedule: Optional[SimulationSchedule] = None
        
        # Results tracking
        self.batch_results: Optional[BatchResults] = None
        
        # Setup run metadata
        self.run_timestamp = datetime.now()
        self.run_folder = self.data_folder / "export" / self.run_timestamp.strftime('%Y_%m_%d_%H%M%S')
        
    def export_comprehensive_analysis(self, output_path: Optional[Path] = None) -> None:
        """Export comprehensive cross-strategy analysis"""
        
        if not self.batch_results:
            print("No batch results available. Run simulations first.")
            return
        
        # 🎯 Passes the path straight down to the operations
        output_path = output_path or self.run_folder / "comprehensive_analysis.xlsx"
        
        print(f"📊 Generating comprehensive analysis...")
        
        # Ensure the subfolder exists dynamically
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            self._export_batch_overview(writer)
            self._export_simulation_comparison(writer)
            self._export_monte_carlo_comparison(writer)
            self._export_risk_analysis(writer)
        
        print(f"📈 Comprehensive analysis exported: {output_path}")
    
    # =================== PRIVATE METHODS ===================

    def _get_strategies_to_run(self, selected_strategies: List[str] = None) -> List[str]:
        """Get list of strategies to run"""
        if selected_strategies:
            # Validate selected strategies
            invalid = set(selected_strategies) - set(CATALOG.keys())
            if invalid:
                raise ValueError(f"Invalid strategies: {invalid}")
            return selected_strategies
        else:
            return list(CATALOG.keys())
    
    def _get_return_rates(self) -> np.ndarray:
        """Get array of return rates to simulate."""

        low = self.config.return_low_rate
        high = self.config.return_high_rate
        step = self.config.return_increment_rate

        # Case 1 — single deterministic return rate
        if step == 0 or low == high:
            return np.array([low], dtype=float)

        # Case 2 — normal sweep
        return np.arange(
            low,
            high + step,
            step
        )

    def _create_simulation_contexts(self, catalog_config: CatalogEntry, return_rate: float):

        schedule = SimulationSchedule.from_account_data(self.portfolio_df, self.config)

        wd_context = SimulationContext(
            config=self.config,
            catalog_config=catalog_config,
            return_rate=return_rate,
            sim_type='wd'
        )

        avg_rate = (self.config.return_low_rate + self.config.return_high_rate) / 2
        mc_context = SimulationContext(
            config=self.config,
            catalog_config=catalog_config,
            return_rate=avg_rate,
            sim_type='mc'
        )

        # Shared runtime state
        wd_context.schedule = schedule
        mc_context.schedule = schedule

        wd_context.portfolio = self.portfolio_df
        mc_context.portfolio = self.portfolio_df

        wd_context.tax_table = self.tax_table
        mc_context.tax_table = self.tax_table

        wd_context.tax_engine = TaxEngine(self.tax_table, self.config)
        mc_context.tax_engine = TaxEngine(self.tax_table, self.config)

        return wd_context, mc_context, schedule

    def _create_run_metadata(self) -> Dict[str, Any]:
        """Create metadata about the simulation run"""
        if self.batch_results and self.batch_results.runs:
            strategies_run = len(set(run.strategy_id for run in self.batch_results.runs))
        else:
            strategies_run = 0

        return {
            'timestamp': self.run_timestamp.isoformat(),
            'config_file': str(self.config_path),
            'portfolio_accounts': len(self.portfolio_df),
            'portfolio_value': float(self.portfolio_df['base_balance'].sum()),
            'simulation_years': self.schedule.duration,
            'base_age': self.schedule.base_age,
            'strategies_run': strategies_run,
            'return_rate_range': f"{self.config.return_low_rate:.1%} to {self.config.return_high_rate:.1%}",
            'python_version': f"{pd.__version__} (pandas)"  # Basic version info
        }
    
    def _print_batch_summary(self) -> None:
        """Print summary of batch execution"""
        
        if not self.batch_results:
            return
        
        results = self.batch_results
        
        print(f"\n🎉 Batch Execution Complete")
        print("=" * 60)
        print(f"Total runs: {len(results.runs)}")
        print(f"Successful: {results.successful_runs}")
        print(f"Failed: {results.failed_runs}")
        print(f"Success rate: {(results.successful_runs/len(results.runs)*100):.1f}%")
        print(f"Total time: {results.total_execution_time:.1f} seconds")
        print(f"Average per run: {results.total_execution_time/len(results.runs):.1f} seconds")
        
        # Failed runs details
        if results.failed_runs > 0:
            print(f"\n❌ Failed Runs:")
            for run in results.runs:
                if not run.success:
                    print(f"   • {run.strategy_id} @ {run.return_rate:.1%}: {run.error_message}")

    def _export_batch_summary(self) -> None:
        """Export batch summary to Excel"""
        
        if not self.batch_results:
            return
        
        summary_path = self.run_folder / "batch_summary.xlsx"
        
        # Create summary DataFrame
        summary_data = []
        for run in self.batch_results.runs:
            summary_data.append({
                'strategy_id': run.strategy_id,
                'return_rate': run.return_rate,
                'success': run.success,
                'execution_time_s': run.execution_time,
                'error_message': run.error_message or '',
                'output_folder': str(run.run_folder.relative_to(self.run_folder))
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # Export to Excel
        with pd.ExcelWriter(summary_path, engine='xlsxwriter') as writer:
            summary_df.to_excel(writer, sheet_name='Run_Summary', index=False)
            
            # Metadata
            metadata_df = pd.DataFrame(
                list(self.batch_results.run_metadata.items()),
                columns=['Parameter', 'Value']
            )
            metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
        
        print(f"📊 Batch summary exported: {summary_path}")
    
    def _export_batch_overview(self, writer: pd.ExcelWriter) -> None:
        """Export batch overview to Excel writer"""
        
        # Summary statistics across all runs
        summary_data = []
        for run in self.batch_results.runs:
            if run.success and run.mc_results:
                # Extract key metrics from Monte Carlo results
                # This would need to be adapted based on your MC results structure
                summary_data.append({
                    'strategy': run.strategy_id,
                    'return_rate': run.return_rate,
                    'success_rate': run.mc_results.get_metric('success_rate_%'),
                    'median_final_balance': run.mc_results.get_metric('median_final_balance', 0),
                    'failure_rate_0': run.mc_results.get_metric('failure_rate_0', 0)
                })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            df.to_excel(writer, sheet_name='Batch_Overview', index=False)
    
    def _export_simulation_comparison(self, writer: pd.ExcelWriter) -> None:
        """Export simulation comparison to Excel writer"""
        # Implementation would depend on specific comparison metrics needed
        pass
    
    def _export_monte_carlo_comparison(self, writer: pd.ExcelWriter) -> None:
        """Export Monte Carlo comparison across simulations"""
        # Implementation would aggregate MC results across simulations
        pass
    
    def _export_risk_analysis(self, writer: pd.ExcelWriter) -> None:
        """Export risk analysis across simulations and return rates"""
        # Implementation would analyze risk metrics across all runs
        pass

from orchestration.orch_initialize import (
    initialize, _load_configuration, _load_tax_data,
    _load_portfolio_data, _create_simulation_schedule,
    _validate_initialization
)

RetirementSimulationOrchestrator.initialize = initialize
RetirementSimulationOrchestrator._load_configuration = _load_configuration
RetirementSimulationOrchestrator._load_tax_data = _load_tax_data
RetirementSimulationOrchestrator._load_portfolio_data = _load_portfolio_data
RetirementSimulationOrchestrator._create_simulation_schedule = _create_simulation_schedule
RetirementSimulationOrchestrator._validate_initialization = _validate_initialization

from orchestration.orch_strategy import (
    run_all_strategies, run_single_strategy, _run_strategy_suite
)

RetirementSimulationOrchestrator.run_all_strategies = run_all_strategies
RetirementSimulationOrchestrator.run_single_strategy = run_single_strategy
RetirementSimulationOrchestrator._run_strategy_suite = _run_strategy_suite

# =================== MAIN ORCHESTRATION FUNCTION ===================

def main():
    """
    Main orchestration function - simplified and cleaner
    """
    
    # Initialize orchestrator
    orchestrator = RetirementSimulationOrchestrator()
    orchestrator.initialize()

    # Run all strategies (or specify selected ones)
    batch_results = orchestrator.run_all_strategies(
        selected_strategies=['deferred_first', 'taxable_first', 'fixed_rate_tax_efficient']
    )

    # Generate comprehensive analysis
    orchestrator.export_comprehensive_analysis()
    
    print(f"\n🎯 All simulations complete!")
    print(f"📁 Results available in: {orchestrator.run_folder}")
    
    return batch_results

# =================== UTILITY FUNCTIONS ===================

def run_quick_test(strategy_id: str = 'fixed_rate', return_rate: float = 0.06):
    """
    Quick test function for development/debugging
    """
    
    orchestrator = RetirementSimulationOrchestrator()
    orchestrator.initialize()

    result = orchestrator.run_single_strategy(
        strategy_id=strategy_id,
        return_rate=return_rate,
        mc_simulations=100  # Smaller for testing
    )
    
    print(f"Test complete: {result.success}")
    return result


if __name__ == "__main__":
    main()
