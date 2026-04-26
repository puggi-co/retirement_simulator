from dataclasses import dataclass, asdict
from typing import Optional, Any
from datetime import datetime as dt
import pandas as pd

from src.config.config_schema import SimulationConfig
from src.core.strategy_catalog import StrategyDefinition

# ── Unified Simulation Context ───────────────────
@dataclass
class SimulationContext:
    # Core simulation identifiers
    sim_mode: str = 'fixed_rate'
    sim_id: str = 'mc_fixed_rate'
    sim_rate: float = 0.04
    sim_type: str = 'mc'  # 'mc' for Monte Carlo, 'wd' for Withdrawal

    # Injected components
    config: Optional[SimulationConfig] = None
    strategy_config: Optional[StrategyDefinition] = None
    return_rate: Optional[float] = None

    # Runtime state (optional)
    portfolio: Optional[pd.DataFrame] = None
    tax_table: Optional[Any] = None

    def __post_init__(self):
        if self.strategy_config and hasattr(self.strategy_config, 'strategy_id'):
            self.sim_id = self.strategy_config.strategy_id
        if self.return_rate is not None:
            self.sim_rate = self.return_rate

    def __repr__(self) -> str:
        return f"SimulationContext(sim_id='{self.sim_id}', sim_mode='{self.sim_mode}', sim_type='{self.sim_type}')"

    def __str__(self) -> str:
        return f"{self.sim_id} ({self.sim_mode}, {self.sim_type})"

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self.config, key, default) if self.config else default

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_summary_row(self, summary_df: Optional[pd.DataFrame] = None) -> dict[str, Any]:
        row = {
            'sim_id': self.sim_id,
            'sim_mode': self.sim_mode,
            'sim_type': self.sim_type,
            'timestamp': dt.now().isoformat()
        }

        if self.config:
            row.update(self.config.to_dict())

        if isinstance(summary_df, pd.DataFrame):
            for col in summary_df.columns:
                row[col] = summary_df[col].values[0]

        return dict(sorted(row.items()))

    def sample_return(self, year: int = 0) -> float:
        if self.sim_type == 'mc' and self.config:
            return self.config.sample_return(year)
        return self.sim_rate

    def get_return_rate(self, year: int = 0) -> float:
        return self.sample_return(year)
