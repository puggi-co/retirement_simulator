# Withdrawal Simulation Engine

## Overview

The withdrawal simulation engine is the core component that models retirement portfolio behavior over time. It simulates various withdrawal strategies, handles tax calculations, manages required minimum distributions (RMDs), and tracks portfolio performance across different market scenarios.

## Key Classes and Functions

### Core Simulation Function

#### `simulate_scenario_withdrawals()`

The main simulation function that orchestrates withdrawal strategies, tax calculations, and portfolio management over the retirement timeline.

**Signature:**
```python
def simulate_scenario_withdrawals(
    context: WithdrawalContext, 
    tax_tables: TaxTables, 
    portfolio_df, 
    return_rate, 
    ledger, 
    roth=False
) -> pd.DataFrame
```

**Parameters:**
- `context`: WithdrawalContext containing simulation configuration
- `tax_tables`: TaxTables object with deduction and bracket data
- `portfolio_df`: DataFrame containing account details and balances
- `return_rate`: Expected return rate for growth calculations
- `ledger`: AccountLedger for tracking detailed transactions
- `roth`: Boolean flag for Roth conversion strategies

**Returns:**
- DataFrame containing detailed withdrawal results for each year

**Key Features:**
- Handles multiple withdrawal modes (fixed_rate, target_amount, guardrail_amount)
- Processes income streams (Social Security, FERS, ordinary income)
- Applies guardrail adjustments based on portfolio performance
- Calculates taxes and effective spending power
- Tracks shortfalls when withdrawal targets cannot be met

### Withdrawal Strategy Functions

#### `apply_rate_based_withdrawals()`

Implements fixed-rate withdrawal strategy where a consistent percentage is withdrawn from each account annually.

**Signature:**
```python
def apply_rate_based_withdrawals(
    context: WithdrawalContext,
    ledger, account, return_rate,
    year, age, current_balance, ord_inc, ssa_inc
) -> tuple[AccountLedger, float, float, float]
```

**Features:**
- Calculates RMDs for tax-deferred accounts
- Applies fixed withdrawal rates to taxable accounts
- Handles account closure when balance falls below threshold
- Tracks taxable income and capital gains separately

#### `apply_amount_based_withdrawals()`

Implements target-amount withdrawal strategy with tax-smart ordering.

**Signature:**
```python
def apply_amount_based_withdrawals(
    context: SimulationContext,
    ledger, account, portfolio_df, draw_order, withdrawal_mode,
    year, age, current_balance, withdrawal_goal, income_total, roth, 
    assumed_gain_rate, actual_rate, df_lef, schedule
) -> tuple[AccountLedger, float, pd.DataFrame, float, float, float]
```

**Features:**
- Prioritizes RMD requirements
- Uses tax-smart withdrawal ordering
- Supports Roth conversion strategies
- Handles shortfalls gracefully

#### `apply_tax_smart_withdrawals()`

Implements tax-efficient withdrawal ordering across different account types.

**Signature:**
```python
def apply_tax_smart_withdrawals(
    portfolio_df, draw_order, year, age, roth, 
    assumed_gain_rate, withdrawal_target
) -> tuple[pd.DataFrame, float, float, list]
```

**Tax-Smart Draw Orders:**
- **Standard Order**: taxable → deferred → tax_free
- **Roth Conversion Order**: deferred → taxable → tax_free

**Features:**
- Draws from smallest balances first within each tax category
- Tracks taxable income vs. capital gains appropriately
- Supports Roth conversion strategies

## Withdrawal Modes

### 1. Fixed Rate (`fixed_rate`)
- Withdraws a fixed percentage from each account annually
- RMDs override fixed rate for tax-deferred accounts when higher
- Simple and predictable, but may not meet spending goals

### 2. Target Amount (`target_amount`)
- Attempts to withdraw a specific dollar amount each year
- Uses tax-smart ordering to minimize tax impact
- Adjusts for inflation if configured

### 3. Guardrail Amount (`guardrail_amount`)
- Similar to target amount but with dynamic adjustments
- Increases/decreases withdrawals based on portfolio performance
- **Floor Trigger**: If withdrawal rate > ceiling, reduce by 10%
- **Ceiling Trigger**: If withdrawal rate < floor, increase by 10%
- **Default Range**: 3.5% - 5.5% of portfolio value

## Income Stream Processing

### Social Security Income (`ssa_income`)
- Grows with inflation (full CPI adjustment)
- Subject to taxation based on configured `ssa_tax_rate`
- Begins at specified age (typically 62-70)

### FERS Pension Income (`fers_income`)
- Special COLA adjustment using `get_fers_cola()` function
- **COLA Rules**:
  - If inflation ≤ 2%: Full inflation adjustment
  - If 2% < inflation < 3%: 2% adjustment
  - If inflation ≥ 3%: Inflation - 1% adjustment

### Ordinary Income (`ordinary_income`)
- No growth adjustment (fixed nominal amount)
- Fully taxable as ordinary income

## Tax Calculations

### Tax Components Tracked
- **Ordinary Income**: Salary, pension, traditional IRA/401k withdrawals
- **Capital Gains**: Assumed percentage of taxable account withdrawals
- **Social Security**: Portion subject to taxation
- **Standard Deduction**: Inflation-adjusted over time

### Tax Computation Process
1. Calculate gross income from all sources
2. Apply inflation-adjusted standard deduction
3. Compute tax using brackets for filing status and year
4. Calculate effective tax rate and net spending power

## Required Minimum Distributions (RMDs)

### RMD Calculation
- Uses IRS life expectancy tables (Uniform, Joint, Single)
- Formula: `current_balance / life_expectancy_factor`
- Required for traditional IRAs and TSP accounts starting at age 73+

### RMD Integration
- RMDs are mandatory and override other withdrawal strategies
- Excess RMD amounts count toward withdrawal goals
- Properly categorized as ordinary income for tax purposes

## Utility Functions

### `get_fers_cola(inflation)`
Calculates FERS pension cost-of-living adjustment based on inflation rate.

### `summarize_spending_sources(df_withdrawals)`
Creates summary showing how annual spending is funded across different sources.

**Source Categories:**
- Income streams (Social Security, pension, etc.)
- Required minimum distributions
- Roth conversions
- Discretionary withdrawals
- Shortfalls (unmet needs)

## Example Usage

```python
# Setup withdrawal context
context = WithdrawalContext(
    config=simulation_config,
    schedule=retirement_schedule,
    withdrawal_mode='guardrail_amount'
)

# Run simulation
results_df = simulate_scenario_withdrawals(
    context=context,
    tax_tables=tax_tables,
    portfolio_df=portfolio_data,
    return_rate=0.07,
    ledger=account_ledger,
    roth=False
)

# Analyze spending sources
spending_summary = summarize_spending_sources(results_df)
```

## Key Design Patterns

### Context-Based Configuration
Uses `WithdrawalContext` to encapsulate all simulation parameters, making the code more maintainable and testable.

### Ledger Integration
All transactions are recorded in the `AccountLedger` for detailed tracking and analysis.

### Tax-Smart Optimization
Implements sophisticated withdrawal ordering to minimize tax burden while meeting income needs.

### Shortfall Handling
Gracefully handles scenarios where portfolio cannot meet withdrawal targets, tracking unmet needs for analysis.

## Performance Considerations

- Processes years sequentially to maintain state consistency
- Uses efficient DataFrame operations for portfolio updates
- Caches tax table lookups to avoid repeated calculations
- Rounds financial amounts appropriately to avoid floating-point precision issues

## Future Enhancements

- Support for additional income stream types
- More sophisticated guardrail algorithms
- Tax-loss harvesting simulation
- Asset allocation rebalancing during withdrawals
- Monte Carlo integration for uncertainty modeling