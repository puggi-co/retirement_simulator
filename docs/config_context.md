# Configuration and Context Classes

**File: `config_context.py`**

This module contains the core configuration and context classes that define simulation parameters and carry state throughout the retirement simulation workflow.

## Module Dependencies

```python
from adjustments import FinancialAdjustmentMixin
```

## Class Hierarchy

```
DictMixin (base utility)
├── SimulationConfig
├── SimulationSchedule  
└── SimulationContext
    ├── WithdrawalContext (+ FinancialAdjustmentMixin from adjustments.py)
    └── MonteCarloContext

Standalone:
├── MonteCarloConfig
└── WithdrawalConfig

External (adjustments.py):
└── FinancialAdjustmentMixin
```

## Core Configuration Classes

### SimulationConfig
**Main configuration container for all simulation parameters**

```python
config = SimulationConfig(
    withdrawal_amount=100000,
    years=36,
    inflation_rate=0.03,
    max_tax_rate=0.22
)

# Access nested configs
config.withdrawal.withdrawal_rate = 0.04
config.montecarlo.seed = 42
```

**Key Parameters:**
- `withdrawal_amount`: Target annual withdrawal amount
- `years`: Simulation duration
- `inflation_rate`: Annual inflation rate (default: 3%)
- `max_tax_rate`: Maximum tax rate for optimization
- `account_closure_amount`: Minimum balance before closing account
- `adjust_for_inflation`: Whether to apply inflation adjustments

**Nested Configurations:**
- `withdrawal`: `WithdrawalConfig` instance
- `montecarlo`: `MonteCarloConfig` instance

**Methods:**
- `get_return_rates()`: Returns numpy array of return rates for analysis
- `get(key, default)`: Safe parameter retrieval with fallback
- `as_dict()`: Convert to dictionary representation

### WithdrawalConfig
**Parameters specific to withdrawal strategies**

```python
withdrawal_config = WithdrawalConfig(
    withdrawal_mode='target_amount',
    withdrawal_rate=0.04,
    guardrail_ceiling=0.055,  # 5.5% max
    guardrail_floor=0.035     # 3.5% min
)
```

**Key Parameters:**
- `withdrawal_mode`: Strategy type ('target_amount', 'fixed_rate', etc.)
- `withdrawal_rate`: Initial withdrawal rate (4% = 0.04)
- `guardrail_ceiling/floor`: Dynamic adjustment boundaries
- `assumed_gain_rate`: Expected portfolio growth rate
- `early_retirement_age`: Age for penalty-free withdrawals

**Methods:**
- `apply_guardrails(rate)`: Clamps withdrawal rate within floor/ceiling

### MonteCarloConfig
**Parameters for Monte Carlo simulations**

```python
def normal_sampler(seed):
    np.random.seed(seed)
    return np.random.normal(0.07, 0.15)  # 7% mean, 15% volatility

monte_config = MonteCarloConfig(
    return_sampler=normal_sampler,
    seed=42
)
```

**Parameters:**
- `return_sampler`: Callable that generates market returns
- `seed`: Random seed for reproducible results

**Methods:**
- `sample(year)`: Generate market return for given year

## Context Classes

### SimulationContext
**Base context class that carries metadata throughout simulation**

```python
context = SimulationContext(
    scenario_id='withdrawal_amount',
    withdrawal_mode='target_amount',
    config=simulation_config
)

# Check if Monte Carlo scenario
if context.is_montecarlo:
    print("Running Monte Carlo analysis")

# Safe parameter access
tax_rate = context.get('max_tax_rate', 0.22)
```

**Properties:**
- `scenario_id`: Unique identifier for the scenario
- `withdrawal_mode`: Type of withdrawal strategy
- `config`: Associated `SimulationConfig` instance
- `schedule`: `SimulationSchedule` for timeline management

**Methods:**
- `is_montecarlo`: Property that checks if scenario is Monte Carlo
- `get(key, default)`: Safe config parameter retrieval
- `get_tax_tables(workbook)`: Extract tax tables from Excel workbook
- `to_summary_row(summary_df)`: Generate flat summary dictionary

### WithdrawalContext
**Extended context for withdrawal-specific simulations**

```python
withdrawal_context = WithdrawalContext(
    scenario_id='withdrawal_guardrail',
    withdrawal_mode='guardrail',
    config=config
)

# Apply guardrail constraints
adjusted_rate = withdrawal_context.apply_guardrails(0.06)  # Returns 0.055

# Inflation adjustments (inherited from FinancialAdjustmentMixin)
real_spending = withdrawal_context.compute_real_spend(50000, year=5)
```

**Inherits from:**
- `SimulationContext`: Base functionality
- `FinancialAdjustmentMixin` (from `adjustments.py`): Inflation calculations

**Additional Methods:**
- `apply_guardrails(rate)`: Apply withdrawal rate constraints
- `use_inflation()`: Check if inflation adjustments are enabled
- `compute_real_spend(net_spend, year)`: Calculate inflation-adjusted spending (via mixin)

### MonteCarloContext
**Context for Monte Carlo simulations**

```python
monte_context = MonteCarloContext(
    scenario_id='mc_guardrail',
    config=config
)

# Sample market return for year 10
return_rate = monte_context.sample_return(year=10)
```

**Methods:**
- `sample_return(year)`: Generate market return for specific year

## Utility Classes

### SimulationSchedule
**Timeline management for simulations**

```python
schedule = SimulationSchedule(
    begin_age=65,
    begin_year=2024,
    duration=30,
    end_age=95,
    end_year=2054
)
```

### DictMixin
**Base mixin providing dictionary conversion utilities**

**Methods:**
- `as_dict()`: Convert dataclass to dictionary
- `to_summary_row(extra)`: Generate summary with timestamp

## External Dependencies

### FinancialAdjustmentMixin (from adjustments.py)
**Mixin providing inflation adjustment calculations**

```python
# Used via WithdrawalContext inheritance
future_value = context.adjust_for_inflation(100000, years=10)
present_value = context.adjust_for_real_spend(150000, years=10)
```

**Methods:**
- `adjust_for_inflation(value, years)`: Calculate future value with inflation
- `adjust_for_real_spend(value, years)`: Calculate present value (deflate)

## Usage Patterns

### Basic Configuration Setup
```python
# Create main configuration
config = SimulationConfig(
    withdrawal_amount=80000,
    years=30,
    inflation_rate=0.025,
    max_tax_rate=0.22
)

# Customize withdrawal parameters
config.withdrawal.guardrail_ceiling = 0.06
config.withdrawal.guardrail_floor = 0.03

# Setup Monte Carlo
config.montecarlo.seed = 12345
```

### Context Creation for Different Scenarios
```python
# Tax-smart withdrawal
withdrawal_ctx = WithdrawalContext(
    scenario_id='withdrawal_amount',
    withdrawal_mode='target_amount',
    config=config
)

# Monte Carlo analysis
monte_ctx = MonteCarloContext(
    scenario_id='mc_guardrail',
    config=config
)
```

### Safe Parameter Access
```python
# Always use .get() for optional parameters
withdrawal_rate = context.get('withdrawal_rate', 0.04)
years = context.get('years', 30)

# Check configuration state
if context.use_inflation():
    adjusted_amount = context.adjust_for_inflation(base_amount, year)
```

## Code Organization

The module has been refactored for better organization and maintainability:

### File Structure
```
config_context.py        # Main configuration and context classes
adjustments.py          # FinancialAdjustmentMixin (external dependency)
```

### Benefits of Current Organization
- **Modular design**: Financial adjustment logic isolated in separate module
- **Clear dependencies**: Import structure eliminates circular references
- **Reusability**: `FinancialAdjustmentMixin` can be used by other modules
- **Maintainability**: Changes to adjustment logic contained in one file

### Class Definition Order (within config_context.py)
1. `DictMixin`
2. Config classes (`MonteCarloConfig`, `WithdrawalConfig`, `SimulationConfig`)
3. Context classes (`SimulationContext`, `WithdrawalContext`, `MonteCarloContext`)
4. `SimulationSchedule`

**Note**: `FinancialAdjustmentMixin` is now imported from `adjustments.py`, resolving the previous ordering dependency issue.