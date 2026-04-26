import pandas as pd
import json
import csv

from pathlib import Path
from datetime import datetime
from typing import Optional
from src.context.context import SimulationContext

from util_dev.debug_util import debug_view

# ─── Run Management and Export Utilities ──────────────

def export_run_metadata(metadata: dict, folder_path, filename='strategy_link.json'):
    path = folder_path / filename
    with open(path, 'w') as f:
        json.dump(metadata, f, indent=4)

def log_strategy_summary(context: SimulationContext,
                         summary_df: Optional[pd.DataFrame],
                         folder_path: Path,
                         default_strategy: Optional[str] = None,
                         default_simulation: Optional[int] = None,
                         filename: str = "strategy_summary.csv"):
    """Appends strategy summary statistics to a folder-level CSV report."""

    # ── Path setup ─────────────────────────────────────────────
    summary_path = folder_path / filename

    # ── Metadata enrichment ────────────────────────────────────
    debug_view(summary_df, 'log_strategy_summary - summary_df')
    if summary_df is not None:
        summary_df = summary_df[summary_df['sim_type'] == context.sim_type]
#        if 'withdrawal' not in summary_df.columns and default_strategy:
#            summary_df['withdrawal'] = default_strategy
#        if 'montecarlo' not in summary_df.columns and default_simulation is not None:
#            summary_df['montecarlo'] = default_simulation

    # ── Row extraction ─────────────────────────────────────────
    row = context.to_summary_row(summary_df)

    # ── Write header (only if file doesn't exist) ──────────────
    write_header = not summary_path.exists()
    with open(summary_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    print(f"✅ Strategy summary logged to: {summary_path}")
