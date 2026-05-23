# =================== ORCHESTRATION DATA CLASSES ===================

import pandas as pd
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.catalog import CatalogEntry
from context.context import SimulationContext
from montecarlo.mc_outcome import MCOutcome
from withdrawal.wd_ledger import WithdrawalLedger
from withdrawal.wd_outcome import WDOutcome


# ── MONTE CARLO ORCHESTRATION TYPES ────────────────────────────────

@dataclass
class MCMetadata:
    """
    Logically grouped metadata for a Monte Carlo simulation run.
    All fields are JSON-serializable; no DataFrames here.
    """
    # --- Simulation identity & configuration ---
    simulation: Dict[str, Any] = field(default_factory=dict)
    # --- Portfolio & return model parameters ---
    portfolio: Dict[str, Any] = field(default_factory=dict)
    # --- Spending model & withdrawal policy ---
    spending: Dict[str, Any] = field(default_factory=dict)
    # --- Tax model parameters ---
    tax: Dict[str, Any] = field(default_factory=dict)
    # --- Failure thresholds & success metrics ---
    failure: Dict[str, Any] = field(default_factory=dict)
    # --- Derived statistics (computed after simulation) ---
    derived: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCRunResults:
    """Raw trial-level output from Monte Carlo simulation."""
    raw_data: MCOutcome


@dataclass
class MCAnalyzeResults:
    """Aggregated metrics from Monte Carlo simulation analysis."""
    summary: pd.DataFrame
    failures: pd.DataFrame
    median: pd.DataFrame
    percentiles: Optional[pd.DataFrame] = None
    extra: Optional[Dict[str, pd.DataFrame]] = None


# ── WITHDRAWAL ORCHESTRATION TYPES ────────────────────────────────

@dataclass
class WDMetadata:
    """Structured metadata for a withdrawal simulation."""
    duration: int
    strategy_id: str
    sim_mode: str
    success: bool
    return_rate: Optional[float] = None


@dataclass
class WDRunResults:
    """Container for withdrawal simulation raw data."""
    dashboard_df: pd.DataFrame
    annotations: pd.DataFrame
    total_withdrawn: float
    wd_outcome: WDOutcome
    wd_ledger: Optional[WithdrawalLedger] = None  # Optional: include the raw withdrawal ledger


@dataclass
class WDAnalyzeResults:
    """Container for withdrawal simulation analysis results."""
    goal_success: pd.DataFrame
    rmd_trigger_ages: pd.DataFrame
    withdrawal_efficiency: pd.DataFrame
    depletion_flags: pd.DataFrame


# ── BASE STRATEGY RESULT TYPE ─────────────────────────────────────

@dataclass
class BaseStrategyResults:
    """
    Base container for strategy results (MC or WD).
    Concrete subclasses must implement get_outcome_df() and final_balance().
    """
    run: Any
    analysis: Any
    metadata: Any

    def get_outcome_df(self) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement get_outcome_df().")

    def final_balance(self) -> float:
        raise NotImplementedError("Subclasses must implement final_balance().")

    def to_dict(self) -> Dict[str, Any]:
        """
        Lightweight, export-friendly representation.
        Note: run/analysis may still contain DataFrames.
        """
        return {
            "run": self.run,
            "analysis": self.analysis,
            "metadata": self.metadata,
        }


# ── CONCRETE STRATEGY RESULT TYPES ────────────────────────────────

@dataclass
class MCStrategyResults(BaseStrategyResults):
    """Container for Monte Carlo simulation results and metadata."""
    run: MCRunResults
    analysis: MCAnalyzeResults
    metadata: MCMetadata
    # Unified success flag at strategy level (can be set by orchestrator)
    success: bool = False

    def get_outcome_df(self) -> pd.DataFrame:
        return self.run.raw_data.frame.df

    def get_metric(self, key: str, default: float = 0.0) -> float:
        if self.analysis and self.analysis.extra and key in self.analysis.extra:
            return self.analysis.extra.get(key, default)
        return default

    def final_balance(self) -> float:
        """
        Median final-year end_balance across all Monte Carlo trials.
        """
        df = self.get_outcome_df()
        if df.empty:
            return 0.0
        last_idx = df["year_index"].max()
        return float(df.loc[df["year_index"] == last_idx, "end_balance"].median())


@dataclass
class WDStrategyResults(BaseStrategyResults):
    """Container for withdrawal simulation results and metadata."""
    run: WDRunResults
    analysis: WDAnalyzeResults
    metadata: WDMetadata

    def get_outcome_df(self) -> pd.DataFrame:
        # For WD, the dashboard_df is the primary outcome view.
        return self.run.dashboard_df

    def final_balance(self) -> float:
        """
        Final end_balance from the deterministic withdrawal dashboard.
        """
        df = self.run.dashboard_df
        if df.empty:
            return 0.0
        return float(df["end_balance"].iloc[-1])


# ── ORCHESTRATION RUN / BATCH TYPES ───────────────────────────────

@dataclass
class SimulationRun:
    """Container for a single simulation run configuration and results."""
    strategy_id: str
    catalog_config: CatalogEntry
    # Deterministic return rate (for WD). MC runs may leave this as None.
    return_rate: Optional[float] = None
    run_folder: Path = None
    context: SimulationContext = None
    wd_results: Optional[WDStrategyResults] = None
    mc_results: Optional[MCStrategyResults] = None
    execution_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class BatchResults:
    """Container for batch simulation results."""
    runs: List[SimulationRun]
    total_execution_time: float
    successful_runs: int
    failed_runs: int
    run_metadata: Dict[str, Any]
