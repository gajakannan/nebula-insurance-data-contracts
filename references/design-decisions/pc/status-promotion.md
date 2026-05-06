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

Gates are split into two groups: **validator-enforced** gates that the YAML alone can prove, and **process-enforced** gates that depend on facts outside the contract file (steward sign-off, downstream consumer commitments, deprecation timing) and that must be confirmed by a human reviewer.

### draft → proposed

- Validator-enforced: contract passes the standard validation pass; `customProperties.changelog` contains at least one entry.
- Process-enforced: pull request opened with the contract owner identified; relevant patterns or design-decision docs cross-referenced.

### proposed → approved

- Validator-enforced (every promoted contract — `approved`, `deprecated`, or `retired` — must satisfy these; the validator emits a finding when any fail):
  - `customProperties.changelog` is a non-empty list.
  - Every relationship's `targetContractId` resolves to a contract id that exists in the canonical surface.
  - Every `*_code` field either has a `relationships` entry pointing at a reference-data contract under `references/odcs/pc/reference-data/`, or carries `customProperties.codesetExempt: true` plus a `codesetExemptReason` string. (Inherited from the cross-cutting C1.2 rule, applied to every contract regardless of status.)
  - All quality rules at severity `error` are stated.
- Process-enforced (not checked by the validator):
  - Domain steward sign-off recorded in the PR or in `customProperties.stewardApproval`.
  - At least one downstream consumer or target use case identified (logged in `customProperties.knownConsumers` or in the PR description).
  - All `*_code` fields reference a codeset contract that is itself at least `proposed`.

### approved → deprecated

- Validator-enforced: `customProperties.deprecation` (or equivalent changelog entry) names the effective date and replacement reference.
- Process-enforced: a successor contract or successor major version is at least `proposed`; at least one minor-version notice period elapses before retirement is permitted.

### deprecated → retired

- Validator-enforced: contract retains its file, schema, and changelog; `status: retired` is set.
- Process-enforced: at least one major version has elapsed since deprecation; no remaining known consumers (verified through `knownConsumers` and any registered downstream targets).

## Consequences

- The validator enforces the validator-enforceable gates above on every contract whose status is `approved`, `deprecated`, or `retired`. Process-enforced gates are out of scope for the validator and are confirmed by reviewers at promotion time.
- Below `1.0.0`, a contract may be `approved` if it meets the gates above; the pre-stable version simply signals that breaking changes are still permitted (per the versioning policy).
- The planning STATUS.md tracks contracts by state so that promotion progress is visible.

## Guidance

- Promote in cohorts where contracts depend on each other. Promoting `Policy` to `approved` while `PolicyTerm` stays `draft` creates a brittle approval.
- Do not skip `proposed`. The proposed state is where consumer feedback shapes the contract; skipping it costs more than it saves.
- Retirement is a deletion of capability, not a deletion of artifact. Keep retired contract files in the repo with `status: retired` so historical references resolve.
- When promoting, expect the validator to reject `approved`-status contracts that lack a changelog, have unresolved `targetContractId` references, or have unbound `*_code` fields. These are the gates the validator can prove from YAML alone.

## Related

- `references/design-decisions/pc/versioning-policy.md`
- `references/design-decisions/pc/identifier-strategy.md`
- `docs/authoring-guide.md`
