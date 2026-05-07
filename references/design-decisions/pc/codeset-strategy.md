# Codeset Strategy

## Decision

Every `*_code` field in a canonical contract refers to a **codeset contract** — a small, governed reference-data contract whose rows enumerate the allowed values, their human-readable labels, and their effective windows.

`*_code` fields are not free-form strings. They are foreign-key references to a codeset contract.

## Rationale

Insurance is dense with coded vocabularies — policy status, coverage basis, claim cause-of-loss, transaction type, line of business, lifecycle event type, jurisdiction, currency, party type. Allowing each `*_code` to be an ungoverned string forces every consumer to invent its own validation, mappings, and reporting joins. It also blocks generation of typed enums or check constraints in downstream targets.

Centralizing codes into governed codeset contracts gives a single place to evolve allowed values, attach descriptions, capture mappings to external standards (ACORD, NAIC, ISO), and surface change history.

## Consequences

- Every `*_code` field on an entity contract has a paired codeset contract under `references/odcs/pc/reference-data/`. Existing examples: `LineOfBusiness`, `LifecycleStatus`, `LifecycleEventType`, `TransactionType`. Missing examples to be added: `PolicyStatusCode`, `PolicyTypeCode`, `CoverageBasisCode`, `CoverageLevelCode`, `CoverageStatusCode`, `TermStatusCode`, `RecordStatusCode`, `PartyTypeCode`, `PartyRoleTypeCode`, `ClaimStatusCode`, `CauseOfLossCode`, `JurisdictionCode`, `CurrencyCode`, and any other code referenced from an entity contract.
- Codeset contracts share a common shape:
  - `*_code_uid` (GUID PK)
  - `code_value` (business-friendly key, the value referenced by entity contracts)
  - `code_label` (human-readable name)
  - `code_description`
  - `external_standard_code` and `external_standard_name` (optional, for ACORD/NAIC/ISO mappings)
  - SCD2 fields and `record_status_code` per the temporal and record-state ADRs
- Entity-contract relationships explicitly target the codeset contract via `targetContractId` and `targetFields: [code_value]`.
- The validator must enforce that every `*_code` field on an entity contract has a corresponding codeset contract.
- A code value is added/changed via a versioned change to the codeset contract. Adding a value is MINOR; removing or renaming a value is MAJOR (per versioning policy).

## Guidance

- Do not create a codeset contract for one-off enumerations that are unlikely to grow or be referenced from more than one place. Inline allowed-values can be expressed as quality rules on the field.
- Codesets that map cleanly to an external standard (e.g. ISO 4217 for currency) should still be modeled as canonical codeset contracts, with the external standard captured as a mapping. The canonical layer owns the values it accepts; it does not re-export the external list.
- Avoid encoding semantics into the `code_value` itself (e.g. `01_PREMIUM`, `02_FEE`). Use a clean alphabetic key and rely on `code_label` for presentation.

## Pure codeset vs reference-data entity (canonical hardening C5.3 addendum)

Two contract shapes live under `references/odcs/pc/reference-data/`. Both are governed reference data, but their conventions differ.

**Pure codeset.** Filename ends `-code` (e.g. `policy-status-code.odcs.yaml`). Single business-meaning field (`code_value`) plus the standard codeset shape (`*_code_uid`, `code_label`, `code_description`, `external_standard_code`, `external_standard_name`, SCD2 fields, `record_status_code`). Carries `customProperties.codesetContract: true` and `classificationProfile: PUBLIC`. All field-level sensitivities are `PUBLIC`. Used for status, type, classification, and outcome enumerations whose values can be exposed publicly without sensitivity concerns.

**Reference-data entity.** Filename does not require the `-code` suffix. Carries the codeset shape's identity columns (`*_uid`, `code_value`, `code_label`, `code_description`) plus richer business attributes (subject classification, parent/child hierarchy, regulatory mappings, effective ranges beyond SCD2 system time). `customProperties.codesetContract` is omitted or `false`. `classificationProfile: INTERNAL` is permitted because the richer attributes are operationally sensitive even when `code_value` and `code_label` are not. Examples: `LineOfBusiness`, `LifecycleStatus`, `LifecycleEventType`, `TransactionType`, `GeographicLocation`, `LocationAddress`. The `code_value` field on a reference-data entity is `PUBLIC`; other fields default to `INTERNAL`.

The validator's C1.2 (`*_code` codeset binding) treats both shapes as valid codeset targets — entity contracts may bind a `*_code` field to either a pure codeset or a reference-data entity via `relationships`.

## `record-status-code` self-reference (canonical hardening C5.8 addendum)

The `record-status-code` codeset contract carries a `record_status_code` field that references the same codeset. This self-reference is intentional. It bootstraps with the codeset's own `ACTIVE` value once; subsequent code-row supersession marks rows `SUPERSEDED` using the same codeset's allowed values. The validator does not flag self-referential bindings on reference-data contracts.

## Related

- `references/design-decisions/pc/versioning-policy.md`
- `references/design-decisions/pc/null-semantics.md`
- `references/design-decisions/pc/data-classification.md`
