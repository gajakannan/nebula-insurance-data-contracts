# Policy Lifecycle Pattern

Use the policy lifecycle pattern to model changes after quote, bind, and issue.

## Intent

Policies continue to evolve after issuance. Endorsements, renewals, cancellations, reinstatements, non-renewals, rewrites, audits, and expiration should be represented without flattening all history into the current policy row.

## Recommended Contracts

```text
Policy
PolicyTerm
PolicyPartyRole
PolicyLifecycleEvent
PolicyTransaction
PolicyDocument
```

## Lifecycle Event Examples

```text
Bind
Issue
Endorsement
Renewal
Cancellation
Reinstatement
NonRenewal
Rewrite
Audit
Expiration
```

## Modeling Guidance

Use `Policy` for the durable policy identity.

Use `PolicyTerm` for term-specific effective and expiration periods.

Use `PolicyLifecycleEvent` for meaningful business state changes (signal: *what happened*).

Use `PolicyTransaction` when the change has financial impact, document generation, or independent processing identity (signal: *what was processed*).

Events and transactions are complementary, not alternatives. The full rule and worked examples are in `references/design-decisions/pc/event-and-transaction.md`. When both are emitted for the same business moment, the transaction carries `lifecycle_event_uid` referring to the event.

Both `PolicyLifecycleEvent` and `PolicyTransaction` are append-only. Corrections are emitted as new immutable rows referencing the corrected row via `corrects_*_uid`.
