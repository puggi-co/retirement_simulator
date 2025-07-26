# simulation/schedule.py

from dataclasses import dataclass
from typing import Optional
from simulation.context import DictMixin

@dataclass
class SimulationSchedule:
    begin_age: int
    begin_year: int
    duration: int
    end_age: int
    end_year: int

    @classmethod
    def from_dict(cls, d: dict) -> "SimulationSchedule":
        return cls(
            begin_age=d['begin_age'],
            begin_year=d['begin_year'],
            duration=d['duration'],
            end_age=d['end_age'],
            end_year=d['end_year']
        )