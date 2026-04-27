import pandas as pd

from pathlib import Path
from datetime import datetime

# Core imports
from src.core.schedule import SimulationSchedule
from src.config.config_schema import SimulationConfig
from src.config.config_loader import get_simulation_config

# Input/Output imports
from src.io.portfolio_loader import prepare_portfolio, get_portfolio_from_excel
from src.io.tax_loader import get_tax_table

# Display settings
from src.export_util import debug_view
pd.options.display.float_format = '{:,.2f}'.format

def initialize(self) -> None:
    """Load and validate all required data"""
    print("🏗️  Initializing Retirement Simulation Orchestrator...")
    print("=" * 60)

    # 🎯 Safeguard: Python will make data/export/ folder if Git didn't track it!
    self.run_folder.mkdir(parents=True, exist_ok=True)
    print(f"📁 Created run folder: {self.run_folder}")

    self._load_configuration()
    self._load_tax_data()
    self._load_portfolio_data()
    self._create_simulation_schedule()

    print("✅ Initialization complete")
    print(f"   • Portfolio value: ${self.portfolio_df['base_balance'].sum():,.0f}")
    print(f"   • Simulation period: {self.schedule.duration} years (age {self.schedule.base_age}-{self.schedule.end_age})")
    print(f"   • Return rates: {self.config.return_low_rate:.1%} to {self.config.return_high_rate:.1%}")

# =================== PRIVATE METHODS ===================
    
def _load_configuration(self) -> None:
    """Load simulation configuration"""
    print("⚙️  Loading configuration...")
    # 🎯 self.config_path is already set to data/user/config.xlsx by the orchestrator!
    self.config = get_simulation_config(self.config_path)
    print(f"   • Base year: {self.config.base_year}")
    print(f"   • Spending target: ${self.config.spending_target:,.0f}")

def _load_tax_data(self) -> None:
    """Load tax tables"""
    print("💰 Loading tax data...")
    # 🎯 Pointing directly to your new data/import folder
    tax_path = self.data_folder / "import" / "tax_table.xlsx"
    self.tax_table = get_tax_table(file_path=tax_path)
    print("   • Tax tables loaded")

def _load_portfolio_data(self) -> None:
    """Load and process portfolio data"""
    print("💼 Loading portfolio data...")
    # 🎯 Pointing directly to your new data/user folder
    account_path = self.data_folder / "user" / "portfolio.xlsx"
    portfolio_loader = get_portfolio_from_excel(account_path)

    df_my_account = portfolio_loader.get('account')
    df_my_income = portfolio_loader.get('income')

    self.portfolio_df = prepare_portfolio(
        self.config, df_my_account, df_my_income
    )

    print(f"   • Accounts loaded: {len(df_my_account)} investment + {len(df_my_income)} income")

def _create_simulation_schedule(self) -> None:
    """Create simulation schedule from portfolio data"""
    print("📅 Creating simulation schedule...")
    self.schedule = SimulationSchedule.from_account_data(
        self.portfolio_df, config=self.config
    )
    print(f"   • Schedule: {self.schedule.duration} years (age {self.schedule.base_age} to {self.schedule.end_age})")

def _validate_initialization(self) -> bool:
    """Validate that all required components are initialized"""
    return all([
        self.config is not None,
        self.tax_table is not None,
        self.portfolio_df is not None,
        self.schedule is not None
    ])