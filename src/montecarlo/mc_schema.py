# ======================================================================
# MC OUTCOME LEDGER — SCHEMA CONSTANTS
# ======================================================================

MC_OUTCOME_SCHEMA_VERSION = "2025.05"

# --- 1. TEMPORAL & SIMULATION ID -------------------------------------

MC_OUTCOME_TEMPORAL_COLUMNS = [
    'year',
    'age',
    'sim_num',          # simulation index (0..N-1)
]

# --- 2. BALANCE COLUMNS ----------------------------------------------

MC_OUTCOME_BALANCE_COLUMNS = [
    'base_balance',     # starting balance for the year
    'end_balance',      # ending balance after MC return
]

# --- 3. INCOME & WITHDRAWAL-LIKE FLOWS -------------------------------

MC_OUTCOME_INCOME_COLUMNS = [
    'income_amount',    # sum of inc_* mc_amount
    'mc_amount',        # total MC withdrawal/spend for the year
    'mc_return_rate',   # return rate applied this year
]

# --- 4. GOAL / STATUS COLUMNS ----------------------------------------

MC_OUTCOME_GOAL_COLUMNS = [
    'goal_met',         # funding_total >= spending_target (legacy)
    'rmd_met',          # RMD satisfied (legacy)
    'shortfall_amount', # legacy shortfall logic
    'synthetic_flag',   # legacy synthetic rows
]

# --- 5. METADATA COLUMNS ---------------------------------------------

MC_OUTCOME_METADATA_COLUMNS = [
    'sim_type',         # always 'mc'
    'strategy_id',
    'sim_mode',
    'sim_rate',
    'mc_failure_flag',  # MC-only failure indicator
    'mc_percentile',    # percentile for aggregated MC results
    'schema_version',
]

# --- CONSOLIDATED MC OUTCOME SCHEMA ----------------------------------

MC_OUTCOME_SCHEMA_COLUMNS = (
    MC_OUTCOME_TEMPORAL_COLUMNS +
    MC_OUTCOME_BALANCE_COLUMNS +
    MC_OUTCOME_INCOME_COLUMNS +
    MC_OUTCOME_GOAL_COLUMNS +
    MC_OUTCOME_METADATA_COLUMNS
)

# ======================================================================
# MC OUTCOME LEDGER — SCHEMA DTYPES
# ======================================================================

MC_OUTCOME_TEMPORAL_DTYPES = {
    'year': 'Int64',
    'age': 'Int64',
    'sim_num': 'Int64',
}

MC_OUTCOME_BALANCE_DTYPES = {
    'base_balance': 'Float64',
    'end_balance': 'Float64',
}

MC_OUTCOME_INCOME_DTYPES = {
    'income_amount': 'Float64',
    'mc_amount': 'Float64',
    'mc_return_rate': 'Float64',
}

MC_OUTCOME_GOAL_DTYPES = {
    'goal_met': 'boolean',
    'rmd_met': 'boolean',
    'shortfall_amount': 'Float64',
    'synthetic_flag': 'boolean',
}

MC_OUTCOME_METADATA_DTYPES = {
    'sim_type': 'string',
    'strategy_id': 'string',
    'sim_mode': 'string',
    'sim_rate': 'Float64',
    'mc_failure_flag': 'boolean',
    'mc_percentile': 'Float64',
    'schema_version': 'string',
}

MC_OUTCOME_SCHEMA_DTYPES = {
    **MC_OUTCOME_TEMPORAL_DTYPES,
    **MC_OUTCOME_BALANCE_DTYPES,
    **MC_OUTCOME_INCOME_DTYPES,
    **MC_OUTCOME_GOAL_DTYPES,
    **MC_OUTCOME_METADATA_DTYPES,
}
