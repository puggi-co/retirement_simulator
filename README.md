# Retirement Simulator

A Python-based retirement planning tool that simulates various withdrawal strategies and market scenarios to help evaluate retirement portfolio sustainability.

## Overview

This simulator helps answer critical retirement planning questions:
- How can I optimize withdrawals across different account types (taxable, tax-deferred, tax-free)?
- What's the impact of tax-smart withdrawal sequencing on portfolio longevity?
- How do Roth conversions affect my long-term tax burden?
- When should I use guardrails to adjust withdrawal amounts?
- What's the optimal strategy for managing RMDs while minimizing taxes?

## Features

- **Tax-Smart Withdrawal Strategies**: Optimize withdrawal sequencing across account types
- **Multiple Account Support**: Taxable, Tax-Deferred (Traditional IRA/401k), Tax-Free (Roth IRA)
- **Advanced Strategies**: Fixed rate, target amount, guardrails, Roth conversion ladders
- **Tax Optimization**: Stay within tax brackets, harvest losses, manage capital gains
- **RMD Management**: Automatic handling of Required Minimum Distributions
- **Monte Carlo Simulations**: Test portfolio performance across thousands of market scenarios
- **Guardrail Adjustments**: Dynamic withdrawal adjustments based on portfolio performance
- **Comprehensive Tax Modeling**: Ordinary income, capital gains, qualified dividends, AMT
- **Dashboard Integration**: Results staged for downstream visualization tools
- **Flexible Configuration**: Easily adjust assumptions, time horizons, and tax parameters

## Quick Start

### Basic Usage

```python
from config_context import SimulationConfig
from runner import ScenarioRunner
from strategy_withdrawals import simulate_scenario_withdrawals

# Configure your retirement scenario
config = SimulationConfig(
    initial_balance=1000000,
    retirement_years=30,
    annual_expenses=40000,
    inflation_rate=0.025
)

# Run tax-smart withdrawal strategy
runner = ScenarioRunner(config)
results = runner.run_scenario("withdrawal_amount")

# Run fixed rate strategy (traditional 4% rule)
results = runner.run_scenario("withdrawal_rate")

# Run guardrails strategy with dynamic adjustments
results = runner.run_scenario("withdrawal_guardrail")
```

### Monte Carlo Analysis

```python
from strategy_montecarlo import simulate_montecarlo_withdrawals

# Run Monte Carlo for tax-smart target amount strategy
results = simulate_montecarlo_withdrawals(
    scenario_id="withdrawal_amount",
    config=config,
    num_simulations=1000,
    market_return_mean=0.07,
    market_volatility=0.15
)

# Compare Roth conversion strategy
roth_results = simulate_montecarlo_withdrawals(
    scenario_id="roth_conversion",
    config=config,
    num_simulations=1000
)

print(f"Tax-smart success rate: {results.success_rate}%")
print(f"Roth conversion success rate: {roth_results.success_rate}%")
```

## Project Structure

```
retirement-simulator/
├── README.md                    # This file
├── config_context.py           # Configuration and context classes
├── adjustments.py              # Financial adjustment utilities (inflation, etc.)
├── ledger.py                   # Account ledger and transaction tracking
├── runner.py                   # Main simulation runner
├── workbook_interface.py       # Excel/CSV data loading
├── strategy_withdrawals.py     # Withdrawal strategy implementations
├── strategy_montecarlo.py      # Monte Carlo simulation engine
└── tax_models.py              # Tax calculation models
```

## Core Components

### Configuration (`config_context.py`)
- **SimulationConfig**: Main configuration class for retirement assumptions
- **WithdrawalContext**: Context for tracking withdrawal state (uses `FinancialAdjustmentMixin`)
- **MonteCarloContext**: Context for Monte Carlo simulations
- **SimulationSchedule**: Timeline management utilities

### Financial Adjustments (`adjustments.py`)
- **FinancialAdjustmentMixin**: Inflation adjustment calculations and utilities
- Provides methods for real spending calculations and future value adjustments

### Simulation Engine (`runner.py`)
- **ScenarioRunner**: Orchestrates simulation execution
- **SimulationBundle**: Groups related scenarios for comparison

### Strategies (`strategy_withdrawals.py`)
- **Fixed Rate (`withdrawal_rate`)**: Traditional 4% rule with inflation adjustments
- **Tax-Smart Target Amount (`withdrawal_amount`)**: Optimized withdrawal sequencing across account types
- **Guardrails (`withdrawal_guardrail`)**: Dynamic adjustments based on portfolio performance
- **Roth Conversion (`roth_conversion`)**: Tax-deferred to Roth conversion strategies

### Analysis (`strategy_montecarlo.py`)
- Monte Carlo simulation engine
- Statistical analysis of outcomes
- Risk assessment tools

## Installation & Requirements

### Dependencies
```bash
pip install pandas numpy matplotlib scipy openpyxl
```

### Python Version
- Python 3.8 or higher required
- Tested on Python 3.9+

## Withdrawal Strategies

### 1. Fixed Rate (`withdrawal_rate`)
**"All Account Types, Fixed Rate"**
- Withdraws a fixed rate (e.g., 4%) from each account annually
- Rate adjusted for inflation each year
- Handles RMDs and tax implications per account type
- **Pros**: Simple, predictable
- **Cons**: Doesn't optimize across account types

### 2. Tax-Smart Target Amount (`withdrawal_amount`)
**"Tax Smart, Target Amount"**
- Withdrawal sequence: Taxable → Tax-Deferred → Tax-Free
- Delays RMDs until required age
- Optimizes tax brackets and capital gains treatment
- **Pros**: Leverages account type mix for tax efficiency
- **Cons**: May trigger capital gains, reduces taxable account compounding

### 3. Guardrails (`withdrawal_guardrail`)
**"Tax Smart, Target Amount w/Guardrails"**
- Same tax-smart sequencing as Target Amount
- Dynamically adjusts withdrawal amounts based on portfolio performance
- Maintains withdrawal guardrails to protect portfolio longevity
- **Pros**: Combines tax optimization with dynamic adjustments
- **Cons**: More complex, variable income

### 4. Roth Conversion (`roth_conversion`)
**"Tax Smart, Roth Conversion"**
- Withdrawal sequence: Tax-Deferred → Taxable → Tax-Free
- Converts tax-deferred withdrawals to Roth IRA
- Maximizes conversions while staying within target tax brackets
- **Pros**: Reduces future RMDs, tax-free growth
- **Cons**: Current tax burden, 5-year waiting period

## Configuration Examples

### Conservative Approach
```python
config = SimulationConfig(
    initial_balance=800000,
    retirement_years=25,
    annual_expenses=32000,
    withdrawal_rate=0.035,  # 3.5% initial withdrawal
    asset_allocation={'stocks': 0.4, 'bonds': 0.6}
)
```

### Aggressive Growth
```python
config = SimulationConfig(
    initial_balance=1500000,
    retirement_years=35,
    annual_expenses=60000,
    withdrawal_rate=0.04,
    asset_allocation={'stocks': 0.8, 'bonds': 0.2}
)
```

## Output & Results

The simulator provides detailed analysis including:
- Year-by-year portfolio balances
- Withdrawal amounts and adjustments
- Success/failure probability
- Statistical summaries (percentiles, confidence intervals)
- Visualizations of portfolio trajectories

## Next Steps

1. **Create your first simulation**: Start with the Quick Start examples
2. **Customize parameters**: Modify `SimulationConfig` for your situation
3. **Run Monte Carlo analysis**: Test thousands of market scenarios
4. **Compare strategies**: Evaluate different withdrawal approaches
5. **Analyze results**: Review success rates and portfolio longevity

## Documentation

Each Python module has a corresponding .md file with detailed documentation:
- `config_context.md` - Configuration options and examples
- `strategy_withdrawals.md` - Available withdrawal strategies
- `strategy_montecarlo.md` - Monte Carlo simulation details
- And more...

## Contributing

When modifying code:
1. Update the corresponding .md documentation file
2. Add examples for new functions/classes
3. Update this README if adding major features

## License

[Specify your license here]

---

**⚠️ Disclaimer**: This tool is for educational and planning purposes only. Consult with financial professionals for actual retirement planning decisions.