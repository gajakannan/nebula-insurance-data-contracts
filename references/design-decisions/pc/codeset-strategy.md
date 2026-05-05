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

## Related

- `references/design-decisions/pc/versioning-policy.md`
- `references/design-decisions/pc/null-semantics.md`
