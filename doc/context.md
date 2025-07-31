# Context Module Documentation

_Save this as: `docs/architecture/context-module.md`_

## Overview

The `simulation/context.py` module defines runtime context classes for retirement
simulations. These classes encapsulate scenario-specific state, configuration access,
and operational methods such as inflation adjustment, guardrail enforcement, and return
sampling.

## Module Structure

```text
simulation/context.py
├── DictMixin                # Base mixin for serialization
├── SimulationContext        # Core context class
├── FinancialAdjustmentMixin # Inflation adjustment logic
├── WithdrawalContext        # Withdrawal scenario context
└── MonteCarloContext        # Monte Carlo scenario context
```

## Core Design Principles

### Context vs Configuration Separation

- **Configuration** (`SimulationConfig`): Static parameters and settings
- **Context**: Runtime state, scenario identification, and operational methods
- Context _contains_ configuration but adds scenario-specific behavior

### Mixin Architecture

- `DictMixin`: Provides serialization capabilities
- `FinancialAdjustmentMixin`: Adds inflation adjustment methods
- Contexts inherit appropriate mixins based on their needs

## Class Definitions

### DictMixin

**Purpose**: Base mixin providing dictionary serialization and summary generation

**Methods**:

- `as_dict() -> dict` - Convert dataclass fields to dictionary
- `to_summary_row(extra: Optional[dict] = None) -> dict` - Create timestamped summary
  with optional extra fields

**Usage Pattern**:

```python
context = SimulationContext(scenario_id='test_scenario')
data_dict = context.as_dict()
summary = context.to_summary_row(extra={'portfolio_value': 1000000})
```

### SimulationContext

**Purpose**: Base context class for all simulation scenarios

**Core Attributes**:

- `scenario_id: str = 'unknown'` - Unique identifier for the simulation scenario
- `withdrawal_mode: str = 'unknown'` - Type of withdrawal strategy being used
- `config: Optional[SimulationConfig] = None` - Associated configuration object
- `schedule: SimulationSchedule` - Timeline and scheduling information

**Key Methods**:

- `get(key: str, default=None)` - Access configuration attributes with fallback
- `is_montecarlo -> bool` - Property to detect Monte Carlo scenarios (IDs starting with
  'mc\_')
- `get_tax_tables(workbook) -> TaxTables` - Factory method for tax table creation
- `to_summary_row(summary_df=None) -> dict` - Extended summary generation with DataFrame
  integration

**String Representations**:

- `__repr__()`: Detailed representation for debugging
- `__str__()`: Concise display format

**Usage Example**:

```python
from simulation.config import SimulationConfig

config = SimulationConfig(inflation_rate=0.025, years=30)
context = SimulationContext(
    scenario_id='withdrawal_001',
    withdrawal_mode='fixed_rate',
    config=config
)

# Access configuration through context
inflation = context.get('inflation_rate', 0.03)  # Returns 0.025
years = context.get('years')  # Returns 30

# Check scenario type
is_mc = context.is_montecarlo  # Returns False (ID doesn't start with 'mc_')
```

### FinancialAdjustmentMixin

**Purpose**: Provides inflation adjustment calculations for financial values

**Methods**:

- `adjust_for_inflation(value: float, years: int) -> float` - Convert present value to
  future value
- `adjust_for_real_spend(value: float, years: int) -> float` - Convert future value to
  present value

**Formulas**:

- **Future Value**: `value * (1 + inflation_rate)^years`
- **Present Value**: `value / (1 + inflation_rate)^years`

**Usage Example**:

```python
# Assumes context has config with inflation_rate = 0.03
present_value = 100000
years_ahead = 10

# What $100k today will be worth in 10 years
future_value = context.adjust_for_inflation(present_value, years_ahead)
# Returns: 100000 * (1.03)^10 ≈ $134,392

# What $100k in 10 years is worth today
real_value = context.adjust_for_real_spend(100000, years_ahead)
# Returns: 100000 / (1.03)^10 ≈ $74,409
```

### WithdrawalContext

**Purpose**: Specialized context for withdrawal-based simulations

**Inheritance**: `SimulationContext + FinancialAdjustmentMixin`

**Specialized Methods**:

- `apply_guardrails(rate: float) -> float` - Apply withdrawal rate guardrails
- `use_inflation() -> bool` - Check if inflation adjustments are enabled
- `compute_real_spend(net_spend: float, ydx: int) -> float` - Calculate
  inflation-adjusted spending

**Workflow Integration**:

```python
withdrawal_context = WithdrawalContext(
    scenario_id='withdrawal_conservative',
    withdrawal_mode='guardrails',
    config=config
)

# Calculate safe withdrawal rate
proposed_rate = 0.06  # 6%
safe_rate = withdrawal_context.apply_guardrails(proposed_rate)  # Clamped to ceiling

# Adjust spending for inflation if enabled
if withdrawal_context.use_inflation():
    real_spending = withdrawal_context.compute_real_spend(50000, year_index)
```

### MonteCarloContext

**Purpose**: Specialized context for Monte Carlo simulations

**Inheritance**: `SimulationContext` only (no financial adjustments needed)

**Specialized Methods**:

- `sample_return(year: int = 0) -> float` - Generate market return sample for specified
  year

**Monte Carlo Integration**:

```python
mc_context = MonteCarloContext(
    scenario_id='mc_aggressive_001',
    withdrawal_mode='dynamic',
    config=config  # Config should have montecarlo.return_sampler set
)

# Generate returns for simulation
portfolio_returns = []
for year in range(30):
    annual_return = mc_context.sample_return(year)
    portfolio_returns.append(annual_return)
```

## Context Lifecycle and Usage Patterns

### Context Creation and Configuration

```python
# 1. Create configuration
config = SimulationConfig(
    years=25,
    inflation_rate=0.025,
    withdrawal=WithdrawalConfig(withdrawal_rate=0.04)
)

# 2. Create appropriate context
context = WithdrawalContext(
    scenario_id='retirement_plan_2025',
    withdrawal_mode='target_amount',
    config=config
)

# 3. Use context throughout simulation
for year in range(config.years):
    # Context provides both state and behavior
    if context.use_inflation():
        adjusted_amount = context.adjust_for_inflation(base_amount, year)

    safe_rate = context.apply_guardrails(calculated_rate)
```

### Summary Generation for Analysis

```python
# Generate summary for data analysis
summary = context.to_summary_row()
print(summary)
# Output:
# {
#   'config_years': 25,
#   'guardrail_ceiling': 0.055,
#   'guardrail_floor': 0.035,
#   'inflation_rate': 0.025,
#   'max_tax_rate': 0.22,
#   'montecarlo': False,
#   'scenario_id': 'retirement_plan_2025',
#   'timestamp': '2025-07-24T12:30:45.123456',
#   'withdrawal_mode': 'target_amount'
# }
```

### Tax Table Integration

```python
# Context provides factory method for tax tables
workbook = load_tax_data()  # External data source
tax_tables = context.get_tax_tables(workbook)

# Use tax tables in calculations
tax_owed = tax_tables.calculate_tax(taxable_income)
```

## Integration with Simulation Workflows

### Withdrawal Scenario Workflow

```python
def run_withdrawal_simulation(context: WithdrawalContext, portfolio):
    results = []

    for year in range(context.get('years', 30)):
        # Use context for inflation adjustments
        if context.use_inflation():
            target_amount = context.adjust_for_inflation(
                context.get('withdrawal_amount'), year
            )

        # Apply guardrails through context
        withdrawal_rate = calculate_base_rate(portfolio)
        safe_rate = context.apply_guardrails(withdrawal_rate)

        # Update portfolio and collect results
        portfolio = update_portfolio(portfolio, safe_rate)
        results.append(context.to_summary_row({'portfolio_value': portfolio.value}))

    return results
```

### Monte Carlo Scenario Workflow

```python
def run_monte_carlo_simulation(context: MonteCarloContext, portfolio):
    results = []

    for year in range(context.get('years', 30)):
        # Sample market return through context
        market_return = context.sample_return(year)

        # Apply return to portfolio
        portfolio = apply_market_return(portfolio, market_return)
        results.append(context.to_summary_row({'return': market_return}))

    return results
```

## Context Factory Pattern

### Scenario-Based Context Creation

```python
def create_context(scenario_type: str, scenario_id: str, config: SimulationConfig):
    """Factory function for creating appropriate context types"""

    if scenario_type == 'withdrawal':
        return WithdrawalContext(
            scenario_id=scenario_id,
            withdrawal_mode=config.withdrawal.withdrawal_mode,
            config=config
        )

    elif scenario_type == 'montecarlo':
        return MonteCarloContext(
            scenario_id=f'mc_{scenario_id}',
            withdrawal_mode=config.withdrawal.withdrawal_mode,
            config=config
        )

    else:
        return SimulationContext(
            scenario_id=scenario_id,
            withdrawal_mode='unknown',
            config=config
        )
```

## Best Practices

### Context Usage Guidelines

1. **One Context Per Simulation**: Each simulation run should have its own context
   instance
2. **Configuration Immutability**: Don't modify config through context; create new
   context if needed
3. **Method Delegation**: Use context methods rather than accessing config directly
4. **Summary Generation**: Use `to_summary_row()` for consistent result formatting

### Error Handling

```python
# Safe configuration access
withdrawal_rate = context.get('withdrawal_rate', 0.04)  # Fallback to 4%

# Validate context state
if not context.config:
    raise ValueError(f"Context {context.scenario_id} missing configuration")

# Check for required methods
if hasattr(context, 'apply_guardrails'):
    safe_rate = context.apply_guardrails(rate)
```

### Testing Patterns

```python
def test_withdrawal_context():
    config = SimulationConfig(inflation_rate=0.025)
    context = WithdrawalContext(scenario_id='test', config=config)

    # Test inflation adjustment
    future_value = context.adjust_for_inflation(100000, 10)
    assert abs(future_value - 128008.75) < 0.01  # Allow for floating point precision

    # Test summary generation
    summary = context.to_summary_row()
    assert summary['scenario_id'] == 'test'
    assert 'timestamp' in summary
```

This context architecture provides a clean separation between configuration and runtime
state while offering specialized behavior for different simulation types.
