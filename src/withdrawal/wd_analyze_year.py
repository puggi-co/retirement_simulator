from dataclasses import dataclass
from typing import Optional

@dataclass
class YearAnnotation:
    year: int
    deduction: float
    taxable_gross_income: float
    tax_owed: float
    effective_tax_rate: float
    net_spending_power: float
    real_spending_power: float
    guardrail_triggered: bool = False
    guardrail_direction: str = 'none'
    actual_rate: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            'year': self.year,
            'deduction': round(self.deduction, 2),
            'taxable_gross_income': round(self.taxable_gross_income, 2),
            'tax_owed': round(self.tax_owed, 2),
            'effective_tax_rate': round(self.effective_tax_rate, 4),
            'net_spending_power': round(self.net_spending_power, 2),
            'real_spending_power': round(self.real_spending_power, 2),
            'guardrail_triggered': self.guardrail_triggered,
            'guardrail_direction': self.guardrail_direction,
            'actual_rate': self.actual_rate
        }

    def emoji_overlay(self) -> str:
        """Returns a quick visual cue based on real spending power."""
        if self.real_spending_power >= self.net_spending_power:
            return "🟢💰"
        elif self.real_spending_power >= 0.75 * self.net_spending_power:
            return "🟡📉"
        else:
            return "🔴⚠️"

    @staticmethod
    def create(year: int, deduction: float, taxable_gross_income: float, tax_owed: float,
               effective_tax_rate: float, net_spending_power: float, real_spending_power: float,
               guardrail_triggered: bool = False, guardrail_direction: str = 'none',
               actual_rate: Optional[float] = None) -> "YearAnnotation":
        return YearAnnotation(
            year=year,
            guardrail_triggered=guardrail_triggered,
            guardrail_direction=guardrail_direction,
            actual_rate=actual_rate,
            deduction=deduction,
            taxable_gross_income=taxable_gross_income,
            tax_owed=tax_owed,
            effective_tax_rate=effective_tax_rate,
            net_spending_power=net_spending_power,
            real_spending_power=real_spending_power
        )
