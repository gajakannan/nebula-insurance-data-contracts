# Status Promotion

## Decision

Canonical contracts move through five lifecycle states with explicit promotion gates:

```text
draft -> proposed -> approved -> deprecated -> retired
```

Each transition has a documented gate. A contract may regress from `proposed` back to `draft`. A contract that is `approved` cannot regress; corrections are made by a new version.

## Rationale

Without explicit gates, every contract stays at `draft` indefinitely. Consumers cannot tell which contracts are safe to depend on. Authors cannot tell when a contract has earned the right to be promoted.

The five states match the way ODCS and most data-contract tooling expect lifecycle to be modeled and align with the lifecycle in `docs/authoring-guide.md`.

## Promotion gates

- **draft → proposed**
  - Contract passes the validator.
  - Contract has a non-empty changelog entry.
  - Pull request opened with the contract owner identified.
  - At least one of the existing patterns or design-decision docs is referenced if applicable.

- **proposed → approved**
  - Domain steward sign-off recorded in `customProperties.stewardApproval` (steward identifier and date).
  - At least one downstream consumer or target use case has been identified (logged in `customProperties.knownConsumers`, even informally).
  - All quality rules at severity `error` are stated.
  - All `*_code` fields reference a codeset contract that is itself at least `proposed`.
  - Cross-contract relationships resolve to existing contract IDs.

- **approved → deprecated**
  - A successor contract or a successor major version is at least `proposed`.
  - Deprecation notice recorded in `customProperties.deprecation` with effective date and replacement reference.
  - At least one minor-version notice period elapses before retirement is permitted.

- **deprecated → retired**
  - At least one major version has elapsed since deprecation.
  - No remaining known consumers (verified through `knownConsumers` and through any registered downstream targets).
  - The contract file remains in the repository for historical reference but emits no target artifacts.

## Consequences

- The validator checks that contracts in `proposed` or higher meet the gates relevant to their state. Authors cannot promote ad hoc by editing the `status` field alone.
- Below `1.0.0`, a contract may be `approved` if it meets the gates above; the pre-stable version simply signals that breaking changes are still permitted (per the versioning policy).
- The planning STATUS.md tracks contracts by state so that promotion progress is visible.

## Guidance

- Promote in cohorts where contracts depend on each other. Promoting `Policy` to `approved` while `PolicyTerm` stays `draft` creates a brittle approval.
- Do not skip `proposed`. The proposed state is where consumer feedback shapes the contract; skipping it costs more than it saves.
- Retirement is a deletion of capability, not a deletion of artifact. Keep retired contract files in the repo with `status: retired` so historical references resolve.

## Related

- `references/design-decisions/pc/versioning-policy.md`
- `docs/authoring-guide.md`
