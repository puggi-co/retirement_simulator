# ── Workbook Interface ──────────────────────────
class WorkbookInterface:
    """Loads user input via Excel and exposes structured DataFrames."""

    def __init__(self, workbook='RetirementPlan-Input.xlsx'):
        # ─ Inputs ─
        self.workbook = workbook
        self.tabs = WORKBOOK_TABS

        # ─ User Input / Scenario Data ─
        self.df_my_portfolio = None
        self.df_scenario = None
        self.config=None

        # ─ Tax Tables ─
        self.df_amt = None
        self.df_capital_gain = None
        self.df_standard_deduction = None
        self.df_tax_brackets = None
        self.df_lef_factors = None

        # ── Accessor Registry ────────────────────────
        self._registry = {
            'porfolio': lambda: self.df_my_portfolio,
            'scenario': lambda: self.df_scenario,
            'schedule': lambda: self.sim_schedule,
            'config': lambda: self.config,
            'scenario_config': lambda: self.scenario_config,
            'montecarlo_config': lambda: self.montecarlo_config,
            'amt': lambda: self.df_amt,
            'capital_gain': lambda: self.df_capital_gain,
            'lef': lambda: self.df_lef,
            'standard_deduction': lambda: self.df_standard_deduction,
            'tax_bracket': lambda: self.df_tax_bracket
        }

    def get(self, name):
        if name in self._registry:
            return self._registry[name]()
        raise KeyError(f"No accessor named '{name}' found.")
        
    # ── Loaders ──────────────────────────────────
    def load_workbook(self):
        """Reads Excel sheets and builds structured DataFrames."""
        try:
            for tab in self.tabs:
                
                raw_df = pd.read_excel(self.workbook, sheet_name=tab)
                cleaned_df = self.clean_sheet(raw_df, REQUIRED_COLUMNS.get(tab), sheet_name=tab)
                
                if tab == 'My_Accounts':
                    self.df_my_account = cleaned_df
                elif tab == 'My_Income':
                    df_my_income = cleaned_df
                elif tab == 'My_Config':
                    df_config = cleaned_df
                elif tab == 'T_AMT':
                    self.df_amt = cleaned_df
                elif tab == 'T_CapitalGain':
                    self.df_capital_gain = cleaned_df
                elif tab == 'T_TaxBrackets':
                    self.df_tax_bracket = cleaned_df
                elif tab == 'T_StandardDeduction':
                    self.df_standard_deduction = cleaned_df
                elif tab == 'T_LEF':
                    self.df_lef = cleaned_df
                    

        except Exception as e:
            raise RuntimeError(f'❌ Error loading workbook: {e}')
        
        self.df_my_portfolio = merge_income_sources(self.df_my_account, df_my_income)
        self.df_scenario = self.load_scenarios()

        self.config, self.scenario_config, self.montecarlo_config = self.split_config(df_config)
        self.sim_schedule = self.sim_schedule(self.df_my_portfolio, inflation_rate=self.config.inflation_rate)

    def load_scenarios(self, source=None):
        if source is None:
            df = pd.DataFrame(SCENARIO_DATA)
        elif source.endswith('.json'):
            df = pd.read_json(source)
        else:
            df = pd.read_excel(self.workbook, sheet_name='My Scenarios')

        return self.clean_sheet(df, REQUIRED_COLUMNS.get('My Scenarios'), sheet_name='My Scenarios')

    def clean_sheet(self, df, required_cols=None, sheet_name=''):
        """Standardizes column names and validates required fields."""
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
#        print(f'Columns found in '{sheet_name}':', list(df.columns))

        if required_cols:
            missing = required_cols - set(df.columns)
            if missing:
                raise ValueError(f"❌ Sheet '{sheet_name}' is missing required column(s): {missing}")

        reserved = {'Name', 'Index', 'Values', 'Dtype', 'Shape', 'Size'}
        risky = set(df.columns) & reserved
        if risky:
            print(f"⚠️ Sheet '{sheet_name}': Column(s) {risky} may conflict with pandas attributes. Use row[...] syntax.")

        return df
        
    def FUTURE_convert_excel_to_json(workbook_path, sheet_name='My Scenarios', output_path='MyScenarios.json'):
        df = pd.read_excel(workbook_path, sheet_name=sheet_name)
        clean_df = self.clean_sheet(df, REQUIRED_COLUMNS.get(sheet_name), sheet_name=sheet_name)
        clean_df.to_json(output_path, orient='records', indent=2)

    def split_config(self, config_df):
        """Returns consolidated and split configs into simulation-specific config objects using 'Y'/'N'/blank flags."""

        # Normalize scenario flags
        cols = ["scenario_default", "montecarlo_default"]
        config_df[cols] = (
            config_df[cols]
            .fillna("N")
            .astype(str)
            .apply(lambda s: s.str.strip().str.upper() == "Y")
        )

        # Create default SimulationConfig instance for fallback values
        defaults = SimulationConfig()

        def to_simulation_config(df_filtered):
            config_dict = dict(zip(df_filtered["parameter"], df_filtered["value"]))

            def get_val(key):
                val = config_dict.get(key)
                if pd.isna(val):
                    return getattr(defaults, key)
                return val

            def get_typed_val(key):
                default_val = getattr(defaults, key)
                val = get_val(key)
                if isinstance(default_val, bool):
                    val_str = str(val).strip().lower()
                    if isinstance(val, bool):
                        return val
                    if val_str in ("true", "yes", "1", "y"):
                        return True
                    if val_str in ("false", "no", "0", "n"):
                        return False
                    return default_val
                if isinstance(default_val, int):
                    return int(val)
                if isinstance(default_val, float):
                    return float(val)
                if isinstance(default_val, str):
                    return str(val)
                return val  # Fallback for optional or non-scalar fields

            kwargs = {f.name: get_typed_val(f.name) for f in fields(SimulationConfig) if f.init}
            return SimulationConfig(**kwargs)

        config = to_simulation_config(config_df)
        scenario_config = to_simulation_config(config_df[config_df["scenario_default"]])
        montecarlo_config = to_simulation_config(config_df[config_df["montecarlo_default"]])

        return config, scenario_config, montecarlo_config

    def sim_schedule(self, df_my_account, inflation_rate = DEFAULT_INFLATION, max_age=120):
        """Compute simulation timing parameters based on birth year."""

        begin_year = df_my_account['begin_year'].min()
        begin_age = df_my_account['owner_age'].min()
        duration = max_age - begin_age
        end_year = begin_year + duration - 1
        end_age = begin_age + duration

        return SimulationSchedule(
            begin_age=int(begin_age),
            begin_year=int(begin_year),
            duration=int(duration),
            end_age=int(end_age),
            end_year=int(end_year),
            inflation_rate=float(inflation_rate)
        )
        
    def build_schedule(schedule_dict) -> SimulationSchedule:
        return SimulationSchedule(
            begin_age=schedule_dict['begin_age'],
            begin_year=schedule_dict['begin_year'],
            duration=schedule_dict['duration'],
            end_age=schedule_dict['end_age'],
            end_year=schedule_dict['end_year']
        )