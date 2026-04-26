from dataclasses import dataclass
from datetime import date
from typing import Optional
from src.config.config_schema import SimulationConfig

@dataclass
class SimulationSchedule:
    base_age: int
    base_year: int
    duration: int
    end_age: int
    end_year: int

    def year(self, year_index: int) -> int:
        """Returns the calendar year corresponding to a simulation index."""
        return self.base_year + year_index

    def age(self, year_index: int) -> int:
        """Returns the retiree's age for a given simulation index."""
        return self.base_age + year_index

    def is_rmd_year(self, year_index: int, rmd_age: int = 73) -> bool:
        return self.age(year_index) >= rmd_age

    def ssa_start_year(self, ssa_age: int = 67) -> Optional[int]:
        if ssa_age < self.base_age or ssa_age > self.end_age:
            return None
        return self.base_year + (ssa_age - self.base_age)
    
    def to_dict(self) -> dict:
        """Returns a dictionary representation of the schedule."""
        return {
            "base_age": self.base_age,
            "base_year": self.base_year,
            "duration": self.duration,
            "end_age": self.end_age,
            "end_year": self.end_year
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SimulationSchedule":
        """Initialize SimulationSchedule from a dictionary."""
        return cls(**d)

    @classmethod
    def from_account_data(cls, df_my_account, config: SimulationConfig) -> "SimulationSchedule":
        """Factory method to build SimulationSchedule from portfolio and config."""
        base_year = int(config.base_year)
        base_age = int(df_my_account['owner_age'].min())
        duration = int(config.retire_max_age - base_age)
        end_year = base_year + duration - 1
        end_age = base_age + duration

        return cls(
            base_age=base_age,
            base_year=base_year,
            duration=duration,
            end_age=end_age,
            end_year=end_year
        )

# ── Utility ──────────────────────────────────────────────────────

def calculate_age(birth_date_or_year, reference_year):
    """
    Calculate age given a birth year or date and a reference year.
    """
    if isinstance(birth_date_or_year, date):
        birth_year = birth_date_or_year.year
    elif isinstance(birth_date_or_year, int):
        birth_year = birth_date_or_year
    else:
        raise TypeError("birth_date_or_year must be a datetime.date or int")

    return reference_year - birth_year
