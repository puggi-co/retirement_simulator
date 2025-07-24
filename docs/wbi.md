# WorkbookInterface Documentation

## Overview
The `WorkbookInterface` class serves as the primary data loading and management component for the retirement planning tool. It reads user input from Excel workbooks, processes tax tables, and exposes structured DataFrames through a centralized accessor registry. This class acts as the bridge between raw Excel data and the simulation engine.

## Class: WorkbookInterface

### Purpose
- Load and validate user portfolio and configuration data from Excel
- Process multiple tax tables and reference data
- Provide standardized data access through a registry pattern
- Handle data cleaning and type conversion
- Generate simulation schedules based on user inputs

### Key Features
- **Excel Integration**: Reads multiple worksheets from a single Excel workbook
- **Data Validation**: Validates required columns and handles missing data
- **Registry Pattern**: Centralized access to all loaded data through named accessors
- **Configuration Management**: Splits configuration data into simulation-specific objects
- **Schedule Generation**: Creates simulation timing parameters automatically
- **Flexible Data Sources**: Supports Excel, JSON, and hardcoded scenario data

## Constructor

### `__init__(workbook='RetirementPlan-Input.xlsx')`
Initializes the WorkbookInterface with an Excel workbook path and sets up the data structure.

**Parameters:**
- `workbook` (str): Path to the Excel workbook file (default: 'RetirementPlan-Input.xlsx')

**Initialized Attributes:**
- `workbook`: Path to Excel file
- `tabs`: List of worksheet tabs to process
- `df_my_portfolio`: Combined portfolio and income data
- `df_scenario`: Scenario configuration data
- `config`: Main simulation configuration
- Tax table DataFrames: `df_amt`, `df_capital_gain`, `df_standard_deduction`, `df_tax_brackets`, `df_lef_factors`

**Usage:**
```python
wbi = WorkbookInterface('MyRetirementPlan.xlsx')
wbi = WorkbookInterface()  # Uses default workbook name
```

## Registry System

### Accessor Registry
The class uses a registry pattern to provide standardized access to all loaded data:

**Available Accessors:**
- `'porfolio'`: Returns `df_my_portfolio` (combined account and income data)
- `'scenario'`: Returns `df_scenario` (scenario configurations)
- `'schedule'`: Returns `sim_schedule` (simulation timing parameters)
- `'config'`: Returns main `SimulationConfig` object
- `'scenario_config'`: Returns scenario-specific config
- `'montecarlo_config'`: Returns Monte Carlo-specific config
- `'amt'`: Returns Alternative Minimum Tax table
- `'capital_gain'`: Returns capital gains tax table
- `'lef'`: Returns Life Expectancy Factor table
- `'standard_deduction'`: Returns standard deduction table
- `'tax_bracket'`: Returns tax bracket table

### `get(name)`
Retrieves data through the registry system.

**Parameters:**
- `name` (str): Accessor name from the registry

**Returns:**
- Data object corresponding to the accessor name

**Raises:**
- `KeyError`: If accessor name is not found

**Usage:**
```python
portfolio = wbi.get('porfolio')
config = wbi.get('config')
tax_brackets = wbi.get('tax_bracket')
```

## Data Loading Methods

### `load_workbook()`
Main method that orchestrates loading and processing of all Excel worksheets.

**Process Flow:**
1. Reads each worksheet tab defined in `WORKBOOK_TABS`
2. Cleans and validates each sheet using `clean_sheet()`
3. Assigns processed data to appropriate instance attributes
4. Merges account and income data into portfolio
5. Loads scenario configurations
6. Splits configuration data into typed objects
7. Generates simulation schedule

**Processed Worksheets:**
- `'My_Accounts'`: User account information
- `'My_Income'`: Income source data
- `'My_Config'`: Configuration parameters
- `'T_AMT'`: Alternative Minimum Tax table
- `'T_CapitalGain'`: Capital gains tax rates
- `'T_TaxBrackets'`: Federal tax brackets
- `'T_StandardDeduction'`: Standard deduction amounts
- `'T_LEF'`: Life Expectancy Factors for RMD calculations

**Usage:**
```python
wbi = WorkbookInterface()
wbi.load_workbook()  # Loads and processes all data
```

### `load_scenarios(source=None)`
Loads scenario configuration data from various sources.

**Parameters:**
- `source` (str, optional): Data source specification
  - `None`: Uses hardcoded `SCENARIO_DATA`
  - `.json` extension: Loads from JSON file
  - Other: Loads from Excel worksheet 'My Scenarios'

**Returns:**
- `DataFrame`: Cleaned scenario configuration data

**Usage:**
```python
# Load from default hardcoded data
scenarios = wbi.load_scenarios()

# Load from JSON file
scenarios = wbi.load_scenarios('custom_scenarios.json')

# Load from Excel worksheet
scenarios = wbi.load_scenarios('workbook')
```

### `clean_sheet(df, required_cols=None, sheet_name='')`
Standardizes DataFrame formatting and validates required columns.

**Parameters:**
- `df` (DataFrame): Raw DataFrame to clean
- `required_cols` (set, optional): Set of required column names
- `sheet_name` (str): Name of the worksheet for error reporting

**Processing Steps:**
1. Standardizes column names (strip whitespace, replace spaces with underscores, lowercase)
2. Validates presence of required columns
3. Warns about potential conflicts with pandas reserved attributes
4. Returns cleaned DataFrame

**Usage:**
```python
cleaned_df = wbi.clean_sheet(raw_df, {'account_name', 'balance'}, 'My_Accounts')
```

## Configuration Processing

### `split_config(config_df)`
Processes configuration DataFrame and creates typed configuration objects.

**Parameters:**
- `config_df` (DataFrame): Raw configuration data with parameter/value pairs

**Process:**
1. Normalizes boolean flags (`scenario_default`, `montecarlo_default`)
2. Creates default `SimulationConfig` for fallback values
3. Applies type conversion based on default values
4. Generates three configuration objects

**Returns:**
- `tuple`: (main_config, scenario_config, montecarlo_config)
  - `main_config`: Complete configuration object
  - `scenario_config`: Configuration for scenario-flagged parameters
  - `montecarlo_config`: Configuration for Monte Carlo-flagged parameters

**Type Conversion Logic:**
- **Boolean**: Converts strings like "true", "yes", "1", "y" to `True`
- **Integer**: Converts numeric values to int
- **Float**: Converts numeric values to float
- **String**: Converts to string representation
- **Missing Values**: Uses defaults from `SimulationConfig`

**Usage:**
```python
config, scenario_config, mc_config = wbi.split_config(config_df)
```

## Schedule Generation

### `sim_schedule(df_my_account, inflation_rate=DEFAULT_INFLATION, max_age=120)`
Generates simulation timing parameters based on account data.

**Parameters:**
- `df_my_account` (DataFrame): Account data containing age and year information
- `inflation_rate` (float): Annual inflation rate (default: `DEFAULT_INFLATION`)
- `max_age` (int): Maximum simulation age (default: 120)

**Calculation Logic:**
- `begin_year`: Minimum begin year from accounts
- `begin_age`: Minimum owner age from accounts
- `duration`: `max_age - begin_age`
- `end_year`: `begin_year + duration - 1`
- `end_age`: `begin_age + duration`

**Returns:**
- `SimulationSchedule`: Object containing timing parameters

**Usage:**
```python
schedule = wbi.sim_schedule(df_accounts, inflation_rate=0.025)
```

### `build_schedule(schedule_dict)` (Static Method)
Creates a `SimulationSchedule` object from a dictionary.

**Parameters:**
- `schedule_dict` (dict): Dictionary with schedule parameters

**Required Keys:**
- `begin_age`, `begin_year`, `duration`, `end_age`, `end_year`

**Returns:**
- `SimulationSchedule`: Typed schedule object

**Usage:**
```python
schedule_data = {
    'begin_age': 65,
    'begin_year': 2024,
    'duration': 30,
    'end_age': 95,
    'end_year': 2054
}
schedule = WorkbookInterface.build_schedule(schedule_data)
```

## Utility Methods

### `FUTURE_convert_excel_to_json(workbook_path, sheet_name='My Scenarios', output_path='MyScenarios.json')`
Planned utility method to convert Excel worksheets to JSON format.

**Parameters:**
- `workbook_path` (str): Path to Excel workbook
- `sheet_name` (str): Worksheet name to convert
- `output_path` (str): Output JSON file path

## Data Integration Patterns

### Portfolio Data Assembly
```python
# Load workbook data
wbi = WorkbookInterface()
wbi.load_workbook()

# Access assembled portfolio data
portfolio = wbi.get('porfolio')  # Combined accounts + income
accounts_only = wbi.df_my_account  # Direct account data
```

### Configuration Access
```python
# Get different configuration levels
main_config = wbi.get('config')           # Full configuration
scenario_config = wbi.get('scenario_config')  # Scenario defaults
mc_config = wbi.get('montecarlo_config')      # Monte Carlo defaults
```

### Tax Table Access
```python
# Access tax calculation tables
tax_brackets = wbi.get('tax_bracket')
capital_gains = wbi.get('capital_gain')
standard_ded = wbi.get('standard_deduction')
```

## Error Handling

### Common Exceptions
- **`RuntimeError`**: Excel file loading failures
- **`ValueError`**: Missing required columns in worksheets
- **`KeyError`**: Invalid accessor names in registry

### Validation Features
- **Column Requirements**: Validates required columns per worksheet
- **Reserved Names**: Warns about pandas attribute conflicts
- **Type Safety**: Handles missing values and type conversion errors

## Example Workflow

```python
# Initialize and load all data
wbi = WorkbookInterface('RetirementPlan-Input.xlsx')
wbi.load_workbook()

# Access different data types
portfolio = wbi.get('porfolio')
config = wbi.get('config')
schedule = wbi.get('schedule')
scenarios = wbi.get('scenario')

# Use in simulation
simulator = RetirementSimulator(
    portfolio=portfolio,
    config=config,
    schedule=schedule,
    scenarios=scenarios
)
```

## Dependencies

### Required External Data
- `WORKBOOK_TABS`: List of worksheet names to process
- `REQUIRED_COLUMNS`: Dictionary mapping worksheets to required columns
- `SCENARIO_DATA`: Default scenario configuration data
- `DEFAULT_INFLATION`: Default inflation rate constant

### Integration Classes
- `SimulationConfig`: Configuration data class
- `SimulationSchedule`: Schedule timing data class
- `merge_income_sources()`: Function to combine account and income data

## Notes
- The registry pattern provides consistent data access across the application
- Configuration splitting allows different parameter sets for various simulation types
- Data cleaning standardizes column names and handles Excel formatting inconsistencies
- Schedule generation automates timing calculations based on user age and target retirement duration
- Type conversion in configuration processing maintains data integrity while handling Excel's mixed data types