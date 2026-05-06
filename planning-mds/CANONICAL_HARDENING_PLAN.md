# Canonical Hardening Plan

This plan defines how the locked-but-imperfect 0.2.0 P&C canonical surface is brought to a clean 0.4.x state before any target projection consumes it. It is the detailed companion to **Milestone 8.5: Canonical Hardening** in `planning-mds/IMPLEMENTATION_PLAN.md` and to work items **W025–W031** in `planning-mds/STATUS.md`.

This document is authoritative for canonical hardening. ADRs, validator code, contract YAML, and pattern documents follow what this plan specifies; if they diverge, this plan is the source of truth and the artifacts must be re-aligned.

Last updated: 2026-05-05.

## 1. Intent

Bring the 54-contract P&C canonical surface to a state where:

- Every cross-cutting convention named in an ADR is mechanically enforced by `scripts/validation/validate-contracts.py`.
- Every contract is internally consistent: ADR ↔ pattern ↔ glossary ↔ contract ↔ validator agree on the same rule set.
- Canonical entity coverage is sufficient for first-wave use cases (claims correlated by occurrence, catastrophe-driven aggregation, per-vehicle and per-property claim lookup, additional-insured and named-driver semantics on insurable objects).
- The codeset taxonomy is complete enough that the Fabric target's `code-reference` role has somewhere to point for every `*_code` field.
- New contributors can navigate the canonical layer without prior context.

Hardening output is a 0.4.x canonical surface with zero validator findings, zero ADR/pattern/glossary/contract contradictions, and a documented set of deliberate departures from the recommended modeling defaults.

### Success criteria

- Validator enforces every cross-cutting rule named in `references/design-decisions/pc/`. New rules added in this plan (currency pairing, codeset relationship resolution, target-contract resolution, append-only field bans, classification heuristics, status-promotion gates, changelog-on-version-bump, ADR-id resolution) all run as part of the standard validation pass.
- All 54 contracts pass the strengthened validator without exclusions or `validatorException` flags.
- All four cross-source contradictions (identifier strategy, `review` status, status-promotion gates, narrative-classification defaults) are reconciled, and ADR text matches what shipped.
- Six canonical entity gaps (`Occurrence`, `Catastrophe`, `InsurableObjectPartyRole`, direct `insurable_object_uid` FK on `Claim`, decision on `Account`/`Agreement`, decision on `PolicyFinancialTransaction`) are closed.
- Codeset coverage extends to the 10–15 highest-frequency status/type/classification families currently missing.
- `customProperties.adrs: [...]` appears on every contract, and the validator confirms each ADR id resolves to a file under `references/design-decisions/pc/`.
- The canonical-alignment ADR documents every deliberate departure from the recommended modeling defaults, so reviewers do not have to reverse-engineer the answer.

## 2. Non-Negotiable Boundaries

The following are constraints. The implementation must obey them; if a phase pulls in tension with one, the phase is wrong, not the constraint.

- **Source-neutral framing.** No tracked artifact (this plan, ADRs, contract docs, glossary, patterns, code) names external reference models, source URLs, source-document identifiers, copied class hierarchies, or scratch mappings. Findings are framed as canonical-modeling decisions justified on business grounds.
- **Validator-first ordering.** Phase C1 (validator strengthening) runs before any contract is edited. The validator's findings are the punch list for the bulk refactor, not a human-curated list.
- **One bulk version bump per refactor wave.** Phase C3 produces a single 0.3.0 wave across all touched contracts; phase C4 produces a single 0.4.0 wave. Per-contract piecemeal version bumps are not used during hardening.
- **No target work pulled forward.** The Fabric target (`planning-mds/FABRIC_IMPLEMENTATION_PLAN.md`, W023.F1–F8) does not start until canonical hardening completes. The metadata-driven Fabric posture depends on a clean canonical layer; a partial refactor would force manifest regeneration midway through.
- **Deferred scope stays deferred.** Risk-transfer (reinsurance, coinsurance, fronting, self-insurance), litigation/arbitration as first-class entities, the full assessment-subtype hierarchy, and semantic projection are not pulled into hardening. Each is acknowledged in §11 so the deferral is deliberate, not silent.
- **ADR primacy.** Where ADR text and shipped contracts disagree, the resolution is decided per case in phase C2: rewrite the ADR to match what shipped *or* refactor contracts to match the ADR. The default is to rewrite the ADR to match what shipped, since the contracts have been reviewed; departures from this default are documented per ADR.

## 3. Architectural Posture

### 3.1 Hardening flow

```
ODCS contracts at 0.2.0
        │
        ▼  C1: validator strengthening
Validator with new rules + violation report
        │
        ▼  C2: ADR/validator/glossary reconciliation
Coherent rule set
        │
        ▼  C3: bulk 0.3.0 refactor (validator-driven)
Clean 0.3.0 contracts
        │
        ▼  C4: canonical entity gaps
0.4.0 contracts with Occurrence, Catastrophe, InsurableObjectPartyRole
        │
        ▼  C5: codeset and reference-data hygiene
Codeset taxonomy enforced
        │
        ▼  C6: cross-source coherence and authoring discipline
ADR-back-linked contracts, canonical-alignment ADR
        │
        ▼  C7: single-contract cleanups
0.4.x final
        │
        ▼  → handoff to Fabric (W023.F1–F8)
```

### 3.2 Versioning during hardening

- C1, C2, C6 do not bump contract versions — they touch validator code, ADRs, and `customProperties.adrs` lists, which the versioning policy treats as documentation/governance changes.
- C3 bumps every touched contract to 0.3.0 in a single commit, mirroring the W015 0.2.0 refactor.
- C4 bumps the affected contracts (claim, claim-feature, claim-coverage, exposure, party-role, plus new entities) to 0.4.0.
- C5 bumps codesets and any contracts whose `*_code` fields gain `relationships:` blocks to a 0.4.x patch.
- C7 produces small per-contract patches.

The full set lands at 0.4.x by the end of C7. The Fabric target consumes the 0.4.x surface.

### 3.3 ADRs added or amended during hardening

| ADR | Phase | Action |
|---|---|---|
| `identifier-strategy.md` | C2 | Rewrite to match shipped naming (`*_uid` PK, `*_number` business key, `*_code` codeset reference). Drop dead-letter `*_id` clause. |
| `null-semantics.md` | C2 | Add a one-liner distinguishing business-meaning booleans (`*_indicator` carrying real semantics) from null-presence indicators. |
| `data-classification.md` | C2 | Clarify default for narrative free-text (`*_description`, `*_summary`, `*_narrative`, `*_notes`, `*_text`) and the carve-out for codeset `code_value` fields. |
| `status-promotion.md` | C2 | Either add `review` to the allowed states or remove from the validator. (Default: drop from validator.) Rephrase enforcement claims to match what the validator actually checks. |
| `scd2-primary-key.md` | C3 | New ADR: choose between composite logical PK (`*_uid + valid_from_datetime`) and dual-identity (per-version `*_record_uid` plus logical `*_uid`). Decision documented with rationale. |
| `codeset-strategy.md` | C5 | Addendum: distinguish pure-codeset contracts (PUBLIC profile, `*_code` filename suffix, single `code_value` field) from richer reference-data-entity contracts (`LineOfBusiness`, `LifecycleStatus`, `LifecycleEventType`, `TransactionType`, `GeographicLocation`, `LocationAddress`). |
| `canonical-alignment.md` | C6 | New ADR: documents every deliberate departure from the recommended modeling defaults, with rationale per departure. Lists deferrals (risk-transfer, litigation, full assessment hierarchy) so reviewers find them in one place. |
| `authoring-source-primacy.md` | C6 | New ADR: documents the primacy order (ADR > pattern > glossary > contract > validator) so contributors know which to update first when something changes. |

## 4. Phasing

Each phase ends with a green validator run and a documented checkpoint in `planning-mds/STATUS.md`.

### Phase C1 — Validator-first enforcement

**Goal:** make the validator the authority for every cross-cutting rule named in an ADR, before any contract is edited.

Deliverables (all in `scripts/validation/validate-contracts.py`):

- **C1.1** `*_amount` / `*_currency_code` pairing. Detect any property whose name ends `_amount` and require a sibling `*_currency_code` in the same `properties:` array, unless `customProperties.amountCurrencyExempt: true` with a written rationale.
- **C1.2** `*_code` codeset reference resolution. For each property ending `_code` (excluding codeset contracts themselves), require either (a) a `relationships:` entry whose `sourceFields` contains it pointing at a codeset contract under `references/odcs/pc/reference-data/`, or (b) `customProperties.codesetExempt: true` with rationale.
- **C1.3** `targetContractId` resolution. Build the set of contract ids from filenames; for every relationship's `targetContractId`, verify the target exists. Flag typos and dead references.
- **C1.4** `corrects_*_uid` field presence on append-only contracts. Currently only `correction_indicator` is checked. Add: when `correction_indicator` is present, a `corrects_*_uid` field must also be present.
- **C1.5** Forbid `created_datetime` / `updated_datetime` on append-only contracts (those carrying `correction_indicator`). Append-only rows are immutable; an "updated" datetime is incoherent.
- **C1.6** Forbid `*_uid` + `*_code` redundancy for the same lookup. Detect pairs `<name>_uid` and `<name>_code` in the same schema where `<name>` matches a known codeset; flag for review.
- **C1.7** Narrative free-text classification heuristic. Detect properties whose name ends in `_description` / `_notes` / `_narrative` / `_text` / `_summary` and require sensitivity ≥ `CONFIDENTIAL` and at least one regulatory tag, unless `customProperties.classifications.narrativeException: true`.
- **C1.8** Status / period / territory over-classification heuristic. Flag any field whose name contains `_status_code` / `_result_code` / `_period_code` / `_territory_code` / `_region_code` / `_accounting_*` AND tagged `RESTRICTED + PII` for reviewer attention (warning, not error).
- **C1.9** `classificationProfile` matches maximum field-level sensitivity. Profile cannot be `INTERNAL` if any field is tagged `CONFIDENTIAL` or higher.
- **C1.10** Status-promotion gates. Implement the gates documented in `status-promotion.md` (steward approval, known consumers, codeset reference resolution, `targetContractId` existence on promotion). If a gate cannot be checked from YAML alone, mark it explicitly as out-of-scope in the ADR.
- **C1.11** Changelog-on-version-bump. When a contract's version differs from the previous git revision, require a corresponding `customProperties.changelog` entry naming the version.
- **C1.12** ADR id resolution. When `customProperties.adrs: [...]` is present, every id must resolve to a file under `references/design-decisions/pc/`. (The list is added per-contract in C6; the validator rule is shipped in C1 so the resolution check is ready when the lists arrive.)

Acceptance criteria:

- Each of the 12 rules has a unit test or small fixture confirming pass and fail behavior.
- Running the validator against the unmodified 0.2.0 contract set produces a deterministic violation report.
- The violation report is checked into `planning-mds/CANONICAL_HARDENING_PUNCH_LIST.md` (transient artifact, deleted at the end of C3).
- No contract is edited in this phase. Only the validator changes.

Estimated scope: 1 week.

### Phase C2 — ADR / validator / glossary reconciliation

**Goal:** eliminate the contradictions between what ADRs say and what the validator and shipped contracts do.

Deliverables (ADR text changes only; no contract edits):

- **C2.1** Rewrite `identifier-strategy.md` to match shipped naming. The current ADR text reserves `*_id` for legacy/business-key naming where it already exists. Validator rejects `*_id` non-PKs. No contract uses `*_id`. Resolution: drop the `*_id` clause, codify the shipped `*_uid` / `*_number` / `*_code` triad.
- **C2.2** Reconcile `review` status. Validator's `ALLOWED_STATUSES` set has six values; `status-promotion.md` ADR has five. Default resolution: drop `review` from the validator allowlist (the ADR's five-state lifecycle is the documented model). Alternative: add `review` to the ADR with documented gates.
- **C2.3** Rephrase `status-promotion.md` enforcement claims. The ADR claims the validator checks steward approval, known consumers, codeset reference resolution, and `targetContractId` existence on promotion. C1.10 adds what can be checked from YAML; remaining items become "guidance, not enforced" in the ADR text.
- **C2.4** Add a one-liner to `null-semantics.md` distinguishing business-meaning booleans (`litigation_indicator`, `catastrophe_indicator`, `mandatory_indicator`, `selected_indicator`, `active_status_indicator`, `terminal_status_indicator`) from null-presence indicators. The ADR's existing prohibition on companion presence-indicators stands; the addendum makes clear it does not apply to business booleans.
- **C2.5** Clarify `data-classification.md` narrative defaults. State explicitly that narrative free-text fields default to `CONFIDENTIAL + PII` unless a written exception applies. Document the carve-out for codeset `code_value` fields (which are `PUBLIC`). The narrative-classification fixes themselves land in C3.

Acceptance criteria:

- Every ADR claim about validator enforcement matches what the validator actually checks (post-C1).
- Validator allowed-status set matches `status-promotion.md`.
- `null-semantics.md` and `data-classification.md` are unambiguous on the cases that previously required reviewer interpretation.
- No contract is edited in this phase.

Estimated scope: 2–3 days.

### Phase C3 — Bulk 0.3.0 refactor

**Goal:** apply the C1 validator's findings as one cross-cutting commit, mirroring the W015 0.2.0 refactor.

Deliverables (contract edits across the full 54-contract set, scripted where possible via `scripts/refactor/apply-hardening-c3.py`):

- **C3.1** **SCD2 PK resolution.** Land `references/design-decisions/pc/scd2-primary-key.md` ADR. Default decision: composite logical PK `(*_uid, valid_from_datetime)` declared via `primaryKey: true` on both fields. Apply to all 34 entity contracts. Add quality rule `single_current_row_per_key` if not present.
- **C3.2** **Drop `created_datetime` / `updated_datetime` from append-only contracts.** Apply to `policy-lifecycle-event`, `policy-transaction`, `submission-lifecycle-event`, `financial-transaction`. (`claim-lifecycle-event` and `claim-financial-transaction` already correct.)
- **C3.3** **Drop mutable `transaction_status_code`** from `policy-transaction` and `financial-transaction`. Status changes belong on lifecycle events, not on the immutable transaction row.
- **C3.4** **Add currency pairing** to four exposure subtypes: `property-exposure.building_value_amount`, `property-exposure.contents_value_amount`, `vehicle-exposure.stated_value_amount`, `workers-comp-exposure.payroll_amount`. Each gets a sibling `*_currency_code` field with appropriate codeset relationship.
- **C3.5** **Fix over-classification.** Re-tag `policy-lifecycle-event.resulting_status_code`, `submission-lifecycle-event.resulting_status_code`, `lifecycle-event-type.resulting_lifecycle_status_uid`, `financial-transaction.accounting_period_code`, `exposure.rating_territory_code` to `INTERNAL` (no PII tag). Re-tag `location-address.location_address_uid` (PK GUID) and `location-address.address_type_code` to `INTERNAL`. Run the C1.8 heuristic across the full set and apply the same fix wherever the pattern appears.
- **C3.6** **Fix narrative under-classification.** Run the C1.7 heuristic across the full set. Re-tag `claim.claim_description`, `policy.policy_description`, `claim-document.document_title`, `submission.submission_description`, `submission-risk.risk_description`, `coverage.coverage_description`, `submission-assessment.assessment_summary`, and any other narrative free-text field caught by the heuristic, to `CONFIDENTIAL` with appropriate regulatory tags.
- **C3.7** **Drop redundant `*_uid` + `*_code` pairs** from `policy-lifecycle-event` (`lifecycle_event_type_uid` / `lifecycle_event_type_code`), `submission-lifecycle-event` (same pair), `policy-transaction` (`transaction_type_uid` / `transaction_type_code`). Keep the `_code` form. Update relationships to use the `_code` form.
- **C3.8** **Replace YAML anchors with explicit lists** in `policy-deductible`, `property-exposure`, `location-address`. Anchors (`&id001` / `*id001`) are not preserved by all downstream parsers.
- **C3.9** **Bump every touched contract to 0.3.0** with a changelog entry naming the specific issues fixed per contract.

Acceptance criteria:

- Validator passes against all 54 contracts with zero findings.
- Every touched contract carries a 0.3.0 changelog entry naming the specific C1 rule(s) that drove the change.
- The C1 punch-list file is empty and is deleted from `planning-mds/`.
- Single bulk commit, mirroring the W015 0.2.0 commit shape.

Estimated scope: 1 week.

### Phase C4 — Canonical entity gaps

**Goal:** close the missing-entity gaps that block first-wave use cases (multi-claim correlation, catastrophe rollup, named-driver / additional-insured semantics, direct claim-to-insurable-object lookup).

Deliverables (new contracts plus targeted edits):

- **C4.1** **`Occurrence` contract** under `references/odcs/pc/claims/occurrence.odcs.yaml`. Carries occurrence id, occurrence date, occurrence type code, occurrence description, location reference, and SCD2 / record-state cross-cutting fields. Multiple `Claim` rows can share an `occurrence_uid` so per-occurrence limits can be enforced and multi-claim incidents (e.g. one auto accident, three claimants) correlate cleanly. Add `occurrence_uid` FK on `Claim`.
- **C4.2** **`Catastrophe` contract** under `references/odcs/pc/claims/catastrophe.odcs.yaml`. Carries catastrophe id, industry catastrophe code, company catastrophe code, name, type code, start datetime, end datetime, and SCD2 / record-state cross-cutting fields. Replace `claim.catastrophe_code` (free string) with `catastrophe_uid` FK; keep `catastrophe_indicator` as a derived business boolean.
- **C4.3** **`InsurableObjectPartyRole` contract** under `references/odcs/pc/exposure/insurable-object-party-role.odcs.yaml`. Already documented in `references/patterns/pc/party-role-pattern.md` but not yet shipped. Carries the standard party-role shape (`role_type_code`, `start_date`, `end_date`, `role_status_code`, plus `insurable_object_uid` and `party_uid` FKs). Enables canonical expression of "named driver of vehicle", "additional insured on building", "loss-payee on property".
- **C4.4** **Direct `insurable_object_uid` FK on `Claim`.** Currently claim has `exposure_uid` only, forcing a two-hop join to find claims by VIN or property. Add the direct FK; quality rule confirms the FK aligns with the path through `exposure`.
- **C4.5** **Decision: `Account` and `Agreement` contracts.** The architecture doc claims `core/` covers `(party, account, agreement)` but only `party` / `party-relationship` / `party-role` exist. Two paths:
  - **Ship**: land `Account`, `InsuredAccount`, `AccountPartyRole`, `AccountAgreement` under `references/odcs/pc/core/`. Recommended for commercial-line use cases where account-level grouping matters.
  - **Amend**: update the architecture doc to scope `core/` to party-only and defer account/agreement to a future milestone.
  - Default decision pending user input: **amend**, since first-wave use cases do not require account-level grouping; revisit when commercial-line scope expands. Document in `canonical-alignment.md` ADR (C6) as a deliberate departure.
- **C4.6** **Decision: `PolicyFinancialTransaction` contract.** `financial-transaction-pattern.md` lists four contracts in the family; only `FinancialTransaction` and `ClaimFinancialTransaction` exist. Two paths:
  - **Ship**: land `PolicyFinancialTransaction` and `FinancialTransactionClassification` under `references/odcs/pc/financial/`. Recommended if policy-side financial activity (premium movements, fee posts, commission accruals) needs a separate lifecycle from generic financial-transaction.
  - **Amend**: update `financial-transaction-pattern.md` to list only the two shipped contracts; route policy-side financial activity through generic `FinancialTransaction` with a `transaction_classification_code`.
  - Default decision pending user input: **ship**, since claim-side has its own and the asymmetry is operationally awkward.
- **C4.7** **Drop generic `pc.party-role` contract.** Specific role contracts (`policy-party-role`, `claim-party-role`, `submission-party-role`, plus new `insurable-object-party-role` from C4.3) exist; the generic version's polymorphic `context_type_code` + `context_uid` cannot be validated by ODCS. Remove the contract and any references.
- **C4.8** **Rename `claim-party-role.party_role_type_code`** → `role_type_code` for consistency with the other three role contracts.
- **C4.9** **Align document-contract field naming.** Pick the cleanest schema (currently `claim-document`'s) and align `policy-document` and `submission-document` to it. Specifically: unify `document_title` vs `document_name` (default to `document_title`), unify `external_storage_reference` vs `document_reference` (default to `external_storage_reference`), unify `capture_datetime` vs `received_datetime` (default to `capture_datetime` plus `received_datetime` for documents that have both), propagate `contains_phi_indicator` to all three document contracts.
- **C4.10** **Bump affected contracts to 0.4.0.** New contracts ship at 0.1.0. Existing contracts touched in C4 (claim, claim-feature, claim-coverage, claim-party-role, exposure, policy-document, submission-document) bump to 0.4.0.

Acceptance criteria:

- New contracts pass the strengthened validator with zero findings.
- Every existing claim and exposure contract has an accessible path to its insurable object in one hop.
- `Occurrence` and `Catastrophe` are ready to anchor analytics queries (per-occurrence limit math, catastrophe rollup) once data lands.
- Pattern documents (`party-role-pattern.md`, `financial-transaction-pattern.md`) match what the contract set actually contains.

Estimated scope: 1–2 weeks.

### Phase C5 — Codeset and reference-data hygiene

**Goal:** complete the codeset taxonomy enough that the Fabric target's `code-reference` role has a target for every `*_code` field.

Deliverables:

- **C5.1** **Land top 10–15 missing codesets.** Prioritized by frequency of use across the contract set. Initial slate: `feature-status-code`, `document-type-code`, `document-status-code`, `coverage-decision-code`, `relationship-type-code`, `relationship-status-code`, `role-status-code`, `assessment-type-code`, `assessment-status-code`, `assessment-result-code`, `submission-status-code`, `submission-type-code`, `transaction-classification-code`, `expense-classification-code` (ALAE/ULAE per glossary), `claim-type-code`. Generate via `scripts/refactor/generate-codesets.py` extended with the new slate.
- **C5.2** **Add codeset relationships to all `*_code` fields where the codeset exists.** Run scripted across the contract set: for every `*_code` field, if a matching codeset contract exists under `references/odcs/pc/reference-data/`, add a `relationships:` entry pointing to it. C1.2 enforces presence after this phase.
- **C5.3** **Codeset-strategy ADR addendum.** Document the pure-codeset vs reference-data-entity distinction in `references/design-decisions/pc/codeset-strategy.md`:
  - **Pure codeset**: filename ends `-code`, single `code_value` field, `classificationProfile: PUBLIC`, `customProperties.codesetContract: true`. Used for status / type / classification enumerations.
  - **Reference-data entity**: filename does not require `-code` suffix, richer field set (description, hierarchy, active range), `classificationProfile: INTERNAL` permitted, `customProperties.codesetContract: false` or absent. Used for `LineOfBusiness`, `LifecycleStatus`, `LifecycleEventType`, `TransactionType`, `GeographicLocation`, `LocationAddress`.
- **C5.4** **Set pure-codeset `classificationProfile: PUBLIC`** across the 13 pure codesets. Currently they tag every field `PUBLIC` but set the profile `INTERNAL` — wrong profile triggers unnecessary masking when downstream targets emit sensitivity labels.
- **C5.5** **Unify `*_status_code` field naming on reference contracts.** Inconsistencies: `insurable-object-classification.status_code`, `lifecycle-event-type.status_code`, `lifecycle-status.reference_status_code`, `line-of-business.status_code`, `transaction-type.status_code`, `coverage.coverage_status_code`, `policy-term.term_status_code`. Pick `<entity>_status_code` as the convention and rename.
- **C5.6** **Fix `pc.product` `subjectArea`** from `coverage` to `product` (or `core` if no `product` subject area exists; align to whatever the architecture doc says).
- **C5.7** **Fix `lifecycle-event-type` and `lifecycle-status` `code_value` sensitivity** to `PUBLIC`. Currently tagged `INTERNAL`, inconsistent with pure codesets.
- **C5.8** **Document `record-status-code` self-reference.** Add an addendum to `codeset-strategy.md`: "the `record-status-code` codeset bootstraps using its own `ACTIVE` / `SUPERSEDED` values; this self-reference is intentional."

Acceptance criteria:

- Every `*_code` field in the canonical surface either has a codeset relationship or carries `customProperties.codesetExempt: true` with a written rationale.
- C1.2 validator passes with zero findings.
- Pure codesets and reference-data entities are clearly distinguished in glossary, validator behavior, and field-naming convention.
- Pure-codeset `classificationProfile` is `PUBLIC` throughout.

Estimated scope: 3–5 days.

### Phase C6 — Cross-source coherence and authoring discipline

**Goal:** make the canonical layer navigable for new contributors without prior context, and make the rule set self-documenting via per-contract ADR back-links.

Deliverables:

- **C6.1** **Land `canonical-alignment.md` ADR** under `references/design-decisions/pc/`. Documents:
  - Every deliberate departure from recommended modeling defaults, with rationale per departure (e.g. "Agreement-as-parent collapsed into Policy because risk-transfer is deferred"; "Identifier `_uid` instead of `_identifier` for compactness"; "Coverage Group rendered as a codeset rather than a separate hierarchy entity"; "Policy Amount rendered as a transaction-classification rather than a separate `Amount` entity").
  - Deferrals (risk-transfer family, litigation/arbitration as first-class entities, full assessment subtype hierarchy, semantic projection, additional targets beyond Fabric).
  - Cross-references to the relevant ADRs and patterns.
- **C6.2** **Land `authoring-source-primacy.md` ADR.** Documents the primacy order — ADR > pattern > glossary > contract > validator — so contributors know which to update first when something changes. Without this, the next author won't know whether the ADR or the contract is wrong.
- **C6.3** **Add `customProperties.adrs: [...]` on every contract.** Each contract names the ADRs that govern its shape: identifier-strategy, temporal-modeling, record-state, codeset-strategy, currency-convention, data-classification, etc. C1.12 (validator rule) confirms each id resolves.
- **C6.4** **Per-contract changelogs name specific ADRs.** Replace generic `0.2.0: Apply cross-cutting ADRs (...)` entries with entries that name which ADR drove which field addition. Apply going forward; do not retroactively rewrite existing 0.2.0 entries (those are git history). Land the discipline starting with C3's 0.3.0 changelog entries.
- **C6.5** **Update authoring guide** under `docs/authoring-guide.md` to reference `authoring-source-primacy.md` and document the workflow: when a rule changes, update the ADR first, then the validator, then the contracts, then the patterns and glossary.
- **C6.6** **Update architecture doc** under `docs/repository-and-architecture.md` to reflect the C4.5 decision on `Account`/`Agreement` (whichever path was chosen).
- **C6.7** **Resolve pattern-vs-contract gaps.** Update `party-role-pattern.md` to remove `InsurableObjectPartyRole` reference (now exists per C4.3). Update `financial-transaction-pattern.md` to reflect the C4.6 decision.

Acceptance criteria:

- Every contract carries `customProperties.adrs: [...]`.
- C1.12 passes (every ADR id resolves).
- A new contributor can read `authoring-source-primacy.md` and know which artifact to update first when something changes.
- `canonical-alignment.md` is the single place a reviewer can look to find every deliberate departure.
- No pattern document references a contract that does not exist, and vice versa.

Estimated scope: 3–5 days.

### Phase C7 — Single-contract cleanups

**Goal:** close the long tail of single-contract issues that don't fit into the cross-cutting waves above.

Deliverables (per-contract patches):

- **C7.1** **`vehicle-exposure.vehicle_identifier`** → `vin_number`. Aligns with the authoring-guide naming-convention requirement that business keys end in `_number`.
- **C7.2** **Resolve `submission-lifecycle-event.triggering_transaction_uid`** dead reference. Either remove the field (no `submission-transaction` contract exists) or land `submission-transaction` if submission-side transactions need their own lifecycle. Default: remove the field; submission lifecycle is event-only.
- **C7.3** **Add quality rule** to `submission`: at most one of `bind_date`, `decline_date`, `withdrawn_date` is populated per snapshot. Outcomes are mutually exclusive but no rule currently enforces it.
- **C7.4** **Resolve `created_datetime` / `updated_datetime` semantic ambiguity.** Two paths per contract:
  - Rename to `source_created_datetime` / `source_updated_datetime` if the field captures the source-system timestamp (useful for late-arriving-data analysis).
  - Drop if redundant with `valid_from_datetime` / `valid_to_datetime`.
  - Decide per contract; document the decision in the per-contract changelog entry.
- **C7.5** **Address `source_natural_key` single-slot multi-source provenance.** Either land a `*-source-provenance` 1:N child contract for entities that may merge across multiple source systems, or amend `identifier-strategy.md` to say "primary source key only; multi-source provenance is an MDM concern outside the canonical layer." Default: amend the ADR; defer the child contract until an MDM use case bites.

Acceptance criteria:

- All single-contract issues from the C1 violation report (post-C3) are resolved.
- Validator passes with zero findings.
- Every changelog entry names the specific issue closed.

Estimated scope: 2–3 days.

## 5. Sequencing and Dependencies

```
C1 ───────► C2 ───────► C3 ───────► C4 ───────► C5 ───────► C6 ───────► C7 ───────► Fabric (W023.F1–F8)
(validator) (ADR        (bulk        (entity      (codeset     (ADR back-   (single
            reconciliation) refactor) gaps)        hygiene)     links)       cleanup)
```

- **C1 must precede everything.** The validator is the punch-list source.
- **C2 must precede C3.** Some C3 fixes depend on knowing whether the ADR or the contract was wrong.
- **C3 must precede C4 and C5.** New entities and new codeset relationships should be authored against the strengthened validator, not the 0.2.0 one.
- **C4 and C5 can run partially in parallel.** New entities (C4) need codesets to reference; the C5 codeset slate covers most of those needs. If a C4 entity needs a codeset C5 hasn't shipped, ship that codeset opportunistically as part of C4.
- **C6 follows C4 and C5.** Per-contract ADR back-links can't be added until the contract set is stable.
- **C7 follows C6.** Per-contract changelogs gain the C6 discipline, so single-contract patches should follow.
- **Fabric (W023) starts only after C7.** This is the non-negotiable boundary in §2.

Total estimated scope: 4–6 weeks of focused work, plus pause-for-review checkpoints after C1 (validator behavior), C3 (bulk refactor outcome), and C4 (entity-gap decisions on Account/Agreement and PolicyFinancialTransaction).

## 6. Pause Checkpoints

Three checkpoints where work halts and the user reviews:

1. **After C1.** Review the validator's deterministic violation report. Confirm rule semantics before C3 acts on them.
2. **After C2.** Review the ADR text changes. Confirm the resolution direction (default: rewrite ADR to match shipped contracts) is correct per ADR.
3. **After C4.** Review the C4.5 (`Account`/`Agreement`) and C4.6 (`PolicyFinancialTransaction`) decisions. These have business implications beyond canonical hygiene.

Each checkpoint is brief — confirm and proceed, or course-correct.

## 7. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Validator changes (C1) break the existing 0.2.0 contracts en masse, blocking all forward work | C1 explicitly does not edit contracts. Violation report is captured as a transient punch list; contracts stay unchanged until C3 acts on it. |
| Bulk refactor (C3) introduces regressions in contracts not flagged by the validator | C3 uses scripted refactor (`scripts/refactor/apply-hardening-c3.py`) wherever possible. Manual edits are reviewed against a diff per contract. Changelogs name the specific rule that drove each change. |
| New entity contracts (C4) require ADR decisions that are not pre-aligned | Defaults documented per decision (C4.5, C4.6). User-review checkpoint after C4 catches misalignment. |
| Codeset slate (C5.1) misses a high-frequency codeset, forcing a follow-up wave | The C1.2 validator finding is the source of the slate; if a codeset's absence becomes a finding, it lands in C5.1 by definition. |
| ADR back-links (C6.3) drift from the actual ADRs that drove a field | C1.12 validator rule confirms every ADR id resolves. New ADRs added in C2/C3/C5/C6 are themselves checked. |
| Hardening completes but Fabric work surfaces a missing canonical signal | Open questions (§9) flag known unknowns. If Fabric F1–F2 surfaces an unforeseen gap, it returns as a hardening follow-up, not a Fabric scope creep. |
| Commercial-line scope (account/agreement, full assessment hierarchy, litigation) becomes urgent before hardening completes | These are deferred per §2 and §11; pulling them in is an explicit re-scope, not a silent scope expansion. |

## 8. Out of Scope for This Milestone

- **Risk-transfer family** (reinsurance, coinsurance, fronting, self-insurance). Deferred per `risk-transfer-scope.md`.
- **Litigation / Arbitration as first-class entities.** Currently modeled as `litigation_indicator: boolean` on `Claim`. Acceptable for first-wave; promotion to first-class entities is a future milestone.
- **Full assessment subtype hierarchy.** `submission-assessment` is the only assessment contract; the broader assessment family is deferred. Documented as a deliberate departure in `canonical-alignment.md` (C6.1).
- **`Account` and `Agreement` contracts** (default amend per C4.5). Re-evaluate when commercial-line scope expands.
- **Semantic projection** (RDF / OWL / SKOS / knowledge graph). Deferred per W009.
- **Additional targets beyond Fabric.** Out of scope per IMPLEMENTATION_PLAN.md.
- **Bronze / ingestion / connector concerns.** Outside the canonical layer.
- **Streaming ingestion.** Out of scope.

## 9. Open Questions

Known unknowns that may surface during execution:

1. **SCD2 PK style: composite vs dual-identity.** Default in `scd2-primary-key.md` (C3.1) is composite. If downstream tooling (Fabric, future targets, MDM) prefers dual-identity, the ADR's default flips. Decision lives in the ADR, not in this plan.
2. **Severity of the C1.8 over-classification heuristic.** Currently warning-only. If the heuristic produces too many false positives, it stays warning. If it catches real bugs reliably, it promotes to error in a follow-up wave.
3. **Severity of C1.11 changelog-on-version-bump.** May be impractical for pure docs-only ADR back-link additions in C6. If so, narrow the rule to only fire when contract `properties:` change.
4. **Whether `Account` / `Agreement` ship now or later.** C4.5 default is "amend" (defer). If commercial-line use cases land sooner, the decision flips and a follow-up phase ships them.
5. **Whether `PolicyFinancialTransaction` ships now.** C4.6 default is "ship". If user input is "amend the pattern instead", the decision flips.
6. **Multi-source provenance handling.** C7.5 default is "amend ADR; defer the child contract." If MDM pressure arrives, the child contract becomes a follow-up.

## 10. Definition of Done

The milestone is complete when:

- All 12 C1 validator rules are live and passing on the full contract set.
- All 5 C2 ADR reconciliations are landed.
- All 9 C3 bulk-refactor tasks are landed; full contract set is at 0.3.x with no validator findings.
- All 10 C4 entity-gap tasks are landed (or the decision-deferral path is documented in `canonical-alignment.md`); affected contracts are at 0.4.0.
- All 8 C5 codeset/reference-data tasks are landed; every `*_code` field has a codeset relationship or a written exemption.
- All 7 C6 cross-source coherence tasks are landed; every contract carries `customProperties.adrs: [...]`.
- All 5 C7 single-contract cleanups are landed; final canonical surface is at 0.4.x.
- `planning-mds/STATUS.md` reflects the post-milestone state and W023 is the active focus.
- `references/design-decisions/pc/` contains `canonical-alignment.md`, `authoring-source-primacy.md`, `scd2-primary-key.md`, plus the addended existing ADRs.
- No tracked file leaks external source names, URLs, copied class hierarchies, or scratch mappings.

## 11. Reference Implementation Index

When the milestone is complete the following file map describes the canonical hardening output:

```text
references/
  design-decisions/pc/
    canonical-alignment.md                    # NEW — deliberate departures + deferrals
    authoring-source-primacy.md               # NEW — ADR > pattern > glossary > contract > validator
    scd2-primary-key.md                       # NEW — composite vs dual-identity decision
    codeset-strategy.md                       # ADDENDUM — pure-codeset vs reference-data-entity
    identifier-strategy.md                    # REWRITTEN — drop _id, codify shipped triad
    null-semantics.md                         # ADDENDUM — business booleans vs null indicators
    data-classification.md                    # CLARIFIED — narrative defaults
    status-promotion.md                       # CLARIFIED — enforcement claims match validator
    (other ADRs unchanged)
  odcs/pc/
    claims/
      occurrence.odcs.yaml                    # NEW (C4.1)
      catastrophe.odcs.yaml                   # NEW (C4.2)
      (existing claim contracts at 0.4.0)
    exposure/
      insurable-object-party-role.odcs.yaml   # NEW (C4.3)
      (existing exposure contracts at 0.4.0)
    financial/
      policy-financial-transaction.odcs.yaml  # NEW if C4.6 ships (default)
      financial-transaction-classification.odcs.yaml  # NEW if C4.6 ships
      (existing financial contracts at 0.4.0)
    reference-data/
      (existing 19 + ~10–15 new codesets from C5.1)
    (other contracts at 0.3.0–0.4.0 with customProperties.adrs)
  patterns/pc/
    party-role-pattern.md                     # UPDATED — InsurableObjectPartyRole now exists
    financial-transaction-pattern.md          # UPDATED per C4.6 decision
    (other patterns unchanged)

scripts/
  validation/
    validate-contracts.py                     # 12 new rules from C1
  refactor/
    apply-hardening-c3.py                     # NEW — C3 bulk refactor
    generate-codesets.py                      # EXTENDED — C5.1 new slate

docs/
  authoring-guide.md                          # UPDATED — references authoring-source-primacy.md
  repository-and-architecture.md              # UPDATED — reflects C4.5 decision

planning-mds/
  STATUS.md                                   # W025–W031 registered; W023 still active
  IMPLEMENTATION_PLAN.md                      # Milestone 8.5 inserted
  CANONICAL_HARDENING_PLAN.md                 # this file
  FABRIC_IMPLEMENTATION_PLAN.md               # precondition note added at top; F-phase reordering per §3
```
