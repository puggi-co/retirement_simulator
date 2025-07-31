import numpy as np

def create_downturn_years(years, count=4, seed=None):
    rng = np.random.default_rng(seed)
    return sorted(rng.choice(range(1, years + 1), size=count, replace=False).tolist())

def simulate_one_year(balance, withdrawal_target, return_rate, ydx, downturn_years, cfg, inflation_rate):
    year = ydx + 1
    is_downturn = year in downturn_years

    balance *= (1 + return_rate / 100)

    mode = cfg.withdrawal_mode
    updated_target = withdrawal_target

    if mode == 'fixed_rate':
        withdrawal_amt = balance * cfg.withdrawal_rate

    elif mode == 'target_amount':
        withdrawal_amt = withdrawal_target * ((1 + inflation_rate) ** ydx)

    elif mode == 'guardrail_amount':
        actual_rate = withdrawal_target / balance if balance > 0 else 0
        if actual_rate > cfg.guardrail_ceiling:
            updated_target *= 0.90
        elif actual_rate < cfg.guardrail_floor:
            updated_target *= 1.10
        else:
            updated_target *= (1 + inflation_rate)
        withdrawal_amt = min(updated_target, balance)

    else:
        raise ValueError(f"Unsupported mode: {mode}")

    withdrawal_amt = min(balance, withdrawal_amt)
    balance -= withdrawal_amt
    actual_rate = withdrawal_amt / balance if balance > 0 else np.nan

    return {
        'year': year,
        'return_%': return_rate,
        'withdrawal': withdrawal_amt,
        'portfolio_balance': balance,
        'actual_rate': actual_rate,
        'withdrawal_target': updated_target,
        'downturn': is_downturn
    }
