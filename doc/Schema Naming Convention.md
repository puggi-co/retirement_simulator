# 📘 Schema Naming Governance Document

**Retirement Simulator — Schema & Column Naming Standards**  
**Version:** 2025.04.30  
**Status:** Active  
**Scope:** Excel Input Schemas, Portfolio Schema, Withdrawal Ledger, Outcome Ledger,
Future Tax Summary Ledger

---

## 1. Purpose

This document defines the authoritative naming conventions for all schema constants and
column names used across the Retirement Simulator.  
It ensures:

- deterministic schema evolution
- backward‑compatible data structures
- consistent naming across all surfaces
- clarity for developers and analysts
- prevention of schema drift

These rules apply to:

- Excel input schemas
- Portfolio schema
- Withdrawal Ledger (WD)
- Outcome Ledger
- Future Tax Summary Ledger

---

## 2. Global Naming Rules

### 2.1 Column Names

All column names must follow:

- lowercase snake_case
- data‑first naming (avoid semantic/descriptive naming)
- no prefixes or suffixes except `_flag` or `_met` for booleans
- no abbreviations unless industry‑standard (e.g., ltcg, qcd)

**Correct examples:**

```
account_name
base_balance
taxable_income
qualified_dividend_income
qcd_amount
goal_met
synthetic_flag
```

**Incorrect examples:**

```
AccountName
ownerAge
withdrawalAmount
isGoalMet
```

---

### 2.2 Temporal Fields

Temporal fields are unified across all schemas:

| Concept                | Column Name |
| ---------------------- | ----------- |
| Simulation year        | `year`      |
| Owner age in that year | `age`       |

These names are reserved and must not be repurposed.

---

### 2.3 Balance Lifecycle Fields

Balance fields follow a strict lifecycle naming pattern:

| Meaning                   | Column Name       | Surfaces               |
| ------------------------- | ----------------- | ---------------------- |
| Starting balance (static) | `base_balance`    | Portfolio, WD, Outcome |
| Start‑of‑year balance     | `current_balance` | WD                     |
| End‑of‑year balance       | `end_balance`     | WD, Outcome            |

No other balance field names are permitted.

---

### 2.4 Boolean Fields

Boolean fields must end with:

- `_flag` (state indicator)
- `_met` (goal/condition satisfied)

**Examples:**

```
synthetic_flag
shortfall_flag
goal_met
closure_met
rmd_met
mc_failure_flag
```

---

### 2.5 Tax Fields

Tax fields must align with IRS categories:

| Category                           | Column Name                 | Notes                                      |
| ---------------------------------- | --------------------------- | ------------------------------------------ |
| Ordinary income                    | `ordinary_income`           | Includes interest, STCG, IRA distributions |
| Long‑term capital gains            | `ltcg_income`               | Year‑level aggregate                       |
| Qualified dividends                | `qualified_dividend_income` | Year‑level aggregate                       |
| Qualified charitable distributions | `qcd_amount`                | Not income                                 |

**WD Ledger Rule:**  
WD ledger remains minimal and uses only:

```
taxable_income
taxable_gain
```

Decomposition occurs only in the Outcome Ledger.

---

## 3. Schema Constant Naming Rules

### 3.1 Schema Column Groups

Schema column groups follow this pattern:

```
<SCHEMA>_<CATEGORY>_COLUMNS
```

Where `<SCHEMA>` ∈ { ACCOUNT_SHEET, INCOME_SHEET, PORTFOLIO, WD_LEDGER, OUTCOME }.

**Examples:**

```
PORTFOLIO_OWNER_COLUMNS
WD_LEDGER_FINANCIAL_COLUMNS
OUTCOME_TAX_COLUMNS
```

---

### 3.2 Consolidated Schema Columns

Each schema defines a consolidated list:

```
<SCHEMA>_SCHEMA_COLUMNS
```

This is the authoritative column order.

---

### 3.3 Dtype Constants

Dtypes follow:

```
<SCHEMA>_SCHEMA_DTYPES
```

Allowed dtype strings:

- string
- Int64
- Float64
- boolean

---

### 3.4 Schema Groups

Grouping constants follow:

```
<SCHEMA>_SCHEMA_GROUPS
```

Groups must map semantic categories to column lists.

Groups must not include:

- version constants
- metadata not tied to columns
- derived fields

---

### 3.5 Schema Version Constants

Each schema has exactly one version constant:

```
<SCHEMA>_SCHEMA_VERSION = "YYYY.MM.DD"
```

Rules:

- Version increments only when schema columns change
- Logic changes do not trigger version bumps
- Version is written into ledger rows via `schema_version`
- Version is not included in schema groups

---

## 4. Reserved Column Names

The following names are globally reserved and must not be repurposed:

```
year
age
base_balance
current_balance
end_balance
taxable_income
taxable_gain
ordinary_income
ltcg_income
qualified_dividend_income
qcd_amount
schema_version
sim_id
sim_mode
sim_type
sim_num
sim_rate
```

---

## 5. Governance Enforcement

### 5.1 Required Checks Before Merging Schema Changes

Any schema change must include:

- schema diff summary
- version bump
- updated documentation
- updated validation tests
- backward‑compatibility review

---

### 5.2 Required Tests

- Column presence validation
- Dtype validation
- Group membership validation
- Schema version propagation test
- Round‑trip CSV/Parquet compatibility test

---

## 6. Future Extensions

This governance document anticipates:

- Tax Summary Ledger schema
- RMD Ledger schema
- Income Projection schema
- Multi‑scenario comparison schema

All future schemas must follow the rules defined here.

---

## 7. Change Log

| Version    | Date    | Description                      |
| ---------- | ------- | -------------------------------- |
| 2025.04.30 | Initial | First formal governance document |
