# Repository And Architecture

This document preserves the detailed repository structure and architecture flow diagrams for Nebula Insurance Data Contracts.

## Repository Structure

```text
nebula-insurance-data-contracts/
├── SKILL.md
├── README.md
├── LICENSE
├── references/
│   ├── odcs/
│   │   ├── pc/
│   │   │   ├── core/
│   │   │   │   ├── party.odcs.yaml
│   │   │   │   ├── party-relationship.odcs.yaml
│   │   │   │   ├── account.odcs.yaml
│   │   │   │   ├── account-relationship.odcs.yaml
│   │   │   │   ├── account-party-role.odcs.yaml
│   │   │   │   └── agreement.odcs.yaml
│   │   │   │
│   │   │   ├── submission/
│   │   │   │   ├── submission.odcs.yaml
│   │   │   │   ├── submission-party-role.odcs.yaml
│   │   │   │   ├── submission-risk.odcs.yaml
│   │   │   │   ├── submission-assessment.odcs.yaml
│   │   │   │   ├── submission-document.odcs.yaml
│   │   │   │   └── submission-lifecycle-event.odcs.yaml
│   │   │   │
│   │   │   ├── policy/
│   │   │   │   ├── policy.odcs.yaml
│   │   │   │   ├── policy-term.odcs.yaml
│   │   │   │   ├── policy-party-role.odcs.yaml
│   │   │   │   ├── policy-lifecycle-event.odcs.yaml
│   │   │   │   ├── policy-transaction.odcs.yaml
│   │   │   │   └── policy-document.odcs.yaml
│   │   │   │
│   │   │   ├── coverage/
│   │   │   │   ├── product.odcs.yaml
│   │   │   │   ├── coverage.odcs.yaml
│   │   │   │   ├── product-coverage.odcs.yaml
│   │   │   │   ├── policy-coverage.odcs.yaml
│   │   │   │   ├── policy-limit.odcs.yaml
│   │   │   │   └── policy-deductible.odcs.yaml
│   │   │   │
│   │   │   ├── exposure/
│   │   │   │   ├── insurable-object.odcs.yaml
│   │   │   │   ├── insurable-object-classification.odcs.yaml
│   │   │   │   ├── insurable-object-party-role.odcs.yaml
│   │   │   │   ├── exposure.odcs.yaml
│   │   │   │   ├── vehicle-exposure.odcs.yaml
│   │   │   │   ├── property-exposure.odcs.yaml
│   │   │   │   └── workers-comp-exposure.odcs.yaml
│   │   │   │
│   │   │   ├── claims/
│   │   │   │   ├── claim.odcs.yaml
│   │   │   │   ├── claim-coverage.odcs.yaml
│   │   │   │   ├── claim-feature.odcs.yaml
│   │   │   │   ├── claim-party-role.odcs.yaml
│   │   │   │   ├── claim-document.odcs.yaml
│   │   │   │   ├── claim-lifecycle-event.odcs.yaml
│   │   │   │   ├── claim-financial-transaction.odcs.yaml
│   │   │   │   ├── occurrence.odcs.yaml
│   │   │   │   └── catastrophe.odcs.yaml
│   │   │   │
│   │   │   ├── financial/
│   │   │   │   ├── financial-transaction.odcs.yaml
│   │   │   │   └── policy-financial-transaction.odcs.yaml
│   │   │   │
│   │   │   └── reference-data/
│   │   │       ├── geographic-location.odcs.yaml
│   │   │       ├── location-address.odcs.yaml
│   │   │       ├── line-of-business.odcs.yaml
│   │   │       ├── transaction-type.odcs.yaml
│   │   │       ├── lifecycle-status.odcs.yaml
│   │   │       ├── lifecycle-event-type.odcs.yaml
│   │   │       ├── financial-transaction-classification.odcs.yaml
│   │   │       └── ... (pure codesets: *-status-code, *-type-code, etc.)
│   │   │
│   │   ├── life/
│   │   ├── health/
│   │   ├── annuity/
│   │   ├── reinsurance/
│   │   └── shared/
│   │
│   ├── glossary/
│   │   ├── README.md
│   │   └── pc/
│   │
│   ├── design-decisions/
│   │   ├── README.md
│   │   └── pc/
│   │       ├── canonical-alignment.md
│   │       ├── authoring-source-primacy.md
│   │       ├── entity-boundaries.md
│   │       ├── submission-modeling.md
│   │       ├── policy-lifecycle-modeling.md
│   │       ├── exposure-modeling.md
│   │       ├── financial-modeling.md
│   │       ├── role-modeling.md
│   │       ├── identifier-strategy.md
│   │       ├── temporal-modeling.md
│   │       ├── scd2-primary-key.md
│   │       ├── record-state.md
│   │       ├── codeset-strategy.md
│   │       └── ... (full ADR index in references/design-decisions/README.md)
│   │
│   └── patterns/
│       ├── README.md
│       └── pc/
│           ├── account-pattern.md
│           ├── party-role-pattern.md
│           ├── submission-lifecycle-pattern.md
│           ├── policy-lifecycle-pattern.md
│           ├── policy-coverage-pattern.md
│           ├── claim-lifecycle-pattern.md
│           ├── exposure-pattern.md
│           └── financial-transaction-pattern.md
│
├── targets/
│   ├── README.md
│   ├── fabric/
│   ├── databricks/
│   ├── snowflake/
│   ├── dbt/
│   ├── kafka/
│   └── api/
│
├── scripts/
│   ├── README.md
│   ├── validation/
│   └── generation/
│
└── docs/
    ├── README.md
    ├── authoring-guide.md
    ├── repository-and-architecture.md
    ├── examples/
    └── roadmap/
        └── pc-contract-backlog.md
```

## Medallion Architecture Data Flow

```text
+-----------------------------+
| Source Systems              |
|                             |
| Policy Admin                |
| Submission / Intake         |
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
| Core examples:                                    |
| Party                                             |
| Submission                                        |
| Policy                                            |
| PolicyLifecycleEvent                              |
| PolicyTransaction                                 |
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
| Submission analytics        |
| Policy lifecycle analytics  |
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

## P&C Operating Lifecycle Flow

The medallion view explains where the contracts fit in the data platform. The operating lifecycle view explains how the first P&C domain package is expected to behave from an insurance business perspective.

```text
+-----------------------------+
| Submission                  |
|                             |
| Intake                      |
| Producer / broker context   |
| Applicant / insured context |
| Initial risk information    |
| Documents                   |
+-------------+---------------+
              |
              v
+-----------------------------+
| Underwriting Assessment     |
|                             |
| Clearance                   |
| Triage                      |
| Risk review                 |
| Referral                    |
| Declination                 |
+-------------+---------------+
              |
              v
+-----------------------------+
| Quote / Indication          |
|                             |
| Proposed terms              |
| Proposed coverage           |
| Proposed pricing            |
| Subjectivities              |
+-------------+---------------+
              |
              v
+-----------------------------+
| Bind                        |
|                             |
| Coverage intent             |
| Binder period               |
| Bound terms                 |
| Bind authority              |
+-------------+---------------+
              |
              v
+-----------------------------+
| Issue Policy                |
|                             |
| Legal contract              |
| Policy term                 |
| Policy coverage             |
| Policy parties              |
| Policy documents            |
+-------------+---------------+
              |
              v
+---------------------------------------------------+
| Policy Lifecycle                                  |
|                                                   |
| Endorsement                                       |
| Renewal                                           |
| Cancellation                                      |
| Reinstatement                                     |
| Non-renewal                                       |
| Rewrite                                           |
| Audit                                             |
| Expiration                                        |
+-------------+-------------------------------------+
              |
              v
+-----------------------------+
| Claim                       |
|                             |
| Loss event                  |
| Claim intake                |
| Coverage association        |
| Claim parties               |
| Reserves / payments         |
| Recovery / salvage          |
+-----------------------------+
```

The canonical model should support both views:

```text
Medallion view        = how data moves through the platform
Operating lifecycle   = how insurance work moves through the business
Canonical contracts   = the stable agreement between both
```

## Commercial Lines Boundary

The `core/` subject area carries `Account`, `AccountRelationship`, `AccountPartyRole`, and `Agreement` contracts that support commercial-lines business where one customer holds multiple policies under a master agreement.

```text
Account
    │
    ├── AccountRelationship   (parent / subsidiary / aggregation)
    ├── AccountPartyRole      (named insured, billing contact, broker of record, ...)
    └── Agreement             (master policy, blanket coverage, schedule, program)
            │
            └── Policy        (account_uid + agreement_uid as optional FKs)
```

This shape was added during canonical hardening C4.5 as a deliberate scope expansion. The original C4.5 default was to amend — defer the account / agreement layer until commercial-line scope expanded. The reversal landed because the user-driven scope expansion brought commercial-lines into the first wave. `Policy`, `Submission`, and `PolicyFinancialTransaction` carry optional `account_uid` and `agreement_uid` FKs that are populated for commercial-lines records and left null for personal-lines records.

The deliberate-departure rationale and the cross-references to `entity-boundaries.md` and `account-pattern.md` are recorded in `references/design-decisions/pc/canonical-alignment.md`.
