WORKBOOK_TABS = [
    'My_Accounts', 'My_Income', 'My_Config'

]

REQUIRED_COLUMNS = {
    'My_Accounts': {'account_name', 'account_type', 'begin_year', 'begin_balance', 'owner_birthdate_iso', 'filing_status'},
    'My_Income': {'account_name', 'account_type', 'begin_age', 'base_income', 'owner_birthdate_iso', 'filing_status'},
    'My_Config': {'parameter', 'value', 'scenario_default', 'montecarlo_default', 'comment'},
    'my_scenarios': {'scenario_id', 'montecarlo_id', 'scenario_name', 'withdrawal_mode', 'scenario_description', 'include_dashboard'}
}

CONDITIONAL_REQUIRED_COLUMNS = {
    'My_Accounts': [
        {
            'if': {'account_type': 'ira-inherited'},
            'then': {'prior_owner_birthdate_iso', 'prior_owner_death_year', 'beneficiary_birth_year'}
        }
    ]
}

OPTIONAL_COLUMNS = {
    'My Config': {'scenario_default', 'montecarlo_default', 'comment'},
}