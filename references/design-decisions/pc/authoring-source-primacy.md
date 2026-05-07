# Authoring Source Primacy

## Decision

When the canonical contract layer changes, contributors update artifacts in a fixed primacy order:

```text
ADR  >  pattern  >  glossary  >  contract  >  validator
```

The leftmost artifact is **authoritative**. When two artifacts disagree, the leftmost one wins, and the rightmost is the one that must catch up. When proposing a change, contributors update the authoritative artifact first, then propagate the change rightwards to the dependents. The validator is updated last because it codifies what the ADR has already decided — it is the enforcement layer, not the source of truth.

## Rationale

Canonical hardening surfaced a recurring class of confusion: when an ADR, a pattern doc, a glossary entry, a contract, and a validator rule disagree, contributors do not know which one to trust. Without a documented primacy order, every disagreement triggers a re-litigation — does the contract reflect what we decided, or did the validator drift, or did the ADR forget to update? The disagreement consumes more review effort than the underlying change.

A documented primacy order replaces re-litigation with a procedure: the ADR is the source of truth; whichever rightward artifact disagrees is wrong; update the rightward artifact to match. Disagreements still happen, but the resolution is mechanical rather than discretionary.

The chosen order — ADR first, validator last — reflects how decisions actually flow through the repository:

- **ADRs** capture the modeling decision plus its rationale. They are the longest-lived artifact and the one that survives re-namings, restructurings, and contributor turnover.
- **Patterns** describe the contract families that implement the ADR. They are derivative of the ADR's decisions but explain how to apply them across multiple contracts.
- **Glossary** entries describe canonical business terms. They are derivative of the ADRs that decided where the term lands in the canonical surface.
- **Contracts** are the materialization of ADR decisions in YAML. They are downstream of ADRs and patterns; when the ADR changes, contracts must follow.
- **Validator rules** are the automated enforcement of ADR decisions. They are the rightmost artifact because they cannot encode anything the ADR has not already decided.

## Consequences

When a rule changes:

1. **Update the relevant ADR first.** Edit the rule statement, add a dated entry under "Related" or "Consequences" if the change is non-trivial. If the change introduces a new rule, the ADR may need a new section. If the change reverses a prior decision, the prior decision moves to a "Superseded" or "History" subsection rather than being deleted.
2. **Update patterns next** if the change affects how the ADR is applied across a family of contracts.
3. **Update the glossary** if the change renames or re-scopes a canonical business term.
4. **Apply the change to contracts.** Use a refactor script under `scripts/refactor/` when the change touches more than three contracts; one-off edits are acceptable for narrower changes. Bump the contract version per `versioning-policy.md` and append a changelog entry that names the specific ADR (or ADR section) driving the change.
5. **Update the validator last.** Add or modify the rule in `scripts/validation/validate-contracts.py`. Add a unit test under `scripts/validation/tests/`. The unit test asserts the ADR's decision; the rule asserts compliance.

When a contributor finds a disagreement during review:

- ADR vs. pattern: the ADR is authoritative. Either update the pattern, or the ADR is wrong and should be updated first.
- ADR vs. contract: the ADR is authoritative. Either update the contract, or the ADR is wrong.
- ADR vs. validator: the ADR is authoritative. The validator rule is wrong; update the validator and (if appropriate) backfill contracts that the rule failed to catch.
- Contract vs. validator: the validator is downstream of the ADR. If the validator rejects a contract that the ADR permits, the validator is wrong. If the validator accepts a contract that the ADR forbids, the contract is wrong.

When the ADR is silent on a question that the validator must answer:

- The validator's silence is the right behavior. Do not add an undocumented validator rule. Surface the question in the planning STATUS doc and add an ADR (or extend an existing one) before adding the validator rule.

## Guidance

- **The ADR is the merge gate, not the validator.** A contract that fails the validator but matches a not-yet-shipped ADR change should be reviewed against the proposed ADR change — not against the current validator. Land the ADR change first, then the contract, then the validator.
- **Refactor scripts are the right tool for mass changes.** When an ADR change affects ten or more contracts, write a refactor script under `scripts/refactor/` (modeled on `apply-hardening-c5.py`) that applies the change idempotently. The script's name should reference the milestone phase that landed the change. The script lives in the repository as the audit trail for the bulk change.
- **Validator rules are tested.** Each rule has at least one passing case and one failing case in `scripts/validation/tests/test_hardening_rules.py`. The unit tests are how the validator's intent is documented; the rule code is how the intent is enforced.
- **Disagreement during review is not a tie-breaker prompt.** If a reviewer finds an ADR / contract / validator disagreement, the reviewer flags which artifact must change to resolve it, naming the leftmost authoritative artifact. The author resolves accordingly. Re-opening the prior ADR decision is a separate proposal.
- **`customProperties.adrs: [...]` on each contract names the ADRs that govern its shape.** When the ADR list on a contract drifts from the actual ADRs that drove the field set, update the contract's `customProperties.adrs` to match. The validator's C1.12 rule confirms each ADR id resolves to a file under `references/design-decisions/pc/`.

## Consequences for governance

- A new contributor reading this ADR and `canonical-alignment.md` knows where to start: which artifact is authoritative, which deliberate departures the canonical surface carries, and which deferrals are out of scope.
- A reviewer evaluating a proposed change can ask one question: "Does the leftmost relevant artifact (ADR) reflect this change?" If yes, the change can proceed downstream. If no, the change is premature.
- The canonical layer becomes a system whose rules are knowable, traceable, and auditable rather than a corpus of contracts that happen to agree with each other through informal coordination.

## Related

- `references/design-decisions/pc/canonical-alignment.md` — register of deliberate departures and deferrals.
- `references/design-decisions/README.md` — full ADR index (left edge of the primacy chain).
- `references/patterns/README.md` — pattern index.
- `references/glossary/README.md` — glossary index.
- `docs/authoring-guide.md` — applies the primacy order to the per-contract authoring workflow.
- `scripts/validation/validate-contracts.py` — validator (right edge of the primacy chain).
- `scripts/validation/tests/test_hardening_rules.py` — unit tests that document validator-rule intent.
