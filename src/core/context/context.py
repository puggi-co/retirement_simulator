# simulation/context.py

from dataclasses import dataclass, field
from typing import Optional
import datetime
import pandas as pd
from simulation.config import SimulationConfig
from simulation.schedule import SimulationSchedule
from simulation.tax_tables import TaxTables  # If this is defined elsewhere

class DictMixin:
    def as_dict(self):
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }

    def to_summary_row(self, extra: Optional[dict] = None):
        row = self.as_dict()
        if extra:
            row.update(extra)
        row['timestamp'] = datetime.datetime.now().isoformat()
        return dict(sorted(row.items()))

@dataclass
class SimulationContext(DictMixin):
    scenario_id: str = 'unknown'
    withdrawal_mode: str = 'unknown'
    config: Optional[SimulationConfig] = None
    schedule: SimulationSchedule = field(default_factory=SimulationSchedule)

    def __repr__(self):
        return f"SimulationContext(scenario_id='{self.scenario_id}', withdrawal_mode='{self.withdrawal_mode}')"

    def __str__(self):
        return f"{self.scenario_id} ({self.withdrawal_mode})"

    def get(self, key: str, default=None):
        if self.config:
            return getattr(self.config, key, default)
        return default

    @property
    def is_montecarlo(self) -> bool:
        return self.scenario_id.startswith('mc_')

    def get_tax_tables(self, workbook) -> TaxTables:
        return TaxTables(
            deduction=workbook.get('standard_deduction'),
            bracket=workbook.get('tax_bracket'),
            lef=workbook.get('lef')
        )

    def to_summary_row(self, summary_df=None):
        row = {
            'scenario_id': self.scenario_id,
            'withdrawal_mode': self.withdrawal_mode,
            'inflation_rate': self.get('inflation_rate'),
            'max_tax_rate': self.get('max_tax_rate'),
            'config_years': self.get('years'),
            'guardrail_floor': self.get('guardrail_floor'),
            'guardrail_ceiling': self.get('guardrail_ceiling'),
            'seed': self.get('seed'),
            'montecarlo': self.is_montecarlo,
            'timestamp': datetime.datetime.now().isoformat()
        }

        if isinstance(summary_df, pd.DataFrame):
            for col in summary_df.columns:
                row[col] = summary_df[col].values[0]

        return dict(sorted(row.items()))

@dataclass
class FinancialAdjustmentMixin:
    def adjust_for_inflation(self, value: float, years: int) -> float:
        return value * ((1 + self.config.inflation_rate) ** years)

    def adjust_for_real_spend(self, value: float, years: int) -> float:
        return value / ((1 + self.config.inflation_rate) ** years)

from simulation.ledger_writer import LedgerWriterMixin
@dataclass
class WithdrawalContext(SimulationContext, FinancialAdjustmentMixin, LedgerWriterMixin):

    def apply_guardrails(self, rate: float) -> float:
        return self.config.withdrawal.apply_guardrails(rate)

    def use_inflation(self) -> bool:
        return self.config.adjust_for_inflation

    def compute_real_spend(self, net_spend: float, ydx: int) -> float:
        return self.adjust_for_real_spend(net_spend, ydx)

@dataclass
class MonteCarloContext(SimulationContext):
    def sample_return(self, year: int = 0) -> float:
        return self.config.montecarlo.sample(year)