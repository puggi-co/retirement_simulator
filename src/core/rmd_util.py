import pandas as pd
from datetime import datetime, date

from src.config.config_schema import SimulationConfig
from src.core.schedule import SimulationSchedule
#from src.io.export_util import debug_view

# ── RMD Enrichment ──────────────────────────────

def rmd_enrichment(account: pd.Series, owner_birth_date: date, owner_age: int, base_year: int) -> dict:
    """
    Determine distribution metadata for an account.
    """
    account_type = account['account_type']
    distribution_year = None
    distribution_table = None

    if account_type == 'ira_inherited':
        prior_birth_year = datetime.strptime(account['prior_owner_birthdate_iso'], '%Y-%m-%d').year
        prior_death_year = account['prior_owner_death_year']
        beneficiary_birth_year = account['beneficiary_birth_year']

        distribution_age, distribution_year = calculate_rmd_age(datetime(prior_birth_year, 1, 1))
        if distribution_year < prior_death_year:
            distribution_age = prior_death_year - owner_birth_date.year
            distribution_table = (
                'lef_2021_present' if prior_death_year >= 2021 else
                'lef_2001' if prior_death_year <= 2001 else
                'lef_2002_2020'
            )
        else:
            distribution_age = base_year - beneficiary_birth_year
            distribution_table = 'uniform_2021_present'

    elif account_type in ('ira', 'tsp'):
        distribution_age, distribution_year = calculate_rmd_age(owner_birth_date)
        distribution_table = 'uniform_2021_present'

    elif account_type == 'brokerage':
        distribution_age = owner_age
        distribution_year = base_year
        distribution_table = 'uniform_2021_present'
#        distribution_table = account.get('distribution_table', 'uniform_2021_present')

    elif account_type in ('inc_fers', 'inc_ord', 'inc_ssa'):
        distribution_age = account['distribution_age']
        distribution_year = owner_birth_date.year + distribution_age
        distribution_table = 'n/a'

    else:
        print(f"⚠️ Unknown account type: {account_type}")
        distribution_age = 99
        distribution_year = base_year
        distribution_table = 'uniform_2021_present'

    return {
        'distribution_age': int(distribution_age),
        'distribution_year': int(distribution_year),
        'distribution_table': distribution_table
    }

def enrich_portfolio_rmd(df: pd.DataFrame, config: SimulationConfig) -> pd.DataFrame:

    '''Enrich the Portfolio DataFrame with RMD-related fields.'''

    base_year = int(config.base_year)
    df['owner_birth_date'] = None
    df['owner_age'] = 0
    df['distribution_year'] = 0
    df['distribution_table'] = 'n/a'

    for adx, account in df.iterrows():
        try:
            birth_date = datetime.strptime(account['owner_birthdate_iso'], '%Y-%m-%d').date()
            age = calculate_age(birth_date.year, base_year)
            df.at[adx, 'owner_birth_date'] = birth_date
            df.at[adx, 'owner_age'] = age

            rmd_info = rmd_enrichment(account, birth_date, age, base_year)
            df.at[adx, 'distribution_age'] = rmd_info['distribution_age']
            df.at[adx, 'distribution_year'] = rmd_info['distribution_year']
            df.at[adx, 'distribution_table'] = rmd_info['distribution_table']
        except Exception as e:
            print(f"⚠️ Skipping RMD enrichment for row {adx} due to error: {e}")
    return df

def calculate_rmd_age(birthdate):
    """
    Determine RMD age and distribution year based on IRS rules.
    """
    if isinstance(birthdate, str):
        birthdate = datetime.strptime(birthdate, '%Y-%m-%d').date()
    elif isinstance(birthdate, datetime):
        birthdate = birthdate.date()
    elif not isinstance(birthdate, date):
        raise TypeError("birthdate must be a date, datetime, or ISO string")

    if birthdate < date(1949, 7, 1):
        rmd_age = 70.5
    elif date(1949, 7, 1) <= birthdate <= date(1950, 12, 31):
        rmd_age = 72
    elif date(1951, 1, 1) <= birthdate <= date(1958, 12, 31):
        rmd_age = 73
    elif birthdate <= date.today():
        rmd_age = 75
    else:
        rmd_age = 75
        print('Warning: Account owner has a future birthdate. Default RMD age is', rmd_age)

    rmd_age = int(round(rmd_age))
    rmd_begin_year = birthdate.year + rmd_age
    return rmd_age, rmd_begin_year

# ── RMD Calculation ──────────────────────────────

def get_rmd_factor(age: int, account: pd.Series, df_lef: pd.DataFrame, schedule: SimulationSchedule) -> float:
    """
    Retrieve the IRS life expectancy factor (RMD divisor) for a given age and account type.

    The account must specify distribution table key that matches a column name in df_lef.
    If missing, defaults to 'uniform_lifetime'.

    Raises:
        ValueError: If the factor cannot be found for the given age and table.
    """
    lookup_age = min(age, schedule.end_age)
    distribution_table = account.get('distribution_table', 'uniform_lifetime')
    try:
        factor = df_lef.loc[df_lef['age'] == lookup_age, distribution_table].iloc[0]
    except (KeyError, IndexError):
        raise ValueError(f"Missing RMD factor for age {lookup_age} and table '{distribution_table}'")
    
#    print(f"RMD lookup: age={lookup_age}, table={distribution_table}, factor={factor}")
    return factor

def get_rmd_amount(balance: float, age: int, account: pd.Series, df_lef: pd.DataFrame, schedule) -> float:
    """
    Calculate the RMD amount for a given account balance and age.

    Returns:
        float: Required Minimum Distribution amount.
    """
    factor = get_rmd_factor(age, account, df_lef, schedule)
    return round(balance / factor, 2)

