'''Schema constants for the withdrawal ledgers.'''

# ======================================================================
# WITHDRAWAL LEDGER — SCHEMA CONSTANTS
# ======================================================================

WD_LEDGER_SCHEMA_VERSION = "2025.05"

WD_LEDGER_TEMPORAL_COLUMNS = [
    'year', 'age',
]

WD_LEDGER_BALANCE_COLUMNS = [
    'base_balance', 'current_balance', 'end_balance',
]

WD_LEDGER_WITHDRAWAL_COLUMNS = [
    'wd_amount', 'wd_type',
]

WD_LEDGER_TAX_COLUMNS = [
    'taxable_income', 'taxable_gain', 'marginal_rate',
]

WD_LEDGER_SOURCE_COLUMNS = [
    'source_name', 'source_type', 'source_tax_type', 'filing_status',
]

WD_LEDGER_DISTRIBUTION_COLUMNS = [
    'distribution_year', 'distribution_age', 'distribution_table',
]

WD_LEDGER_OUTCOME_COLUMNS = [
    'closure_met', 'guardrail_triggered', 'guardrail_direction',
]

WD_LEDGER_METADATA_COLUMNS = [
    'strategy_id', 'sim_mode', 'sim_type',
    'return_rate', 'spending_target',
    'schema_version',
]

# --- CONSOLIDATED WD LEDGER SCHEMA -----------------------------------

WD_LEDGER_SCHEMA_COLUMNS = (
    WD_LEDGER_TEMPORAL_COLUMNS +
    WD_LEDGER_BALANCE_COLUMNS +
    WD_LEDGER_WITHDRAWAL_COLUMNS +
    WD_LEDGER_TAX_COLUMNS +
    WD_LEDGER_SOURCE_COLUMNS +
    WD_LEDGER_DISTRIBUTION_COLUMNS +
    WD_LEDGER_OUTCOME_COLUMNS +
    WD_LEDGER_METADATA_COLUMNS
)

# ======================================================================
# WITHDRAWAL LEDGER — SCHEMA CONSTANT DTYPES
# ======================================================================

WD_LEDGER_TEMPORAL_DTYPES = {
    'year': 'Int64',
    'age': 'Int64',
}

WD_LEDGER_BALANCE_DTYPES = {
    'base_balance': 'Float64',
    'current_balance': 'Float64',
    'end_balance': 'Float64',
}

WD_LEDGER_WITHDRAWAL_DTYPES = {
    'wd_amount': 'Float64',
    'wd_type': 'string',
}

WD_LEDGER_TAX_DTYPES = {
    'taxable_income': 'Float64',
    'taxable_gain': 'Float64',
    'marginal_rate': 'Float64',
}

WD_LEDGER_SOURCE_DTYPES = {
    'source_name': 'string',
    'source_type': 'string',        # ira, roth, taxable, inherited_ira
    'source_tax_type': 'string',    # ordinary, qualified, tax_free
    'filing_status': 'string',      # single, mfj, hoh
}

WD_LEDGER_DISTRIBUTION_DTYPES = {
    'distribution_year': 'Int64',
    'distribution_age': 'Int64',
    'distribution_table': 'string',  # uniform, single_life, inherited
}

WD_LEDGER_OUTCOME_DTYPES = {
    'closure_met': 'boolean',
    'guardrail_triggered': 'boolean',
    'guardrail_direction': 'string',  # 'upward', 'downward', or None
}

WD_LEDGER_METADATA_DTYPES = {
    'strategy_id': 'string',
    'sim_mode': 'string',
    'sim_type': 'string',
    'return_rate': 'Float64',
    'spending_target': 'Float64',
    'schema_version': 'string',
}

WD_LEDGER_SCHEMA_DTYPES = {
    **WD_LEDGER_TEMPORAL_DTYPES,
    **WD_LEDGER_BALANCE_DTYPES,
    **WD_LEDGER_WITHDRAWAL_DTYPES,
    **WD_LEDGER_TAX_DTYPES,
    **WD_LEDGER_SOURCE_DTYPES,
    **WD_LEDGER_DISTRIBUTION_DTYPES,
    **WD_LEDGER_OUTCOME_DTYPES,
    **WD_LEDGER_METADATA_DTYPES,
}

# ======================================================================
# OUTCOME LEDGER — SCHEMA CONSTANTS
# ======================================================================

WD_OUTCOME_SCHEMA_VERSION = "2025.05"

WD_OUTCOME_TEMPORAL_COLUMNS = [
    'year',
    'age',
]

WD_OUTCOME_BALANCE_COLUMNS = [
    'base_balance',   # sum of WD ledger base_balance for the year
    'end_balance',    # final portfolio balance (WD mode only)
]

WD_OUTCOME_INCOME_COLUMNS = [
    'income_amount',        # sum of inc_* wd_amount
    'portfolio_amount',     # total discretionary + RMD withdrawals
    'portfolio_rate',       # wd_amount / base_balance
]

WD_OUTCOME_FUNDING_COLUMNS = [
    'spending_target',
    'portfolio_funding_total',  # income_amount + portfolio_amount
    'portfolio_funding_delta',  # portfolio_funding_total - spending_target
]

WD_OUTCOME_GOAL_COLUMNS = [
    'goal_met',        # portfolio_funding_total >= spending_target
    'closure_met',     # any account closed this year
    'rmd_met',         # all RMDs satisfied this year
]


WD_OUTCOME_METADATA_COLUMNS = [
    'strategy_id',
    'sim_mode',
    'sim_type',
    'sim_rate',
    'schema_version',
]

WD_OUTCOME_SCHEMA_COLUMNS = (
    WD_OUTCOME_TEMPORAL_COLUMNS +
    WD_OUTCOME_BALANCE_COLUMNS +
    WD_OUTCOME_INCOME_COLUMNS +
    WD_OUTCOME_FUNDING_COLUMNS +
    WD_OUTCOME_GOAL_COLUMNS +
    WD_OUTCOME_METADATA_COLUMNS
)

# ======================================================================
# OUTCOME LEDGER — SCHEMA CONSTANTS DTYPES
# ======================================================================

WD_OUTCOME_TEMPORAL_DTYPES = {
    'year': 'Int64',
    'age': 'Int64',
}

WD_OUTCOME_BALANCE_DTYPES = {
    'base_balance': 'Float64',
    'end_balance': 'Float64',
}

WD_OUTCOME_INCOME_DTYPES = {
    'income_amount': 'Float64',
    'portfolio_amount': 'Float64',
    'portfolio_rate': 'Float64',
}

WD_OUTCOME_FUNDING_DTYPES = {
    'spending_target': 'Float64',
    'portfolio_funding_total': 'Float64',
    'portfolio_funding_delta': 'Float64',
}

WD_OUTCOME_GOAL_DTYPES = {
    'goal_met': 'boolean',
    'closure_met': 'boolean',
    'rmd_met': 'boolean',
}

WD_OUTCOME_METADATA_DTYPES = {
    'strategy_id': 'string',
    'sim_mode': 'string',
    'sim_type': 'string',
    'sim_rate': 'Float64',
    'schema_version': 'string',
}

WD_OUTCOME_SCHEMA_DTYPES = {
    **WD_OUTCOME_TEMPORAL_DTYPES,
    **WD_OUTCOME_BALANCE_DTYPES,
    **WD_OUTCOME_INCOME_DTYPES,
    **WD_OUTCOME_FUNDING_DTYPES,
    **WD_OUTCOME_GOAL_DTYPES,
    **WD_OUTCOME_METADATA_DTYPES,
}
