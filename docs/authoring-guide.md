# Authoring Guide

This guide contains the reusable authoring rules for Nebula Insurance Data Contracts. The root README explains what the repository is; this file explains how to add or change contracts.

## Authoring Source Primacy

When the canonical layer changes, contributors update artifacts in a fixed primacy order:

```text
ADR  >  pattern  >  glossary  >  contract  >  validator
```

The leftmost artifact is authoritative. When two artifacts disagree, the leftmost wins, and the rightmost is the one that must catch up. Update the ADR first; then patterns, glossary, and contracts; the validator is updated last because it codifies what the ADR has already decided. See `references/design-decisions/pc/authoring-source-primacy.md` for the full rationale and resolution procedure.

A practical workflow when a rule changes:

1. Update the relevant ADR — edit the rule statement, note the change in the ADR's "Consequences" or "Related" section, and (if the change reverses a prior decision) move the prior decision to a "Superseded" or "History" subsection rather than deleting it.
2. Update patterns under `references/patterns/pc/` if the change affects how the ADR is applied across a contract family.
3. Update the glossary if the change renames or re-scopes a canonical term.
4. Apply the change to contracts. For changes touching more than three contracts, write an idempotent refactor script under `scripts/refactor/` (modeled on `apply-hardening-c5.py` or `apply-hardening-c6.py`). Bump the version per `versioning-policy.md` and append a changelog entry that names the specific ADR (or ADR section) driving the change.
5. Update the validator last. Add the rule to `scripts/validation/validate-contracts.py` and a unit test under `scripts/validation/tests/`.

The deliberate departures and deferrals that shape the current canonical surface are documented in `references/design-decisions/pc/canonical-alignment.md`. Read that ADR before introducing new contracts, reversing a deferral, or proposing a new departure.

## Cross-Cutting Conventions

Every contract authored or changed in this repository must comply with the cross-cutting design decisions in `references/design-decisions/pc/`. Read the index at `references/design-decisions/README.md` first; the conventions below summarize what the validator enforces.

- **Identifiers** — every entity contract has a `*_uid` GUID primary key plus a business-friendly key where the business assigns one. See `identifier-strategy.md`.
- **Bi-temporal modeling** — every entity contract carries `valid_from_datetime`, `valid_to_datetime`, and `is_current_indicator` for SCD2 system time. Business-effective dates stay where they belong. See `temporal-modeling.md`.
- **Record state** — every entity contract carries `record_status_code` (`ACTIVE` / `SUPERSEDED` / `SOFT_DELETED` / `RESTATED` / `MERGED`). Soft delete is the only delete. See `record-state.md`.
- **Event vs transaction** — append-only `*LifecycleEvent` and `*Transaction` contracts skip SCD2; corrections are new immutable rows linked via `corrects_*_uid`. See `event-and-transaction.md`.
- **Codesets** — every `*_code` field references a governed codeset contract under `references/odcs/pc/reference-data/`. See `codeset-strategy.md`.
- **Null semantics** — null means "value not present, reason unspecified." Distinguish "unknown" vs "not applicable" via codeset sentinels, never via overloading null. See `null-semantics.md`.
- **Currency** — every monetary field is paired with a sibling `*_currency_code` referencing the `CurrencyCode` codeset. No house currency at the canonical layer. See `currency-convention.md`.
- **Data classification** — every property declares `customProperties.classifications` with a `sensitivity` tier and any applicable regulatory tags (PII, PHI, PCI, SPI, FINANCIAL). Contract-level `classificationProfile` summarizes the most-sensitive class present. See `data-classification.md`.
- **Versioning** — SemVer with data-contract semantics; the validator checks well-formedness. See `versioning-policy.md`.
- **Status promotion** — gated transitions `draft → proposed → approved → deprecated → retired`. See `status-promotion.md`.
- **ADR back-links** — every contract carries `customProperties.adrs: [...]` naming the ADRs that govern its shape. The validator's C1.12 rule confirms each id resolves to a file under `references/design-decisions/pc/`. When an ADR change drives a contract change, update the contract's `adrs` list to match.

## Contract Workflow

When adding or changing a contract:

1. Start with the business concept.
2. Decide whether it belongs to an existing contract, a role contract, a classification, reference data, a lifecycle event, or a new contract — see `separation-and-nesting.md`.
3. Check existing patterns under `references/patterns/`.
4. Check design rationale under `references/design-decisions/`. If a deliberate departure or deferral might apply, check `canonical-alignment.md`.
5. Add or update the ODCS YAML using the cross-cutting conventions above.
6. Add meaningful data quality rules.
7. Add design rationale if the modeling choice is significant. When a new ADR is introduced, follow the primacy order: ADR first, then pattern/glossary, then contracts, then validator.
8. Keep platform-specific guidance out of canonical contracts.
9. Update `customProperties.adrs: [...]` to name the ADRs that govern the contract's shape. The validator's C1.12 rule confirms each id resolves.
10. Run the validator (`python3 scripts/validation/validate-contracts.py`).
11. Update examples, glossary terms, or documentation when needed.
12. Bump version per `versioning-policy.md` and append a changelog entry under `customProperties.changelog` that names the specific ADR (or ADR section) driving the change. Generic "apply cross-cutting ADRs" entries are no longer acceptable; entries should name which ADR drove which field addition. Existing pre-0.3.0 entries are not retroactively rewritten — those are git history.

Use `references/odcs/templates/pc-contract-template.odcs.yaml` as the starting point for new P&C contracts.

Validate one contract while authoring:

```bash
python3 scripts/validation/validate-contracts.py references/odcs/pc/core/party.odcs.yaml
```

Validate all tracked contract files:

```bash
python3 scripts/validation/validate-contracts.py
```

## Contract Naming

Use clear, singular, business-meaningful names.

Preferred examples:

```text
Policy
Claim
Coverage
Exposure
FinancialTransaction
InsurableObject
GeographicLocation
```

Avoid names shaped by source systems, databases, reports, or implementation patterns:

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

Contract names should represent canonical business concepts, not physical tables or source application artifacts.

## Field Naming

Use lowercase snake_case for physical field names.

Preferred examples:

```text
policy_uid
policy_number
effective_date
expiration_date
policy_status_code
coverage_uid
claim_uid
transaction_amount
transaction_currency_code
```

General rules:

- Use singular names.
- Use `_uid` for system-generated GUID identity columns. The `*_uid` is the primary key and the join key for every relationship (per `identifier-strategy.md`).
- Use `_number` for business-friendly identifiers that the business or operations assigns (e.g. `policy_number`, `claim_number`).
- Use `_code` for coded values that reference a codeset contract (per `codeset-strategy.md`).
- Use `_date` for dates.
- Use `_datetime` or `_timestamp` only when time precision is required.
- Use `_amount` for monetary amounts; pair every monetary field with a sibling `_currency_code` (per `currency-convention.md`).
- Use `_count` for counts.
- Use `_indicator` for yes/no or true/false business indicators.
- Avoid abbreviations unless they are widely understood in insurance or finance.

Do not use plain `_id` for new fields. Existing legacy `_id` names have been migrated to `_uid` per `identifier-strategy.md`; the validator rejects new non-PK `_id` fields.

## ODCS Expectations

Each ODCS contract should include:

- Contract identity
- Version
- Status
- Description
- Business domain
- Schema
- Fields
- Logical types
- Required/optional indicators
- Primary keys where applicable
- Relationships where applicable
- Data quality rules where meaningful
- Ownership or support metadata where appropriate
- Custom properties for domain and target hints

Suggested starting skeleton (entity contract):

```yaml
apiVersion: v3.0.2
kind: DataContract
id: pc.policy
name: Policy
version: 0.1.0
status: draft
description: Canonical contract for a Property and Casualty insurance policy.
domain: property-and-casualty
schema:
  - name: policy
    physicalType: table
    description: Canonical policy record.
    properties:
      - name: policy_uid
        businessName: Policy Identifier
        logicalType: string
        required: true
        primaryKey: true
        description: Immutable system-generated GUID that uniquely identifies the canonical policy record.
        customProperties:
          classifications:
            sensitivity: INTERNAL
      - name: policy_number
        businessName: Policy Number
        logicalType: string
        required: true
        description: Business-facing number assigned to the policy.
        customProperties:
          classifications:
            sensitivity: INTERNAL
      - name: record_status_code
        businessName: Record Status Code
        logicalType: string
        required: true
        description: Warehouse-level state of the record.
        customProperties:
          classifications:
            sensitivity: INTERNAL
      - name: valid_from_datetime
        businessName: Valid From Datetime
        logicalType: datetime
        required: true
        description: System-time start of the SCD2 window for this record version.
        customProperties:
          classifications:
            sensitivity: INTERNAL
      - name: valid_to_datetime
        businessName: Valid To Datetime
        logicalType: datetime
        required: false
        description: System-time end of the SCD2 window. Null indicates the current row.
        customProperties:
          classifications:
            sensitivity: INTERNAL
      - name: is_current_indicator
        businessName: Is Current Indicator
        logicalType: boolean
        required: true
        description: True for exactly one row per logical key.
        customProperties:
          classifications:
            sensitivity: INTERNAL
quality:
  - rule: policy_uid_required
    description: policy_uid must be populated.
    dimension: completeness
    severity: error
  - rule: valid_from_datetime_required
    description: valid_from_datetime must be populated for every record version.
    dimension: completeness
    severity: error
customProperties:
  canonicalLayer: silver
  contractFamily: property-and-casualty
  domainPackage: pc
  classificationProfile: INTERNAL
  adrs:
    - authoring-source-primacy
    - canonical-alignment
    - codeset-strategy
    - data-classification
    - identifier-strategy
    - record-state
    - scd2-primary-key
    - status-promotion
    - temporal-modeling
    - versioning-policy
```

Append-only event/transaction contracts use a different shape: they skip SCD2 and `record_status_code` and instead carry `correction_indicator` plus `corrects_*_uid` per `event-and-transaction.md`.

## Versioning

Contracts use SemVer with data-contract semantics defined in `references/design-decisions/pc/versioning-policy.md`. Summary:

- **MAJOR** — breaking: drop/rename field, tighten type, optional → required, narrow allowed code values, drop relationship.
- **MINOR** — additive: add optional field, add quality rule, widen allowed code values, add relationship.
- **PATCH** — no schema impact: description/businessName/comment fixes.

Below `1.0.0`, the contract is pre-stable. Breaking changes are permitted between `0.x` minor versions but must be recorded in the contract's changelog.

Each version bump should add an entry to `customProperties.changelog`.

## Status Lifecycle

Statuses and gates are defined in `references/design-decisions/pc/status-promotion.md`:

```text
draft → proposed → approved → deprecated → retired
```

Promotion is gated; the status field is not advanced ad hoc. See the ADR for the gates that apply at each transition.

## What Not To Commit

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

Private research, comparison work, downloaded artifacts, source review, and scratch mappings belong in local ignored folders such as `_private-research/`, `_external-sources/`, `_source-review/`, and `_scratch/`.
