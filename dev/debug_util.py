# utils/print_debug.py

import pandas as pd

from dataclasses import asdict, is_dataclass
from pprint import pprint
from typing import Optional

def debug_view(obj: pd.DataFrame, label: str = '', max_rows: Optional[int] = 100):
    """Universal debug printer that adapts to common data types.
    Filtered Usage: use standard pandas

    debug_view(portfolio_df[portfolio_df['account_name'] == 'Vanguard IRA'], label='Vanguard IRA Snapshot')

    debug_view(
    self.wd_results[self.wd_results['account_type'].str.startswith('inc')],
    label='Runner WD Results',
    max_rows=20
    )

    filtered = ledger.df_ledger[
        (ledger.df_ledger['account_type'] == 'ira') &
        (ledger.df_ledger['age'] >= 72)
    ]
    debug_view(filtered, label='IRA Accounts Age 72+')

    """
    if label:
        print(f"\n=== {label} ===")

    if isinstance(obj, pd.DataFrame):
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)

        print(f"[DataFrame] shape={obj.shape}")

        # Column summary
#        print("\n--- Column Types ---")
#        print(obj.dtypes)

#        null_counts = obj.isnull().sum()
#        nonzero_nulls = null_counts[null_counts > 0]

#        if not nonzero_nulls.empty:
#            print("\n--- Null Counts (non-zero only) ---")
#            print(nonzero_nulls)
#        else:
#            print("\n--- Null Counts ---")
#            print("✅ No missing values")

        # Head/Tail logic
        n_rows = obj.shape[0]
        print(f"\n🔍 {label} — {n_rows} rows")

        if max_rows is None or n_rows <= max_rows * 2:
            print("\n--- Full DataFrame ---")
            print(obj.to_string(line_width=2000))
        else:
            print(f"\n--- Head (first {max_rows}) ---")
            print(obj.head(max_rows).to_string(line_width=2000))
            print(f"\n--- Tail (last {max_rows}) ---")
            print(obj.tail(max_rows).to_string(line_width=2000))

    elif isinstance(obj, dict):
        for key, val in obj.items():
            debug_view(val, label=f"{label}.{key}" if label else key, max_rows=max_rows)

    elif isinstance(obj, list):
        for i, item in enumerate(obj[:max_rows]):
            debug_view(item, label=f"{label}[{i}]" if label else f"[{i}]", max_rows=max_rows)

    elif is_dataclass(obj):
        pprint(asdict(obj))

    else:
        print(obj)
