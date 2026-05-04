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

Use `PolicyLifecycleEvent` for meaningful business state changes.

Use `PolicyTransaction` when a policy change has transaction-level business meaning such as endorsement, cancellation, renewal, or audit processing.
