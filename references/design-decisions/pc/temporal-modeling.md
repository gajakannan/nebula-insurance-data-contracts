# Temporal Modeling

## Decision

Canonical P&C contracts are bi-temporal. Every entity contract carries:

- **Business-time** fields where the business concept has its own validity window (e.g. `term_effective_date`, `term_expiration_date`, `coverage_effective_date`, `coverage_expiration_date`).
- **System-time** fields that record when the canonical record was valid in the warehouse, in SCD2 form: `valid_from_datetime`, `valid_to_datetime`, `is_current_indicator`.

The two timelines are independent and both must be preserved.

## Rationale

Insurance is bi-temporal by nature. A backdated endorsement booked today changes both *what was effective* (business time) and *what we knew, when* (system time). Storing only the business-effective dates loses the audit trail of corrections, late-arriving data, and restatements. Storing only system time loses the answer to "what was the policy on the date of loss."

Single-timeline approximations (Type 1 current-state, append-only events without explicit valid windows) cannot reconstruct both views.

## Naming convention for business-time windows

Where an entity carries a business-time validity window, the two endpoints are named **`effective_date` / `expiration_date`** (or `effective_datetime` / `expiration_datetime` when finer granularity is needed). This is the canonical pair across the entire surface — Policy, PolicyTerm, Coverage, party-role contracts, document contracts, party, party-relationship, insurable-object, catastrophe, and any other entity with a business validity window.

Do not introduce alternative pairs (`start_date` / `end_date`, `from_date` / `to_date`, `inception_date` / `termination_date`, `begin_date` / `end_date`, `active_from` / `active_to`). The single canonical pair removes ambiguity for consumers, makes window-overlap quality rules uniform, and keeps the Fabric target's window-handling code one shape.

The naming convention does **not** apply to:

- **Point-in-time event timestamps** (`loss_date`, `reported_datetime`, `opened_date`, `closed_date`, `bind_date`, `decline_date`, `event_datetime`, `transaction_effective_date`, `transaction_processed_datetime`, `occurrence_date`, etc.). These are single business timestamps with distinct semantics, not window endpoints.
- **System-time SCD2 fields** (`valid_from_datetime` / `valid_to_datetime`). These describe warehouse system time per this ADR, not business validity.

## Consequences

- Every entity contract gains `valid_from_datetime`, `valid_to_datetime`, and `is_current_indicator`. `valid_to_datetime` is open-ended (null or far-future sentinel) for the current row; `is_current_indicator` is true for exactly one row per logical key.
- Business-time fields remain on the contracts where they already exist and are not replaced by the SCD2 fields. Where they form a validity window, the canonical naming above applies.
- The composite "natural" SCD2 key for any entity is `(*_uid, valid_from_datetime)`. The `*_uid` alone is not unique across history; it is unique only among current rows.
- Quality rules per entity contract:
  - `valid_from_datetime` must be populated.
  - `valid_to_datetime` must be greater than `valid_from_datetime` when populated.
  - Exactly one row per `*_uid` has `is_current_indicator = true`.
  - SCD2 windows for the same `*_uid` must not overlap.
- Reference-data and codeset contracts (lookup-style) follow the same SCD2 pattern. Code values are also versioned through history so that "what code values existed on a given date" is answerable.

## Guidance

- Append-only event contracts (`*LifecycleEvent`, `*Transaction`) do not carry SCD2 fields at all. Each event row is immutable; corrections are emitted as new rows referencing the corrected row via `correction_indicator` + `corrects_*_uid` (per the event-and-transaction ADR). The system-time the record landed is captured upstream by ingestion metadata and is not modeled as a canonical column on these contracts.
- Junction contracts (e.g. `ProductCoverage`) follow SCD2 because the relationship itself can change over time.
- Downstream targets (dbt snapshots, Fabric Lakehouse Delta tables) materialize SCD2 directly. The contract carries the seam; the target chooses the storage strategy.

## Related

- `references/design-decisions/pc/record-state.md`
- `references/design-decisions/pc/event-and-transaction.md`
- `references/design-decisions/pc/identifier-strategy.md`
