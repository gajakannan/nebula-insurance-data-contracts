# SCD2 Primary Key

## Decision

Every contract that carries SCD2 system-time fields (`valid_from_datetime`, `valid_to_datetime`, `is_current_indicator`) declares a **composite logical primary key** of `(*_uid, valid_from_datetime)`. Both fields carry `primaryKey: true` in the ODCS schema, both are `required: true`, and both participate in the uniqueness constraint that downstream targets enforce.

This applies to every entity contract and every codeset / reference-data contract in the canonical surface. It does **not** apply to append-only event or transaction contracts, which are PK'd on their `*_uid` alone and use `correction_indicator` + `corrects_*_uid` instead of SCD2.

## Rationale

`temporal-modeling.md` already declares the natural SCD2 key as `(*_uid, valid_from_datetime)`. The remaining decision is how that natural key is realized at the contract level: as a single composite PK, or as a dual-identity pair where a per-version `*_record_uid` is the PK and the logical `*_uid` is a non-PK identity column.

**Composite logical PK** (chosen):

- The PK is `(*_uid, valid_from_datetime)`. Each version is a distinct PK row.
- Joins use `*_uid` (the logical key); the SCD2 window is filtered separately.
- One column to read from, one to track. Field count stays the same as the dual-identity option.
- Maps cleanly to Spark / Delta merge semantics, BigQuery clustering, and dbt snapshot internals.

**Dual-identity** (rejected default):

- A separate `*_record_uid` is generated per version and PK'd alone; `*_uid` is a non-PK identity column.
- Useful when downstream tooling (foreign-key constraints, MDM survivorship, change-data-capture pipelines) genuinely needs a single-column PK per version.
- Costs an extra column on every entity, plus authoring discipline to keep the two GUIDs straight.
- No current consumer requires it; the canonical-layer contracts hand the PK shape to whichever target consumes them, and Fabric Delta / Spark merges handle composite PKs natively.

The composite form preserves the simpler authoring shape while still expressing the bi-temporal natural key explicitly. If a future target or MDM tool requires per-version single-column PKs, the dual-identity form can be added as a target-side projection without changing the canonical contract.

## Consequences

- On every entity / codeset contract, both `*_uid` and `valid_from_datetime` carry `primaryKey: true`. The validator's identifier-strategy rule still requires the `_uid`-suffix on the PK property; the additional `primaryKey: true` on `valid_from_datetime` is permitted (it is the second component of the composite, not a renamed identity).
- Quality rule `single_current_row_per_key` remains: exactly one row per `*_uid` has `is_current_indicator = true`. The composite PK does not replace this rule, because `is_current_indicator` is the seam consumers use to ask "what does the current row say."
- Quality rule `valid_window_consistent` remains: `valid_to_datetime > valid_from_datetime` when populated. The PK does not enforce window semantics, only uniqueness.
- Append-only event / transaction contracts retain their `*_uid`-only PK. They are not SCD2; their immutability guarantees are encoded in `correction_indicator` + `corrects_*_uid`.
- Targets that materialize SCD2 (Fabric Delta merge notebooks, dbt snapshots) project the composite PK directly. No target-specific shim is required.

## Guidance

- Do not introduce a separate `*_record_uid` column on canonical contracts. If a target needs one, generate it in the target layer.
- Do not declare `is_current_indicator` as part of the PK. It is derived state, not identity.
- When authoring a new entity contract, set `primaryKey: true` on both `*_uid` and `valid_from_datetime`, both `required: true`. The validator confirms.
- When authoring an append-only event or transaction contract, set `primaryKey: true` on the `*_uid` only. Do not add `valid_from_datetime`.

## Related

- `references/design-decisions/pc/identifier-strategy.md`
- `references/design-decisions/pc/temporal-modeling.md`
- `references/design-decisions/pc/record-state.md`
- `references/design-decisions/pc/event-and-transaction.md`
