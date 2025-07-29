# simulation/config.py

from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
import numpy as np

@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo market simulations."""
    return_sampler: Optional[Callable] = None
    seed: Optional[int] = None

    def sample(self, year: int = 0) -> float:
        """Return a simulated market return for a given year."""
        if callable(self.return_sampler):
            seed_offset = self.seed or 42
            return self.return_sampler(seed_offset + year)
        return 0.0

@dataclass
class WithdrawalConfig:
    """Parameters specific to withdrawal strategy behavior."""
    withdrawal_mode: str = 'target_amount'
    withdrawal_rate: float = 0.04
    guardrail_ceiling: float = 0.055
    guardrail_floor: float = 0.035
    assumed_gain_rate: float = 0.30
    withdrawal_after_growth: bool = True
    early_retirement_age: int = 55
    historical_cola: float = 0.0

    def apply_guardrails(self, rate: float) -> float:
        """Clamp the withdrawal rate within guardrail limits."""
        return max(self.guardrail_floor, min(rate, self.guardrail_ceiling))
    
    def goal_for_year(self, ydx: int, rate: Optional[float] = None) -> float:
        """Returns the inflation-adjusted and guardrail-bounded withdrawal goal 
        for a given simulation year."""
        r = rate if rate is not None else self.assumed_inflation_rate
        inflated = self.withdrawal_amount * ((1 + r) ** ydx)
        return self.apply_guardrails(inflated)


@dataclass
class SimulationConfig:
    """Global configuration for retirement simulation scenarios."""
    montecarlo: MonteCarloConfig = field(default_factory=MonteCarloConfig)
    withdrawal: WithdrawalConfig = field(default_factory=WithdrawalConfig)

    # Core simulation parameters
    years: int = 36
    withdrawal_amount: float = 100_000
    inflation_rate: float = 0.03
    max_tax_rate: float = 0.22
    adjust_for_inflation: bool = True
    inflation_mode: str = 'fixed'
    account_closure_amount: float = 10_000
    ssa_tax_rate: float = 0.085

    # Market return sweep for sensitivity analysis
    high_return_rate: float = 0.0
    low_return_rate: float = 0.0
    return_rate_increment: float = 0.01

    def get_return_rates(self) -> np.ndarray:
        """Generate an array of return rates for analysis."""
        return np.arange(
            self.low_return_rate,
            self.high_return_rate + self.return_rate_increment,
            self.return_rate_increment
        )

    def get_param(self, key: str, default=None):
        """Safely access a top-level configuration parameter."""
        return getattr(self, key, default)

    def to_dict(self) -> dict:
        """Return a dictionary representation of the config."""
        return asdict(self)