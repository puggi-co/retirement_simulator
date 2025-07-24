# Scenario Execution Engine

**File: `runner.py`**

This module provides the main execution engine for running retirement simulation scenarios. The `ScenarioRunner` class orchestrates the simulation workflow, manages results, and handles exports.

## Module Dependencies

```python
from ledger import AccountLedger
from tax_models import TaxTables
from strategy_withdrawals import simulate_scenario_withdrawals
from strategy_montecarlo import simulate_montecarlo_withdrawals
from analysis import summarize_spending_sources, log_scenario_summary
```

## Core Classes

### ScenarioRunner
**Main execution engine for withdrawal and Monte Carlo simulations**

The `ScenarioRunner` class manages the complete simulation lifecycle from initialization through analysis and export.

#### Initialization

```python
runner = ScenarioRunner(
    context=withdrawal_context,      # SimulationContext instance
    df_my_portfolio=portfolio_df,    # Portfolio account data
    return_rate=0.07,               # Expected return rate
    wb=workbook                     # Excel workbook (optional)
)
```

**Parameters:**
- `context`: `SimulationContext` or subclass containing scenario configuration
- `df_my_portfolio`: DataFrame with account balances and metadata
- `return_rate`: Annual return rate for deterministic simulations
- `wb`: Excel workbook object for tax table extraction (optional)

**Initialization Features:**
- Creates `AccountLedger` instance for transaction tracking
- Assigns scenario ID to ledger for downstream reporting
- Stores context, config, and schedule references for easy access

#### Properties
- `context`: Associated simulation context
- `config`: Configuration object (from context)
- `schedule`: Timeline schedule (from context)
- `ledger`: Account transaction ledger
- `results`: Simulation results DataFrame
- `analysis`: Analysis results (after `analyze_results()`)

## Core Methods

### run_strategy()
**Execute simulation based on context metadata**

```python
runner = ScenarioRunner(context, portfolio_df, return_rate, wb)
runner.run_strategy()

# Results available in runner.results
print(f"Simulation complete: {len(runner.results)} years")
```

**Workflow:**
1. **Extract tax tables** from workbook using `context.get_tax_tables()`
2. **Prepare portfolio** data with computed columns
3. **Determine simulation type** (Monte Carlo vs. single scenario)
4. **Execute appropriate strategy** based on `context.scenario_id`

**Supported Scenarios:**
- `withdrawal_amount`: Tax-smart target amount strategy
- `withdrawal_rate`: Fixed rate strategy
- `withdrawal_guardrail`: Guardrails strategy
- `roth_conversion`: Roth conversion strategy
- Monte Carlo variations of all above strategies

### prepare_portfolio_df()
**Augment portfolio data with simulation columns**

```python
# Called automatically by run_strategy()
portfolio_df = runner.prepare_portfolio_df()
```

**Enhancements:**
- Adds computed columns: `return_rate`, `withdrawal_mode`, `current_balance`
- Initializes tracking fields: `year`, `age`, `withdrawal_amount`, `tax_owed`
- Sets scenario metadata: `scenario_id`
- Standardizes column ordering for consistent processing

**Output Columns:**
```
year, age, return_rate, withdrawal_mode, account_name, scenario_id,
begin_balance, current_balance, end_balance, withdrawal_amount, omd, rmd,
ord_inc, ssa_inc, taxable_gain, taxable_income, taxable_ssa, tax_owed,
effective_tax_rate, roth_convert_amount, rmd_begin_year, rmd_age,
rmd_table, account_type, account_tax_type, filing_status
```

## Monte Carlo Simulation

### run_simulation()
**Execute Monte Carlo analysis with multiple market scenarios**

```python
# Explicit Monte Carlo run
runner.run_simulation(
    mode='withdrawal_amount',
    num_simulations=1000
)

# Or automatically via run_strategy() if context.is_montecarlo
runner.run_strategy()  # Detects Monte Carlo context automatically
```

**Parameters:**
- `mode`: Withdrawal strategy mode ('fixed_rate', 'withdrawal_amount', etc.)
- `num_simulations`: Number of Monte Carlo iterations (default: 1000)

**Features:**
- Progress indication during execution
- Automatic result storage in `runner.results`
- Integration with Monte Carlo strategy engine

## Results Analysis

### analyze_results()
**Analyze simulation outcomes and generate reports**

```python
# Basic analysis
runner.analyze_results()

# With export paths
runner.analyze_results(
    excel_path='results/scenario_results.xlsx',
    pdf_path='results/scenario_charts.pdf'
)
```

**Analysis Features:**
- **Spending composition**: Breakdown of withdrawal sources by year
- **Excel export**: Detailed results in spreadsheet format
- **Summary statistics**: Key performance metrics
- **Spending sources**: Account-by-account contribution analysis

**Outputs:**
- `runner.spending_summary`: DataFrame with spending composition
- Console display of yearly spending breakdown
- Optional Excel/PDF exports

### preview_summary()
**Display quick summary of analysis results**

```python
runner.analyze_results()
runner.preview_summary()

# Output:
# 🧾 Summary: [key metrics]
# 🚧 Failure Thresholds: [risk analysis]
```

## Export and Reporting

### export_all_to_folder()
**Comprehensive export of all simulation artifacts**

```python
runner.export_all_to_folder(
    folder='output/retirement_analysis',
    include_summary=True,
    include_dashboard=True
)
```

**Parameters:**
- `folder`: Target directory for exports
- `include_summary`: Generate scenario summary logs (default: True)
- `include_dashboard`: Create dashboard-ready exports (default: True)

**Export Artifacts:**
- `{scenario_id}_results.xlsx`: Detailed simulation results
- `{scenario_id}_charts.pdf`: Visualization charts
- Summary logs for scenario comparison
- Dashboard-compatible data formats

**Data Preparation:**
- Ensures `strategy` column exists for dashboard compatibility
- Adds `simulation` column for Monte Carlo results
- Maintains consistent data structure across export formats

## Usage Patterns

### Basic Single Scenario
```python
from config_context import WithdrawalContext, SimulationConfig

# Setup
config = SimulationConfig(withdrawal_amount=80000, years=30)
context = WithdrawalContext('withdrawal_amount', 'target_amount', config)

# Execute
runner = ScenarioRunner(context, portfolio_df, return_rate=0.07)
runner.run_strategy()
runner.analyze_results()
```

### Monte Carlo Analysis
```python
from config_context import MonteCarloContext

# Monte Carlo context
mc_context = MonteCarloContext('mc_withdrawal_amount', config)

# Execute with multiple simulations
runner = ScenarioRunner(mc_context, portfolio_df, return_rate=0.07)
runner.run_strategy()  # Automatically detects Monte Carlo
runner.analyze_results()
```

### Batch Processing with Export
```python
scenarios = ['withdrawal_amount', 'withdrawal_guardrail', 'roth_conversion']

for scenario_id in scenarios:
    context = WithdrawalContext(scenario_id, 'target_amount', config)
    runner = ScenarioRunner(context, portfolio_df, return_rate, workbook)
    
    runner.run_strategy()
    runner.export_all_to_folder(
        folder=f'results/{scenario_id}',
        include_summary=True,
        include_dashboard=True
    )
    print(f"✅ Completed {scenario_id}")
```

### Results Inspection
```python
# After running simulation
print(f"Years simulated: {len(runner.results)}")
print(f"Accounts tracked: {runner.results['account_name'].nunique()}")
print(f"Total withdrawals: ${runner.results['withdrawal_amount'].sum():,.0f}")

# Access spending breakdown
if hasattr(runner, 'spending_summary'):
    print("Spending by source:")
    print(runner.spending_summary.groupby('account_type')['amount'].sum())
```

## Integration Points

### Strategy Modules
- **`strategy_withdrawals.py`**: Single scenario execution
- **`strategy_montecarlo.py`**: Monte Carlo simulation engine
- **`analysis.py`**: Results analysis and summarization

### Data Sources
- **Portfolio data**: Account balances and metadata
- **Tax tables**: Extracted from Excel workbooks
- **Context configuration**: Simulation parameters and settings

### Output Destinations
- **Excel files**: Detailed tabular results
- **PDF reports**: Charts and visualizations
- **Summary logs**: Scenario comparison data
- **Dashboard exports**: Visualization-ready formats

## Error Handling

```python
# Check for results before analysis
if runner.results is None:
    raise ValueError('Run the simulation first.')

# Validate context configuration
if not runner.context.is_montecarlo and num_simulations > 1:
    print("Warning: Single scenario context with multiple simulations")

# Ensure required columns exist for export
if 'strategy' not in runner.results.columns:
    runner.results['strategy'] = runner.context.scenario_id
```

## Performance Considerations

- **Monte Carlo simulations** can be time-intensive with high iteration counts
- **Portfolio preparation** is optimized for repeated scenario runs
- **Memory usage** scales with simulation length and number of accounts
- **Export operations** benefit from SSD storage for large result sets

## Future Enhancements

- Parallel execution for Monte Carlo simulations
- Streaming results for very long simulations  
- Custom analysis plugins
- Interactive dashboard integration
- Scenario comparison utilities