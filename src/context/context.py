from dataclasses import dataclass, asdict
from typing import Optional, Any
from datetime import datetime as dt
import pandas as pd

from config.config_schema import SimulationConfig
from config.catalog import CatalogEntry
from core.schedule import SimulationSchedule

# ── Unified Simulation Context ───────────────────
@dataclass
class SimulationContext:
    strategy_id: str = None     # from catalog_config
    sim_mode: str = None        # from catalog_config
    sim_type: str = 'wd'        # 'wd' or 'mc' (set by orchestrator)
    sim_rate: float = 0.04

    config: Optional[SimulationConfig] = None
    catalog_config: Optional[CatalogEntry] = None
    return_rate: Optional[float] = None
    schedule: Optional[SimulationSchedule] = None

    portfolio: Optional[pd.DataFrame] = None
    tax_engine: Optional[Any] = None
    tax_table: Optional[Any] = None

    def __post_init__(self):
        if self.catalog_config:
            self.strategy_id = self.catalog_config.strategy_id
            self.sim_mode = self.catalog_config.sim_mode

        # WD uses deterministic return_rate, MC ignores deterministic return_rate
        if self.sim_type == 'wd' and self.return_rate is not None:
            self.sim_rate = self.return_rate

    def __repr__(self) -> str:
        return f"SimulationContext(strategy_id='{self.strategy_id}', sim_mode='{self.sim_mode}', sim_type='{self.sim_type}')"

    def __str__(self) -> str:
        return f"{self.strategy_id} ({self.sim_mode}, {self.sim_type})"

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self.config, key, default) if self.config else default

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_summary_row(self, summary_df: Optional[pd.DataFrame] = None) -> dict[str, Any]:
        row = {
            'strategy_id': self.strategy_id,
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

    def sample_return(self, year: int = 0, sim_num: int = 0) -> float:
        if self.sim_type == 'mc' and self.config:
            return self.config.sample_return(year=year, sim_num=sim_num)
        return self.sim_rate

    def get_return_rate(self, year: int = 0, sim_num: int = 0) -> float:
        return self.sample_return(year=year, sim_num=sim_num)
