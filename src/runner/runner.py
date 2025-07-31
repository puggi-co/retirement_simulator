# ── Standard Library ─────────────────────────────
import os

# ── Third-Party Libraries ────────────────────────
import pandas as pd

# ── Internal Modules ─────────────────────────────
from ledger import AccountLedger
from tax_models import TaxTables
from src.workstream.withdrawal.sim_withdrawal import simulate_scenario_withdrawals
from src.workstream.montecarlo.sim_montecarlo import simulate_montecarlo_withdrawals
from src.core.workstream.tax.tax_accessors import get_tax_tables
from analysis import summarize_spending_sources, log_scenario_summary

from src.workstream.scenario.scenario_config import SCENARIO_CATALOG
from src.context.context import SimulationContext  

def build_context_objects(config, schedule, scenario_key):
    scenario_cfg = SCENARIO_CATALOG[scenario_key]
    return SimulationContext(
        config=config,
        schedule=schedule,
        scenario_id=scenario_cfg.scenario_id,
        withdrawal_mode=scenario_cfg.withdrawal_mode,
        include_dashboard=scenario_cfg.include_dashboard,
        is_montecarlo=bool(scenario_cfg.montecarlo_id),
    )

# ── Scenario Execution Engine ───────────────────
class ScenarioRunner:
    """Run withdrawal and montecarlo simulations and exports results."""

    def __init__(self, context, df_my_portfolio, return_rate, wb=None):
        self.context = context
        self.config = context.config
        self.schedule = context.schedule
        self.df_my_portfolio = df_my_portfolio
        self.return_rate = return_rate
        self.wb = wb
        self.ledger = AccountLedger()
        self.results = None
        self.analysis = None

        # Assign scenario ID to the ledger for downstream reporting
        self.ledger.set_scenario(self.context.scenario_id)
        
        # Assign context values to the ledger
#        self.scenario_id = context.scenario_id
#        self.mode = context.withdrawal_mode
#        self.ledger.set_scenario(self.scenario_id)

    # ── Core Engine ──────────────────────────────
    def run_strategy(self):
        """Run a single scenario based on context metadata."""
    
        tax_tables = get_tax_tables(self.wb)
        df_deduction = tax_tables.deduction
        df_bracket   = tax_tables.bracket
        df_lef       = tax_tables.lef

        portfolio_df = self.prepare_portfolio_df()
        scenario_id = self.context.scenario_id
        withdrawal_mode = self.context.withdrawal_mode
        roth_flag = (scenario_id == 'roth_conversion')
        
        if self.context.is_montecarlo:
            self.run_simulation(mode=withdrawal_mode)
        else:
            self.results = simulate_scenario_withdrawals(
                context=self.context,
                tax_tables=tax_tables,
                portfolio_df=portfolio_df,
                return_rate=self.return_rate,
                ledger=self.ledger,
                roth=roth_flag 
            )

    def prepare_portfolio_df(self):
        """Augments user portfolio with computed columns needed for simulation."""
        
        portfolio_df = self.df_my_portfolio.copy()
        
        portfolio_df['return_rate'] = self.return_rate
        portfolio_df['withdrawal_mode'] = self.context.withdrawal_mode
        portfolio_df['current_balance'] = portfolio_df['begin_balance']
        portfolio_df['end_balance'] = portfolio_df['begin_balance']
    
        portfolio_df['year'] = portfolio_df['age'] = None
        portfolio_df[['withdrawal_amount', 'omd', 'rmd', 'ord_inc', 'ssa_inc', 'roth_convert_amount',
                      'tax_owed', 'taxable_gain', 'taxable_income', 'taxable_ssa', 'effective_tax_rate']] = 0.0
        portfolio_df['scenario_id'] = self.context.scenario_id
    
        portfolio_df = portfolio_df[[  # column ordering
            'year', 'age', 'return_rate','withdrawal_mode', 'account_name',
            'scenario_id', 'begin_balance', 'current_balance', 'end_balance',
            'withdrawal_amount', 'omd', 'rmd', 'ord_inc', 'ssa_inc',
            'taxable_gain', 'taxable_income', 'taxable_ssa', 'tax_owed', 'effective_tax_rate',
            'roth_convert_amount', 'rmd_begin_year', 'rmd_age', 'rmd_table',
            'account_type', 'account_tax_type', 'filing_status'
        ]]
        
        return portfolio_df

    # Monte Carlo Simulation
    def run_simulation(self, mode='fixed_rate', num_simulations=1000):
        print(f'🔁 Running Monte Carlo simulation for mode [{mode}]...')
 
        self.results = simulate_montecarlo_withdrawals(
            context=self.context,
            df_accounts=self.df_my_portfolio,
            num_simulations=num_simulations
        )
#        display('runner mc run_sim', self.results)
        print('✅ Simulation complete.')

    def analyze_results(self, excel_path=None, pdf_path=None):
        if self.results is None:
            raise ValueError('Run the simulation first.')
        print('📊 Analyzing results...')
#        display(self.results)
#        self.analysis = summarize_withdrawal_outcomes(
#            df_sim_results=self.results,
#            export_excel_path=excel_path,
#            export_pdf_path=pdf_path
#        )
        
        df_spending_sources = summarize_spending_sources(self.results)
        self.spending_summary = df_spending_sources  # optional: store for later access
#        df_spending_sources.to_excel(writer, sheet_name='Spending Sources', index=False)
        df_spending_sources.to_excel('spending_sources.xlsx', index=False)

        print('\n💵 Spending Composition by Year')
        print(df_spending_sources.round(2).to_string(index=False))
        
        print('📁 Results exported.' if excel_path or pdf_path else '📈 Analysis complete.')

    def preview_summary(self):
        if self.analysis:
            summary, failures, *_ = self.analysis
            print('\n🧾 Summary:'); print(summary)
            print('\n🚧 Failure Thresholds:'); print(failures)
        else:
            print('No analysis available yet.')

    # ── Exporters ────────────────────────────────
    def export_all_to_folder(self, folder: str, include_summary=True, include_dashboard=True):
        import os  # defensive import
    
        scenario_id = self.context.scenario_id
        excel_name = f'{scenario_id}_results.xlsx'
        pdf_name = f'{scenario_id}_charts.pdf'
        excel_path = os.path.join(folder, excel_name)
        pdf_path = os.path.join(folder, pdf_name)
    
        # 🔍 Optional summary logging
        if include_summary:
            log_scenario_summary(
                context=self.context,
                summary_df=self.spending_summary if hasattr(self, 'spending_summary') else None,
                folder=folder
            )
    
        # 💾 Export dashboard if requested
        if include_dashboard:
            # Ensure result structure compatibility
            if 'strategy' not in self.results.columns:
                self.results['strategy'] = scenario_id
            if 'simulation' not in self.results.columns:
                self.results['simulation'] = 1  # default for single-run
    
            self.analyze_results(
                excel_path=excel_path,
                pdf_path=pdf_path
            )
    
        print(f"📦 Export complete for strategy '{self.context}' → {folder}")

