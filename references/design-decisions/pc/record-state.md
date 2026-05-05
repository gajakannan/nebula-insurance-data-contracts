# Record State (Soft Delete and Correction)

## Decision

Every entity contract carries a `record_status_code` field that captures the warehouse-level state of the record, distinct from any business lifecycle status the entity may also carry.

Allowed values for `record_status_code`:

```text
ACTIVE
SUPERSEDED
SOFT_DELETED
RESTATED
MERGED
```

Records are never physically deleted from canonical contracts. Deletes from source systems are represented by transitioning the canonical row to `SOFT_DELETED` and closing its SCD2 window.

## Rationale

Business status (`policy_status_code`, `claim_status_code`, etc.) describes the real-world state of the entity — a policy can be `CANCELLED` and still be a perfectly valid, queryable, current canonical record. Record status describes the *record itself* — was it retracted, replaced by a corrected version, or merged into another?

Conflating the two leaves CDC consumers, audit, and reporting unable to distinguish "policy was cancelled" from "the policy record was a data-entry error and has been retracted."

## Consequences

- Every entity contract gains `record_status_code` (required, default `ACTIVE`).
- Append-only event/transaction contracts do not carry `record_status_code` directly. A correction is modeled as a new event/transaction with a `correction_indicator` and a `corrects_*_uid` reference to the row being corrected. Original events are never mutated.
- Soft-deleted rows remain queryable but are excluded from default downstream materializations unless explicitly requested.
- `MERGED` rows carry a `merged_into_uid` reference to the surviving record.
- Quality rule: every entity contract must populate `record_status_code` with one of the allowed values.

## Guidance

- Do not use `record_status_code` to express business lifecycle. If the modeling answer is "the policy was cancelled," that belongs on `policy_status_code` and `PolicyLifecycleEvent`.
- Use `SOFT_DELETED` only when the upstream truth is that the record should not have existed (data-entry error, duplicate, system-of-record retraction). Do not use it for lifecycle endings such as cancellation, lapse, or expiration.
- Downstream targets should default to filtering `record_status_code IN ('ACTIVE')` and `is_current_indicator = true` for "current canonical view" materializations.

## Related

- `references/design-decisions/pc/temporal-modeling.md`
- `references/design-decisions/pc/identifier-strategy.md`
