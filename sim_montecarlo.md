# Monte Carlo Simulation Engine

## Overview

The Monte Carlo simulation engine enables probabilistic analysis of retirement portfolio outcomes by running thousands of simulations with randomized market returns. This approach helps evaluate the robustness of different withdrawal strategies under various market conditions and provides statistical measures of portfolio sustainability.

## Core Functions

### `simulate_montecarlo_withdrawals()`

The primary Monte Carlo simulation function that runs multiple scenarios with randomized returns to evaluate withdrawal strategy performance.

**Signature:**
```python
def simulate_montecarlo_withdrawals(
    context: SimulationContext,
    config,
    df_accounts,
    rate,
    mode='target_amount',
    num_simulations=1000
) -> pd.DataFrame
```

**Parameters:**
- `context`: SimulationContext containing configuration and schedule data
- `config`: Configuration object with simulation parameters
- `df_accounts`: DataFrame containing account details and balances
- `rate`: Expected return rate (mean for normal distribution)
- `mode`: Withdrawal strategy ('fixed_rate', 'target_amount', 'guardrail_amount')
- `num_simulations`: Number of Monte Carlo iterations to run (default: 1000)

**Returns:**
- DataFrame with simulation results including portfolio balances, withdrawals, and returns for each year/simulation

**Key Features:**
- Configurable return sampling (normal distribution by default)
- Random downturn year selection (4 years per simulation)
- Supports multiple withdrawal strategies
- Seeded random number generation for reproducibility

## Withdrawal Strategies

### 1. Fixed Rate (`fixed_rate`)
Withdraws a fixed percentage of the current portfolio balance each year.

**Characteristics:**
- Dynamic withdrawal amounts based on portfolio performance
- Natural guardrails (withdrawals decrease when portfolio declines)
- No risk of complete portfolio depletion in finite time

**Formula:**
```python
withdrawal_amt = balance * withdrawal_rate
```

### 2. Target Amount (`target_amount`)
Attempts to withdraw a specific dollar amount, adjusted for inflation.

**Characteristics:**
- Consistent purchasing power over time
- Higher failure risk during market downturns
- Predictable spending capacity for retirees

**Formula:**
```python
withdrawal_amt = withdrawal_target * ((1 + inflation_rate) ** year_index)
```

### 3. Guardrail Amount (`guardrail_amount`)
Dynamic target amount with portfolio-based adjustments using guardrail methodology.

**Characteristics:**
- Combines benefits of target amount with portfolio protection
- Automatically adjusts spending based on portfolio performance
- Reduces sequence-of-returns risk

**Guardrail Logic:**
```python
actual_rate = withdrawal_target / balance
if actual_rate > guardrail_ceiling:
    withdrawal_target *= 0.9  # Reduce by 10%
elif actual_rate < guardrail_floor:
    withdrawal_target *= 1.1  # Increase by 10%
else:
    withdrawal_target *= (1 + inflation_rate)  # Inflation adjust
```

**Default Guardrail Parameters:**
- **Floor**: 3.5% of portfolio value
- **Ceiling**: 5.5% of portfolio value

## Return Modeling

### Default Return Sampler
Uses normal distribution with configurable parameters:

```python
return_sampler = lambda n: np.random.normal(loc=rate, scale=5, size=n)
```

**Parameters:**
- `loc`: Mean return (typically 7-10% for equity-heavy portfolios)
- `scale`: Standard deviation (default: 5%)
- `size`: Number of years to generate

### Custom Return Samplers
Users can provide custom return sampling functions:

```python
# Example: Historical bootstrap sampling
def bootstrap_returns(n):
    historical_returns = load_historical_data()
    return np.random.choice(historical_returns, size=n, replace=True)

config.return_sampler = bootstrap_returns
```

### Downturn Modeling
Each simulation randomly selects 4 years as "downturn years" to model realistic market volatility clustering.

## Analysis and Reporting

### `summarize_withdrawal_outcomes()`

Comprehensive analysis function that generates statistical summaries and visualizations of Monte Carlo results.

**Signature:**
```python
def summarize_withdrawal_outcomes(
    df_sim_results,
    failure_thresholds=[0, 100_000, 250_000],
    export_excel_path=None,
    export_pdf_path=None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]
```

**Parameters:**
- `df_sim_results`: Results from Monte Carlo simulations
- `failure_thresholds`: Portfolio balance thresholds for failure analysis
- `export_excel_path`: Optional Excel export path
- `export_pdf_path`: Optional PDF chart export path

**Returns:**
- `df_summary`: Statistical summary (median, mean, std, min, max)
- `df_failures`: Failure rates by threshold
- `df_median`: Median portfolio trajectories by year
- `df_percentiles`: 10th, 25th, 75th, 90th percentiles by year

### Failure Rate Analysis

Calculates the percentage of simulations that end with portfolio balances below specified thresholds:

**Default Thresholds:**
- **$0**: Complete depletion
- **$100,000**: Critical low balance
- **$250,000**: Conservative safety margin

**Example Output:**
```
strategy        threshold    failure_rate_(%)
guardrail_amount    ≤ $0           2.3
guardrail_amount    ≤ $100,000     8.7
guardrail_amount    ≤ $250,000    15.4
```

### Statistical Metrics

**Portfolio Balance Statistics:**
- **Median**: 50th percentile outcome (robust central tendency)
- **Mean**: Average outcome (affected by extreme values)
- **Standard Deviation**: Measure of outcome variability
- **Min/Max**: Range of possible outcomes

## Visualization Capabilities

### 1. Portfolio Trajectory Chart
- Median trajectory line for each strategy
- 10th-90th percentile confidence band