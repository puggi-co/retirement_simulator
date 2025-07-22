class AccountLedger:
    """Tracks one account's year-by-year ledger"""
    def __init__(self):
        self.scenario_id = ''
        self.df_ledger = pd.DataFrame({
            'year': pd.Series(dtype='int'),
            'age': pd.Series(dtype='int'),
            'account_name': pd.Series(dtype='string'),
            'return_rate': pd.Series(dtype='float'),
            'withdrawal_mode': pd.Series(dtype='string'),
            'scenario_id': pd.Series(dtype='string'),
            'begin_balance': pd.Series(dtype='float'),
            'current_balance': pd.Series(dtype='float'),
            'end_balance': pd.Series(dtype='float'),
            'withdrawal_amount': pd.Series(dtype='float'),
            'omd': pd.Series(dtype='float'),
            'rmd': pd.Series(dtype='float'),
            'ord_inc': pd.Series(dtype='float'),
            'ssa_inc': pd.Series(dtype='float'),
            'taxable_gain': pd.Series(dtype='float'),
            'taxable_income': pd.Series(dtype='float'),
            'taxable_ssa': pd.Series(dtype='float'),
            'tax_owed': pd.Series(dtype='float'),
            'effective_tax_rate': pd.Series(dtype='float'),
            'rmd_begin_year': pd.Series(dtype='int'),
            'rmd_age': pd.Series(dtype='int'),
            'rmd_table': pd.Series(dtype='string'),
            'roth_convert_amount': pd.Series(dtype='float'),
            'account_type': pd.Series(dtype='string'),
            'filing_status': pd.Series(dtype='string'),
            'account_tax_type': pd.Series(dtype='string'),
        })

    def set_scenario(self, scenario_id):
        self.scenario_id = scenario_id
        
    def add_year(
        self, year=0, age=0, return_rate=0.0, withdrawal_mode='unknown', account_name='', 
        begin_balance=0.0, current_balance=0.0, end_balance=0.0, 
        withdraw_amount=0.0, omd=0.0, rmd=0.0, ord_inc=0.0, ssa_inc=0.0, 
        taxable_income=0.0, taxable_gain=0.0, taxable_ssa=0.0, tax_owed=0.0, effective_tax_rate=0.0, 
        roth_convert_amount=0.0,rmd_begin_year=0, rmd_age=0, rmd_table='',
        account_type='', account_tax_type='', filing_status=''
    ):
    
        new_year = {
            'year': year,
            'age': age,
            'return_rate': return_rate,
            'withdrawal_mode': withdrawal_mode,
            'account_name': account_name,
            'scenario_id': self.scenario_id,
            'begin_balance': round(begin_balance, 2),
            'current_balance': round(current_balance, 2),
            'end_balance': round(end_balance, 2),
            'withdrawal_amount': round(withdraw_amount, 2),
            'omd': round(omd, 2),
            'rmd': round(rmd, 2),
            'ord_inc': round(ord_inc, 2),
            'ssa_inc': round(ssa_inc, 2),
            'taxable_gain': round(taxable_gain, 2),
            'taxable_income': round(taxable_income, 2),
            'taxable_ssa': round(taxable_ssa, 2),
            'tax_owed': round(tax_owed, 2),
            'effective_tax_rate': round(effective_tax_rate, 3),
            'roth_convert_amount': round(roth_convert_amount, 2),
            'rmd_begin_year': rmd_begin_year,
            'rmd_age': rmd_age,
            'rmd_table': rmd_table,
            'account_type': account_type,
            'account_tax_type': account_tax_type or None,
            'filing_status': filing_status or None
        }
    
        self.df_ledger = pd.concat([self.df_ledger, pd.DataFrame([new_year])], ignore_index=True)

