# Authoring Guide

This guide contains the reusable authoring rules for Nebula Insurance Data Contracts. The root README explains what the repository is; this file explains how to add or change contracts.

## Contract Workflow

When adding or changing a contract:

1. Start with the business concept.
2. Decide whether it belongs to an existing contract, a role contract, a classification, reference data, a lifecycle event, or a new contract.
3. Check existing patterns under `references/patterns/`.
4. Check design rationale under `references/design-decisions/`.
5. Add or update the ODCS YAML.
6. Add meaningful data quality rules.
7. Add design rationale if the modeling choice is significant.
8. Keep platform-specific guidance out of canonical contracts.
9. Validate the contract when validation tooling exists.
10. Update examples, glossary terms, or documentation when needed.

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

- Use singular names.
- Use `_id` for identifiers.
- Use `_code` for coded values.
- Use `_date` for dates.
- Use `_datetime` or `_timestamp` only when time precision is required.
- Use `_amount` for monetary amounts.
- Use `_count` for counts.
- Use `_indicator` for yes/no or true/false business indicators.
- Avoid abbreviations unless they are widely understood in insurance or finance.

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

Suggested starting skeleton:

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

## Versioning

Contracts should follow semantic versioning where practical:

```text
MAJOR.MINOR.PATCH
```

Suggested interpretation:

- `PATCH`: documentation, metadata, or non-breaking clarification.
- `MINOR`: additive, backward-compatible field or rule.
- `MAJOR`: breaking schema, meaning, or compatibility change.

Examples:

```text
0.1.0 = initial draft
0.2.0 = adds optional fields
1.0.0 = stable first release
2.0.0 = breaking redesign
```

## Status Lifecycle

Recommended statuses:

```text
draft
review
approved
deprecated
retired
```

Suggested meaning:

- `draft`: actively being shaped.
- `review`: ready for domain and data review.
- `approved`: stable enough for implementation.
- `deprecated`: still available but should not be used for new work.
- `retired`: no longer active.

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
