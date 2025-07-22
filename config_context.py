# Configuration and Context Classes
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
class SimulationConfig(DictMixin):
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
        """Safely retrieve config parameter with fallback."""
        return getattr(self, key, default)

    def as_dict(self):
        return {field.name: getattr(self, field.name) for field in self.__dataclass_fields__.values()}
    
@dataclass
class SimulationContext(DictMixin):
    """Carries scenario-level metadata across the simulation workflow."""
    
    scenario_id: str = 'unknown'
    withdrawal_mode: str = 'unknown'
    config: Optional[SimulationConfig] = None
    schedule: SimulationSchedule = field(default_factory=SimulationSchedule)

    def __repr__(self) -> str:
        return f"SimulationContext(scenario_id='{self.scenario_id}', withdrawal_mode='{self.withdrawal_mode}')"

    def __str__(self) -> str:
        return f"{self.scenario_id} ({self.withdrawal_mode})"

    def get(self, key: str, default=None):
        """Safely retrieve a config parameter with fallback."""
        if self.config:
            return getattr(self.config, key, default)
        return default

    @property
    def is_montecarlo(self) -> bool:
        return self.scenario_id.startswith('mc_')

    def get_tax_tables(self, workbook) -> TaxTables:
        """Returns structured tax tables extracted from workbook."""
        return TaxTables(
            deduction=workbook.get('standard_deduction'),
            bracket=workbook.get('tax_bracket'),
            lef=workbook.get('lef')
        )

    def to_summary_row(self, summary_df=None):
        """Returns a flat dict of scenario metadata and optional summary stats."""
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
class WithdrawalContext(SimulationContext, FinancialAdjustmentMixin):
    def apply_guardrails(self, rate: float) -> float:
        return self.config.withdrawal.apply_guardrails(rate)

    def use_inflation(self) -> bool:
        return self.config.adjust_for_inflation

    def compute_real_spend(self, net_spend: float, ydx: int) -> float:
        return self.adjust_for_real_spend(net_spend, ydx)

@dataclass
class FinancialAdjustmentMixin:
    def adjust_for_inflation(self, value: float, years: int) -> float:
        return value * ((1 + self.config.inflation_rate) ** years)

    def adjust_for_real_spend(self, value: float, years: int) -> float:
        return value / ((1 + self.config.inflation_rate) ** years)

@dataclass
class MonteCarloContext(SimulationContext):
    def sample_return(self, year: int = 0) -> float:
        return self.config.montecarlo.sample(year)

@dataclass
class SimulationSchedule(DictMixin):
    begin_age: int
    begin_year: int
    duration: int
    end_age: int
    end_year: int

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
