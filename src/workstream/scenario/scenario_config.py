from dataclasses import dataclass

@dataclass
class ScenarioConfig:
    scenario_id: str
    scenario_name: str
    withdrawal_mode: str
    montecarlo_id: str
    include_dashboard: bool
    tax_deferred_notes: str
    taxable_notes: str
    tax_free_notes: str
    pros: str
    cons: str
    tips: str = ''
    key_concepts: str = ''  # Optional extras
