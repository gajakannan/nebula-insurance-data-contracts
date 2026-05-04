# Nebula Insurance Data Contracts

Nebula Insurance Data Contracts is a platform-neutral canonical data contract library for insurance data products.

The contracts are authored in **ODCS v3 YAML** and organized by insurance domain. The first domain package focuses on **Property & Casualty (P&C)** insurance, with room to expand later into Life, Health, Annuity, Reinsurance, and shared cross-domain insurance concepts.

This repository is part of the broader Nebula ecosystem: an effort to make AI-assisted insurance software delivery more structured, inspectable, reusable, and governed.

---

## Purpose

Insurance data is usually scattered across policy administration systems, claims systems, billing systems, CRM platforms, spreadsheets, reporting marts, and vendor applications. Each system has its own naming, shape, lifecycle assumptions, and business meaning.

This repository defines a canonical contract layer for insurance data products.

The goal is not to mirror any source system, vendor model, physical database schema, or external reference model. The goal is to define clear, reusable, business-aligned data contracts that can serve as the stable center of gravity for insurance data work.

These contracts are intended to support:

- Data product design
- Lakehouse and warehouse modeling
- Medallion architecture implementation
- Source-to-canonical data mapping
- Data quality validation
- Semantic layer design
- AI-assisted data engineering
- Analytics, reporting, and operational intelligence
- Event and API schema alignment
- Cross-platform implementation

---

## Core idea

The repository follows a contract-first approach:

```text
Business concept
    ↓
Canonical insurance entity
    ↓
ODCS data contract
    ↓
Target-specific implementation
````

The canonical contracts define the intended business shape of the data.

Platform-specific targets such as Microsoft Fabric, Databricks, Snowflake, dbt, Kafka, Postgres, APIs, or semantic models should be generated from or aligned to these contracts, not the other way around.

---

## Design posture

This repository is:

```text
Source-informed
Contract-first
Platform-neutral
Insurance-domain native
P&C-first
Extensible to other insurance domains
```

This repository is not:

```text
A copied reference model
A vendor schema
A database dump
A Fabric-only implementation
A Databricks-only implementation
A reporting mart
A raw source-system model
A one-to-one translation of any external standard
```

---

## Provenance boundary

The distributable contents of this repository should not include raw artifact names, or external source URLs.

The contracts should stand on their own as original canonical insurance data contracts.

Research, comparison work, source review, downloaded artifacts, and scratch mappings must remain outside the committed repository.

Use private/local folders such as:

```text
_private-research/
_external-sources/
_source-review/
_scratch/
```

These folders are intentionally excluded through `.gitignore`.

---

## Why ODCS?

ODCS provides a structured way to describe data contracts using YAML.

In this repository, ODCS is the authoring format for canonical contracts. The repo name intentionally uses `data-contracts` rather than `odcs` because ODCS is the current contract standard, while the broader product concept is canonical insurance data contracts.

The contracts may later be used to generate or align:

* Lakehouse tables
* Warehouse tables
* dbt models
* Kafka schemas
* JSON Schema
* Avro schemas
* API specifications
* Semantic models
* Data quality rules
* Data product documentation

---

## Current domain focus

The first domain package is **Property & Casualty insurance**.

The initial P&C modeling spine is:

```text
Party
PartyRole
PartyRelationship

Agreement
Policy
PolicyTerm

Product
Coverage
PolicyCoverage

InsurableObject
InsurableObjectClassification

Exposure
VehicleExposure
PropertyExposure
WorkersCompExposure

Claim
ClaimEvent
ClaimCoverage

FinancialTransaction
PolicyFinancialTransaction
ClaimFinancialTransaction
FinancialTransactionClassification

GeographicLocation
LocationAddress

Assessment
RiskAssessment
UnderwritingAssessment
```

This shape is intentional. It favors business usability and data product clarity over mechanically reproducing source-system tables or deeply normalized subtype structures.

---

## Key modeling principles

### 1. Canonical contracts are not source tables

A canonical contract should not be copied from a source system, physical DDL, vendor model, external schema, or reporting mart.

Source structures may inform design thinking, but canonical contracts must use stable insurance business concepts.

### 2. Exposures are first-class concepts

In insurance, exposure is where much of the analytical and underwriting value lives.

A policy is the contractual container.
Coverage defines what protection applies.
An insurable object identifies what may be insured.
An exposure describes the measurable risk basis.

Examples:

```text
Exposure
VehicleExposure
PropertyExposure
WorkersCompExposure
```

This is preferred over blindly modeling every insured-object subtype as its own top-level canonical contract.

### 3. Financial activity should be transaction-oriented

Financial concepts should not explode into one contract per money subtype.

Prefer a cleaner model:

```text
FinancialTransaction
PolicyFinancialTransaction
ClaimFinancialTransaction
FinancialTransactionClassification
```

Premium, fee, tax, surcharge, loss payment, reserve, salvage, subrogation, and recovery can often be modeled as transaction types, amount classifications, or financial dimensions.

### 4. Roles should be explicit

A party may participate in different contexts:

```text
Insured
Producer
Broker
Agent
Claimant
Adjuster
LossPayee
ServiceProvider
Underwriter
```

The canonical model should separate the party from the role the party plays.

### 5. Subtypes are design input, not mandatory boundaries

Subtype concepts are useful for understanding the domain, but they should not automatically become separate canonical contracts.

Use subtype concepts to inform:

* Classifications
* Specialized exposure contracts
* Reference data
* Optional extensions
* Data quality rules
* Semantic relationships

### 6. Platform-specific details belong in targets

The core ODCS contracts should remain platform-neutral.

Fabric, Databricks, Snowflake, dbt, Kafka, API, and other implementation guidance belongs under `targets/`.

---

## Repository structure

```text
nebula-insurance-data-contracts/
├── SKILL.md
├── README.md
├── references/
│   ├── odcs/
│   │   ├── pc/
│   │   │   ├── core/
│   │   │   ├── coverage/
│   │   │   ├── exposure/
│   │   │   ├── claims/
│   │   │   ├── financial/
│   │   │   └── reference-data/
│   │   ├── life/
│   │   ├── health/
│   │   ├── annuity/
│   │   ├── reinsurance/
│   │   └── shared/
│   ├── glossary/
│   ├── design-decisions/
│   └── patterns/
├── targets/
│   ├── fabric/
│   ├── databricks/
│   ├── snowflake/
│   ├── dbt/
│   ├── kafka/
│   └── api/
├── scripts/
│   ├── validation/
│   └── generation/
└── docs/
    ├── examples/
    └── roadmap/
```

---

## Folder guide

### `SKILL.md`

Defines the behavior for AI agents working with this repository.

The skill should describe how to design, validate, and evolve canonical insurance data contracts. It should not mention source standards, vendor models, raw research artifacts, or provenance.

The skill is platform-neutral by default.

### `references/odcs/`

Canonical ODCS contracts.

The first domain is:

```text
references/odcs/pc/
```

Future domains may include:

```text
references/odcs/life/
references/odcs/health/
references/odcs/annuity/
references/odcs/reinsurance/
references/odcs/shared/
```

### `references/glossary/`

Canonical business terms used by the contracts.

Definitions should be written in original language for this repository. Avoid copying external definitions verbatim.

### `references/design-decisions/`

Records of canonical modeling decisions.

Examples:

```text
entity-boundaries.md
exposure-modeling.md
financial-modeling.md
role-modeling.md
lifecycle-event-modeling.md
```

Use this area to explain why certain modeling choices were made.

### `references/patterns/`

Reusable modeling patterns.

Examples:

```text
party-role-pattern.md
policy-coverage-pattern.md
exposure-pattern.md
financial-transaction-pattern.md
event-pattern.md
```

Patterns should help future contributors design consistent contracts.

### `targets/`

Platform-specific implementation guidance.

The core contracts are platform-neutral. Target folders explain how to implement or generate platform-specific artifacts.

Examples:

```text
targets/fabric/
targets/databricks/
targets/snowflake/
targets/dbt/
targets/kafka/
targets/api/
```

### `scripts/`

Automation scripts for validation, generation, linting, and contract inspection.

Scripts should support canonical contracts without making the contracts platform-specific.

### `docs/`

General documentation, examples, roadmap notes, and usage guidance.

---

## Medallion architecture alignment

The contracts are especially useful in medallion-style data architecture.

A recommended interpretation:

```text
Bronze = raw, source-shaped, immutable landing data
Silver = canonical, domain-conformed insurance data contracts
Gold   = consumption-specific marts, semantic models, reports, and analytical products
```

This repository primarily defines the Silver canonical contract layer.

Bronze should preserve the source shape.
Gold should serve specific consumption needs.

Silver should provide the stable canonical insurance language between the two.


### Data flow
```
+-----------------------------+
| Source Systems              |
|                             |
| Policy Admin                |
| Claims                      |
| Billing                     |
| CRM                         |
| Broker / Agency Systems     |
| Spreadsheets / Files        |
| Events / APIs               |
+-------------+---------------+
              |
              v
+-----------------------------+
| Bronze Layer                |
|                             |
| Raw source-shaped data      |
| Immutable landing records   |
| Minimal transformation      |
| Source contract stamping    |
+-------------+---------------+
              |
              | validate, standardize, map, conform
              v
+---------------------------------------------------+
| Silver Layer                                      |
|                                                   |
| Canonical insurance data contracts                |
| Authored in ODCS v3 YAML                          |
|                                                   |
| Examples:                                         |
| Party                                             |
| Policy                                            |
| Coverage                                          |
| Exposure                                          |
| Claim                                             |
| FinancialTransaction                              |
+-------------+-------------------------------------+
              |
              | publish, project, aggregate, serve
              v
+-----------------------------+
| Gold Layer                  |
|                             |
| Data marts                  |
| Semantic models             |
| Dashboards                  |
| AI/RAG-ready datasets       |
| Regulatory reporting        |
| Underwriting analytics      |
| Claims analytics            |
+-------------+---------------+
              |
              v
+-----------------------------+
| Consumers                   |
|                             |
| Analysts                    |
| Underwriters                |
| Claims teams                |
| Actuaries                   |
| Data scientists             |
| AI agents                   |
| Applications                |
+-----------------------------+
```

### How this repository fits

This repository does not define Bronze ingestion.
This repository does not define Gold reporting marts.

It defines the canonical Silver contracts that sit between raw source data and downstream consumption.

The intended ecosystem flow is:
```
Source data
    ↓
Bronze landing
    ↓
Canonical contract validation
    ↓
Silver domain-conformed tables
    ↓
Gold marts, semantic models, APIs, events, and AI-ready datasets
```

The ODCS contracts in references/odcs/ should act as the stable agreement between data producers, platform engineers, data product owners, and consumers.

Platform-specific implementations belong under targets/.

Examples:
```
targets/fabric/
targets/databricks/
targets/snowflake/
targets/dbt/
targets/kafka/
targets/api/
```

The core contract should remain platform-neutral. Target folders describe how those contracts may be implemented in a specific ecosystem.

---

## Example: P&C exposure modeling

Instead of mechanically creating separate canonical contracts for every possible insured object subtype, this repository favors an exposure-centered design.

Example:

```text
InsurableObject
InsurableObjectClassification
Exposure
VehicleExposure
PropertyExposure
WorkersCompExposure
```

This supports questions like:

* What is being insured?
* What type of risk basis is being measured?
* Which coverage applies?
* Which policy term does the exposure belong to?
* Which claim arose from which exposure?
* Which rating, underwriting, or loss analytics should use this exposure?

---

## Example: financial modeling

Instead of creating separate top-level contracts for every money subtype, use a financial transaction pattern.

Example:

```text
FinancialTransaction
PolicyFinancialTransaction
ClaimFinancialTransaction
FinancialTransactionClassification
```

Possible transaction classifications:

```text
Premium
Fee
Tax
Surcharge
Commission
LossPayment
ExpensePayment
ClaimReserve
LossReserve
ExpenseReserve
Salvage
Subrogation
Recovery
DeductibleRecovery
ReinsuranceRecovery
```

This gives consumers a cleaner, more queryable model.

---

## Example: role modeling

A person or organization should not be duplicated across every business context.

Use a party-role pattern:

```text
Party
PartyRole
PartyRelationship
PolicyPartyRole
ClaimPartyRole
InsurableObjectPartyRole
```

This makes it possible to represent a party as:

```text
Named insured on one policy
Producer on another policy
Claimant on a claim
Loss payee on a coverage
Service provider on a claim
```

without duplicating the party itself.

---

## Contract naming conventions

Use clear, singular, business-meaningful names.

Preferred:

```text
Policy
Claim
Coverage
Exposure
FinancialTransaction
InsurableObject
GeographicLocation
```

Avoid:

```text
Policies
ClaimTbl
tblPolicy
PolicyHeader
PolicyFact
DimPolicy
SourcePolicy
AdminPolicy
VendorPolicy
```

Contract names should represent canonical business concepts, not source-system or implementation details.

---

## Field naming conventions

Field names should be clear, consistent, and implementation-friendly.

Preferred style:

```text
policy_id
policy_number
effective_date
expiration_date
status_code
coverage_id
claim_id
transaction_amount
transaction_currency_code
```

General rules:

* Use lowercase snake_case for physical field names.
* Use singular names.
* Use `_id` for identifiers.
* Use `_code` for coded values.
* Use `_date` for dates.
* Use `_datetime` or `_timestamp` only when time precision is required.
* Use `_amount` for monetary amounts.
* Use `_count` for counts.
* Use `_indicator` for yes/no or true/false business indicators.
* Avoid abbreviations unless they are widely understood in insurance or finance.

---

## ODCS contract expectations

Each ODCS contract should include:

* Contract identity
* Version
* Status
* Description
* Business domain
* Schema
* Fields
* Logical types
* Required/optional indicators
* Primary keys where applicable
* Relationships where applicable
* Data quality rules
* Ownership/support metadata where appropriate
* Custom properties for domain and target hints

Example skeleton:

```yaml
apiVersion: v3.0.2
kind: DataContract
id: pc.policy
name: Policy
version: 0.1.0
status: draft
description: Canonical contract for a Property & Casualty insurance policy.

domain: property-and-casualty

schema:
  - name: policy
    physicalType: table
    description: Canonical policy record.
    properties:
      - name: policy_id
        businessName: Policy Identifier
        logicalType: string
        required: true
        primaryKey: true

quality:
  - rule: policy_effective_date_required
    description: Policy effective date must be populated.
    dimension: completeness
    severity: error

customProperties:
  canonicalLayer: silver
  contractFamily: property-and-casualty
```

---

## Versioning

Contracts should follow semantic versioning where practical:

```text
MAJOR.MINOR.PATCH
```

Suggested interpretation:

```text
PATCH = documentation, metadata, or non-breaking clarification
MINOR = additive, backward-compatible field or rule
MAJOR = breaking schema, meaning, or compatibility change
```

Examples:

```text
0.1.0 = initial draft
0.2.0 = adds optional fields
1.0.0 = stable first release
2.0.0 = breaking redesign
```

---

## Contract status lifecycle

Recommended statuses:

```text
draft
review
approved
deprecated
retired
```

Suggested meaning:

* `draft`: actively being shaped
* `review`: ready for domain/data review
* `approved`: stable enough for implementation
* `deprecated`: still available but should not be used for new work
* `retired`: no longer active

---

## Target implementation posture

The repository should remain platform-neutral by default.

When a user or agent requests a target implementation, use the relevant target folder.

Examples:

```text
targets/fabric/
targets/databricks/
targets/snowflake/
targets/dbt/
targets/kafka/
targets/api/
```

Target implementations may define:

* Type mappings
* Naming conventions
* Deployment patterns
* Table/view generation
* Notebook generation
* dbt model generation
* Kafka topic/schema generation
* API schema generation
* Semantic model guidance

But the target should not change the canonical business meaning of the contract.

---

## AI agent usage

This repository is intended to be usable by AI coding agents.

The `SKILL.md` file defines the expected agent behavior.

An agent working in this repository should:

* Prefer canonical contracts over platform artifacts.
* Avoid copying source schemas directly.
* Keep contracts platform-neutral unless a target is requested.
* Use design decisions and patterns before inventing new modeling rules.
* Add new P&C contracts under `references/odcs/pc/`.
* Add reusable modeling logic under `references/patterns/`.
* Add rationale under `references/design-decisions/`.
* Avoid adding private research or external source material to the repo.
* Validate ODCS files before completing changes.

---

## Suggested first P&C contracts

The recommended first set of P&C contracts:

```text
references/odcs/pc/core/party.odcs.yaml
references/odcs/pc/core/policy.odcs.yaml
references/odcs/pc/core/policy-term.odcs.yaml

references/odcs/pc/coverage/product.odcs.yaml
references/odcs/pc/coverage/coverage.odcs.yaml
references/odcs/pc/coverage/policy-coverage.odcs.yaml

references/odcs/pc/exposure/insurable-object.odcs.yaml
references/odcs/pc/exposure/insurable-object-classification.odcs.yaml
references/odcs/pc/exposure/exposure.odcs.yaml
references/odcs/pc/exposure/vehicle-exposure.odcs.yaml
references/odcs/pc/exposure/property-exposure.odcs.yaml
references/odcs/pc/exposure/workers-comp-exposure.odcs.yaml

references/odcs/pc/claims/claim.odcs.yaml
references/odcs/pc/claims/claim-event.odcs.yaml
references/odcs/pc/claims/claim-coverage.odcs.yaml

references/odcs/pc/financial/financial-transaction.odcs.yaml
references/odcs/pc/financial/policy-financial-transaction.odcs.yaml
references/odcs/pc/financial/claim-financial-transaction.odcs.yaml

references/odcs/pc/reference-data/geographic-location.odcs.yaml
references/odcs/pc/reference-data/location-address.odcs.yaml
```

---

## Future domain expansion

This repository starts with P&C, but the structure allows future expansion.

Potential future domains:

```text
life/
health/
annuity/
reinsurance/
shared/
```

The `shared/` package should contain reusable concepts that apply across insurance domains, such as:

```text
Party
PartyRole
Location
FinancialTransaction
Document
CommunicationPreference
Organization
Producer
DistributionChannel
```

Be careful not to move concepts into `shared/` too early. Start domain-specific, then promote shared concepts when reuse is proven.

---

## Contribution guidance

When adding or changing a contract:

1. Start with the business concept.
2. Decide whether it belongs to an existing contract or requires a new one.
3. Check existing patterns.
4. Add or update the ODCS YAML.
5. Add data quality rules.
6. Add design rationale if the modeling choice is significant.
7. Keep platform-specific guidance out of the core contract.
8. Validate the contract.
9. Update examples or documentation if needed.

---

## What not to commit

Do not commit:

```text
Raw DDL exports
Raw ontology files
External PDFs
Scratch mappings
Research notes
Source review notes
Credentials
Generated data files
```

These belong outside the distributable repository.

---

## License

See `LICENSE`.

---

## Project status

Early stage.

The initial focus is establishing the repository structure, canonical modeling principles, the P&C contract spine, and the first ODCS contract examples.

The first meaningful milestone is a usable P&C Silver-layer contract set for:

```text
Party
Policy
Coverage
Exposure
Claim
FinancialTransaction
```
