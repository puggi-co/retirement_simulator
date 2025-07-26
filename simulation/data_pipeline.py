# Data Preparation and Transformation

def merge_income_sources(df_my_account, df_my_income):
    """Add income sources into portfolio dataframe; add placehoder columns for scenario simulations"""

    # Define lookup of tax type by account type
    account_type_lkup = pd.DataFrame({
            'account_type': ['brokerage', 'ira', 'ira_inherited', 'tsp', 'roth_ira', 'roth_ira_inherited', 'fers_income', 'ordinary_income', 'ssa_income'],
            'account_tax_type': ['taxable', 'deferred', 'deferred', 'deferred', 'tax_free', 'tax_free', 'taxable', 'taxable', 'tax_ssa']
            })

    my_income_df = df_my_income.copy()
    my_account_df = df_my_account.copy()
    
    # Ensure consistent columns names before combining dataframes
    my_account_df['rmd_age'] = 0
    my_income_df['begin_year'] = my_account_df['begin_year'].min()
    my_income_df = my_income_df.rename(columns={
        'base_income': 'begin_balance', 'begin_age' : 'rmd_age'
    })

    # Add income sources into portfolio 
    my_account_df = pd.concat([my_account_df, my_income_df], ignore_index=True)
    
    # Keep accounts with a positive balance
    my_account_df = my_account_df[my_account_df['begin_balance'] > 0].copy()

    my_account_df['prior_owner_death_year'] = pd.to_numeric(my_account_df['prior_owner_death_year'], errors='coerce').astype('Int64')
    my_account_df['beneficiary_birth_year'] = pd.to_numeric(my_account_df['beneficiary_birth_year'], errors='coerce').astype('Int64')

    # Separate out integer and string columns before replacing NaNs
    int_cols = my_account_df.select_dtypes(include='number').columns
    str_cols = my_account_df.select_dtypes(include='object').columns  # for string-type columns
    my_account_df[int_cols] = my_account_df[int_cols].fillna(0)
    my_account_df[str_cols] = my_account_df[str_cols].fillna('')

    # Normalize filing_status strings
    my_account_df['filing_status'] = (
        my_account_df['filing_status']
        .str.strip()
        .str.lower()
    )

    # Define acceptable values
    valid_statuses = {'single', 'married', 'head'}

    # Flag invalid entries (optional)
    invalid_mask = ~my_account_df['filing_status'].isin(valid_statuses)
    if invalid_mask.any():
        print("⚠️ Invalid filing_status entries found:")
        print(my_account_df.loc[invalid_mask, 'filing_status'])
        # Optionally: raise an error or assign 'unknown'
        my_account_df.loc[invalid_mask, 'filing_status'] = 'unknown'

    # Add and populate column for account_tax_type
    my_account_df = my_account_df.merge(account_type_lkup, on='account_type', how='left')

    # Add placeholders to manage withdraws such as required and optional distribution, and account minimum balance)
    my_account_df['owner_birth_date'] = datetime.now().date
    my_account_df['rmd_table'] = ''
    my_account_df[['owner_age', 'rmd_begin_year']] = 0
    
    for adx, account in my_account_df.iterrows():
        owner_birth_date = datetime.strptime(account['owner_birthdate_iso'], '%Y-%m-%d').date()
        owner_birth_year = owner_birth_date.year
        owner_age = calculate_age(owner_birth_year, account['begin_year'])

        rmd_info = calculate_rmd_fields(account)

        my_account_df.loc[adx, 'owner_birth_date'] = owner_birth_date
        my_account_df.loc[adx, 'owner_age'] = owner_age
        my_account_df.loc[adx, 'rmd_table'] = rmd_info['rmd_table']
        my_account_df.loc[adx, 'rmd_age'] = rmd_info['rmd_age']
        my_account_df.loc[adx, 'rmd_begin_year'] = rmd_info['rmd_begin_year']

     # Return portfolio dataframe with columns in the preferred order
    df_my_portfolio = my_account_df[[
        'account_name', 'account_type', 'account_tax_type', 'begin_year', 'begin_balance', 
        'owner_birth_date', 'owner_age', 'filing_status', 'prior_owner_death_year', 'beneficiary_birth_year', 
        'rmd_begin_year', 'rmd_age', 'rmd_table'
    ]]
    
    return df_my_portfolio

def calculate_rmd_fields(account: pd.Series) -> dict:
    account_type = account['account_type']

    if account_type == 'ira_inherited':
        return handle_inherited_ira(account)
    elif account_type in ('ira', 'tsp'):
        return handle_standard_ira(account)
    elif account_type == 'brokerage':
        return handle_brokerage(account)
    elif account_type in ('fers_income', 'ordinary_income', 'ssa_income'):
        return handle_income_stream(account)
    else:
        return handle_unknown(account)

def handle_inherited_ira(account: pd.Series) -> dict:
    begin_year = account['begin_year']
    owner_birth_year = datetime.strptime(account['owner_birthdate_iso'], '%Y-%m-%d').year
    prior_owner_birth_year = datetime.strptime(account['prior_owner_birthdate_iso'], '%Y-%m-%d').year
    prior_owner_death_year = account['prior_owner_death_year']
    beneficiary_birth_year = account['beneficiary_birth_year']

    rmd_age, rmd_begin_year = get_rmd_age(datetime(prior_owner_birth_year, 1, 1))

    if rmd_begin_year < prior_owner_death_year:
        rmd_age = prior_owner_death_year - owner_birth_year
        if prior_owner_death_year >= 2021:
            rmd_table = 'lef_2021_present'
        elif prior_owner_death_year <= 2001:
            rmd_table = 'lef_2001'
        else:
            rmd_table = 'lef_2002_2020'
    else:
        rmd_age = begin_year - beneficiary_birth_year
        rmd_table = 'uniform_2021_present'

    return {
        'rmd_age': rmd_age,
        'rmd_begin_year': rmd_begin_year,
        'rmd_table': rmd_table
    }

def handle_standard_ira(account: pd.Series) -> dict:
    """Handle standard IRA or TSP accounts."""
    owner_birth_date = datetime.strptime(account['owner_birthdate_iso'], '%Y-%m-%d').date()
    rmd_age, rmd_begin_year = get_rmd_age(owner_birth_date)

    return {
        'rmd_age': rmd_age,
        'rmd_begin_year': rmd_begin_year,
        'rmd_table': 'uniform_2021_present'
    }

def handle_brokerage(account: pd.Series) -> dict:
    # These accounts are not subject to RMD but may be depleted using LEF estimates
    return {
        'rmd_age': 0,
        'rmd_begin_year': 0,
        'rmd_table': 'lef_2021_present'
    }

def handle_income_stream(account: pd.Series) -> dict:
    """Handle income streams like FERS, ordinary income, or SSA."""
    begin_year = account['begin_year']
    owner_birth_date = datetime.strptime(account['owner_birthdate_iso'], '%Y-%m-%d').date()
    owner_birth_year = owner_birth_date.year

    rmd_age = account.get('rmd_age', 0)
    rmd_begin_year = begin_year - owner_birth_year

    return {
        'rmd_age': rmd_age,
        'rmd_begin_year': rmd_begin_year,
        'rmd_table': ''
    }

def handle_unknown(account: pd.Series) -> dict:
    """Handle unknown account types."""
    print(f"Warning: Account type not yet supported: {account['account_type']}")
    return {
        'rmd_age': 0,
        'rmd_begin_year': 0,
        'rmd_table': 'uniform_2021_present'
    }

def dummy2():
    """ Delete once new code is working"""
    for adx, account in my_account_df.iterrows():
        # Fetch existing account details
        account_name = account['account_name']
        account_type = account['account_type']
        begin_year = account['begin_year']
        owner_birth_date = datetime.strptime(account['owner_birthdate_iso'], '%Y-%m-%d').date()
        owner_birth_year = owner_birth_date.year
        owner_age = calculate_age(owner_birth_year, begin_year)

        rmd_begin_year = 0

        if account_type == 'ira_inherited':
            # fetch details to calculate rmd info based on prior owner
            prior_owner_birthdate_iso = account['prior_owner_birthdate_iso']
            prior_owner_death_year = account['prior_owner_death_year']
            beneficiary_birth_year = account['beneficiary_birth_year']
            
            # use prior owner account details to calculate RMD information
            prior_owner_birth_date = datetime.strptime(prior_owner_birthdate_iso, '%Y-%m-%d').date()
            prior_owner_birth_year = prior_owner_birth_date.year
            prior_owner_age = calculate_age(prior_owner_birth_year, begin_year)
            
            rmd_age, rmd_begin_year = get_rmd_age(prior_owner_birth_date)
            if rmd_begin_year < prior_owner_death_year:
                rmd_age = prior_owner_death_year - owner_birth_year
                # Use IRS Life Expectancy table based on original owner death year 
                if prior_owner_death_year >= 2021:
                    rmd_table = 'lef_2021_present'
                elif prior_owner_death_year <= 2001:
                    rmd_table = 'lef_2001'
                else:
                    # Use IRS Life Expectancy table based on beneficiary birth year 
                    rmd_table = 'lef_2002_2020'
                    # Calculate rmd age based on beneficiary (versus prior owner)
            else:
                # Use the latest Uniform Life table
                rmd_age = begin_year - beneficiary_birth_year
                rmd_table = 'uniform_2021_present'
        elif account_type in ('ira', 'tsp'): # not an inherited IRA
            rmd_age, rmd_begin_year = get_rmd_age(owner_birth_date)
            rmd_table = 'uniform_2021_present' # Default to use the latest Uniform Life table
            # Determine which IRS life expectancy table to use
        elif account_type == 'brokerage':
            # Use the uniform life table to estimate optional distributions for non-IRA account
            # This approach is used to optimally deplete the account during the owner life expectancy
            rmd_age = rmd_begin_year = 0
            rmd_table = 'lef_2021_present'
        elif account_type in ('fers_income', 'ordinary_income', 'ssa_income'):
            rmd_table = ''
            rmd_age = my_account_df['rmd_age'].loc[my_account_df['account_name'] == account_name].iloc[0]
            rmd_begin_year = begin_year - owner_birth_year
        else:
            rmd_table = 'uniform_2021_present' # Default to use the latest Uniform Life table
            print('Warning: Account type is not yet supported.', account_type)
    return