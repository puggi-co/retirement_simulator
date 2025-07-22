Module Integration Blueprint
File	Role in Orchestration	Notes
config_context.py	Parse and validate user configuration	Instantiate SimulationConfig, set up context objects
wbi.py	Load market/benchmark/inflation data	Used during ScenarioRunner or Monte Carlo runs
adjustments.py	Apply COLA, inflation, and other adjustments	May hook into initial data setup or simulations
ledger.py	Maintain time-series portfolio/account records	Central to tracking withdrawals, taxes, balances
sim_withdrawal.py	Encode withdrawal logic (e.g., Guardrails)	Receives context + current year and returns actions
tax_models.py	Calculate taxes and impact on ledger	Likely invoked post-withdrawal planning
sim_montecarlo.py	Run simulations across randomized returns	Can use ledger + withdrawal + tax models for each trial
runner.py	Orchestrate full scenario runs	Wrap all the above for year-by-year execution
README.md	Not invoked in code, but should be kept in sync	Document entry point and usage tips