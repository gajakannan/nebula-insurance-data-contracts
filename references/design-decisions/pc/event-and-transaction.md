# Lifecycle Event and Transaction

## Decision

Lifecycle events and transactions are **complementary**, not redundant. They model two different things and either can exist without the other.

- A **`*LifecycleEvent`** records *what changed* — a business-meaningful state change in the entity's history. It is a signal.
- A **`*Transaction`** records *what was processed* — a unit of business activity that has financial impact, document generation, or independent processing identity. It is an action.

Where both apply to the same business moment, they are emitted together and linked.

## Rationale

In practice, some changes are pure signals with no processing weight (a status query, a clearance decision that does not yet bind, a soft state change). Other changes are processing units that already imply a state change (a premium audit booking, an endorsement that calculates premium). Forcing every change into one contract or the other loses information.

The complementary model is also how seasoned canonical insurance models (the conceptual posture behind ACORD-style models, IIDM, and most carrier data warehouses that handle bi-temporal correction) treat the two.

## Rules

1. Emit a `*LifecycleEvent` for every business-meaningful state change in the entity's history. The bar is "would an analyst or auditor want this in the timeline?"
2. Emit a `*Transaction` *additionally* when the change has financial impact, produces a document, or carries its own processing identity that is referenced from elsewhere.
3. When both are emitted, the transaction carries `lifecycle_event_uid` referring to the matching event. The event optionally carries `triggering_transaction_uid` when the event is the consequence of a transaction rather than the cause.
4. A correction to either an event or a transaction is modeled as a new row of the same kind with a `correction_indicator` and a `corrects_*_uid` reference. Original rows are immutable (per the temporal-modeling and record-state ADRs).
5. Reading "the current state of the policy" uses the entity contract (`Policy`, `Claim`, `Submission`). Reading the timeline uses events. Reading processed activity uses transactions.

## Worked examples

- **Endorsement that changes coverage and recalculates premium** — emit `PolicyLifecycleEvent` (event_type: ENDORSEMENT, with effective_date) **and** `PolicyTransaction` (transaction_type: ENDORSEMENT_BOOKING, premium delta, document reference). Linked via `lifecycle_event_uid`.
- **Cancellation effective today, no return premium** — emit `PolicyLifecycleEvent` (event_type: CANCELLATION). No transaction unless cancellation produces a fee or accounting entry.
- **Premium audit booking with no other state change** — emit `PolicyTransaction` (transaction_type: AUDIT_BOOKING). Optionally emit `PolicyLifecycleEvent` of event_type AUDIT_PROCESSED if the audit closure itself counts as a timeline event.
- **Underwriter clearance decision (no bind, no money)** — emit `SubmissionLifecycleEvent` (event_type: CLEARANCE_DECISION). No transaction.
- **FNOL** — emit `ClaimLifecycleEvent` (event_type: FNOL_RECEIVED). No transaction at intake; transactions begin when reserves are set.

## Consequences

- The patterns and pattern docs are updated to describe the rule and link this ADR.
- The validator gains a check that any transaction contract carrying `lifecycle_event_uid` references an existing lifecycle-event contract.
- Downstream targets generate two distinct materializations (event timeline, transaction ledger) that join on `lifecycle_event_uid` when both are present. dbt models for "current state" pull from the entity contract, not from event reduction, except where explicitly modeled as such.

## Related

- `references/design-decisions/pc/policy-lifecycle-modeling.md`
- `references/design-decisions/pc/financial-modeling.md`
- `references/design-decisions/pc/temporal-modeling.md`
- `references/design-decisions/pc/record-state.md`
