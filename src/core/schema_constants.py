'''Defines static schema expectations (columns, dtypes) for each surface.'''

# ── Schema Constants - Excel Sheets ────────────────────────────────
ACCOUNT_SHEET_COLUMNS = [
    'account_name',
    'account_type',
    'account_balance',
    'owner_birthdate_iso',
    'filing_status',
    'prior_owner_birthdate_iso',
    'prior_owner_death_year',
    'beneficiary_birth_year'
]

ACCOUNT_SHEET_DTYPES = {
    'account_name': 'string',
    'account_type': 'string',
    'account_balance': 'Float64',
    'owner_birthdate_iso': 'string',
    'filing_status': 'string',
    'prior_owner_birthdate_iso': 'string',
    'prior_owner_death_year': 'Int64',
    'beneficiary_birth_year': 'Int64'
}

INCOME_SHEET_COLUMNS = [
    'income_name',
    'income_type',
    'income',
    'begin_age',
    'owner_birthdate_iso',
    'filing_status'
]

INCOME_SHEET_DTYPES = {
    'income_name': 'string',
    'income_type': 'string',
    'income': 'Float64',
    'begin_age': 'Int64',
    'owner_birthdate_iso': 'string',
    'filing_status': 'string'
}

# ── Consolidated Account and Income Streams - Base Portfolio Post-Enrichment Schema Constants ────────────────────────────────

# 🧠 Account Identity
PORTFOLIO_ACCOUNT_COLUMNS = [
    'account_name',
    'account_type',
    'account_tax_type',
    'filing_status'
]

# 💰 Financial State
PORTFOLIO_BALANCE_COLUMNS = [
    'base_balance'
]

# 👤 Ownership & Beneficiaries
PORTFOLIO_OWNER_COLUMNS = [
    'owner_age',
    'owner_birthdate_iso',
    'prior_owner_death_year',
    'beneficiary_birth_year'
]

# 📅 Distribution Planning
PORTFOLIO_DISTRIBUTION_COLUMNS = [
    'distribution_year',
    'distribution_age',
    'distribution_table'
]

# 🧩 Consolidated Schema
PORTFOLIO_SCHEMA_COLUMNS = (
    PORTFOLIO_ACCOUNT_COLUMNS +
    PORTFOLIO_BALANCE_COLUMNS +
    PORTFOLIO_OWNER_COLUMNS +
    PORTFOLIO_DISTRIBUTION_COLUMNS
)

PORTFOLIO_SCHEMA_DTYPES = {
    # Account Identity
    'account_name': 'string',
    'account_type': 'string',
    'account_tax_type': 'string',
    'filing_status': 'string',

    # Financial State
    'base_balance': 'Float64',

    # Ownership & Beneficiaries
    'owner_age': 'Int64',
    'owner_birthdate_iso': 'string',
    'prior_owner_death_year': 'Int64',
    'beneficiary_birth_year': 'Int64',

    # Distribution Planning
    'distribution_year': 'Int64',
    'distribution_age': 'Int64',
    'distribution_table': 'string'
}

PORTFOLIO_SCHEMA_GROUPS = {
    "account": PORTFOLIO_ACCOUNT_COLUMNS,
    "balance": PORTFOLIO_BALANCE_COLUMNS,
    "owner": PORTFOLIO_OWNER_COLUMNS,
    "distribution": PORTFOLIO_DISTRIBUTION_COLUMNS
}

# ── Withdrawal Ledger - Schema Constants ────────────────────────────────
WD_LEDGER_TEMPORAL_COLUMNS = [
    'year', 'age'
]
WD_LEDGER_METADATA_COLUMNS = [
    'sim_id', 'sim_type', 'sim_mode', 'return_rate', 'inflation_rate',
    'spending_target', 'withdrawal_rate'
]
WD_LEDGER_FINANCIAL_COLUMNS = [
    'base_balance', 'current_balance', 'end_balance',
    'wd_amount', 'wd_type', 'wd_tax_type', 'wd_indicator', 'closure_met',
    'withdrawal_efficiency'
]
WD_LEDGER_TAX_COLUMNS = [
    'taxable_income', 'taxable_gain'
]
WD_LEDGER_ACCOUNT_COLUMNS = [
    'account_name', 'account_type', 'account_tax_type', 'filing_status',
    'owner_age', 'distribution_year', 'distribution_age', 'distribution_table'
]
WD_LEDGER_OVERRIDE_COLUMNS = [
    # Guardrails
    'guardrail_triggered', 'guardrail_direction', 'guardrail_type',
    'guardrail_rate_high', 'guardrail_rate_low',
    'guardrail_amount_high', 'guardrail_amount_low',
    # Shortfalls
    'synthetic_flag', 'shortfall_flag', 'shortfall_amount'
]

# Withdrawal Ledger - Consolidated schema for withdrawal transactions
WD_LEDGER_SCHEMA_COLUMNS = (
    WD_LEDGER_TEMPORAL_COLUMNS +
    WD_LEDGER_METADATA_COLUMNS +
    WD_LEDGER_FINANCIAL_COLUMNS +
    WD_LEDGER_TAX_COLUMNS +
    WD_LEDGER_ACCOUNT_COLUMNS +
    WD_LEDGER_OVERRIDE_COLUMNS
)

# Withdrawal Ledger - Expected dtypes for each column
WD_LEDGER_SCHEMA_DTYPES = {
    # 📅 Temporal Alignment
    'year': 'Int64', 'age': 'Int64',

    # 🧠 Simulation Metadata
    'sim_id': 'string', 'sim_type': 'string', 'sim_mode': 'string',
    'return_rate': 'Float64', 'inflation_rate': 'Float64',
    'spending_target': 'Float64', 'withdrawal_rate': 'Float64',

    # 💰 Financial Metrics
    'base_balance': 'Float64', 'current_balance': 'Float64', 'end_balance': 'Float64',
    'wd_amount': 'Float64', 'wd_type': 'string', 'wd_tax_type': 'string',
    'wd_indicator': 'bool', 'closure_met': 'bool',
    'withdrawal_efficiency': 'Float64',

    # 💰 Taxation
    'taxable_income': 'Float64', 'taxable_gain': 'Float64',

    # 🏦 Account Attribution
    'account_name': 'string', 'account_type': 'string', 'account_tax_type': 'string',
    'filing_status': 'string', 'owner_age': 'Int64',
    'distribution_year': 'Int64', 'distribution_age': 'Int64',
    'distribution_table': 'string',

    # 🛠 Simulation Overrides (Guardrails + Shortfalls)
    'guardrail_triggered': 'bool', 'guardrail_direction': 'string', 'guardrail_type': 'string',
    'guardrail_rate_high': 'Float64', 'guardrail_rate_low': 'Float64',
    'guardrail_amount_high': 'Float64', 'guardrail_amount_low': 'Float64',
    # Shortfalls
    'synthetic_flag': 'bool', 'shortfall_flag': 'bool', 'shortfall_amount': 'Float64'
}

WD_LEDGER_SCHEMA_GROUPS = {
    'temporal': WD_LEDGER_TEMPORAL_COLUMNS,
    'metadata': WD_LEDGER_METADATA_COLUMNS,
    'financial': WD_LEDGER_FINANCIAL_COLUMNS,
    'taxation': WD_LEDGER_TAX_COLUMNS,
    'account': WD_LEDGER_ACCOUNT_COLUMNS,
    'override': WD_LEDGER_OVERRIDE_COLUMNS
}

# ── Outcome Ledger Schema ───────────────────────────────

OUTCOME_TEMPORAL_COLUMNS = [
    'year', 'age'
]
OUTCOME_BALANCE_COLUMNS = [
    'base_balance', 'income_amount', 'wd_amount', 'actual_rate'
]
OUTCOME_GOAL_COLUMNS = [
    'spending_target', 'funding_total', 'funding_delta',
    'shortfall_amount', 'closure_met', 'goal_met', 'rmd_met', 'synthetic_flag'
]
OUTCOME_SIMULATION_COLUMNS = [
    'sim_type', 'sim_mode', 'sim_id', 'sim_rate',
    'mc_failure_flag', 'mc_percentile'
]

# Outcome Ledger - Consolidated schema for simulation outcomes
OUTCOME_SCHEMA_COLUMNS = (
    OUTCOME_TEMPORAL_COLUMNS +
    OUTCOME_BALANCE_COLUMNS +
    OUTCOME_GOAL_COLUMNS +
    OUTCOME_SIMULATION_COLUMNS
)

OUTCOME_SCHEMA_DTYPES = {
    # Temporal
    'year': 'Int64', 'age': 'Int64',

    # Account State
    'base_balance': 'Float64', 'income_amount': 'Float64',
    'wd_amount': 'Float64', 'actual_rate': 'Float64',

    # Goal Funding
    'spending_target': 'Float64', 'funding_total': 'Float64', 'funding_delta': 'Float64',
    'shortfall_amount': 'Float64', 'closure_met': 'bool',
    'goal_met': 'bool', 'rmd_met': 'bool', 'synthetic_flag': 'bool',

    # Simulation Metadata
    'sim_type': 'string', 'sim_mode': 'string', 'sim_id': 'string',
    'sim_rate': 'Float64', 'mc_failure_flag': 'bool', 'mc_percentile': 'Float64'
}

OUTCOME_SCHEMA_GROUPS = {
    'temporal': OUTCOME_TEMPORAL_COLUMNS,
    'balance': OUTCOME_BALANCE_COLUMNS,
    'goal': OUTCOME_GOAL_COLUMNS,
    'simulation': OUTCOME_SIMULATION_COLUMNS
}
