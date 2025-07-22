from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class SimulationConfig:
    withdrawal_mode: str = "fixed"
    withdrawal_rate: float = 0.04
    withdrawal_target: float = 125_000
    inflation_rate: float = 0.03
    tax_rate: float = 0.22
    years: int = 30
    early_retirement_age: int = 55
    guardrail_floor: float = 0.90
    guardrail_ceiling: float = 1.10
    seed: Optional[int] = None
    return_sampler: Optional[Callable[[int], list]] = None 
