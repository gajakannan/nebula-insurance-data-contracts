# Claim Lifecycle Pattern

Use the claim lifecycle pattern to model claim handling from FNOL through close, reopening, and recovery.

## Intent

Claim activity is dense with party participation, lifecycle events, and financial movement. Mirror the symmetry already used for `Policy` and `Submission` so consumers see consistent shapes across the contract set.

## Recommended Contracts

```text
Claim
ClaimFeature
ClaimLifecycleEvent
ClaimCoverage
ClaimPartyRole
ClaimDocument
ClaimFinancialTransaction
```

## Lifecycle Event Examples

```text
FNOLReceived
Acknowledged
Assigned
ReserveSet
PartialPayment
FullPayment
Closed
Reopened
SubrogationInitiated
SalvageInitiated
Denied
Withdrawn
```

## Modeling Guidance

Use `Claim` for the durable claim identity and current claim summary.

Use `ClaimFeature` to partition a claim into independent handling streams when distinct coverages, perils, or claimants are handled separately. Optional for carriers that do not model features.

Use `ClaimLifecycleEvent` for meaningful business state changes (signal: *what happened*).

Use `ClaimFinancialTransaction` for reserves, payments, recoveries, salvage, subrogation, and expense activity (signal: *what was processed*). The transaction-type code carries the specific kind of money movement.

Events and transactions are complementary, not alternatives. A single payment typically emits both a `ClaimLifecycleEvent` and a `ClaimFinancialTransaction`, linked via `lifecycle_event_uid`. Pure-signal changes (acknowledged, assigned, FNOL received) emit only an event. See `references/design-decisions/pc/event-and-transaction.md`.

Use `ClaimPartyRole` for claimants, adjusters, attorneys, service providers, and other claim participants per `references/patterns/pc/party-role-pattern.md`.

Use `ClaimCoverage` to tie claim handling to the policy coverage that responds to it. Many-to-one from `ClaimFeature` to `PolicyCoverage` when features are used; many-to-many between `Claim` and `PolicyCoverage` when no feature partition is in place.

Use `ClaimDocument` for claim-related document metadata. Document content is held in an external store; the contract carries an opaque reference and a `contains_phi_indicator` for HIPAA-aware target generation.

Reinsurance recoveries, coinsurance settlements, and fronting flows are deferred to the risk-transfer contract family per `references/design-decisions/pc/risk-transfer-scope.md`. Until that family lands, those flows are represented through `ClaimFinancialTransaction` rows with appropriate transaction-type classifications.
