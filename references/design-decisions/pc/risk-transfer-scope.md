# Risk Transfer Scope (Reinsurance, Coinsurance, Self-Insurance, Fronting)

## Decision

Reinsurance, coinsurance, self-insurance, and fronting are recognized canonical concepts but are **deferred** from the current contract set. They will be added in a later milestone with their own contract family rather than retrofitted onto policy or claim contracts.

Until they are added, the current contracts make no implicit assumption that the carrier writing a policy retains all of the risk on it.

## Rationale

Each of these concepts carries enough independent business meaning, party participation, financial flow, and lifecycle to warrant its own contract family. Trying to fold them into `Policy`, `Coverage`, or `Claim` would distort those contracts and entrench shortcuts that are expensive to undo later.

Deferring them deliberately — rather than ignoring them — keeps the door open and avoids accidental modeling that pre-empts the right answer.

## Out of scope for the current milestone

- **Reinsurance** — treaties, facultative arrangements, cessions, retrocessions, layers, attachment points, recoveries.
- **Coinsurance** — multi-carrier participation on a single policy with shared premium and loss.
- **Self-insurance** — captives, retentions, deductible buy-down structures where the named insured retains a layer.
- **Fronting** — arrangements where one carrier issues paper for another carrier's risk.

## Consequences

- The current `Policy`, `Coverage`, `Claim`, and `FinancialTransaction` contracts assume the carrier writing the policy is also the risk-bearer. This assumption is documented at the contract family level.
- When the risk-transfer family is added, expected new contracts include (non-exhaustive): `ReinsuranceTreaty`, `ReinsuranceCession`, `ReinsuranceRecovery`, `CoinsuranceParticipation`, `RetentionStructure`, `FrontingArrangement`, plus role and lifecycle contracts as warranted.
- Until then, recoveries and reinsurance accounting that flow through a carrier's financial system can be represented as `FinancialTransaction` rows with appropriate transaction-type classifications, with the understanding that the structural relationships are not yet modeled.

## Guidance

- Do not add reinsurance attributes (treaty number, cession identifier, attachment point) directly to `Policy` or `Claim` as a stopgap.
- Do not model coinsurance through `PolicyPartyRole` with a "coinsurer" role. The participation has financial structure that needs a dedicated contract.
- When a contributor has a near-term need for one of these concepts, raise it in the planning STATUS doc and treat it as an explicit scope expansion rather than an inline addition.

## Related

- `planning-mds/STATUS.md` (deferred-scope tracking)
- `references/design-decisions/pc/financial-modeling.md`
