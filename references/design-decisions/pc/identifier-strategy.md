# Identifier Strategy

## Decision

Every canonical contract carries two identifiers:

1. A **system identity column** ending in `_uid` — an immutable, opaque GUID used as the primary key and as the join key for every relationship.
2. A **business key** — a human-readable, business-friendly identifier (for example `policy_number`, `claim_number`, `submission_number`) that matches how operations and source systems refer to the entity.

The `*_uid` is the canonical primary key. The business key is required where the business assigns one, but it is never the primary key and never the join target.

## Rationale

Business keys change. Policies are renumbered, parties are merged, claims are re-numbered after restatement, sources rekey on migration. Building joins on a business key forces every consumer to handle remapping. Using a stable opaque identity column isolates downstream models from upstream re-keying.

Business keys are still required because operations, regulators, and source-system reconciliation all need a recognizable identifier. Hiding it behind only a GUID would break operability.

## Consequences

- Every entity contract has `*_uid` as its primary key and `*_id` is reserved for legacy/business-key naming where it already exists. Where contracts currently use `*_id` as the primary key (e.g. `policy_id`), the field is renamed to `*_uid` and a separate `*_number` business key is retained.
- Relationship `sourceFields` and `targetFields` always reference `*_uid` columns.
- Source-system attribution is captured separately on contracts that ingest from multiple sources via `source_system_code` and `source_natural_key`. These do not replace the `*_uid`; they record provenance.
- The `*_uid` value is generated upstream (ingestion or MDM) and is treated as immutable for the life of the record. Re-issuance, restatement, or merge produces a new `*_uid` and a relationship to the prior record.
- Quality rule: `*_uid` must be populated, must be unique, and must not change between snapshots of the same logical record.

## Guidance

- Do not invent a `*_uid` for ephemeral derivations or views — only entities with an independent canonical identity get one.
- Do not encode business meaning into the `*_uid`. No prefixes, no embedded date, no source-system tag.
- For child contracts that belong wholly to a parent (e.g. `PolicyTerm`), still issue a separate `policy_term_uid` rather than a composite key. Composite keys propagate complexity.

## Related

- `references/design-decisions/pc/temporal-modeling.md`
- `references/design-decisions/pc/record-state.md`
