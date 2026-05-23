# ================================================================================
# RMD suppression logic for withdrawals.
# ================================================================================

import pandas as pd

from context.context import SimulationContext


def apply_rmd_suppression(
    context: SimulationContext,
    portfolio_df: pd.DataFrame,
    withdrawal_target: float,
    year: int,
    age: int
) -> float:
    """
    Simple RMD suppression: bias withdrawals toward deferred accounts
    by effectively lowering the target burden on taxable accounts.
    For now, we just return the same target; the behavior is expressed
    by draw_order + sim_mode-specific logic you can extend here.
    """

    # This is the hook where you can:
    # - compute IRA balance
    # - compare to a glidepath
    # - optionally increase withdrawal_target
    # For now, we keep it simple and return the original target.
    return withdrawal_target
