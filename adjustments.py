@dataclass
class FinancialAdjustmentMixin:
    def adjust_for_inflation(self, value: float, years: int) -> float:
        return value * ((1 + self.config.inflation_rate) ** years)

    def adjust_for_real_spend(self, value: float, years: int) -> float:
        return value / ((1 + self.config.inflation_rate) ** years)

