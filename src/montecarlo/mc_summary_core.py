# ── 5. MONTE CARLO ANALYZER (Refactored mc_summary_core.py) ─────────────────────

import pandas as pd
from typing import List
from dataclasses import dataclass

from src.orchestration.orch_entity import MCAnalyzeResults, MCOutcomeLedger

from src.io.export_util import debug_view

class MonteCarloAnalyzer:
    """
    Analyzes Monte Carlo simulation results
    """
    
    def __init__(self, failure_thresholds: List[int] = None):
        self.failure_thresholds = failure_thresholds or [0, 100_000, 250_000]

    def analyze(self, outcome_ledger: MCOutcomeLedger) -> MCAnalyzeResults:
        """
        Comprehensive analysis of Monte Carlo results
        
        Returns:
            MCOutcomeLedger with all summary statistics
        """
        
        print("📊 Analyzing Monte Carlo results...")
        
        df_results = outcome_ledger.frame.df  # ✅ Extract the actual data
        debug_view(df_results, 'df_results')
        
        # Get final year results for each simulation
        df_final = self._get_final_results(df_results)
        
        # Summary statistics
        summary = self._calculate_summary_stats(df_final)
        
        # Failure analysis
        failures = self._calculate_failure_rates(df_final)
        
        # Trajectory analysis
        median = self._calculate_median_trajectory(df_results)
        percentiles = self._calculate_percentiles(df_results)
        
        # Additional insights
        extra = self._calculate_extra_metrics(df_results, df_final)

        return MCAnalyzeResults(
            summary=summary,
            failures=failures,
            median=median,
            percentiles=percentiles,
            extra=extra
        )
    
    def _get_final_results(self, df_results: pd.DataFrame) -> pd.DataFrame:
        """Extract final year results for each simulation"""
        if 'sim_num' in df_results.columns:
            return df_results.groupby('sim_num').tail(1)
        else:
            # Fallback for legacy format
            return df_results.groupby(['sim_type']).tail(1)
    
    def _calculate_summary_stats(self, df_final: pd.DataFrame) -> pd.DataFrame:
        """Calculate summary statistics for final balances"""
        
        groupby_cols = ['sim_type'] if 'sim_type' in df_final.columns else []
            
        if not groupby_cols:
            # No grouping columns, analyze entire dataset
            balance_col = 'base_balance' if 'base_balance' in df_final.columns else 'end_balance'
            summary = pd.DataFrame({
                'Count': [len(df_final)],
                'Mean': [df_final[balance_col].mean()],
                'Median': [df_final[balance_col].median()],
                'Std': [df_final[balance_col].std()],
                'Min': [df_final[balance_col].min()],
                'Max': [df_final[balance_col].max()]
            })
        else:
            balance_col = 'base_balance' if 'base_balance' in df_final.columns else 'end_balance'
            summary = df_final.groupby(groupby_cols)[balance_col].agg([
                ('Count', 'count'),
                ('Mean', 'mean'),
                ('Median', 'median'),
                ('Std', 'std'),
                ('Min', 'min'),
                ('Max', 'max')
            ])
        
        return summary.round(0)

    def _calculate_failure_rates(self, df_final: pd.DataFrame) -> pd.DataFrame:
        """Calculate failure rates at different balance thresholds"""

        balance_col = 'base_balance' if 'base_balance' in df_final.columns else 'end_balance'
        group_col = 'sim_type'  # ✅ Always group by sim_type

        rows = []

        for group in df_final[group_col].unique():
            subset = df_final[df_final[group_col] == group]
            total_sims = len(subset)

            for threshold in self.failure_thresholds:
                failures = (subset[balance_col] <= threshold).sum()
                failure_rate = (failures / total_sims) * 100 if total_sims > 0 else 0

                rows.append({
                    'sim_type': group,  # ✅ Use sim_type as the label
                    'threshold': f'≤ ${threshold:,.0f}',
                    'failures': failures,
                    'total_sims': total_sims,
                    'failure_rate_%': round(failure_rate, 2)
                })

        return pd.DataFrame(rows)

    def _calculate_failure_rates2(self, df_final: pd.DataFrame) -> pd.DataFrame:
        """Calculate failure rates at different balance thresholds"""
        
        balance_col = 'base_balance' if 'base_balance' in df_final.columns else 'end_balance'
        
        # Group by withdrawal type if available
        group_col = 'sim_type' if 'sim_type' in df_final.columns else None
        
        rows = []
        
        if group_col:
            groups = df_final[group_col].unique()
        else:
            groups = ['All Simulations']
            df_final = df_final.copy()
            df_final['group'] = 'All Simulations'
            group_col = 'group'
        
        for group in groups:
            if group_col == 'group':
                subset = df_final
            else:
                subset = df_final[df_final[group_col] == group]
            
            total_sims = len(subset)
            
            for threshold in self.failure_thresholds:
                failures = (subset[balance_col] <= threshold).sum()
                failure_rate = (failures / total_sims) * 100 if total_sims > 0 else 0
                
                rows.append({
                    'group': group,
                    'threshold': f'≤ ${threshold:,.0f}',
                    'failures': failures,
                    'total_sims': total_sims,
                    'failure_rate_%': round(failure_rate, 2)
                })
        
        return pd.DataFrame(rows)
    
    def _calculate_median_trajectory(self, df_results: pd.DataFrame) -> pd.DataFrame:
        """Calculate median balance trajectory over time"""
        
        balance_col = 'base_balance' if 'base_balance' in df_results.columns else 'end_balance'
        
        # Group by year and calculate median
        if 'year' in df_results.columns:
            trajectory = df_results.groupby('year')[balance_col].median().reset_index()
            trajectory.columns = ['year', 'median_balance']
        else:
            # Fallback: assume rows are in chronological order
            trajectory = df_results.groupby(df_results.index // 
                                          (len(df_results) // 30))[balance_col].median().reset_index()
            trajectory.columns = ['year_index', 'median_balance']
        
        return trajectory
    
    def _calculate_percentiles(self, df_results: pd.DataFrame) -> pd.DataFrame:
        """Calculate percentile bands for trajectory analysis"""
        
        balance_col = 'base_balance' if 'base_balance' in df_results.columns else 'end_balance'
        
        if 'year' in df_results.columns:
            percentiles = df_results.groupby('year')[balance_col].quantile(
                [0.05, 0.10, 0.25, 0.75, 0.90, 0.95]
            ).unstack().reset_index()
            
            percentiles.columns = ['year', '5th', '10th', '25th', '75th', '90th', '95th']
        else:
            # Simplified fallback
            overall_percentiles = df_results[balance_col].quantile(
                [0.05, 0.10, 0.25, 0.75, 0.90, 0.95]
            )
            percentiles = pd.DataFrame([overall_percentiles.to_dict()])
        
        return percentiles.round(0)
    
    def _calculate_extra_metrics(self, df_results: pd.DataFrame, 
                               df_final: pd.DataFrame) -> dict:
        """Calculate additional insights and metrics"""
        
        extra = {}
        
        # Success rate (non-zero ending balance)
        balance_col = 'base_balance' if 'base_balance' in df_final.columns else 'end_balance'
        success_rate = ((df_final[balance_col] > 0).sum() / len(df_final)) * 100
        extra['success_rate_%'] = round(success_rate, 2)
        
        # Average years until depletion (for failed simulations)
        if 'year' in df_results.columns:
            failed_sims = df_results[df_results[balance_col] <= 0]
            if not failed_sims.empty:
                avg_depletion_year = failed_sims.groupby('sim_num')['year'].min().mean()
                extra['avg_depletion_year'] = round(avg_depletion_year, 1)
        
        # Goal achievement rate (if withdrawal goals are tracked)
        if 'goal_met' in df_results.columns:
            goal_achievement = (df_results['goal_met'].sum() / 
                              len(df_results)) * 100
            extra['goal_achievement_%'] = round(goal_achievement, 2)
        
        # RMD trigger statistics
        if 'rmd_met' in df_results.columns:
            rmd_rate = (df_results['rmd_met'].sum() / 
                       len(df_results)) * 100
            extra['rmd_trigger_rate_%'] = round(rmd_rate, 2)
        
        return extra
