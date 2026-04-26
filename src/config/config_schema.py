import pandas as pd
import numpy as np

from datetime import datetime as dt
from dataclasses import dataclass
from typing import List, Optional, Callable
from typing import Dict

# ----- Metadata for Excel ingestion -----
TABS: List[str] = ['My_Config']

REQUIRED_COLUMNS: Dict[str, Dict[str, str]] = {
    'My_Config': {
        'parameter': 'string',
        'value': 'string'
    }
}

@dataclass
class SimulationConfig:
    # Optional input
    base_year: Optional[int] = None

    # Simulation-Specific Settings
    mc_historical_cola: float = 0.02
    mc_return_sampler: Optional[str | Callable[[int], float]] = "fixed"
    mc_seed: Optional[int] = 42
    mc_simulations: int = 1000
    mc_years: int = 30

    # Withdrawal and Monte Carlo Shared Settings
    account_closure_amount: float = 10_000
    account_closure_threshold: float = 1.25
    guardrail_rate_high: float = 0.055
    guardrail_rate_low: float = 0.035
    guardrail_amount_low: float = 0.75
    guardrail_amount_high: float = 1.25
    inflation_adjusted: bool = True
    inflation_mode: str = 'fixed'
    inflation_rate: float = 0.03
    retire_begin_age: int = 55
    retire_max_age: int = 120
    retire_max_years: int = 36
    return_high_rate: float = 0.09
    return_increment_rate: float = 0.02
    return_low_rate: float = 0.04
    spending_target: float = 100_000
    tax_gain_rate: float = 0.03
    tax_max_rate: float = 0.24
    tax_ssa_rate: float = 0.085
    withdrawal_after_growth: bool = True
    withdrawal_rate: float = 0.04

    def __post_init__(self):
        if self.base_year is None:
            self.base_year = dt.now().year

        # Normalize mc_seed to int
        if self.mc_seed is not None:
            try:
                self.mc_seed = int(self.mc_seed)
            except ValueError:
                print(f"⚠️ Invalid mc_seed value: {self.mc_seed}. Using default 42.")
                self.mc_seed = 42
        else:
            self.mc_seed = 42

    # Sampling method
    def sample_return(self, year: int = 0) -> float:
        """
        Return sampling logic based on configured strategy.
        Supports callable, fixed, random, historical, and custom_curve modes.
        """
        seed = int(self.mc_seed or 42)

        if callable(self.mc_return_sampler):
            return self.mc_return_sampler(seed + year)

        elif self.mc_return_sampler == "fixed":
            return self.withdrawal_rate  # or self.return_low_rate if preferred

        elif self.mc_return_sampler == "random":
            return np.random.default_rng(seed).normal(loc=self.withdrawal_rate, scale=0.02)

        elif self.mc_return_sampler == "historical":
            # Placeholder historical returns (e.g., S&P 500)
            historical_returns = [0.06, 0.08, -0.02, 0.12, 0.04, 0.07]
            return historical_returns[year % len(historical_returns)]

        elif self.mc_return_sampler == "custom_curve":
            curve = getattr(self, "custom_return_curve", None)
            if isinstance(curve, list) and year < len(curve):
                return curve[year]
            return self.withdrawal_rate  # fallback if curve is missing or short

        return self.withdrawal_rate  # fallback for unknown sampler
