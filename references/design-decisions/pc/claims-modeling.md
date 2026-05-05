# Claims Modeling

## Decision

Claims are modeled with a contract set that mirrors the symmetry of `Policy` and `Submission`:

```text
Claim
ClaimPartyRole
ClaimLifecycleEvent
ClaimFeature
ClaimCoverage
ClaimDocument
ClaimFinancialTransaction
```

`Claim` is the durable claim identity. `ClaimFeature` represents a coverage- or peril-level claim partition (some carriers call this "claim feature," "claim line," or "sub-claim"). `ClaimCoverage` connects a claim or feature to the policy coverage that responds to it. The remaining contracts mirror the role, lifecycle, document, and financial patterns already used by `Policy` and `Submission`.

## Rationale

The current set has only `Claim`, which makes claims a second-class citizen relative to `Policy` (six contracts) and `Submission` (six contracts). Real claim data carries party participation (claimant, adjuster, attorney, service provider), independently meaningful lifecycle events (FNOL, acknowledged, reserved, paid, closed, reopened, subrogated), per-feature partitioning of large claims, document attachment, and dense financial activity.

Forcing all of that onto the `Claim` contract or pushing it into source-system shapes loses the pattern symmetry the rest of the model relies on.

## Consequences

- `ClaimPartyRole` follows the role pattern (Party + role contract per business context). Common claim roles include claimant, insured contact, adjuster, supervisor, attorney, expert, witness, service provider, recovery party.
- `ClaimLifecycleEvent` follows the lifecycle pattern. Event types include FNOL received, acknowledged, assigned, reserved, partial payment, full payment, closed, reopened, subrogation initiated, salvage initiated, denial, withdrawal.
- `ClaimFeature` represents claim partitions where the carrier handles distinct coverages, perils, or claimants on a single claim through separate feature streams. Optional for carriers that do not model features.
- `ClaimCoverage` ties a claim (or claim feature) to the responding `PolicyCoverage`. Many-to-one from claim feature to policy coverage; many-to-many between claim and policy coverage when no feature partition is used.
- `ClaimFinancialTransaction` is a `FinancialTransaction` specialization carrying claim-specific context (claim feature, coverage, payee party role, reserve category). Aligns with the financial-modeling ADR.
- `ClaimDocument` follows the document pattern; metadata only, with URI to external store.

## Guidance

- Reserves and payments are not separate contracts. They are `ClaimFinancialTransaction` rows with appropriate `transaction_type_code` and `transaction_classification_code` values from the codeset.
- Cause-of-loss, catastrophe code, and litigation indicators belong on `Claim` or `ClaimFeature` as classification fields backed by codesets, not as their own contracts.
- Loss date, report date, and entry date are all distinct and all belong on `Claim`. Keep them as separate fields, not derived.

## Related

- `references/design-decisions/pc/role-modeling.md`
- `references/design-decisions/pc/policy-lifecycle-modeling.md`
- `references/design-decisions/pc/financial-modeling.md`
- `references/design-decisions/pc/event-and-transaction.md`
