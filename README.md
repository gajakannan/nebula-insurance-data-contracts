# Nebula Insurance Data Contracts

Nebula Insurance Data Contracts is a platform-neutral canonical data contract library for insurance data products.

The contracts are authored in **ODCS v3 YAML** and organized by insurance domain. The first domain package focuses on **Property and Casualty (P&C)** insurance, with room to expand later into Life, Health, Annuity, Reinsurance, and shared cross-domain insurance concepts.

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

## Core Idea

The repository follows a contract-first approach:

```text
Business concept
    ↓
Canonical insurance entity
    ↓
ODCS data contract
    ↓
Target-specific implementation
```

The canonical contracts define the intended business shape of the data.

Platform-specific targets such as Fabric, Databricks, Snowflake, dbt, Kafka, Postgres, APIs, or semantic models should be generated from or aligned to these contracts, not the other way around.

---

## Design Posture

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

Detailed modeling rationale belongs under `references/design-decisions/`.

---

## Provenance Boundary

The distributable contents of this repository should not include raw artifact names, external source URLs, copied definitions, raw source schemas, or private source review notes.

The contracts should stand on their own as original canonical insurance data contracts.

Research, comparison work, source review, downloaded artifacts, and scratch mappings must remain outside the committed repository in ignored local folders such as:

```text
_private-research/
_external-sources/
_source-review/
_scratch/
```

See `docs/authoring-guide.md` and `SKILL.md` for contribution and agent-specific handling rules.

---

## Why ODCS?

ODCS provides a structured way to describe data contracts using YAML.

In this repository, ODCS is the authoring format for canonical contracts. The repo name intentionally uses `data-contracts` rather than `odcs` because ODCS is the current contract standard, while the broader product concept is canonical insurance data contracts.

The contracts may later be used to generate or align:

- Lakehouse tables
- Warehouse tables
- dbt models
- Kafka schemas
- JSON Schema
- Avro schemas
- API specifications
- Semantic models
- Data quality rules
- Data product documentation

---

## Current Domain Focus

The first domain package is **Property and Casualty insurance**.

The initial P&C modeling spine is:

```text
Party, PartyRole, PartyRelationship
Account, Agreement
Submission, SubmissionPartyRole, SubmissionRisk, SubmissionAssessment, SubmissionDocument
Policy, PolicyTerm, PolicyPartyRole, PolicyLifecycleEvent, PolicyTransaction, PolicyDocument
Product, Coverage, PolicyCoverage, PolicyLimit, PolicyDeductible
InsurableObject, InsurableObjectClassification
Exposure, VehicleExposure, PropertyExposure, WorkersCompExposure
Claim, ClaimEvent, ClaimCoverage, ClaimPartyRole, ClaimDocument
FinancialTransaction, PolicyFinancialTransaction, ClaimFinancialTransaction, FinancialTransactionClassification
GeographicLocation, LocationAddress
Assessment, RiskAssessment, UnderwritingAssessment
```

This shape favors business usability and data product clarity over mechanically reproducing source-system tables or deeply normalized subtype structures.

See `docs/roadmap/pc-contract-backlog.md` for the suggested first contract set.

---

## Repository Map

```text
SKILL.md                         Agent and orchestrator guidance
README.md                        Project overview
references/odcs/                 Canonical ODCS contracts
references/glossary/             Canonical business terms
references/design-decisions/     Modeling rationale
references/patterns/             Reusable modeling patterns
targets/                         Platform-specific implementation guidance
scripts/                         Validation, generation, linting, and inspection scripts
docs/                            Authoring guidance, examples, roadmap, and usage docs
```

Important starting points:

- `docs/repository-and-architecture.md`
- `docs/authoring-guide.md`
- `docs/contract-inventory.md` — generated navigation page covering every canonical contract by kind, schema, version, and status
- `CHANGELOG.md` — generated repository-level changelog aggregating per-contract changelog entries by version wave (`0.4.x` → `0.1.x`)
- `docs/roadmap/pc-contract-backlog.md`
- `references/odcs/pc/README.md`
- `references/patterns/README.md`
- `references/design-decisions/README.md`
- `targets/README.md`
- `SKILL.md`

---

## Architecture Alignment

The contracts are especially useful in medallion-style data architecture:

```text
Bronze = raw, source-shaped, immutable landing data
Silver = canonical, domain-conformed insurance data contracts
Gold   = consumption-specific marts, semantic models, reports, and analytical products
```

This repository defines the Silver canonical contract layer. It does not define Bronze ingestion or Gold reporting marts.

The intended ecosystem flow is:

```text
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

The ODCS contracts in `references/odcs/` should act as the stable agreement between data producers, platform engineers, data product owners, and consumers.

See `docs/repository-and-architecture.md` for the full medallion architecture data flow diagram.

---

## P&C Operating Lifecycle

The first P&C domain package should support the business lifecycle from submission through underwriting, quote or indication, bind, policy issue, policy lifecycle changes, and claims.

```text
Submission
    ↓
Underwriting Assessment
    ↓
Quote / Indication
    ↓
Bind
    ↓
Issue Policy
    ↓
Policy Lifecycle
    ↓
Claim
```

The canonical model should support both views:

```text
Medallion view        = how data moves through the platform
Operating lifecycle   = how insurance work moves through the business
Canonical contracts   = the stable agreement between both
```

Lifecycle-specific guidance lives in:

- `docs/repository-and-architecture.md`
- `references/patterns/pc/submission-lifecycle-pattern.md`
- `references/patterns/pc/policy-lifecycle-pattern.md`
- `references/design-decisions/pc/submission-modeling.md`
- `references/design-decisions/pc/policy-lifecycle-modeling.md`

---

## Modeling References

Use the detailed references instead of expanding the root README. The full ADR index lives at `references/design-decisions/README.md`; the full pattern index at `references/patterns/README.md`.

Cross-cutting conventions (apply to every contract):

- Identifier strategy (GUID `_uid` + business key): `references/design-decisions/pc/identifier-strategy.md`
- Bi-temporal modeling (SCD2 system time): `references/design-decisions/pc/temporal-modeling.md`
- Record state (soft delete, supersession, merge): `references/design-decisions/pc/record-state.md`
- Event vs transaction (complementary, with linkage): `references/design-decisions/pc/event-and-transaction.md`
- Codeset strategy (governed `*_code` references): `references/design-decisions/pc/codeset-strategy.md`
- Null semantics: `references/design-decisions/pc/null-semantics.md`
- Currency convention: `references/design-decisions/pc/currency-convention.md`
- Data classification (PII, PHI, sensitivity): `references/design-decisions/pc/data-classification.md`
- Versioning policy (SemVer for data contracts): `references/design-decisions/pc/versioning-policy.md`
- Status promotion (gated lifecycle): `references/design-decisions/pc/status-promotion.md`
- Separation and nesting: `references/design-decisions/pc/separation-and-nesting.md`

Domain-specific decisions:

- Entity boundaries: `references/design-decisions/pc/entity-boundaries.md`
- Submission modeling: `references/design-decisions/pc/submission-modeling.md`
- Policy lifecycle modeling: `references/design-decisions/pc/policy-lifecycle-modeling.md`
- Claims modeling: `references/design-decisions/pc/claims-modeling.md`
- Product and coverage M:N: `references/design-decisions/pc/product-coverage-modeling.md`
- Exposure modeling: `references/design-decisions/pc/exposure-modeling.md`
- Financial modeling: `references/design-decisions/pc/financial-modeling.md`
- Role modeling: `references/design-decisions/pc/role-modeling.md`
- Risk transfer scope (reinsurance, coinsurance, etc. — deferred): `references/design-decisions/pc/risk-transfer-scope.md`

Patterns:

- Submission lifecycle: `references/patterns/pc/submission-lifecycle-pattern.md`
- Policy lifecycle: `references/patterns/pc/policy-lifecycle-pattern.md`
- Claim lifecycle: `references/patterns/pc/claim-lifecycle-pattern.md`
- Policy coverage: `references/patterns/pc/policy-coverage-pattern.md`
- Exposure: `references/patterns/pc/exposure-pattern.md`
- Financial transaction: `references/patterns/pc/financial-transaction-pattern.md`
- Party role: `references/patterns/pc/party-role-pattern.md`

Authoring rules for naming, fields, ODCS expectations, versioning, status lifecycle, and contribution boundaries live in `docs/authoring-guide.md`.

Agent and orchestration behavior lives in `SKILL.md`.

---

## Target Implementations

The core contracts remain platform-neutral.

Target-specific implementation guidance belongs under `targets/`. The first and only first-wave target is **Microsoft Fabric Lakehouse**, projected from the canonical contracts through a metadata-driven generator chain.

```text
targets/fabric/
  README.md                                  # entry point and persona flow
  conventions.md                             # naming, materialization, runtime conventions
  type-mapping.md                            # ODCS → Spark SQL types
  manifest-schema.md                         # full manifest schema reference
  manifests/pc/<area>/<slug>.fabric.yaml     # 85 generated manifests
  ddl/pc/<area>/<slug>.spark.sql             # 85 generated CREATE TABLE files
  notebooks/silver-{scd2-merge,append,codeset-load}-template.ipynb
  notebooks/lakehouse-binding-template.json  # consumer fills workspace IDs
  purview/sensitivity-labels.json            # 1235 column-level entries
  purview/business-glossary.json             # 308 canonical terms
  examples/end-to-end-policy.md              # worked Policy walkthrough
```

Generators and validator (run from the repository root):

```text
scripts/generation/generate-fabric.py            # orchestrator: runs the four sub-generators in order
scripts/generation/generate-fabric-manifests.py  # ODCS → manifests
scripts/generation/generate-fabric-purview.py    # manifests + glossary → Purview JSON
scripts/generation/generate-fabric-ddl.py        # manifests → Spark SQL DDL
scripts/generation/generate-fabric-notebooks.py  # parameterized SCD2 / append / codeset notebook templates
scripts/validation/validate-fabric-manifests.py  # manifest drift detection (--require-full-coverage)
```

The recommended starting points for a Fabric consumer:

- `targets/fabric/README.md` — purpose, scope, persona flow, and coexistence with `microsoft/skills-for-fabric`.
- `targets/fabric/examples/end-to-end-policy.md` — Policy + PolicyTerm + PolicyCoverage + PolicyStatusCode worked through the full six-persona flow (SCD2 entity merge + codeset SCD2 load).
- `targets/fabric/examples/end-to-end-claims.md` — Claim + ClaimFeature + ClaimLifecycleEvent + ClaimFinancialTransaction + two codesets, exercising the append-only event family, append-only transaction with `lifecycle-event-link`, and the C4.5 commercial-lines spine.
- `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` — authoritative plan for the Fabric target.

Other targets (Databricks, Snowflake, Kafka, API, semantic projection) are deferred or out of scope for this milestone; see `planning-mds/IMPLEMENTATION_PLAN.md` and `targets/README.md` for the full posture.

---

## Future Domain Expansion

This repository starts with P&C, but the structure allows future expansion into:

```text
life/
health/
annuity/
reinsurance/
shared/
```

The `shared/` package should contain reusable concepts only after reuse is proven across insurance domains. Start domain-specific, then promote shared concepts deliberately.

---

## Project Status

Early stage.

The initial focus is establishing the repository structure, canonical modeling principles, the P&C contract spine, and the first ODCS contract examples.

The first meaningful milestone is tracked in `docs/roadmap/pc-contract-backlog.md`.

---

## License

See `LICENSE`.
