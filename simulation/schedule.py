# simulation/schedule.py

from dataclasses import dataclass
from simulation.context import DictMixin  # or define locally if small

@dataclass
class SimulationSchedule(DictMixin):
    begin_age: int
    begin_year: int
    duration: int
    end_age: int
    end_year: int
