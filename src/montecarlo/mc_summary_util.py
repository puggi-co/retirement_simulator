# ── 7. UTILITY FUNCTIONS (Enhanced mc_summary_util.py) ─────────────────────────

import pandas as pd
from typing import List, Dict, Any

from core.schedule import SimulationSchedule


from util_dev.debug_util import debug_view


def validate_mc_inputs(context: 'SimulationContext', schedule: SimulationSchedule portfolio_df: pd.DataFrame, 
                      num_simulations: int) -> None:
    """Validate Monte Carlo simulation inputs"""
    
    # Validate context
    if not schedule:
        raise ValueError("Context must have a valid schedule")
    
    if not hasattr(context, 'wd_type'):
        raise ValueError("Context must specify wd_type")

    # Validate portfolio
    required_portfolio_cols = ['account_tax_type', 'base_balance', 'account_type']
    missing_cols = [col for col in required_portfolio_cols if col not in portfolio_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required portfolio columns: {missing_cols}")
    
    # Check for investment accounts
    investment_accounts = portfolio_df['account_tax_type'].isin(['taxable', 'deferred', 'exempt'])
    if not investment_accounts.any():
        raise ValueError("Portfolio must contain at least one investment account")
    
    # Validate simulation parameters
    if num_simulations < 1:
        raise ValueError("Number of simulations must be positive")
    
    if num_simulations > 10000:
        print(f"⚠️  Warning: {num_simulations:,} simulations may take a long time")


def validate_mc_results(df_results: pd.DataFrame) -> None:
    """Validate Monte Carlo results DataFrame"""
    
    required_cols = [
        'year', 'age', 'sim_mode', 'sim_id', 'sim_type',
        'base_balance', 'wd_amount', 'wd_type'
    ]
    
    missing_cols = [col for col in required_cols if col not in df_results.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in Monte Carlo results: {missing_cols}")
    
    # Check for data integrity
    if df_results.empty:
        raise ValueError("Monte Carlo results are empty")
    
    # Validate numeric columns
    numeric_cols = ['base_balance', 'wd_amount']
    for col in numeric_cols:
        if col in df_results.columns:
            if df_results[col].isna().all():
                raise ValueError(f"Column '{col}' contains only NaN values")


def harmonize_mc_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize Monte Carlo results column names"""
    
    column_mapping = {
        'portfolio_balance': 'base_balance',
        'end_balance': 'base_balance',
        'mc_id': 'sim_num',
        'sim_type': 'sim_type',
        'sim_mode': 'withdrawal_mode'
    }
    
    return df.rename(columns=column_mapping)


def preview_mc_results(df: pd.DataFrame, label: str = 'Monte Carlo Results') -> None:
    """Display preview of Monte Carlo results"""
    
    print(f"\n📊 {label}")
    print("=" * 60)
    
    # Basic info
    print(f"Total rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    
    # Simulation summary
    if 'sim_num' in df.columns:
        num_sims = df['sim_num'].nunique()
        print(f"Number of simulations: {num_sims:,}")
    
    if 'year' in df.columns:
        year_range = f"{df['year'].min()} - {df['year'].max()}"
        print(f"Year range: {year_range}")
    
    # Balance summary
    balance_cols = ['base_balance', 'end_balance', 'portfolio_balance']
    balance_col = next((col for col in balance_cols if col in df.columns), None)
    
    if balance_col:
        print(f"\n💰 Balance Summary ({balance_col}):")
        stats = df[balance_col].describe()
        print(f"  Mean: ${stats['mean']:,.0f}")
        print(f"  Median: ${stats['50%']:,.0f}")
        print(f"  Min: ${stats['min']:,.0f}")
        print(f"  Max: ${stats['max']:,.0f}")
    
    # Sample data
    print(f"\n🔍 Sample Data:")
    
    print(f"\n📋 Column List:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")


def create_simulation_summary(context: 'SimulationContext', 
                          analysis: 'MonteCarloAnalysis') -> Dict[str, Any]:
    """Create comprehensive simulation summary"""
    
    summary = {
        'simulation_info': {
            'sim_id': context.sim_id,
            'sim_mode': context.sim_mode,
            'duration_years': schedule.duration,
            'withdrawal_mode': getattr(context, 'withdrawal_mode', 'Unknown'),
        },
        'key_metrics': {},
        'risk_assessment': {},
        'recommendations': []
    }
    
    # Extract key metrics from analysis
    if hasattr(analysis, 'extra') and analysis.extra:
        if 'success_rate_%' in analysis.extra:
            summary['key_metrics']['success_rate'] = analysis.extra['success_rate_%']
        
        if 'avg_depletion_year' in analysis.extra:
            summary['key_metrics']['avg_depletion_year'] = analysis.extra['avg_depletion_year']
    
    # Risk assessment
    if hasattr(analysis, 'failure_table') and not analysis.failure_table.empty:
        zero_failure_rate = analysis.failure_table[
            analysis.failure_table['threshold'] == '≤ $0'
        ]['failure_rate_%'].iloc[0] if not analysis.failure_table.empty else 0
        
        summary['risk_assessment']['depletion_risk'] = zero_failure_rate
        
        if zero_failure_rate > 20:
            summary['recommendations'].append("High depletion risk - consider reducing withdrawal rate")
        elif zero_failure_rate > 10:
            summary['recommendations'].append("Moderate depletion risk - monitor closely")
        else:
            summary['recommendations'].append("Low depletion risk - plan appears sustainable")
    
    return summary
