# =================== ORCHESTRATION DATA CLASSES ===================

import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.strategy_catalog import StrategyDefinition
from src.context.context import SimulationContext
from src.orchestration.outcome_ledger import MCOutcomeLedger, WDOutcomeLedger
from src.withdrawal.wd_ledger import WithdrawalLedger

@dataclass
class MCMetadata:
    """Structured metadata for a simulation result"""
    num_simulations: int
    failure_thresholds: List[int]
    duration: int
    sim_mode: str
    sim_id: Optional[str] = None
    return_rate: Optional[float] = None
    success: Optional[bool] = None

@dataclass
class MCRunResults:
    """Raw trial-level output from Monte Carlo simulation"""
    raw_data: MCOutcomeLedger

@dataclass
class MCAnalyzeResults:
    """Aggregated metrics from Monte Carlo simulation analysis"""
    summary: pd.DataFrame
    failures: pd.DataFrame
    median: pd.DataFrame
    percentiles: Optional[pd.DataFrame] = None
    extra: Optional[Dict[str, pd.DataFrame]] = None

@dataclass
class MCStrategyResults:
    """Container for Monte Carlo simulation results and metadata"""
    run: MCRunResults
    analysis: MCAnalyzeResults
    metadata: MCMetadata

    def get_outcome_df(self) -> pd.DataFrame:
        return self.run.raw_data.frame.df
    
    def get_metric(self, key: str, default: float = 0.0) -> float:
        return self.analysis.extra.get(key, default) if self.analysis and self.analysis.extra else default
    
@dataclass
class WDMetadata:
    """Structured metadata for a withdrawal simulation"""
    duration: int
    sim_mode: str
    sim_id: str
    return_rate: float
    success: bool

@dataclass
class WDRunResults:
    """Container for withdrawal simulation raw data"""
    dashboard_df: pd.DataFrame
    annotations: pd.DataFrame
    total_withdrawn: float
    outcome_ledger: WDOutcomeLedger
    wd_ledger: WithdrawalLedger = None  # Optional: include the raw withdrawal ledger

@dataclass
class WDAnalyzeResults:
    """Container for withdrawal simulation analysis results"""
    goal_success: pd.DataFrame
    rmd_trigger_ages: pd.DataFrame
    withdrawal_efficiency: pd.DataFrame
    depletion_flags: pd.DataFrame

@dataclass
class WDStrategyResults:
    """Container for withdrawal simulation results and metadata"""
    run: WDRunResults
    analysis: WDAnalyzeResults
    metadata: WDMetadata

@dataclass
class SimulationRun:
    """Container for a single simulation run configuration and results"""
    strategy_id: str
    strategy_config: StrategyDefinition
    return_rate: float
    run_folder: Path
    context: SimulationContext
    wd_results: Optional[WDStrategyResults] = None
    mc_results: Optional[MCStrategyResults] = None
    execution_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None

@dataclass
class BatchResults:
    """Container for batch simulation results"""
    runs: List[SimulationRun]
    total_execution_time: float
    successful_runs: int
    failed_runs: int
    run_metadata: Dict[str, Any]
