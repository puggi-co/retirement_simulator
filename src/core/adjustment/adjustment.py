""" Encapsulates inflation-adjusted calculations for both forward-looking projections and real spending analysis.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class FinancialAdjustmentMixin:
    def adjust_for_inflation(self, value: float, years: int, rate: Optional[float] = None) -> float:
        """Apply compound inflation to a nominal value."""
        r = rate if rate is not None else self.config.inflation_rate
        return value * ((1 + r) ** years)

    def adjust_for_real_spend(self, value: float, years: int, rate: Optional[float] = None) -> float:
        """Convert nominal spending to real dollars, adjusted for inflation."""
        r = rate if rate is not None else self.config.inflation_rate
        return value / ((1 + r) ** years)
