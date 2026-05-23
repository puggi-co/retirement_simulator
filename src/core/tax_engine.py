import pandas as pd
from typing import Optional

from loader.tax_loader import FilingStatus

class TaxEngine:
    """
    Unified tax computation engine used by all withdrawal engines.
    Wraps TaxTable and exposes marginal rate + tax calculation.
    """

    def __init__(self, tax_table, config):
        self.tax_table = tax_table      # TaxTable object
        self.config = config

    # ----------------------------------------------------------
    # Standard Deduction
    # ----------------------------------------------------------
    def get_standard_deduction(self, year: int, filing_status: str) -> Optional[float]:
        table = self.tax_table.standard_deduction
        if table is None:
            return None

        row = table.loc[table["year"] == year]
        if row.empty:
            return None

        return row[filing_status].values[0]

    # ----------------------------------------------------------
    # Tax Brackets (full table for this year)
    # ----------------------------------------------------------
    def get_tax_brackets(self, year: int) -> pd.DataFrame:
        return self.tax_table.tax_bracket[self.tax_table.tax_bracket["year"] == year]

    # ----------------------------------------------------------
    # Marginal Rate
    # ----------------------------------------------------------
    def get_marginal_rate(self, year: int, taxable_income: float, filing_status: str) -> float:
        if taxable_income <= 0:
            return 0.0

        brackets = self.get_tax_brackets(year)

        # Column mapping based on filing status
        if filing_status == FilingStatus.SINGLE:
            low_col = "low_single"
            high_col = "high_single"
        elif filing_status == FilingStatus.MARRIED:
            low_col = "low_married"
            high_col = "high_married"
        elif filing_status == FilingStatus.HEAD:
            low_col = "low_head"
            high_col = "high_head"
        else:
            return 0.0

        marginal_rate = 0.0

        for row in brackets.itertuples():
            low = getattr(row, low_col)
            high = getattr(row, high_col)
            rate = row.tax_rate

            if low <= taxable_income <= high:
                return rate

            marginal_rate = rate  # fallback to highest bracket

        return marginal_rate

    # ----------------------------------------------------------
    # Full Tax Calculation
    # ----------------------------------------------------------
    def calculate_tax(self, year: int, filing_status: str, taxable_income: float):
        if taxable_income <= 0:
            return 0.0, 0.0

        brackets = self.get_tax_brackets(year)

        if filing_status == FilingStatus.SINGLE:
            low_col = "low_single"
            high_col = "high_single"
        elif filing_status == FilingStatus.MARRIED:
            low_col = "low_married"
            high_col = "high_married"
        elif filing_status == FilingStatus.HEAD:
            low_col = "low_head"
            high_col = "high_head"
        else:
            return 0.0, 0.0

        tax_owed = 0.0
        remaining = taxable_income

        for row in brackets.itertuples():
            low = getattr(row, low_col)
            high = getattr(row, high_col)
            rate = row.tax_rate

            if remaining <= 0:
                break

            taxable_portion = min(remaining, high - low)
            tax_owed += taxable_portion * rate
            remaining -= taxable_portion

        effective_rate = tax_owed / taxable_income
        return tax_owed, effective_rate

    # ----------------------------------------------------------
    # RMD Factor
    # ----------------------------------------------------------
    def get_rmd_factor(self, age: int, account: pd.Series, schedule) -> float:
        """
        Retrieve the IRS life expectancy factor (RMD divisor) for a given age
        and account type using the LEF table loaded in TaxTable.
        """

        df_lef = self.tax_table.lef
        distribution_table = account.get('distribution_table')

        if distribution_table is None:
            raise ValueError(f"Account missing distribution_table: {account}")

        lookup_age = min(age, schedule.end_age)

        try:
            factor = df_lef.loc[df_lef['age'] == lookup_age, distribution_table].iloc[0]
        except (KeyError, IndexError):
            raise ValueError(
                f"Missing RMD factor for age {lookup_age} and table '{distribution_table}'"
            )

        return factor
