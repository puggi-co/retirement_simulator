from dataclasses import dataclass

@dataclass
class StrategyDefinition:
    strategy_id: str
    wd_id: str
    mc_id: str
    sim_mode: str
    sim_name: str
    include_dashboard: bool
    tax_deferred_notes: str
    taxable_notes: str
    tax_exempt_notes: str
    pros: str
    cons: str
    key_concepts: str = ''  # Optional extras

    def determine_draw_order(self) -> list[str]:
        """
        Returns account drawdown order based on strategy ID.
        """
        draw_order_map = {
        'fixed_rate': ['taxable', 'deferred', 'exempt'],
        'fixed_amount': ['taxable', 'deferred', 'exempt'],
        'fixed_amount_roth': ['deferred', 'taxable', 'exempt'],
        'guardrail_amount': ['taxable', 'deferred', 'exempt'],
        'guardrail_amount_roth': ['deferred', 'taxable', 'exempt'],
        }

        return draw_order_map.get(self.strategy_id, ['taxable', 'deferred', 'exempt'])

STRATEGY_CATALOG = {
    'fixed_rate': StrategyDefinition(
        strategy_id='fixed_rate',
        wd_id='wd_fixed_rate',
        mc_id='mc_fixed_rate',
        sim_mode='fixed_rate',
        sim_name='Fixed Rate Rule – Taxable First',
        include_dashboard=True,
        tax_deferred_notes="RMDs may force withdrawals beyond the fixed rate %. All withdrawals are taxed as ordinary income.",
        taxable_notes="Withdrawals follow fixed percentage logic. Capital gains and dividends handled via standard deduction and AMT.",
        tax_exempt_notes="Qualified withdrawals are tax-exempt. No RMDs.",
        pros="Simple and predictable.",
        cons="Does not optimize across account types.",
        key_concepts="Withdraws an annual inflation-adjusted fixed percentage. Accounts expected to deplete in ~30 years."
    ),

    'fixed_amount': StrategyDefinition(
        strategy_id='fixed_amount',
        wd_id='wd_fixed_amount',
        mc_id='mc_fixed_amount',
        sim_mode='fixed_amount',
        sim_name='Fixed Amount – Taxable First',
        include_dashboard=True,
        tax_deferred_notes="RMDs are delayed until RMD age. Withdrawals taxed as ordinary income.",
        taxable_notes="Withdraws target amount minus RMDs. Prioritizes taxable accounts first.",
        tax_exempt_notes="Used only after other accounts are depleted. No RMDs.",
        pros="Minimizes deferred account growth early.",
        cons="May trigger capital gains and reduce compounding.",
        key_concepts="Drawdown order: Taxable → Deferred → Exempt."
    ),

    'fixed_amount_roth': StrategyDefinition(
        strategy_id='fixed_amount_roth',
        wd_id='wd_fixed_amount_roth',
        mc_id='mc_fixed_amount_roth',
        sim_mode='fixed_amount_roth',
        sim_name='Fixed Amount – Roth Conversion',
        include_dashboard=True,
        tax_deferred_notes="Withdraws from deferred accounts first and converts to Roth up to bracket ceilings. RMDs begin at RMD age.",
        taxable_notes="Capital gains deferred until later years. Taxable accounts used after Roth conversion window.",
        tax_exempt_notes="Converted Roth accounts grow tax-free. Withdrawals are tax-exempt after 5-year lockout.",
        pros="Minimizes future taxes and boosts tax-exempt compounding.",
        cons="Converted amounts taxed and locked for 5 years.",
        key_concepts="Drawdown order: Deferred → Taxable → Exempt. Roth conversions target bracket ceilings before SSA/RMDs."
    ),

    'guardrail_amount': StrategyDefinition(
        strategy_id='guardrail_amount',
        wd_id='wd_guardrail_amount',
        mc_id='mc_guardrail_amount',
        sim_mode='guardrail_amount',
        sim_name='Guardrail Amount – Taxable First',
        include_dashboard=True,
        tax_deferred_notes="Withdrawals triggered only when taxable accounts can't meet guardrail-adjusted targets. RMDs begin at RMD age.",
        taxable_notes="Primary source of withdrawals. Guardrails adjust annual amounts based on market and inflation conditions.",
        tax_exempt_notes="Used only after taxable and deferred accounts are depleted. No RMDs.",
        pros="Preserves deferred growth while adapting to market conditions.",
        cons="May trigger capital gains and reduce long-term taxable compounding.",
        key_concepts="Dynamic withdrawal targets with drawdown order: Taxable → Deferred → Exempt. Guardrails respond to inflation and market performance."
    ),

    'guardrail_amount_roth': StrategyDefinition(
        strategy_id='guardrail_amount_roth',
        wd_id='wd_guardrail_amount_roth',
        mc_id='mc_guardrail_amount_roth',
        sim_mode='guardrail_amount_roth',
        sim_name='Guardrail Amount – Roth Conversion',
        include_dashboard=True,
        tax_deferred_notes="Primary source of withdrawals. Converts to Roth up to bracket ceilings. RMDs begin at RMD age.",
        taxable_notes="Capital gains deferred until later years. Taxable accounts used after Roth conversion window.",
        tax_exempt_notes="Converted Roth accounts grow tax-free. Withdrawals are tax-exempt after 5-year lockout.",
        pros="Delays taxable events and may reduce early tax burden.",
        cons="Accelerates RMD exposure and ordinary income if conversions are skipped.",
        key_concepts="Dynamic withdrawal targets with drawdown order: Deferred → Taxable → Exempt. Roth conversions respond to market and inflation guardrails."
    )
}
