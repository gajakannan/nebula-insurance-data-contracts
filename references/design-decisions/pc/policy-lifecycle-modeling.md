# Policy Lifecycle Modeling

## Decision

Represent policy lifecycle changes explicitly rather than overwriting policy history.

## Rationale

Policy state changes such as bind, issue, endorsement, renewal, cancellation, reinstatement, non-renewal, rewrite, audit, and expiration are analytically and operationally meaningful.

## Consequences

Use `Policy` for durable identity and `PolicyTerm` for term periods.

Use `PolicyLifecycleEvent` for meaningful state changes.

Use `PolicyTransaction` when a change has transaction-level business meaning and may affect coverage, premium, term, status, documents, or downstream processing.

See `references/patterns/pc/policy-lifecycle-pattern.md`.
