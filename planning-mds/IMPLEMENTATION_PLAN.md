# Implementation Plan

## Intent

Build a canonical, platform-neutral insurance data contract library for Property and Casualty data products. The contracts should define the Silver-layer business agreement between producers, platform engineers, data product owners, and consumers.

The repository should end with:

- Complete ODCS v3 YAML contracts for the first P&C contract set.
- Clear modeling patterns and design decisions.
- A canonical glossary.
- Validation and inspection tooling.
- Target implementation guidance that preserves canonical meaning.
- A semantic projection strategy for ontology, knowledge graph, and AI-assisted use cases.

## Non-Negotiable Boundaries

- Tracked files must not include private source artifact names, source URLs, copied definitions, raw source schemas, raw ontology exports, or source review notes.
- Canonical contracts must be original business-aligned artifacts.
- Private source material can inform entity boundaries, relationship patterns, terminology gaps, and validation questions.
- ODCS contracts are the canonical source of truth.
- Target artifacts and semantic artifacts are generated from or aligned to canonical contracts, not the other way around.

## Current Baseline

The canonical surface is at version 0.2.0 and has known hardening work pending before it can be considered locked:

- `references/odcs/` — 54 contracts pass the current validator (entity, codeset, event, transaction). Cross-cutting conventions (identifier strategy, SCD2, record state, classifications, codesets, currency pairing) are partially enforced; the strengthened rule set lands during canonical hardening.
- `references/design-decisions/` — 14 ADRs plus the original six modeling decisions, indexed in the design-decisions README. Additional ADRs (`canonical-alignment.md`, `authoring-source-primacy.md`, `scd2-primary-key.md`) and ADR amendments land during canonical hardening.
- `references/patterns/` — seven patterns covering party-role, submission-lifecycle, policy-lifecycle, claim-lifecycle, policy-coverage, exposure, and financial-transaction. Cross-linked to ADRs.
- `references/glossary/` — cross-cutting terms file plus area-specific files; refreshed for the post-ADR contract shape.
- `scripts/validation/` — `validate-contracts.py` enforces the current canonical conventions; canonical hardening adds 12 new rules.
- `scripts/refactor/` — one-time migration scripts (`apply-adrs.py`, `generate-codesets.py`) that produced the 0.2.0 surface.
- `docs/` — authoring guide and architecture notes cross-link the ADRs.
- `targets/fabric/` — Fabric target, complete: 4 documentation files (`README.md`, `conventions.md`, `type-mapping.md`, `manifest-schema.md`); 85 generated manifests under `manifests/pc/<area>/`; 85 generated `CREATE TABLE IF NOT EXISTS` files under `ddl/pc/<area>/`; three parameterized notebook templates plus `lakehouse-binding-template.json` under `notebooks/`; consolidated `purview/sensitivity-labels.json` (85 tables, 1235 columns) and `purview/business-glossary.json` (308 terms); two worked walkthroughs at `examples/end-to-end-policy.md` (SCD2 entity + codeset side) and `examples/end-to-end-claims.md` (append-only event + transaction with `lifecycle-event-link` + C4.5 commercial-lines spine). dbt and other platforms are deferred or dropped.
- `docs/contract-inventory.md` — generated navigation surface (M10.2) covering all 85 contracts by Spark schema, kind, version, status, description, and ADR back-links.
- `docs/review-checklist.md` — structured PR review page (M10.4) organized by contract kind, with cross-cutting checks, status-promotion review, and the Fabric impact matrix.
- `CHANGELOG.md` — generated repository-level changelog (M10.3) aggregating per-contract entries by canonical-version wave (`0.4.x` → `0.1.x`); 318 entries post-M10.6.
- `planning-mds/CANONICAL_HARDENING_PLAN.md` — detailed plan for Milestone 8.5, sequenced C1 → C7 (complete).
- `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` — detailed plan for the Fabric Lakehouse projection, sequenced F1 → F8 (complete).
- `planning-mds/MILESTONE_10_PLAN.md` — detailed plan for Milestone 10, sequenced M10.1 → M10.6 (complete).

Canonical hardening (Milestone 8.5, C1–C7) is complete: validator strengthening, ADR/validator/glossary reconciliation, bulk 0.3.0 refactor, missing canonical entities (Occurrence, Catastrophe, InsurableObjectPartyRole, plus the C4.5 commercial-lines spine — Account, AccountRelationship, AccountPartyRole, Agreement), codeset taxonomy completion, ADR back-linking, and single-contract cleanup all shipped. Surface is at 0.4.x.

Fabric target (Milestone 9, F1–F8) is complete: docs, manifest generator + drift validator, manifest fan-out, Purview manifests, Spark SQL DDL, parameterized notebook templates, worked end-to-end Policy walkthrough, and closeout (orchestrator + planning / README pointers) all shipped. The orchestrator at `scripts/generation/generate-fabric.py` runs the four sub-generators in order and ends with a `validate-fabric-manifests.py --require-full-coverage` drift check.

Milestone 10 (W032, M10.1–M10.6) is complete: claims worked example, contract inventory generator + page, repo-level CHANGELOG generator + page, PR review checklist, versioning-policy extension covering manifest version + regeneration cadence + consumer pinning, and status promotion (every contract advanced from `draft` to at least `proposed`; 14-contract policy walkthrough cohort plus dependent codesets advanced to `approved`). The M10.7 follow-up (W033) advanced the 11-contract claims cohort (six walkthrough contracts + five transitively-referenced codesets) to `approved`, bringing the approved cohort to 25 and resolving MILESTONE_10_PLAN.md §5 open question 1.

Remaining work: deferred-scope items only — risk-transfer contract family (W021), semantic projection (W009), additional targets beyond Fabric, and future status-promotion waves (C4.5 commercial-lines spine to `approved` once a documented downstream consumer exists; the rest of the proposed long tail stays at `proposed` pending a consumer).

## Source Review Posture

Use local private research in this order:

1. Conceptual narrative and glossary signal: identify major subject areas, entity boundaries, and terminology pressure points.
2. Semantic graph signal: check class hierarchy, relationship direction, and role modeling patterns.
3. Relational schema signal: check field candidates, keys, cardinality hints, and subtype explosion risks.
4. Link inventory: local reference only, not tracked documentation.

Do not mechanically translate any one source. Use multiple signals to make original canonical decisions.

## Architecture Decision

The canonical layering should be:

```text
Business concept
    -> Canonical entity
    -> ODCS contract
    -> Validation and documentation
    -> Target-specific physical projection
    -> Optional semantic projection
```

ODCS contracts are the contract layer. Ontology is a semantic view over the contract layer.

## Ontology Role

Ontology belongs in this repo as a derived or curated semantic layer, not as the repository's foundation.

Use ontology for:

- Concept hierarchy checks.
- Relationship consistency checks.
- Synonym and term alignment.
- AI/RAG retrieval context.
- Knowledge graph projection.
- Semantic layer documentation.
- Cross-domain reuse decisions.

Do not use ontology for:

- Copying external class names into canonical contracts.
- Replacing ODCS as the contract authoring format.
- Modeling physical database shape.
- Creating one contract per ontology class.
- Storing raw ontology exports in tracked files.

Recommended future structure:

```text
references/semantic/
  README.md
  pc/
    concept-map.md
    relationship-map.md

targets/semantic/
  README.md
  rdf-generation.md
  knowledge-graph-projection.md
```

`references/semantic/` should hold original semantic rationale and concept maps. `targets/semantic/` should explain how to project ODCS contracts into RDF, OWL, SKOS, graph databases, or AI retrieval indexes.

## Is `references/` An Ontology?

No. `references/` is broader than ontology.

In this repo, `references/` is the governed canonical reference library. It contains:

- ODCS contracts.
- Modeling patterns.
- Design decisions.
- Glossary terms.
- Future semantic maps.

Ontology can be one kind of reference artifact, but the current `references/` tree is not itself an ontology. The canonical contracts should remain in `references/odcs/`; semantic and ontology-facing artifacts should be additional views.

## Milestone 0: Repo Hygiene And Planning

Goal: make the workspace safe to scale.

Tasks:

- Keep private research folders ignored.
- Keep tracked planning docs source-neutral.
- Fix misplaced placeholder paths.
- Add a status tracker.
- Add a detailed implementation plan.
- Add a source-neutral review checklist.

Acceptance criteria:

- `git status` shows only intentional repo changes.
- No tracked file contains private source names or URLs.
- Work items are trackable from `planning-mds/STATUS.md`.

## Milestone 1: Authoring Template And Validation

Goal: make one good contract easy to repeat.

Tasks:

- Create a canonical ODCS template under `docs/examples/` or `references/odcs/templates/`.
- Define required metadata fields.
- Define required field metadata.
- Define relationship notation conventions.
- Define quality rule conventions.
- Add a validation script for:
  - YAML parseability.
  - `apiVersion`, `kind`, `id`, `name`, `version`, `status`, and `domain`.
  - Contract id and path alignment.
  - Lowercase snake_case physical field names.
  - Required primary keys.
  - Required descriptions.
  - Required `customProperties`.
  - Banned provenance terms and URLs.
- Add a contract inventory script.

Acceptance criteria:

- Running validation gives actionable pass/fail output.
- Placeholder contracts fail validation until completed.
- Completed contracts can be checked consistently.

## Milestone 2: Core Identity Contracts

Goal: establish reusable identity and participation foundations.

Contracts:

- `Party`
- `PartyRole`
- `PartyRelationship`
- `Account`
- `Agreement`

Key decisions:

- `Party` is the reusable identity anchor.
- Person and organization details should be modeled without source-specific subtype sprawl.
- Contextual participation belongs in role contracts.
- Durable party-to-party relationships belong in `PartyRelationship`.
- Account and Agreement should support customer and contractual grouping without becoming policy-specific.

Deliverables:

- Complete ODCS contracts.
- Role modeling glossary terms.
- Updated role pattern if needed.
- Design decision notes for party subtype boundaries.

Acceptance criteria:

- `Party` can support policy, claim, account, submission, and producer contexts.
- Role contracts carry context, type, dates, status, and relationship keys.
- No duplicated party identity fields are introduced into policy or claim contracts.

## Milestone 3: Policy, Coverage, And Product Contracts

Goal: model issued policy business structure and coverage selection.

Contracts:

- `Policy`
- `PolicyTerm`
- `PolicyPartyRole`
- `PolicyLifecycleEvent`
- `PolicyTransaction`
- `PolicyDocument`
- `Product`
- `Coverage`
- `PolicyCoverage`
- `PolicyLimit`
- `PolicyDeductible`

Key decisions:

- `Policy` is durable identity.
- `PolicyTerm` carries term periods.
- Lifecycle changes are events.
- Transaction-level policy changes are separate from current policy state.
- Reusable coverage definition is separate from policy-applied coverage.
- Limits and deductibles are separate where they have meaningful structure.

Deliverables:

- Complete ODCS contracts.
- Policy lifecycle glossary terms.
- Coverage pattern refinements.
- Example policy contract walkthrough.

Acceptance criteria:

- Bind, issue, endorsement, renewal, cancellation, reinstatement, audit, expiration, and non-renewal can be represented.
- Coverage can be queried by product, policy, term, limit, deductible, and status.
- Policy and coverage contracts remain platform-neutral.

## Milestone 4: Exposure And Insurable Object Contracts

Goal: make risk basis usable for underwriting, rating, claims, and analytics.

Contracts:

- `InsurableObject`
- `InsurableObjectClassification`
- `Exposure`
- `VehicleExposure`
- `PropertyExposure`
- `WorkersCompExposure`

Key decisions:

- `InsurableObject` is what may be insured.
- `Exposure` is the measurable risk basis.
- Specialized exposure contracts are used only when distinct durable fields justify them.
- Vehicle, property, and workers compensation details should not force every subtype into a top-level canonical contract.

Deliverables:

- Complete ODCS contracts.
- Exposure glossary terms.
- Examples for policy-to-coverage-to-exposure relationships.

Acceptance criteria:

- Exposure can be associated with policy term, coverage, insurable object, location, and claim context.
- Subtypes remain manageable and analytically useful.

## Milestone 5: Submission And Underwriting Contracts

Goal: support the pre-policy operating lifecycle.

Contracts:

- `Submission`
- `SubmissionPartyRole`
- `SubmissionRisk`
- `SubmissionAssessment`
- `SubmissionDocument`
- `SubmissionLifecycleEvent`
- `Assessment`
- `RiskAssessment`
- `UnderwritingAssessment`

Key decisions:

- Submission is first-class because many submissions do not become policies.
- Submission status is current-state convenience; lifecycle events preserve history.
- Underwriting assessment should carry result, rationale, dates, and relationship context.

Deliverables:

- Complete ODCS contracts.
- Submission lifecycle examples.
- Assessment modeling rationale.

Acceptance criteria:

- Intake, triage, clearance, referral, indication, quote, bind, decline, and withdrawal can be represented.
- A submission can exist without a policy.
- A bound or issued submission can link to policy context.

## Milestone 6: Claim Contracts

Goal: represent claim intake, lifecycle, coverage association, parties, features, documents, and claim activity. Symmetry with `Policy` and `Submission` is required.

Contracts:

- `Claim`
- `ClaimFeature`
- `ClaimLifecycleEvent`
- `ClaimCoverage`
- `ClaimPartyRole`
- `ClaimDocument`
- `ClaimFinancialTransaction`

Key decisions:

- Claim is tied to loss and policy context where available.
- Claim lifecycle events preserve operational history (per `event-and-transaction.md`).
- Claim financial movement is modeled via `ClaimFinancialTransaction`, never as a sibling subtype contract per money kind.
- Claim party roles follow the party-role pattern (per `role-modeling.md`).
- Claim features partition large claims that handle multiple coverages, perils, or claimants on independent feature streams.
- Claim coverage connects claim or feature handling to policy coverage and exposure where known.
- Reinsurance, coinsurance, and recovery activity is deferred to the risk-transfer contract family (per `risk-transfer-scope.md`).

Deliverables:

- Complete ODCS contracts.
- Claim lifecycle pattern if needed.
- Claim glossary terms.

Acceptance criteria:

- Loss notice, claim open, assignment, reserve change, payment, recovery, litigation, close, and reopen can be represented through events and transactions per `event-and-transaction.md`.
- Claim parties and coverage relationships are explicit.

## Milestone 7: Financial Transaction Contracts

Goal: avoid monetary subtype sprawl while preserving policy and claim financial meaning.

Contracts:

- `FinancialTransaction`
- `PolicyFinancialTransaction`
- `ClaimFinancialTransaction`
- `FinancialTransactionClassification`

Key decisions:

- Premiums, fees, taxes, surcharges, commissions, payments, reserves, recoveries, salvage, and subrogation are classifications or dimensions unless they require independent lifecycle.
- Monetary context should be preserved through policy, claim, coverage, party, exposure, accounting period, and currency references.

Deliverables:

- Complete ODCS contracts.
- Financial transaction glossary.
- Classification starter set.

Acceptance criteria:

- Policy and claim financial movement can be queried through one consistent transaction structure.
- Classification supports analytics without creating one contract per money subtype.

## Milestone 8: Reference Data And Glossary

Goal: stabilize coded values and canonical terminology.

Contracts:

- `GeographicLocation`
- `LocationAddress`
- `LineOfBusiness`
- `TransactionType`
- `LifecycleStatus`
- `LifecycleEventType`

Glossary areas:

- Party and role terms.
- Policy lifecycle terms.
- Submission lifecycle terms.
- Coverage terms.
- Exposure terms.
- Claim terms.
- Financial transaction terms.
- Reference data terms.

Acceptance criteria:

- Common coded values have a canonical home.
- Glossary definitions are original, concise, and aligned with contracts.
- Contract field descriptions use glossary terms consistently.

## Milestone 8.5: Canonical Hardening

Goal: bring the 0.2.0 canonical surface to a clean 0.4.x state before any target projection consumes it.

Detailed plan: `planning-mds/CANONICAL_HARDENING_PLAN.md`. The plan is authoritative for canonical hardening; this milestone summary mirrors it.

This milestone is inserted between the original Milestone 8 (Reference Data and Glossary, complete) and Milestone 9 (Target Implementation Guidance, in progress) because internal validation surfaced a canonical-layer backlog that must be resolved before Fabric generation can begin. The metadata-driven Fabric posture treats canonical contracts as the source of truth; if canonical hygiene is not complete, generated manifests, DDL, notebooks, and Purview labels inherit every issue.

Phasing (per `CANONICAL_HARDENING_PLAN.md`):

- **C1** — Validator-first enforcement. Add 12 new rules covering currency pairing, codeset relationship resolution, target-contract-id resolution, append-only field bans, classification heuristics, status-promotion gates, changelog-on-version-bump, and ADR-id resolution. Pause for review.
- **C2** — Reconcile ADR / validator / glossary contradictions. Rewrite `identifier-strategy.md` to match shipped naming, drop `review` from validator allowlist (or codify in ADR), rephrase `status-promotion.md` enforcement claims, clarify `null-semantics.md` and `data-classification.md` defaults. Pause for review.
- **C3** — Bulk 0.3.0 refactor. Apply the C1 validator's findings as one cross-cutting commit (SCD2 PK resolution, append-only datetime cleanup, currency pairing, classification fixes, redundant `_uid` + `_code` removal, YAML anchor expansion). Bump every touched contract to 0.3.0.
- **C4** — Canonical entity gaps. Land `Occurrence`, `Catastrophe`, `InsurableObjectPartyRole`, direct `insurable_object_uid` FK on `Claim`, decisions on `Account` / `Agreement` and `PolicyFinancialTransaction`, drop generic `pc.party-role`, align role-type and document-contract field naming. Bump to 0.4.0. Pause for review.
- **C5** — Codeset and reference-data hygiene. Land top 10–15 missing codesets, add codeset relationships to all `*_code` fields where the codeset exists, add codeset-strategy ADR addendum on pure-codeset vs reference-data-entity distinction, fix pure-codeset `classificationProfile`.
- **C6** — Cross-source coherence and authoring discipline. Land `canonical-alignment.md` and `authoring-source-primacy.md` ADRs, add `customProperties.adrs: [...]` on every contract, update authoring guide and architecture doc, resolve pattern-vs-contract gaps.
- **C7** — Single-contract cleanups. Rename `vehicle-exposure.vehicle_identifier`, resolve dead references, add mutually-exclusive-outcome quality rule on `submission`, resolve `created_datetime` / `updated_datetime` semantic ambiguity, address `source_natural_key` single-slot question.

Acceptance criteria for the milestone:

- All 12 C1 validator rules are live and pass on the full contract set.
- All cross-source contradictions (identifier strategy, `review` status, status-promotion gates, narrative-classification defaults) are reconciled.
- Six canonical entity gaps are closed (or the deferral is documented in `canonical-alignment.md`).
- Codeset coverage extends to the highest-frequency status / type / classification families.
- `customProperties.adrs: [...]` appears on every contract; validator confirms each id resolves.
- The canonical-alignment ADR documents every deliberate departure from the recommended modeling defaults.
- Final canonical surface is at 0.4.x with zero validator findings.

## Milestone 9: Target Implementation Guidance

Status: **complete** (W023, F1–F8). The Fabric target ships under `targets/fabric/` and `scripts/generation/`; the orchestrator entry point is `scripts/generation/generate-fabric.py`.

Goal: project canonical contracts onto a target platform without changing canonical meaning.

The first and only target in this milestone is **Microsoft Fabric Lakehouse**. The dbt path was retired (W022) once it became clear the consumer is Fabric-native. Databricks, Snowflake, Kafka, API, and semantic projections are out of scope for this milestone and tracked under deferred scope.

The Fabric projection follows a **metadata-driven** posture: the canonical ODCS contract is the only insurance-aware artifact, a generated Fabric manifest is the only platform-aware artifact, and every downstream artifact (Delta DDL, SCD2 / append / codeset notebook templates, Purview sensitivity manifest, business glossary manifest) is derived from the manifest. No bespoke per-contract code; no hand-authored manifests.

Detailed plan: `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md`. The plan is authoritative for the Fabric target; this milestone summary mirrors it.

Phasing (per `FABRIC_IMPLEMENTATION_PLAN.md`):

- **F1** — Conventions and type mapping documentation under `targets/fabric/`.
- **F2** — Manifest generator + manifest validator + one golden manifest example (Policy). Pause for review.
- **F3** — Generate manifests for all 54 contracts.
- **F4** — Generate Purview sensitivity-labels and business-glossary JSON manifests. (Pulled ahead of DDL/notebooks because the data-classification ADR's payoff materializes only when sensitivity labels reach materialized columns.)
- **F5** — Generate Spark SQL `CREATE TABLE IF NOT EXISTS` Delta DDL.
- **F6** — Generate three parameterized Fabric `.ipynb` notebook templates (SCD2 merge, append-only event/transaction, codeset load) plus a lakehouse-binding template.
- **F7** — Worked end-to-end example walkthrough (Policy + PolicyTerm + PolicyCoverage + PolicyStatusCode).
- **F8** — Status, planning, and validator closeout; cross-link from root README.

Acceptance criteria for the milestone:

- Every canonical entity contract has a Spark SQL DDL file and an SCD2-capable manifest.
- Every event/transaction contract has an append-only manifest with correction handling.
- Every codeset has a SCD2 codeset manifest.
- Field-level sensitivity classifications produce a Purview sensitivity manifest covering every Delta column.
- HIPAA-tagged contracts produce PHI-aware Purview entries and notebook annotations.
- Three notebook templates (SCD2, append, codeset) read any conformant manifest at runtime.
- Manifests cannot drift from source ODCS contracts: `validate-fabric-manifests.py` enforces SHA-256 digest pinning and structural alignment.
- The worked example (`targets/fabric/examples/end-to-end-policy.md`) walks the full pipeline end to end.
- Canonical field meaning, relationships, lifecycle semantics, and quality rules are unchanged by Fabric projection.

## Milestone 10: Examples, Docs, And Release Governance

Status: **complete** (W032, M10.1–M10.6). Detailed plan: `planning-mds/MILESTONE_10_PLAN.md`.

Goal: make the library usable and governable.

Phasing (per `MILESTONE_10_PLAN.md`):

- **M10.1** — Claims worked-example walkthrough at `targets/fabric/examples/end-to-end-claims.md`. Six contracts (Claim, ClaimFeature, ClaimLifecycleEvent, ClaimFinancialTransaction, ClaimStatusCode, FinancialTransactionClassification) covering append-only event, append-only transaction with `lifecycle-event-link`, and the C4.5 commercial-lines spine that the policy walkthrough deliberately leaves out.
- **M10.2** — Generated contract inventory at `docs/contract-inventory.md`, produced by `scripts/generation/generate-contract-inventory.py`. Single tracked navigation page covering all 85 contracts by Spark schema, kind, version, status, description, and ADR back-links.
- **M10.3** — Repo-level changelog at `CHANGELOG.md`, produced by `scripts/generation/generate-changelog.py`. Aggregates per-contract `customProperties.changelog` entries grouped by canonical-version wave (`0.4.x` → `0.1.x`).
- **M10.4** — PR review checklist at `docs/review-checklist.md`. Codifies the canonical and Fabric drift validators plus the C7 single-contract cleanups into a structured page organized by contract kind.
- **M10.5** — `versioning-policy.md` extended with three new sections covering the Fabric manifest version surface, the regeneration cadence, and consumer-side pinning patterns.
- **M10.6** — Status promotion via `scripts/refactor/apply-milestone-10-status.py`. Every canonical contract advanced from `draft` to at least `proposed`; the four-contract policy walkthrough cohort plus 10 transitively-referenced codesets advanced to `approved` (14 total).

Acceptance criteria for the milestone:

- One new worked-example walkthrough lives under `targets/fabric/examples/`, covering a non-policy area that exercises the append-only event family, the transaction family, and the C4.5 commercial-lines spine.
- Tracked contract-inventory page exists and is regenerable.
- Repository-level `CHANGELOG.md` aggregates per-contract changelog entries.
- PR review checklist exists and is cross-linked from `docs/authoring-guide.md` and the root README.
- `versioning-policy.md` covers the manifest-version surface, Fabric artifact regeneration cadence, and consumer-side pinning.
- Every contract is at least `status: proposed`; a documented cohort is `status: approved`.

## First Execution Order

Milestones 0–8 are complete: ODCS template, validator, party / policy / coverage / exposure / claim / financial / submission / reference-data contracts, glossary, patterns, and design decisions are all in place.

Milestone 8.5 — Canonical Hardening — is complete: C1 (validator-first enforcement, 12 new rules) → C2 (ADR / validator / glossary reconciliation) → C3 (bulk 0.3.0 refactor) → C4 (canonical entity gaps, including the C4.5 commercial-lines spine reversal) → C5 (codeset and reference-data hygiene) → C6 (cross-source coherence and ADR back-links) → C7 (single-contract cleanups). The canonical surface is at version 0.4.x with 85 contracts that pass the strengthened validator with zero findings.

Milestone 9 — Microsoft Fabric Lakehouse target — is complete: F1 (docs) → F2 (manifest generator + golden Policy example) → F3 (85 manifests) → F4 (Purview manifests) → F5 (Spark SQL DDL) → F6 (notebook templates) → F7 (worked end-to-end Policy walkthrough) → F8 (orchestrator + planning / README pointers). Generation flow: `scripts/generation/generate-fabric.py` runs `generate-fabric-manifests.py` → `generate-fabric-purview.py` → `generate-fabric-ddl.py` → `generate-fabric-notebooks.py` and ends with `validate-fabric-manifests.py --require-full-coverage`.

Milestone 10 — Examples, Docs, And Release Governance — is complete: M10.1 (claims walkthrough) → M10.2 (contract inventory) → M10.3 (repo-level CHANGELOG) → M10.4 (PR review checklist) → M10.5 (versioning-policy extension) → M10.6 (status promotion: 71 `proposed`, 14 `approved`) → M10.7 (W033: claims walkthrough cohort + 5 transitively-referenced codesets advanced to `approved`; 60 `proposed`, 25 `approved`).

Remaining work: deferred scope only — risk-transfer family, litigation/arbitration as first-class entities, full assessment-subtype hierarchy, semantic projection, additional targets beyond Fabric, and future status-promotion waves (C4.5 commercial-lines spine to `approved` once a real downstream consumer exists).

## Cross-Cutting Conventions (ADR-Backed)

The canonical surface is governed by the cross-cutting design decisions in `references/design-decisions/pc/`. Every contract authored or refactored in this repository must comply with:

- `identifier-strategy.md` — `*_uid` GUID primary keys plus a business-friendly key on every entity contract.
- `temporal-modeling.md` — SCD2 system-time fields (`valid_from_datetime`, `valid_to_datetime`, `is_current_indicator`) on every entity contract; business-time fields stay where they belong.
- `record-state.md` — `record_status_code` on every entity contract (default `ACTIVE`); soft delete via state transition, never physical delete.
- `event-and-transaction.md` — events and transactions are complementary; events for state changes, transactions for processed activity; corrections are immutable new rows.
- `codeset-strategy.md` — every `*_code` references a governed codeset contract under `references/odcs/pc/reference-data/`.
- `null-semantics.md` — null is "value not present, reason unspecified"; codeset sentinels are used when "unknown" or "not applicable" must be distinguished.
- `currency-convention.md` — every monetary field paired with `*_currency_code`; no canonical house currency.
- `data-classification.md` — `customProperties.classifications` on every property; `classificationProfile` summarized at contract level.
- `versioning-policy.md` — SemVer with data-contract-specific MAJOR/MINOR/PATCH semantics.
- `status-promotion.md` — `draft → proposed → approved → deprecated → retired` with documented gates per transition.
- `separation-and-nesting.md` — five criteria for when a concept becomes its own contract vs nested attributes.
- `product-coverage-modeling.md` — `Product` ↔ `Coverage` is M:N via `ProductCoverage`.
- `claims-modeling.md` — claim contract symmetry with policy and submission.
- `risk-transfer-scope.md` — reinsurance, coinsurance, self-insurance, and fronting are deferred (W021).

## Deferred Scope

The following business areas are recognized but not modeled in the current milestone. Each is tracked so that the deferral is deliberate, not silent.

- Reinsurance — treaties, cessions, recoveries, layers, attachment points (see `risk-transfer-scope.md`, W021).
- Coinsurance — multi-carrier participation on a single policy (see `risk-transfer-scope.md`, W021).
- Self-insurance — captives, retentions, deductible buy-down structures where the named insured retains a layer (see `risk-transfer-scope.md`, W021).
- Fronting — arrangements where one carrier issues paper for another carrier's risk (see `risk-transfer-scope.md`, W021).
- Semantic projection — RDF/OWL/SKOS/knowledge-graph derivation (W009).
- Target guidance for Databricks, Snowflake, Kafka, API — out of scope for this target milestone. Fabric is the only first-wave target.
- dbt projection — retired (W022). The consumer is Fabric-native; the metadata-driven Fabric projection covers the same ground without an intermediate transformation framework.
- Gold layer marts, semantic models, and Power BI artifacts — downstream of Silver and not generated by this repository.
- Bronze ingestion (connectors, Copy activities, scheduling) — upstream of the canonical layer and not modeled here.
- Streaming ingestion into Silver — out of scope for this target milestone; batch only.
- Real Fabric workspace deployment automation — this repository ships artifacts; deployment is a consumer responsibility.

## Definition Of Done For First Usable Release

- All first milestone contracts are complete ODCS YAML.
- All first milestone contracts pass validation.
- Each contract has primary keys, required fields, descriptions, relationships, quality rules, and custom properties.
- Glossary contains first milestone terms.
- Design decisions explain significant boundaries.
- At least one target guidance path is documented.
- Semantic projection approach is documented.
- No tracked file leaks private source names, URLs, copied definitions, raw schemas, raw ontology exports, or source review notes.
