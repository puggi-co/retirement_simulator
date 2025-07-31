import os
import json
import csv
from datetime import datetime

# Optional: type hint dependency
from src.context.context import SimulationContext

# ─── Run Management and Export Utilities ──────────────

def create_run_subfolder(base_dir='exports', timestamp=None):
    """Creates a unique timestamped folder for a simulation run."""
    timestamp = timestamp or datetime.now().strftime('%Y-%m-%d_%H%M%S')
    folder_path = os.path.join(base_dir, f'Run_{timestamp}')
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def export_run_metadata(config, folder, filename='run_metadata.json'):
    """Saves simulation config parameters to a JSON file."""
    path = os.path.join(folder, filename)
    with open(path, 'w') as f:
        json.dump(config.as_dict(), f, indent=4)

def log_scenario_summary(context: SimulationContext, summary_df, folder, filename='summary_report.csv'):
    """Appends scenario summary statistics to a folder-level CSV report."""
    summary_path = os.path.join(folder, filename)
    row = context.to_summary_row(summary_df)

    write_header = not os.path.exists(summary_path)
    with open(summary_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(row)

