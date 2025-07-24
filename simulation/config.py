# simulation/config.py

from dataclasses import dataclass
from typing import Optional, Callable
import numpy as np

@dataclass
class MonteCarloConfig:
    """Metadata specific to MonteCarlo Scenarios"""
    return_sampler: Optional[Callable] = None
    seed: Optional[int] = None

    def sample(self, year: int = 0) -> float:
        if callable(self.return_sampler):
            seed_offset = self.seed or 42
            return self.return_sampler(seed_offset + year)
        return 0.0

@dataclass
class WithdrawalConfig:
    """Metadata specific to Withdrawal Scenarios"""
    assumed_gain_rate: float = 0.30
    withdrawal_after_growth: bool = True
    early_retirement_age: int = 55
    guardrail_ceiling: float = 0.055
    guardrail_floor: float = 0.035
    historical_cola: float = 0.0
    withdrawal_mode: str = 'target_amount'
    withdrawal_rate: float = 0.04

    def apply_guardrails(self, rate: float) -> float:
        return max(self.guardrail_floor, min(rate, self.guardrail_ceiling))

@dataclass
class SimulationConfig:
    """Metadata shared by MonteCarlo and Withdrawal Scenarios"""
    montecarlo: MonteCarloConfig = MonteCarloConfig()
    withdrawal: WithdrawalConfig = WithdrawalConfig()

    high_return_rate: float = 0.0
    low_return_rate: float = 0.0
    return_rate_increment: float = 0.01
    account_closure_amount: float = 10_000
    inflation_rate: float = 0.03
    max_tax_rate: float = 0.22
    withdrawal_amount: float = 100_000
    adjust_for_inflation: bool = True
    ssa_tax_rate: float = 0.085
    inflation_mode: str = 'fixed'
    years: int = 36

    def get_return_rates(self):
        return np.arange(
            self.low_return_rate,
            self.high_return_rate + self.return_rate_increment,
            self.return_rate_increment
        )

    def get(self, key: str, default=None):
        return getattr(self, key, default)