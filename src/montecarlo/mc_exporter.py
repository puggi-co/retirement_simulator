# ── 6. MONTE CARLO EXPORTER ────────────────────────────────

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from typing import Optional
from dataclasses import asdict, fields

# Simulation imports
from src.context.context import SimulationContext

class MonteCarloExporter:
    """
    Handles export of Monte Carlo results to various formats
    """
    
    def __init__(self, results: 'MCResults', context: SimulationContext):
        self.results = results
        self.context = context
        self.analysis = results.analysis
        
    def export_all(self, folder_path: str, include_charts: bool = True) -> None:
        """Export all Monte Carlo results to folder"""
        
        # Export Excel summary
        excel_path = os.path.join(folder_path, f'{self.context.sim_id}_mc_results.xlsx')
        self.export_excel(excel_path)
        
        # Export charts if requested
        if include_charts:
            pdf_path = os.path.join(folder_path, f'{self.context.sim_id}_mc_charts.pdf')
            self.export_charts(pdf_path)
        
        # Export raw data (optional)
        csv_path = os.path.join(folder_path, f'{self.context.sim_id}_raw_data.csv')
        self.export_raw_data(csv_path)
        
        print(f"📊 Monte Carlo exports completed:")
        print(f"   • Summary: {excel_path}")
        if include_charts:
            print(f"   • Charts: {pdf_path}")
        print(f"   • Raw Data: {csv_path}")
    
    def export_excel(self, excel_path: str) -> None:
        """Export comprehensive Excel workbook with multiple sheets"""
        
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            
            # Summary statistics
            if hasattr(self.analysis, 'summary'):
                self.analysis.summary.to_excel(writer, sheet_name='Summary', index=True)
            
            # Failure analysis
            if hasattr(self.analysis, 'failure_table'):
                self.analysis.failure_table.to_excel(writer, sheet_name='Failure_Analysis', index=False)
            
            # Trajectory data
            if hasattr(self.analysis, 'median_trajectory'):
                self.analysis.median_trajectory.to_excel(writer, sheet_name='Median_Trajectory', index=False)
            
            # Percentiles
            if hasattr(self.analysis, 'percentiles'):
                self.analysis.percentiles.to_excel(writer, sheet_name='Percentiles', index=False)
            
            # Extra metrics
            if hasattr(self.analysis, 'extra') and self.analysis.extra:
                extra_df = pd.DataFrame(list(self.analysis.extra.items()), 
                                       columns=['Metric', 'Value'])
                extra_df.to_excel(writer, sheet_name='Extra_Metrics', index=False)
            
            # Simulation metadata
            if self.results.metadata:
                metadata_dict = asdict(self.results.metadata)
                metadata_df = pd.DataFrame(list(metadata_dict.items()), columns=['Parameter', 'Value'])
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)

        print(f"📈 Excel summary exported: {excel_path}")
    
    def export_charts(self, pdf_path: str) -> None:
        """Export comprehensive chart collection to PDF"""
        
        from matplotlib.backends.backend_pdf import PdfPages
        
        with PdfPages(pdf_path) as pdf:
            
            # 1. Trajectory chart with confidence bands
            if hasattr(self.analysis, 'median_trajectory') and hasattr(self.analysis, 'percentiles'):
                fig = self._create_trajectory_chart()
                if fig:
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)
            
            # 2. Final distribution chart
            fig = self._create_distribution_chart()
            if fig:
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
            
            # 3. Failure rate chart_create_distribution_chart
            if hasattr(self.analysis, 'failure_table'):
                fig = self._create_failure_chart()
                if fig:
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)
            
            # 4. Success probability chart
            fig = self._create_success_probability_chart()
            if fig:
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
        
        print(f"📊 Charts exported: {pdf_path}")
    
    def export_raw_data(self, csv_path: str) -> None:
        """Export raw simulation data to CSV"""
        self.results.get_outcome_df().to_csv(csv_path, index=False)
        print(f"💾 Raw data exported: {csv_path}")
    
    def _create_trajectory_chart(self) -> Optional[plt.Figure]:
        """Create portfolio balance trajectory chart with confidence bands"""
        
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Plot median trajectory
            median_data = self.analysis.median_trajectory
            if 'year' in median_data.columns:
                x_col = 'year'
            else:
                x_col = median_data.columns[0]  # Fallback to first column
            
            ax.plot(median_data[x_col], median_data['median_balance'], 
                   color='blue', linewidth=2, label='Median')
            
            # Add confidence bands if percentiles available
            if hasattr(self.analysis, 'percentiles') and not self.analysis.percentiles.empty:
                pct_data = self.analysis.percentiles
                
                # 80% confidence band (10th-90th percentile)
                if '10th' in pct_data.columns and '90th' in pct_data.columns:
                    ax.fill_between(pct_data[x_col], pct_data['10th'], pct_data['90th'],
                                   alpha=0.2, color='blue', label='10th-90th Percentile')
                
                # 50% confidence band (25th-75th percentile)
                if '25th' in pct_data.columns and '75th' in pct_data.columns:
                    ax.fill_between(pct_data[x_col], pct_data['25th'], pct_data['75th'],
                                   alpha=0.3, color='blue', label='25th-75th Percentile')
            
            # Formatting
            ax.set_xlabel('Year')
            ax.set_ylabel('Portfolio Balance ($)')
            ax.set_title(f'Monte Carlo Trajectory Analysis\n{self.context.sim_id} - {self.results.metadata.num_simulations:,} Simulations')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Format y-axis as currency
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Warning: Could not create trajectory chart: {e}")
            return None
    
    def _create_distribution_chart(self) -> Optional[plt.Figure]:
        """Create final balance distribution chart"""
        
        try:
            # Get final balances
            df = self.results.get_outcome_df()
            balance_col = 'base_balance' if 'base_balance' in df.columns else 'end_balance'

            if 'sim_num' in df.columns:
                final_balances = df.groupby('sim_num')[balance_col].last()
            else:
                final_balances = df[balance_col]
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Histogram
            ax1.hist(final_balances, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
            ax1.axvline(final_balances.median(), color='red', linestyle='--', 
                       label=f'Median: ${final_balances.median():,.0f}')
            ax1.axvline(final_balances.mean(), color='orange', linestyle='--',
                       label=f'Mean: ${final_balances.mean():,.0f}')
            
            # Add failure thresholds
            for threshold in [0, 100_000, 250_000]:
                if threshold <= final_balances.max():
                    ax1.axvline(threshold, color='gray', linestyle=':', alpha=0.5)
                    failure_rate = ((final_balances <= threshold).sum() / len(final_balances)) * 100
                    ax1.text(threshold, ax1.get_ylim()[1] * 0.9, 
                            f'{failure_rate:.1f}% ≤ ${threshold:,.0f}', 
                            rotation=90, ha='right', fontsize=8)
            
            ax1.set_xlabel('Final Portfolio Balance ($)')
            ax1.set_ylabel('Frequency')
            ax1.set_title('Distribution of Final Portfolio Balances')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            # Box plot
            ax2.boxplot(final_balances, vert=False)
            ax2.set_xlabel('Final Portfolio Balance ($)')
            ax2.set_title('Final Balance Box Plot')
            ax2.grid(True, alpha=0.3)
            ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Warning: Could not create distribution chart: {e}")
            return None
    
    def _create_failure_chart(self) -> Optional[plt.Figure]:
        """Create failure rate analysis chart"""
        
        try:
            failure_data = self.analysis.failure_table
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Group by threshold for plotting
            thresholds = failure_data['threshold'].unique()
            failure_rates = []
            threshold_labels = []
            
            for threshold in thresholds:
                threshold_data = failure_data[failure_data['threshold'] == threshold]
                avg_failure_rate = threshold_data['failure_rate_%'].mean()
                failure_rates.append(avg_failure_rate)
                threshold_labels.append(threshold)
            
            # Bar chart
            bars = ax.bar(range(len(threshold_labels)), failure_rates, 
                         color='lightcoral', alpha=0.7, edgecolor='black')
            
            # Add value labels on bars
            for i, (bar, rate) in enumerate(zip(bars, failure_rates)):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{rate:.1f}%', ha='center', va='bottom')
            
            ax.set_xlabel('Failure Threshold')
            ax.set_ylabel('Failure Rate (%)')
            ax.set_title('Monte Carlo Failure Analysis')
            ax.set_xticks(range(len(threshold_labels)))
            ax.set_xticklabels(threshold_labels, rotation=45)
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_ylim(0, max(failure_rates) * 1.1)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Warning: Could not create failure chart: {e}")
            return None
    
    def _create_success_probability_chart(self) -> Optional[plt.Figure]:
        """Create success probability over time chart"""
        
        try:
            # Calculate success rate by year
            df = self.results.get_outcome_df()
            balance_col = 'base_balance' if 'base_balance' in df.columns else 'end_balance'

            if 'year' not in df.columns:
                return None

            yearly_success = df.groupby('year').apply(
                lambda x: (x[balance_col] > 0).mean() * 100
            ).reset_index()
            yearly_success.columns = ['year', 'success_rate']
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(yearly_success['year'], yearly_success['success_rate'], 
                   marker='o', linewidth=2, markersize=4, color='green')
            
            ax.fill_between(yearly_success['year'], yearly_success['success_rate'], 
                           alpha=0.3, color='green')
            
            ax.set_xlabel('Year')
            ax.set_ylabel('Success Rate (%)')
            ax.set_title('Portfolio Success Probability Over Time\n(Percentage of Simulations with Positive Balance)')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 105)
            
            # Add horizontal reference lines
            ax.axhline(y=90, color='orange', linestyle='--', alpha=0.7, label='90% Success')
            ax.axhline(y=95, color='red', linestyle='--', alpha=0.7, label='95% Success')
            ax.legend()
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Warning: Could not create success probability chart: {e}")
            return None
