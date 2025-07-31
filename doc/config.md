# Configuration Module Documentation

_Save this as: `docs/architecture/config-module.md`_

## Overview

The `simulation/config.py` module provides configuration dataclasses for the retirement
simulator, defining parameters that control simulation behavior across Monte Carlo and
withdrawal scenarios.

## Module Structure

### Core Configuration Classes

```python
simulation/config.py
├── MonteCarloConfig     # Market return sampling logic
├── WithdrawalConfig     # Guardrail-based withdrawal logic
└── SimulationConfig     # Unified simulation configuration
```

## Class Definitions

### MonteCarloConfig

**Purpose**: Configuration for stochastic market return generation.

**Attributes**:

- `return_sampler: Optional[Callable]` - Callable that returns a simulated market
  return.
- `seed: Optional[int]` - Base seed for reproducible randomness.

**Methods**:

- `sample(year: int = 0) -> float` - Computes a market return using the provided sampler
  and year-offset seed. Returns 0.0 when no sampler is present.

**Usage Example**:

```python
def normal_return_sampler(seed):
    np.random.seed(seed)
    return np.random.normal(0.07, 0.15)  # 7% mean, 15% volatility

mc_config = MonteCarloConfig(
    return_sampler=normal_return_sampler,
    seed=12345
)

# Generate return for year 5
year_5_return = mc_config.sample(5)  # Uses seed 12350 (12345 + 5)
```

### WithdrawalConfig

**Purpose**: Defines withdrawal behavior, constraints, and policy toggles.

**Core Parameters**:

- `assumed_gain_rate: float = 0.30` - Estimated tax rate for portfolio growth
- `withdrawal_after_growth: bool = True`
- `early_retirement_age: int = 55` - Age threshold for early retirement considerations
- `withdrawal_rate: float = 0.04` - Base withdrawal rate (4%)
- `withdrawal_amount: float = 100_000` - Target withdrawal amount (when using
  target_amount mode)

**Guardrail Parameters**:

- `guardrail_ceiling: float = 0.055` - Maximum allowed withdrawal rate (5.5%)
- `guardrail_floor: float = 0.035` - Minimum allowed withdrawal rate (3.5%)

**Operational Settings**:

- `historical_cola: float = 0.0` - Historical cost of living adjustment
- `withdrawal_mode: str = 'target_amount'` - Withdrawal calculation mode

**Methods**:

- `apply_guardrails(rate: float) -> float` - Ensures rate falls within specified
  guardrails.

**Usage Example**:

```python
config = WithdrawalConfig()
rate = config.apply_guardrails(0.06)  # Clamped to 0.055

# Ensure withdrawal rate stays within bounds
safe_rate = withdrawal_config.apply_guardrails(0.07)  # Returns 0.06
safe_rate = withdrawal_config.apply_guardrails(0.02)  # Returns 0.03
```

### SimulationConfig

**Purpose**: Aggregates simulation-wide settings, including nested Monte Carlo and
withdrawal configs.

**Nested Configurations**:

- `montecarlo: MonteCarloConfig` - Monte Carlo specific settings
- `withdrawal: WithdrawalConfig` - Withdrawal strategy settings

**Market Parameters**:

- `high_return_rate: float = 0.0` - Upper bound for return rate scenarios
- `low_return_rate: float = 0.0` - Lower bound for return rate scenarios
- `return_rate_increment: float = 0.01` - Step size between return scenarios (1%)
- `inflation_rate: float = 0.03` - Annual inflation assumption (3%)

**Financial Parameters**:

- `account_closure_amount: float = 10_000` - Minimum balance before account closure
- `max_tax_rate: float = 0.22` - Maximum tax rate assumption (22%)
- `ssa_tax_rate: float = 0.085` - Social Security tax rate (8.5%)

**Simulation Control**:

- `years: int = 36` - Simulation time horizon in years
- `adjust_for_inflation: bool = True` - Whether to inflation-adjust values
- `inflation_mode: str = 'fixed'` - Inflation calculation method

**Methods**:

- `get_return_rates() -> np.ndarray` - Creates a sweep of return rates for scenario
  analysis.
- `get_param(key: str, default=None)` - Generic attribute accessor with default fallback
- `to_dict()` -> dict – Serializes the entire config tree into a dictionary via
  asdict().

**Usage Example**:

```python
# Configure for 30-year simulation with return rates from 2% to 8%
config = SimulationConfig(
    low_return_rate=0.02,
    high_return_rate=0.08,
    return_rate_increment=0.005,  # 0.5% increments
    years=30,
    withdrawal=WithdrawalConfig(withdrawal_rate=0.035)
)

# Get all return rate scenarios to test
return_scenarios = config.get_return_rates()
# Returns: [0.02, 0.025, 0.03, 0.035, 0.04, ..., 0.08]
```

## Configuration Patterns

### Default Initialization

All classes use dataclass defaults, allowing flexible instantiation:

```python
# Use all defaults
config = SimulationConfig()

# Override specific parameters
config = SimulationConfig(
    years=25,
    inflation_rate=0.025,
    withdrawal=WithdrawalConfig(withdrawal_rate=0.035)
)
```

### Nested Configuration Access

Access nested configurations through the parent:

```python
config = SimulationConfig()

# Configure Monte Carlo
config.montecarlo.seed = 54321
config.montecarlo.return_sampler = my_custom_sampler

# Configure withdrawal strategy
config.withdrawal.guardrail_ceiling = 0.06
safe_rate = config.withdrawal.apply_guardrails(0.08)
```

### Dynamic Return Rate Generation

The `get_return_rates()` method enables systematic scenario testing:

```python
config = SimulationConfig(
    low_return_rate=0.01,
    high_return_rate=0.10,
    return_rate_increment=0.01
)

for return_rate in config.get_return_rates():
    # Run simulation with this return rate
    result = run_simulation(config, return_rate)
```

## Integration Points

### Monte Carlo Simulations

```python
# Configure for 10,000 Monte Carlo iterations
config = SimulationConfig(
    montecarlo=MonteCarloConfig(
        return_sampler=lambda seed: np.random.normal(0.07, 0.12),
        seed=42
    )
)
```

### Withdrawal Strategy Testing

```python
# Test conservative vs aggressive withdrawal strategies
conservative_config = SimulationConfig(
    withdrawal=WithdrawalConfig(
        withdrawal_rate=0.035,
        guardrail_ceiling=0.045,
        guardrail_floor=0.025
    )
)

aggressive_config = SimulationConfig(
    withdrawal=WithdrawalConfig(
        withdrawal_rate=0.05,
        guardrail_ceiling=0.07,
        guardrail_floor=0.035
    )
)
```

## Design Principles

### Separation of Concerns

- **MonteCarloConfig**: Handles randomness and sampling
- **WithdrawalConfig**: Manages withdrawal logic and constraints
- **SimulationConfig**: Coordinates overall simulation parameters

### Extensibility

- Optional callables allow custom return sampling strategies
- Generic `get()` method supports dynamic parameter access
- Dataclass structure enables easy parameter addition

### Validation Through Methods

- `apply_guardrails()` ensures withdrawal rates stay within bounds
- `sample()` handles edge cases (missing sampler)
- `get_return_rates()` generates valid scenario ranges

## Usage in Simulation Workflows

### Basic Simulation Setup

```python
from simulation.config import SimulationConfig

# Create configuration
config = SimulationConfig(
    years=40,
    withdrawal=WithdrawalConfig(withdrawal_rate=0.045),
    montecarlo=MonteCarloConfig(seed=42)
)

# Run simulation using configuration
portfolio = initialize_portfolio()
for year in range(config.years):
    # Apply withdrawal with guardrails
    withdrawal_rate = config.withdrawal.apply_guardrails(
        calculate_dynamic_rate(portfolio)
    )

    # Market return sampling
    r = config.montecarlo.sample(year=12)

    # Guardrail logic
    rate = config.withdrawal.apply_guardrails(0.07)

    # Update portfolio
    portfolio = update_portfolio(portfolio, withdrawal_rate, market_return)
```

# Scenario Sweep

for rate in config.get_return_rates(): result = run_simulation(config, rate)

This configuration design provides a clean, focused interface for controlling simulation
behavior while maintaining clear separation between different types of parameters.
