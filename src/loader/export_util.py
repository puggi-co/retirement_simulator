import pandas as pd
import json
import csv

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
# 🚨 Added for debug_view:
from dataclasses import asdict, is_dataclass
from pprint import pprint

from context.context import SimulationContext

# ─── Centralized Path Management ─────────────────
# Find the directory of this file (src/io), goes up 2 levels to project root,
# and points directly to your new data/export folder!
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "data" / "export"

# ─── Run Management and Export Utilities ──────────────

def export_run_metadata(metadata: dict, folder_path: Optional[Path] = None, filename='strategy_link.json'):
    """Exports run metadata to JSON. Defaults to the new data/export/ folder."""
    
    # Fallback to default if no folder path is provided
    target_folder = folder_path if folder_path else DEFAULT_EXPORT_DIR
    path = target_folder / filename
    
    with open(path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print(f"✅ Metadata exported to: {path}")

def log_strategy_summary(context: SimulationContext,
                         summary_df: Optional[pd.DataFrame],
                         folder_path: Optional[Path] = None,
                         default_strategy: Optional[str] = None,
                         default_simulation: Optional[int] = None,
                         filename: str = "strategy_summary.csv"):
    """Appends strategy summary statistics to a folder-level CSV report."""

    # ── Path setup ─────────────────────────────────────────────
    target_folder = folder_path if folder_path else DEFAULT_EXPORT_DIR
    summary_path = target_folder / filename

    # ── Metadata enrichment ────────────────────────────────────
    debug_view(summary_df, 'log_strategy_summary - summary_df')
    
    if summary_df is not None:
        # Filter by simulation type
        summary_df = summary_df[summary_df['sim_type'] == context.sim_type]

    # ── Row extraction ─────────────────────────────────────────
    row = context.to_summary_row(summary_df)

    # ── Write header (only if file doesn't exist) ──────────────
    write_header = not summary_path.exists()
    
    # Ensure the folder actually exists before writing!
    target_folder.mkdir(parents=True, exist_ok=True)
    
    with open(summary_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    print(f"✅ Strategy summary logged to: {summary_path}")

# ───  Debug Utilities ───────────────────────────────────────────

def debug_view(obj: Any, label: str = '', max_rows: Optional[int] = 100):
    """Universal debug printer that adapts to common data types."""
    if label:
        print(f"\n=== {label} ===")

    if isinstance(obj, pd.DataFrame):
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        pd.set_option('display.max_rows', None)

        # Column summary - Optionally enable for deeper debugging
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

        print(f"[DataFrame] shape={obj.shape}")

        n_rows = obj.shape[0]
        print(f"\n🔍 {label} — {n_rows} rows")

        if max_rows is None or n_rows <= max_rows * 2:
            print("\n--- Full DataFrame ---")
            print(obj.to_string(max_rows=n_rows, max_cols=None, line_width=2000))
            return
        else:
            print(f"\n--- Head (first {max_rows}) ---")
            print(obj.head(max_rows).to_string(max_rows=max_rows, max_cols=None, line_width=2000))
            print(f"\n--- Tail (last {max_rows}) ---")
            print(obj.tail(max_rows).to_string(max_rows=max_rows, max_cols=None, line_width=2000))
            return

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
