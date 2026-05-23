'''Schema constants for Excel sheets and portfolio dataframes.'''
# ── Schema Constants - Excel Sheets ────────────────────────────────
ACCOUNT_SHEET_COLUMNS = [
    'account_name',
    'account_type',
    'account_balance',
    'owner_birthdate_iso',
    'filing_status',
    'prior_owner_birthdate_iso',
    'prior_owner_death_year',
    'beneficiary_birth_year',
]

ACCOUNT_SHEET_DTYPES = {
    'account_name': 'string',
    'account_type': 'string',
    'account_balance': 'Float64',
    'owner_birthdate_iso': 'string',
    'filing_status': 'string',
    'prior_owner_birthdate_iso': 'string',
    'prior_owner_death_year': 'Int64',
    'beneficiary_birth_year': 'Int64',
}

INCOME_SHEET_COLUMNS = [
    'income_name',
    'income_type',
    'income',
    'begin_age',
    'owner_birthdate_iso',
    'filing_status',
]

INCOME_SHEET_DTYPES = {
    'income_name': 'string',
    'income_type': 'string',
    'income': 'Float64',
    'begin_age': 'Int64',
    'owner_birthdate_iso': 'string',
    'filing_status': 'string',
}

EXCEL_CONDITIONAL_COLUMNS = {
    "My_Account": [
        {
            "if": {"account_type": "ira_inherited"},
            "then": {
                "prior_owner_birthdate_iso": "string",
                "prior_owner_death_year": "Int64",
                "beneficiary_birth_year": "Int64",
            }
        },
        {
            "if": {"account_type": "roth_inherited"},
            "then": {
                "prior_owner_death_year": "Int64",
            }
        }
    ],

    "My_Income": [
        {
            "if": {"income_type": "inc_ssa"},
            "then": {"begin_age": "Int64"},
        },
        {
            "if": {"income_type": "inc_fers"},
            "then": {"begin_age": "Int64"},
        },
        {
            "if": {"income_type": "inc_ord"},
            "then": {"begin_age": "Int64"},
        }
    ]
}

# ── Schema Constants - Portfolio DataFrame ────────────────────────────────

# 🧠 Portfolio Identity
PORTFOLIO_SOURCE_COLUMNS = [
    'source_name',
    'source_type',
    'source_tax_type',
    'filing_status',
]

# 💰 Financial State
PORTFOLIO_BALANCE_COLUMNS = [
    'base_balance',
]

# 👤 Ownership & Beneficiaries
PORTFOLIO_OWNER_COLUMNS = [
    'age',
    'owner_birthdate_iso',
    'prior_owner_death_year',
    'beneficiary_birth_year',
]

# 📅 Distribution Planning
PORTFOLIO_DISTRIBUTION_COLUMNS = [
    'distribution_year',
    'distribution_age',
    'distribution_table',
]

# 🧩 Consolidated Schema
PORTFOLIO_SCHEMA_COLUMNS = (
    PORTFOLIO_SOURCE_COLUMNS +
    PORTFOLIO_BALANCE_COLUMNS +
    PORTFOLIO_OWNER_COLUMNS +
    PORTFOLIO_DISTRIBUTION_COLUMNS
)

PORTFOLIO_SCHEMA_DTYPES = {
    # Source Identity
    'source_name': 'string',
    'source_type': 'string',
    'source_tax_type': 'string',
    'filing_status': 'string',

    # Financial State
    'base_balance': 'Float64',

    # Ownership & Beneficiaries
    'age': 'Int64',
    'owner_birthdate_iso': 'string',
    'prior_owner_death_year': 'Int64',
    'beneficiary_birth_year': 'Int64',

    # Distribution Planning
    'distribution_year': 'Int64',
    'distribution_age': 'Int64',
    'distribution_table': 'string',
}

PORTFOLIO_SCHEMA_GROUPS = {
    "source": PORTFOLIO_SOURCE_COLUMNS,
    "balance": PORTFOLIO_BALANCE_COLUMNS,
    "owner": PORTFOLIO_OWNER_COLUMNS,
    "distribution": PORTFOLIO_DISTRIBUTION_COLUMNS
}
