# AccountLedger Documentation

## Overview
The `AccountLedger` class tracks year-by-year financial data for individual retirement accounts during simulation scenarios. It maintains a detailed pandas DataFrame that captures all relevant financial metrics, tax calculations, and withdrawal information for each year of a retirement simulation.

## Class: AccountLedger

### Purpose
- Tracks one account's complete financial history across simulation years
- Stores detailed financial metrics including balances, withdrawals, taxes, and RMDs
- Provides structured data storage for retirement planning analysis
- Supports multiple withdrawal strategies and tax scenarios

### Key Features
- **Comprehensive Data Tracking**: Captures 25+ financial metrics per year
- **Tax Integration**: Tracks taxable income, gains, and effective tax rates
- **RMD Support**: Handles Required Minimum Distribution calculations
- **Withdrawal Flexibility**: Supports multiple withdrawal modes and strategies
- **Roth Conversion Tracking**: Records Roth conversion amounts and timing

### Data Schema

The ledger maintains the following columns in its DataFrame:

#### Core Identification
- `year`: Simulation year (int)
- `age`: Person's age in this year (int) 
- `account_name`: Name of the account being tracked (string)
- `scenario_id`: Unique identifier for this simulation scenario (string)
- `account_type`: Type of account (e.g., "401k", "IRA", "Taxable") (string)
- `account_tax_type`: Tax treatment ("pre-tax", "roth", "taxable") (string)

#### Financial Balances
- `begin_balance`: Account balance at start of year (float)
- `current_balance`: Account balance during year calculations (float)
- `end_balance`: Account balance at end of year (float)
- `return_rate`: Investment return rate applied this year (float)

#### Withdrawal and Distribution Data
- `withdrawal_amount`: Total amount withdrawn this year (float)
- `withdrawal_mode`: Strategy used for withdrawal (string)
- `omd`: Optimal Market Distribution amount (float)
- `rmd`: Required Minimum Distribution amount (float)
- `rmd_begin_year`: Year when RMDs start (int)
- `rmd_age`: Age when RMDs are calculated (int)
- `rmd_table`: RMD table used for calculations (string)

#### Income Sources
- `ord_inc`: Ordinary income from other sources (float)
- `ssa_inc`: Social Security income (float)

#### Tax Calculations
- `taxable_gain`: Capital gains subject to tax (float)
- `taxable_income`: Total taxable ordinary income (float)
- `taxable_ssa`: Portion of Social Security subject to tax (float)
- `tax_owed`: Total tax liability for the year (float)
- `effective_tax_rate`: Calculated effective tax rate (float)
- `filing_status`: Tax filing status (string)

#### Special Transactions
- `roth_convert_amount`: Amount converted from traditional to Roth (float)

## Methods

### `__init__()`
Initializes a new AccountLedger with an empty DataFrame containing all required columns with proper data types.

**Usage:**
```python
ledger = AccountLedger()
```

### `set_scenario(scenario_id)`
Sets the scenario identifier that will be applied to all future ledger entries.

**Parameters:**
- `scenario_id` (str): Unique identifier for the simulation scenario

**Usage:**
```python
ledger.set_scenario("baseline_scenario_001")
```

### `add_year(...)`
Adds a complete year's worth of financial data to the ledger.

**Parameters:**
All parameters have default values and are optional:

- `year` (int): Simulation year (default: 0)
- `age` (int): Person's age (default: 0)
- `return_rate` (float): Investment return rate (default: 0.0)
- `withdrawal_mode` (str): Withdrawal strategy used (default: 'unknown')
- `account_name` (str): Name of account (default: '')
- `begin_balance` (float): Starting balance (default: 0.0)
- `current_balance` (float): Current balance (default: 0.0)
- `end_balance` (float): Ending balance (default: 0.0)
- `withdraw_amount` (float): Amount withdrawn (default: 0.0)
- `omd` (float): Optimal Market Distribution (default: 0.0)
- `rmd` (float): Required Minimum Distribution (default: 0.0)
- `ord_inc` (float): Ordinary income (default: 0.0)
- `ssa_inc` (float): Social Security income (default: 0.0)
- `taxable_income` (float): Taxable ordinary income (default: 0.0)
- `taxable_gain` (float): Taxable capital gains (default: 0.0)
- `taxable_ssa` (float): Taxable Social Security (default: 0.0)
- `tax_owed` (float): Tax liability (default: 0.0)
- `effective_tax_rate` (float): Effective tax rate (default: 0.0)
- `roth_convert_amount` (float): Roth conversion amount (default: 0.0)
- `rmd_begin_year` (int): RMD start year (default: 0)
- `rmd_age` (int): RMD calculation age (default: 0)
- `rmd_table` (str): RMD table identifier (default: '')
- `account_type` (str): Account type (default: '')
- `account_tax_type` (str): Tax treatment type (default: '')
- `filing_status` (str): Tax filing status (default: '')

**Data Processing:**
- Automatically rounds monetary values to 2 decimal places
- Rounds effective tax rate to 3 decimal places
- Applies the current scenario_id to the entry
- Handles None values for optional string fields

**Usage:**
```python
ledger.add_year(
    year=2024,
    age=65,
    account_name="401k_primary",
    begin_balance=500000.00,
    end_balance=485000.00,
    withdraw_amount=40000.00,
    return_rate=0.07,
    withdrawal_mode="4_percent_rule",
    taxable_income=40000.00,
    tax_owed=6000.00,
    effective_tax_rate=0.150
)
```

## Data Access Patterns

### Accessing the DataFrame
```python
# Get the complete ledger
df = ledger.df_ledger

# Filter by specific years
recent_years = df[df['year'] >= 2024]

# Get specific metrics
withdrawals = df['withdrawal_amount']
balances = df[['begin_balance', 'end_balance']]
```

### Common Analysis Operations
```python
# Calculate total withdrawals
total_withdrawn = df['withdrawal_amount'].sum()

# Get final balance
final_balance = df['end_balance'].iloc[-1] if not df.empty else 0

# Calculate average effective tax rate
avg_tax_rate = df['effective_tax_rate'].mean()
```

## Integration Points

### With SimulationConfig
- Uses account configurations from SimulationConfig
- Applies withdrawal strategies defined in config
- Respects RMD rules and tax settings

### With Tax Models
- Receives calculated tax amounts and rates
- Stores detailed tax breakdowns
- Tracks filing status and tax-advantaged account types

### With Withdrawal Strategies
- Records which withdrawal mode was used each year
- Stores withdrawal amounts and distribution types
- Tracks special distributions like RMDs and conversions

## Example Workflow

```python
# Initialize ledger for a scenario
ledger = AccountLedger()
ledger.set_scenario("conservative_withdrawal")

# Simulate multiple years
for year in range(2024, 2044):
    # ... perform calculations ...
    
    ledger.add_year(
        year=year,
        age=base_age + (year - 2024),
        account_name="primary_401k",
        begin_balance=start_balance,
        end_balance=end_balance,
        withdraw_amount=withdrawal,
        return_rate=market_return,
        withdrawal_mode="bucket_strategy",
        tax_owed=calculated_tax,
        effective_tax_rate=tax_rate
    )

# Access results
final_ledger = ledger.df_ledger
```

## Notes
- All monetary values are automatically rounded to 2 decimal places for consistency
- The DataFrame grows dynamically as years are added
- Scenario ID is automatically applied to maintain data integrity
- Empty string defaults are used for optional string parameters
- The ledger maintains data type integrity through pandas Series type declarations