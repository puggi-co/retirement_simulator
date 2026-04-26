# Retirement Simulator Project Setup

_Save this as: `docs/context/project-setup.md`_

## Workspace Structure

```
retirement-simulator/
├── .vscode/
│   ├── settings.json
│   ├── tasks.json
│   └── extensions.json
├── docs/
│   ├── architecture/
│   │   ├── ADRs/
│   │   ├── data-models.md
│   │   └── api-contracts.md
│   ├── context/
│   │   ├── project-state.md
│   │   ├── constraints.md
│   │   └── ai-context.md
│   └── README.md
├── schemas/
│   ├── account-schema.json
│   ├── simulation-config-schema.json
│   └── results-schema.json
├── src/
│   ├── config/ # Static or user-defined settings: initialization and parameters
│   ├── context/ # Runtime metadata container: coordinates how workstreams are used
│   ├── ledger/ # Output recorder and financial tracking for simulation events
│   ├── runner/ # Execution flow controller: invokes context and workstreams
│   ├── schedule/
│   ├── workstream/ # Domain modules: perform and structure logic (e.g., tax, withdrawals)
│   ├── adjustment/
│   ├── interface/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── config/
    ├── tax-tables/
    └── life-expectancy/
```

## Initial VS Code Configuration

### .vscode/settings.json

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.rulers": [88, 120],
  "files.associations": {
    "*.md": "markdown",
    "*.json": "jsonc"
  },
  "json.schemas": [
    {
      "fileMatch": ["**/schemas/*.json"],
      "url": "./schemas/base-schema.json"
    }
  ]
}
```

### .vscode/tasks.json

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Setup Python Environment",
      "type": "shell",
      "command": "python",
      "args": ["-m", "venv", "venv"],
      "group": "build"
    },
    {
      "label": "Install Dependencies",
      "type": "shell",
      "command": "./venv/bin/pip",
      "args": ["install", "-r", "requirements.txt"],
      "group": "build"
    },
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "./venv/bin/pytest",
      "args": ["tests/", "-v"],
      "group": "test"
    },
    {
      "label": "Validate Schemas",
      "type": "shell",
      "command": "./venv/bin/python",
      "args": ["-m", "jsonschema", "schemas/"],
      "group": "build"
    },
    {
      "label": "Run Simulation",
      "type": "shell",
      "command": "./venv/bin/python",
      "args": ["-m", "src.main"],
      "group": "build"
    }
  ]
}
```

### .vscode/extensions.json

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint",
    "ms-python.black-formatter",
    "humao.rest-client",
    "redhat.vscode-yaml",
    "ms-vscode.vscode-json",
    "streetsidesoftware.code-spell-checker"
  ]
}
```

## Technology Stack Decisions

### Core Technologies

- **Language**: Python 3.9+ (excellent for financial calculations and data analysis)
- **Dependencies**:
  - NumPy/Pandas for numerical computations
  - Pydantic for data validation and serialization
  - Typer for CLI interface
  - Pytest for testing
  - JSONSchema for configuration validation

### Architecture Patterns

- **Domain-Driven Design**: Clear separation of financial domain logic
- **Hexagonal Architecture**: Ports and adapters for testing and extensibility
- **Strategy Pattern**: Different withdrawal and simulation strategies
- **Factory Pattern**: Creating different account types and simulation engines

## Next Steps

1. **Phase 1: Architectural Definition**

   - Define data models for accounts, transactions, and simulation results
   - Design API contracts for simulation services
   - Create JSON schemas for configuration validation

2. **Phase 2: AI-Assisted Implementation**

   - Generate domain models using Pydantic
   - Implement calculation engines with AI assistance
   - Create CLI interface and configuration management

3. **Phase 3: Testing & Integration**
   - Generate comprehensive test suites
   - Validate against real financial scenarios
   - Create documentation and usage examples

Would you like to proceed with Phase 1 and start defining the data architecture?
