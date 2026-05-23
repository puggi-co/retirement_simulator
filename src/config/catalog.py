from dataclasses import dataclass
from typing import List

@dataclass
class CatalogEntry:
    strategy_id: str
    sim_mode: str
    draw_order: List[str]


CATALOG = {

    # ---------------------------------------------------------
    # WITHDRAWAL ORDER AND SPENDING MODEL COMBINATIONS
    # ---------------------------------------------------------

    'taxable_first': CatalogEntry(
        strategy_id='taxable_first',
        sim_mode='taxable_first',
        draw_order=['taxable', 'deferred', 'exempt'],
    ),

    'deferred_first': CatalogEntry(
        strategy_id='deferred_first',
        sim_mode='deferred_first',
        draw_order=['deferred', 'taxable', 'exempt'],
    ),

    'fixed_rate_tax_efficient': CatalogEntry(
        strategy_id='fixed_rate_tax_efficient',
        sim_mode='fixed_rate_tax_efficient',
        draw_order=['taxable', 'deferred', 'exempt'],
    ),

}
