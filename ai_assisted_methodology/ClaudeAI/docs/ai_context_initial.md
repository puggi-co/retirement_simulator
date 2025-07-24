# AI Context - Retirement Simulator
*Save this as: `docs/context/ai-context.md`*

## Current Objective
Setting up foundational data architecture for retirement planning simulator with focus on account models, tax calculations, and withdrawal strategies.

## Project Overview
Python-based retirement simulator that models:
- Multiple account types (taxable, tax-deferred, tax-free)
- Various withdrawal strategies with tax optimization
- Monte Carlo analysis across market scenarios
- RMD management and Roth conversion strategies

## Relevant Architecture
- **Domain Model**: Financial accounts, tax models, simulation configurations
- **Patterns**: Domain-driven design, hexagonal architecture, strategy pattern
- **Data Validation**: Pydantic models with JSON schema validation
- **Testing**: Pytest with comprehensive financial scenario coverage

## Technical Constraints
- **Language**: Python 3.9+
- **Key Dependencies**: NumPy, Pandas, Pydantic, Typer
- **Code Style**: Black formatting, 88-character line limit
- **Architecture**: Clear separation between domain logic and infrastructure
- **Testing**: Unit tests for all financial calculations, integration tests for workflows

## Current Phase: Data Architecture Definition
**Priority**: Define core domain models starting with account structures

**Next Steps**:
1. Create JSON schemas for account types and portfolio structure
2. Design simulation configuration schema
3. Model tax calculation inputs and results
4. Generate corresponding Pydantic models

## Coding Standards
- Use Pydantic for all data models with validation
- Type hints required for all functions
- Docstrings following Google style
- Separate pure functions for calculations from stateful services
- Configuration-driven rather than hard-coded values

## Financial Domain Rules
- Account types have different tax treatment (ordinary income vs capital gains)
- RMDs are mandatory after age 73 for tax-deferred accounts
- Tax brackets and rates change annually
- Withdrawal order affects tax efficiency
- Social Security has complex taxation rules

## Success Criteria
- Clean, validated data models that accurately represent financial concepts
- Extensible architecture that supports multiple withdrawal strategies
- Comprehensive test coverage for financial calculations
- Clear separation between tax rules and calculation logic