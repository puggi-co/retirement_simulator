import pandas as pd
from datetime import datetime, date

from config.config_schema import SimulationConfig
from core.schedule import SimulationSchedule, calculate_age
#from storage.export_util import debug_view

# ── RMD Enrichment ──────────────────────────────

def rmd_enrichment(account: pd.Series, owner_birth_date: date, age: int, base_year: int) -> dict:
    """
    Determine distribution metadata for an account.
    """
    source_type = account['source_type']
    distribution_year = None
    distribution_table = None

    if source_type in ('brokerage', 'roth', 'roth_inherited'):
        return {
            'distribution_age': 0,
            'distribution_year': 0,
            'distribution_table': 'none'
        }

    elif source_type in ('inc_fers', 'inc_ord', 'inc_ssa'):
        distribution_age = account['distribution_age']
        distribution_year = owner_birth_date.year + distribution_age
        distribution_table = 'none'

    elif source_type in ('ira', 'tsp'):
        distribution_age, distribution_year = calculate_rmd_age(owner_birth_date)
        distribution_table = 'uniform_2021_present'

    elif source_type == 'ira_inherited':
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

    else:
        print(f"⚠️ Unknown source type: {source_type}")
        distribution_age = 99
        distribution_year = base_year
        distribution_table = 'none'

    return {
        'distribution_age': int(distribution_age),
        'distribution_year': int(distribution_year),
        'distribution_table': distribution_table
    }

def enrich_portfolio_rmd(df: pd.DataFrame, config: SimulationConfig) -> pd.DataFrame:

    '''Enrich the Portfolio DataFrame with RMD-related fields.'''

    base_year = int(config.base_year)
    df['owner_birth_date'] = None
    df['age'] = 0
    df['distribution_year'] = 0
    df['distribution_table'] = 'none'

    for adx, account in df.iterrows():
        try:
            birth_date = datetime.strptime(account['owner_birthdate_iso'], '%Y-%m-%d').date()
            age = calculate_age(birth_date.year, base_year)
            df.at[adx, 'owner_birth_date'] = birth_date
            df.at[adx, 'age'] = age

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

def get_rmd_amount(
    *,
    context,
    account: dict,
    age: int
) -> float:
    """
    WD-only RMD calculation using TaxEngine.get_rmd_factor.
    """

    balance = account["current_balance"]

    # Retrieve the IRS divisor from the LEF table
    try:
        factor = context.tax_engine.get_rmd_factor(
            age=age,
            account=account,
            schedule=context.schedule
        )
    except Exception:
        return 0.0

    if factor is None or factor <= 0:
        return 0.0

    rmd_amount = balance / factor
    return min(rmd_amount, balance)
