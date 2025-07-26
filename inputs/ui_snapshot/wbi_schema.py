WORKBOOK_TABS = [
    'My_Accounts', 'My_Income', 'My_Config',
    'T_AMT', 'T_CapitalGain', 'T_TaxBracket', 'T_StandardDeduction', 'T_LEF'
]

REQUIRED_COLUMNS = {
    'My_Accounts': {'account_name', 'account_type', 'begin_year', 'begin_balance', 'owner_birthdate_iso', 'filing_status'},
    'My_Income': {'account_name', 'account_type', 'begin_age', 'base_income', 'owner_birthdate_iso', 'filing_status'},
    'My_Config': {'parameter', 'value', 'scenario_default', 'montecarlo_default', 'comment'},
    'T_AMT': {'year', 'tax_type', 'low_single', 'high_single', 'low_married', 'high_married'},
    'T_CapitalGain': {'year', 'tax_type', 'tax_rate', 'single', 'married', 'head'},
    'T_TaxBracket': {'year', 'tax_type', 'tax_rate', 'low_single', 'high_single', 'low_married', 'high_married', 'low_head', 'high_head'},
    'T_StandardDeduction': {'year', 'tax_type', 'single', 'married', 'head'},
    'T_LEF': {'age', 'lef_2001', 'uniform_2001', 'lef_2002_2020', 'uniform_2002_2020', 'lef_2021_present', 'uniform_2021_present'},
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