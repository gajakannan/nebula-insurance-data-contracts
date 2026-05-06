# Status

Last updated: 2026-05-06

## Current Goal

Bring the 0.2.0 canonical P&C ODCS contract surface to a clean 0.4.x state through canonical hardening (Milestone 8.5, W025–W031) before Fabric generation begins. Detailed plan: `planning-mds/CANONICAL_HARDENING_PLAN.md`. Hardening sequences validator strengthening (C1), ADR/validator/glossary reconciliation (C2), bulk 0.3.0 refactor (C3), missing canonical entities (C4), codeset and reference-data hygiene (C5), cross-source coherence and authoring discipline (C6), and single-contract cleanups (C7).

Once hardening completes, the active goal moves to projecting the canonical surface into a Microsoft Fabric Lakehouse Silver layer through a metadata-driven approach: generated manifests drive Purview sensitivity and glossary artifacts, Delta DDL, and parameterized SCD2 / append-only / codeset notebooks. Detailed plan: `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md`.

## Guardrails

- Keep tracked files source-neutral.
- Do not commit private source review notes, raw source artifact names, URLs, copied definitions, raw schemas, ontology exports, or scratch mappings.
- Use private research only as design signal.
- Keep canonical contracts platform-neutral.
- Put implementation details under `targets/`.
- Put modeling rationale under `references/design-decisions/`.

## Current Repo State

- Repository structure is established.
- README, authoring guide, architecture notes, patterns, design decisions, and backlog exist.
- Cross-cutting design decisions are complete and indexed in `references/design-decisions/README.md` (identifier strategy, bi-temporal modeling, record state, codeset strategy, separation-and-nesting, currency, null semantics, data classification, versioning, status promotion, claims modeling, product-coverage M:N, risk-transfer scope, event-and-transaction). Three additional ADRs (`canonical-alignment.md`, `authoring-source-primacy.md`, `scd2-primary-key.md`) plus targeted ADR amendments land during canonical hardening.
- 54 P&C ODCS contracts at version 0.2.0 pass the current validator (`*_uid` GUID PKs, SCD2 fields, `record_status_code`, source-attribution, classifications, event/transaction correction-row enforcement, `_uid`-suffix discipline). Internal validation has surfaced a canonical-layer backlog — cross-cutting bugs (SCD2 PK ambiguity, append-only datetime drift, currency-pairing gaps, classification drift), ADR/validator contradictions, missing first-wave entities (Occurrence, Catastrophe, InsurableObjectPartyRole), codeset taxonomy gaps, and pattern-vs-contract gaps. These are addressed in canonical hardening (W025–W031) before Fabric generation begins.
- Glossary covers cross-cutting and area-specific terms; `references/glossary/pc/cross-cutting.md` is the single source for shared concepts.
- Authoring guide and patterns cross-link the ADRs.
- Target folders exist but the dbt path has been retired in favor of a Fabric-native approach (W022 dropped). The Fabric target is planned per `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` (W023) and is gated on canonical hardening completion.

## Active Work Items

| ID | Work Item | Status | Notes |
| --- | --- | --- | --- |
| W001 | Fix policy placeholder path mismatch | Done | `Policy` now lives under `references/odcs/pc/policy/`. |
| W002 | Add planning tracker | Done | This file tracks execution status. |
| W003 | Add implementation plan | Done | See `planning-mds/IMPLEMENTATION_PLAN.md`. |
| W004 | Create ODCS authoring template | Done | Template lives at `references/odcs/templates/pc-contract-template.odcs.yaml`. |
| W005 | Add contract validation tooling | Done | `scripts/validation/validate-contracts.py` validates YAML shape, required metadata, naming, primary keys, descriptions, custom properties, and source-neutrality guardrails. |
| W006 | Author first milestone contracts | Done | `Party`, `PartyRole`, `PartyRelationship`, `Policy`, `Coverage`, `PolicyCoverage`, `Exposure`, exposure subtypes, `Claim`, and `FinancialTransaction` are complete and pass validation. |
| W007 | Add glossary starter set | Done | Property and Casualty starter glossary lives under `references/glossary/pc/`. |
| W008 | Add target type mapping guidance | Superseded | Replaced by W023.F1 (Fabric type mapping). dbt path retired with W022. |
| W009 | Define semantic and ontology projection approach | Not started | Treat ontology as derived semantic view, not as the canonical source of truth. |
| W010 | Add missing `Coverage` placeholder | Done | Roadmap and first milestone now align to `references/odcs/pc/coverage/coverage.odcs.yaml`. |
| W011 | Add missing referenced and dependent contracts | Done | Reference data plus `PolicyTerm`, `Product`, `PolicyLimit`, `PolicyDeductible`, `InsurableObject`, and `InsurableObjectClassification` are complete and pass validation. |
| W012 | Add submission contract set | Done | `Submission`, `SubmissionPartyRole`, `SubmissionRisk`, `SubmissionAssessment`, `SubmissionDocument`, and `SubmissionLifecycleEvent` are complete and pass validation. |
| W013 | Add policy lifecycle detail contracts | Done | `PolicyPartyRole`, `PolicyLifecycleEvent`, `PolicyTransaction`, and `PolicyDocument` are complete and pass validation. |
| W014 | Author cross-cutting design decisions | Done | Fourteen ADRs added/refined under `references/design-decisions/pc/` and indexed in the design-decisions README. |
| W015 | Bulk YAML refactor to align with new ADRs | Done | All 34 prior contracts refactored to v0.2.0 with `*_uid` PKs, SCD2 fields, `record_status_code`, source-attribution, and per-property classifications. Generator at `scripts/refactor/apply-adrs.py`. |
| W016 | Add `ProductCoverage` M:N junction contract | Done | `references/odcs/pc/coverage/product-coverage.odcs.yaml` per `product-coverage-modeling.md`. |
| W017 | Add missing codeset contracts | Done | 13 codeset contracts under `references/odcs/pc/reference-data/` generated via `scripts/refactor/generate-codesets.py`. |
| W018 | Fill in claims contract set | Done | `ClaimPartyRole`, `ClaimLifecycleEvent`, `ClaimFeature`, `ClaimCoverage`, `ClaimDocument`, `ClaimFinancialTransaction` are complete and pass validation. |
| W019 | Update validator to enforce new conventions | Done | Validator enforces `*_uid` PK suffix, classifications presence with allowed sensitivity / regulatory tags, SCD2 fields on entities, correction fields on event/transaction contracts, and `proposed` status. |
| W020 | Update authoring guide and patterns to reference new ADRs | Done | `docs/authoring-guide.md`, `references/patterns/pc/*`, and root `README.md` cross-link the ADRs. New `claim-lifecycle-pattern.md` added. |
| W021 | Risk-transfer contract family (deferred scope) | Deferred | Reinsurance, coinsurance, self-insurance, and fronting are deferred per `risk-transfer-scope.md`. Tracked here so the deferral does not get lost. |
| W022 | Author target guidance for dbt | Dropped | Retired in favor of Fabric-native projection. The user is Fabric-only and does not run dbt; supporting both targets is unnecessary scope. |
| W023 | Author target guidance for Microsoft Fabric | Blocked | First and only target. Metadata-driven projection per `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md`. Broken into F1–F8 phases below. Blocked on canonical hardening (W025–W031) completion. |
| W023.F1 | Fabric: conventions and type mapping | Not started | `targets/fabric/README.md`, `type-mapping.md`, `conventions.md`, `manifest-schema.md`. Documentation only; no generators yet. |
| W023.F2 | Fabric: manifest generator and one example | Not started | `scripts/generation/generate-fabric-manifests.py`, `scripts/validation/validate-fabric-manifests.py`, plus the Policy manifest as the golden example. Pause for user review of manifest shape after this phase. |
| W023.F3 | Fabric: manifest generation for all 54 contracts | Not started | Run the generator across the contract set; spot-check entity, codeset, event, and transaction kinds. |
| W023.F4 | Fabric: DDL generation | Not started | `scripts/generation/generate-fabric-ddl.py` and 54 Spark SQL `CREATE TABLE IF NOT EXISTS` files under `targets/fabric/ddl/pc/`. |
| W023.F5 | Fabric: notebook templates | Not started | Three parameterized `.ipynb` templates (SCD2 merge, append-only, codeset load) plus lakehouse-binding template. Honors Fabric `.ipynb` validation rules (`outputs: []`, `execution_count: null`). |
| W023.F6 | Fabric: Purview manifests | Not started | `sensitivity-labels.json` and `business-glossary.json` under `targets/fabric/purview/`, generated from manifests + glossary. |
| W023.F7 | Fabric: worked-example walkthrough | Not started | `targets/fabric/examples/end-to-end-policy.md` walks Policy + PolicyTerm + PolicyCoverage + PolicyStatusCode end to end. |
| W023.F8 | Fabric: status, planning, validator closeout | Not started | Update STATUS, IMPLEMENTATION_PLAN, root README. Wire `validate-fabric-manifests.py` into the documented validation flow. |
| W024 | Glossary refresh for new conventions | Done | Added `references/glossary/pc/cross-cutting.md` (single source for shared terms); refreshed area files for GUID vs business-key identifiers, ProductCoverage, the six new claims contracts, immutability/correction language, and the new codesets. Glossary index updated to point at `cross-cutting.md` first. |
| W025 | Canonical hardening C1 — validator-first enforcement | Pause for review | 12 new validator rules implemented in `scripts/validation/validate-contracts.py` (C1.1–C1.12). Unit tests in `scripts/validation/tests/test_hardening_rules.py` (35 tests, all green). Run produces 195 errors + 7 warnings (202 total) across the unmodified 0.2.0 surface; deterministic punch list at `planning-mds/CANONICAL_HARDENING_PUNCH_LIST.md`. By rule: C1.1=10, C1.2=160, C1.5=8, C1.6=3 (warning), C1.7=17, C1.8=4 (warning); C1.3, C1.4, C1.9, C1.10, C1.11, C1.12 produce zero findings on 0.2.0 (no unresolved targets, all append-only contracts have `corrects_*_uid`, every `classificationProfile` ≥ max field sensitivity, no contracts at `approved`, no version bumps vs HEAD, no `customProperties.adrs` yet). No contract edits made. Pause for review per CANONICAL_HARDENING_PLAN.md §6 checkpoint 1 before C2 begins. |
| W026 | Canonical hardening C2 — ADR / validator / glossary reconciliation | Not started | Rewrite `identifier-strategy.md` to match shipped naming, drop `review` status from validator allowlist (or codify in ADR), rephrase `status-promotion.md` enforcement claims to match validator, add `null-semantics.md` addendum on business booleans vs null indicators, clarify `data-classification.md` narrative defaults. ADR text only; no contract edits. Detail: `planning-mds/CANONICAL_HARDENING_PLAN.md` §4 phase C2. Pause for review after completion. |
| W027 | Canonical hardening C3 — bulk 0.3.0 refactor | Not started | Apply C1 validator's findings as one cross-cutting commit: SCD2 PK resolution (new `scd2-primary-key.md` ADR), drop `created/updated_datetime` from append-only contracts, drop mutable `transaction_status_code`, add currency pairing to four exposure subtypes, fix over- and under-classified fields, drop redundant `*_uid + *_code` pairs, replace YAML anchors with explicit lists. Bump every touched contract to 0.3.0. Scripted via `scripts/refactor/apply-hardening-c3.py`. Detail: `planning-mds/CANONICAL_HARDENING_PLAN.md` §4 phase C3. |
| W028 | Canonical hardening C4 — canonical entity gaps | Not started | Land `Occurrence`, `Catastrophe`, `InsurableObjectPartyRole`, direct `insurable_object_uid` FK on `Claim`. Decisions on `Account` / `Agreement` (default amend), `PolicyFinancialTransaction` (default ship). Drop generic `pc.party-role`. Rename `claim-party-role.party_role_type_code` → `role_type_code`. Align document-contract field naming on cleanest schema; propagate `contains_phi_indicator`. Bump affected contracts to 0.4.0. Detail: `planning-mds/CANONICAL_HARDENING_PLAN.md` §4 phase C4. Pause for review after completion. |
| W029 | Canonical hardening C5 — codeset and reference-data hygiene | Not started | Land top 10–15 missing codesets; add codeset relationships to all `*_code` fields where the codeset exists; codeset-strategy ADR addendum on pure-codeset vs reference-data-entity distinction; set pure-codeset `classificationProfile: PUBLIC`; unify `*_status_code` field naming on reference contracts; document `record-status-code` self-reference. Detail: `planning-mds/CANONICAL_HARDENING_PLAN.md` §4 phase C5. |
| W030 | Canonical hardening C6 — cross-source coherence and authoring discipline | Not started | Land `canonical-alignment.md` ADR (deliberate departures + deferrals) and `authoring-source-primacy.md` ADR (ADR > pattern > glossary > contract > validator). Add `customProperties.adrs: [...]` on every contract; validator confirms each id resolves. Update authoring guide and architecture doc. Resolve pattern-vs-contract gaps (`party-role-pattern.md`, `financial-transaction-pattern.md`). Detail: `planning-mds/CANONICAL_HARDENING_PLAN.md` §4 phase C6. |
| W031 | Canonical hardening C7 — single-contract cleanups | Not started | Rename `vehicle-exposure.vehicle_identifier` → `vin_number`; resolve `submission-lifecycle-event.triggering_transaction_uid` dead reference; add mutually-exclusive-outcome quality rule on `submission`; resolve `created_datetime` / `updated_datetime` semantic ambiguity per contract; address `source_natural_key` single-slot multi-source provenance. Final canonical surface lands at 0.4.x. Detail: `planning-mds/CANONICAL_HARDENING_PLAN.md` §4 phase C7. |

## Next Recommended Step

W025 (C1) is complete and at the §6 checkpoint 1 pause. The 12 validator rules are live, the test suite is green, and the punch list at `planning-mds/CANONICAL_HARDENING_PUNCH_LIST.md` lists 202 findings against the unmodified 0.2.0 surface. Review the rule semantics and the punch-list shape before C2 begins.

Items the reviewer should confirm before C2:

- **C1.2 noise from `source_system_code`** — every contract has this field and none has a codeset relationship for it (because it is a source-attribution field, not a codeset reference per `identifier-strategy.md`). C3 will either add `customProperties.codesetExempt: true` per contract or refine C1.2 to whitelist source-attribution fields by name. Decision pending.
- **C1.1 surfaces 6 currency-pairing findings, not the 4 listed in `CANONICAL_HARDENING_PLAN.md` §4 C3.4** — the strict same-prefix matcher catches `policy-term.annualized_premium_amount` and `policy-transaction.premium_change_amount` in addition to the four exposure-subtype amounts. Both are real same-shape issues; recommend folding them into C3.4.
- **C1.6 warning severity is correct** (`flag for review` per the plan); C1.7 narrative-classification findings are errors (per the plan).
- **C1.8 over-classification heuristic** confirms the four `RESTRICTED + PII` mis-tags named in `§4 C3.5` (`policy-lifecycle-event.resulting_status_code`, `submission-lifecycle-event.resulting_status_code`, plus two others). It does not yet flag `lifecycle-event-type.resulting_lifecycle_status_uid` (a `_uid` field, not `_code`) or `exposure.rating_territory_code`/`financial-transaction.accounting_period_code` if those are at INTERNAL — confirm whether the heuristic is wide enough.

Once the C1 outputs are confirmed, W026 (C2 — ADR / validator / glossary reconciliation) starts: ADR text-only edits resolving the four contradictions named in `§4 phase C2`. No contract edits until C3.

Sequencing remains: **W025 (C1, paused) → W026 (C2) → W027 (C3) → W028 (C4) → W029 (C5) → W030 (C6) → W031 (C7) → W023 (Fabric F1–F8) → Milestone 10**. Pause-for-review checkpoints after C1 (active now), C2, and C4. W023 (Fabric) does not begin until W031 closes.
