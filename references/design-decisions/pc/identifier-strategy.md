# Identifier Strategy

## Decision

Every canonical contract names its identifiers from a single three-part vocabulary:

1. **`*_uid`** — system identity column. Immutable, opaque GUID. Every entity has one as its primary key. Every relationship's `sourceFields` and `targetFields` join on `*_uid` columns.
2. **`*_number`** — business key. Human-readable, business-friendly identifier (`policy_number`, `claim_number`, `submission_number`, `vin_number`) matching how operations and source systems refer to the entity. Required where the business assigns one. Never the primary key, never a join target.
3. **`*_code`** — codeset reference. Resolves to a reference-data contract under `references/odcs/pc/reference-data/` (a `code_value` column on a pure codeset, or the equivalent on a richer reference-data entity).

These are the only identifier suffixes canonical contracts use. The `*_id` suffix is **not** part of the canonical vocabulary and is reserved as a dead-letter — the validator rejects any non-PK property whose name ends in `_id`.

## Rationale

Business keys change. Policies are renumbered, parties merged, claims renumbered after restatement, sources rekey on migration. Building joins on a business key forces every consumer to handle remapping. A stable opaque identity column isolates downstream models from upstream re-keying.

Business keys are still required because operations, regulators, and source-system reconciliation all need a recognizable identifier. Hiding them behind only a GUID would break operability.

Codeset references are kept distinct from both because they reference an external enumeration, not a record identity. Conflating `*_uid` and `*_code` (e.g. carrying both `transaction_type_uid` and `transaction_type_code` for the same lookup) duplicates the join and forces consumers to pick one — see `record-state.md` for the analogous discipline on record state.

## Consequences

- Every entity contract declares `*_uid` as its primary key. The validator enforces the `_uid` suffix on primary-key properties.
- Every relationship's `sourceFields` and `targetFields` reference `*_uid` columns (with one exception: relationships into pure-codeset contracts target the codeset's `code_value` field, since that is the business-friendly join key downstream consumers expect).
- Source-system attribution is captured separately on contracts that ingest from multiple sources via `source_system_code` and `source_natural_key`. These do not replace the `*_uid`; they record provenance. `source_system_code` follows the standard `*_code` discipline — it binds to the `source-system-code` codeset under `references/odcs/pc/reference-data/` like every other `*_code` field. The codeset rows are populated per deployment; the contract defines the schema. `source_natural_key` is a free-form identifier (the source's own primary-key value) and is not a codeset reference.
- `source_natural_key` carries the **primary** source key only — the natural-key value from the source system named in `source_system_code`. It is a single slot, not a multi-source provenance ledger. When a canonical record is mastered from multiple source systems (e.g. a Party merged from a policy administration system, a CRM, and a claims system), the canonical record carries one primary `source_system_code` + `source_natural_key` pair; the other source associations are an MDM concern and live outside the canonical layer until a use case requires modeling them. If that need arises, the answer is a dedicated `*-source-provenance` 1:N child contract per affected entity, not a widened `source_natural_key` slot. Until then, multi-source mastering remains explicitly out of scope.
- The `*_uid` value is generated upstream (ingestion or MDM) and is treated as immutable for the life of the record. Re-issuance, restatement, or merge produces a new `*_uid` and a relationship to the prior record.
- Quality rule: `*_uid` must be populated, must be unique, and must not change between snapshots of the same logical record.

## Guidance

- Do not invent a `*_uid` for ephemeral derivations or views — only entities with an independent canonical identity get one.
- Do not encode business meaning into the `*_uid`. No prefixes, no embedded date, no source-system tag.
- For child contracts that belong wholly to a parent (e.g. `PolicyTerm`), still issue a separate `policy_term_uid` rather than a composite key. Composite keys propagate complexity. (The SCD2 PK shape is a separate decision documented in `scd2-primary-key.md`.)
- Do not pair a `*_uid` and a `*_code` for the same lookup. Pick the form the business uses to talk about the value: codeset references use `*_code`, entity references use `*_uid`. The validator flags `<prefix>_uid` + `<prefix>_code` co-occurrence where `<prefix>` matches a known codeset.
- Do not use `*_id` as a property name. The suffix is reserved as a dead-letter so that drift toward inconsistent naming is caught at validation time rather than at consumption time.

## Related

- `references/design-decisions/pc/temporal-modeling.md`
- `references/design-decisions/pc/record-state.md`
- `references/design-decisions/pc/codeset-strategy.md`
