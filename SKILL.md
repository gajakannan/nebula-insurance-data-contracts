---
name: nebula-insurance-data-contracts
description: "Work on Nebula's platform-neutral canonical insurance data contracts. Use when designing, editing, validating, documenting, or generating ODCS v3 YAML contracts, modeling patterns, design decisions, glossary terms, or target-specific implementation guidance for this repository."
compatibility: ["manual-orchestration-contract"]
metadata:
  allowed-tools: "Read Write Edit Bash(git:*) Bash(rg:*) Bash(find:*) Bash(sed:*) Bash(python3:*)"
  version: "0.2.0"
  author: "Nebula Framework Team"
  tags: ["insurance", "data-contracts", "odcs", "canonical-modeling"]
  last_updated: "2026-05-09"
---

# Nebula Insurance Data Contracts

## Current Repository State (post-Milestone 10, post-M10.7)

The canonical surface is at version 0.1.x–0.4.x with **85 P&C ODCS contracts** that pass the strengthened canonical validator with zero findings. Status distribution after M10.7:

- **25 `approved`** — the M10.6 cohort (the four-contract policy walkthrough `pc.policy`, `pc.policy-term`, `pc.policy-coverage`, `pc.policy-status-code` plus the 10 codesets it transitively references) and the M10.7 cohort (the six-contract claims walkthrough `pc.claim`, `pc.claim-feature`, `pc.claim-lifecycle-event`, `pc.claim-financial-transaction`, `pc.claim-status-code`, `pc.financial-transaction-classification` plus the 5 codesets it transitively references — `pc.claim-type-code`, `pc.feature-status-code`, `pc.cause-of-loss-code`, `pc.lifecycle-event-type`, `pc.transaction-type`).
- **60 `proposed`** — every other canonical contract.
- **0 `draft`** — every contract has been promoted at least to `proposed` (M10.6).

Kind distribution: 35 entity, 43 codeset, 3 event, 4 transaction. The full per-contract listing is generated at `docs/contract-inventory.md`; consult it before authoring a new contract or asking what already exists.

The Microsoft Fabric Lakehouse target (Milestone 9) is fully shipped under `targets/fabric/` — 85 manifests, 85 DDL files, three parameterized notebook templates, consolidated Purview JSON. Two worked walkthroughs trace the canonical-to-Fabric flow:

- `targets/fabric/examples/end-to-end-policy.md` — SCD2 entity merge + codeset SCD2 load.
- `targets/fabric/examples/end-to-end-claims.md` — append-only event + append-only transaction with `lifecycle-event-link` + the C4.5 commercial-lines spine.

Documentation produced by Milestone 10:

- `docs/contract-inventory.md` — generated navigation surface (regenerate via `scripts/generation/generate-contract-inventory.py`).
- `CHANGELOG.md` — generated repo-level changelog (regenerate via `scripts/generation/generate-changelog.py`).
- `docs/review-checklist.md` — structured PR review page; consult before opening or reviewing any canonical-layer PR.
- `planning-mds/MILESTONE_10_PLAN.md` — authoritative plan for M10 (M10.1–M10.6 complete; M10.7 follow-up resolved §5 open question 1 by promoting the claims walkthrough cohort to `approved` via `scripts/refactor/apply-milestone-10-7-status.py`).

Active path drops to **deferred scope only**: risk-transfer family (W021), semantic projection (W009), targets beyond Fabric, and future status-promotion waves (the C4.5 commercial-lines spine is the next plausible cohort once a documented downstream consumer exists). None are on the immediate path.

## Operating Posture

Treat this repository as a canonical insurance data contract library, not as a source-system model, vendor schema, reporting mart, ontology copy, or platform implementation.

Default to:

- Contract-first modeling.
- Platform-neutral ODCS v3 YAML.
- Property and Casualty first.
- Business-meaningful canonical entities.
- Source-informed judgment without copied source structure.
- Original wording in all distributable files.

Do not commit raw research, external source artifacts, URLs, copied definitions, source table dumps, ontology exports, scratch mappings, generated data, credentials, or provenance notes.

## Provenance Boundary

Private research folders are local-only design inputs. They may help identify recurring insurance concepts, relationship patterns, and terminology gaps, but distributable repository files must stand on their own.

When using private research:

- Extract design signals, not names, URLs, definitions, or schema shape.
- Reframe concepts in original repository language.
- Prefer the repository README, existing contracts, patterns, and design decisions over private artifacts.
- Do not cite private artifacts in contract descriptions, comments, docs, or commit messages.
- Do not copy table names, class names, attribute lists, relationship labels, or source documentation into canonical files.

## Repository Map

Use these locations:

- `references/odcs/` for canonical ODCS contracts.
- `references/odcs/pc/` for Property and Casualty contracts.
- `references/glossary/` for original canonical business terms.
- `references/design-decisions/` for rationale behind modeling choices.
- `references/patterns/` for reusable modeling patterns.
- `targets/` for platform-specific implementation guidance.
- `scripts/` for validation, generation, linting, and contract inspection.
- `docs/` for examples, roadmap notes, and usage guidance.

Do not put target-specific fields, physical deployment choices, or implementation-specific names into core ODCS contracts. Put those under the relevant `targets/` folder.

## P&C Contract Spine

The canonical surface ships 85 P&C contracts. Read `docs/contract-inventory.md` for the full listing by Spark schema (`silver_core`, `silver_policy`, `silver_coverage`, `silver_product`, `silver_exposure`, `silver_submission`, `silver_claims`, `silver_financial`, `silver_reference_data`); that page is the source of truth for what exists today.

The major spine areas are:

- Core (`silver_core`): `Party`, `PartyRelationship`, plus the C4.5 commercial-lines spine — `Account`, `AccountRelationship`, `AccountPartyRole`, `Agreement`. There is **no generic `PartyRole`** (deliberate departure documented in `canonical-alignment.md` — context-specific role contracts are used instead).
- Submission (`silver_submission`): `Submission`, `SubmissionPartyRole`, `SubmissionRisk`, `SubmissionAssessment`, `SubmissionDocument`, `SubmissionLifecycleEvent`.
- Policy (`silver_policy`): `Policy`, `PolicyTerm`, `PolicyPartyRole`, `PolicyLifecycleEvent`, `PolicyTransaction`, `PolicyDocument`.
- Coverage (`silver_coverage`): `Coverage`, `PolicyCoverage`, `PolicyLimit`, `PolicyDeductible`, `ProductCoverage` (M:N junction).
- Product (`silver_product`): `Product`.
- Exposure (`silver_exposure`): `InsurableObject`, `InsurableObjectClassification`, `InsurableObjectPartyRole` (C4.3), `Exposure`, `VehicleExposure`, `PropertyExposure`, `WorkersCompExposure`.
- Claims (`silver_claims`): `Claim`, `ClaimFeature`, `ClaimCoverage`, `ClaimPartyRole`, `ClaimDocument`, `ClaimLifecycleEvent`, `ClaimFinancialTransaction`, `Occurrence` (C4.1), `Catastrophe` (C4.2).
- Financial (`silver_financial`): `FinancialTransaction`, `PolicyFinancialTransaction`. `ClaimFinancialTransaction` lives under `silver_claims`. `FinancialTransactionClassification` is a codeset under `silver_reference_data`.
- Reference data (`silver_reference_data`): 43 codeset contracts. The pure codesets carry `code_value` / `code_label` and ship with `classificationProfile: PUBLIC`; the richer reference-data entities (`LineOfBusiness`, `LifecycleStatus`, `LifecycleEventType`, `TransactionType`, `GeographicLocation`, `LocationAddress`) carry domain-specific extra fields.

Add new P&C contracts under the closest folder in `references/odcs/pc/`. Create a new folder only when the concept does not fit the existing domain areas. Risk-transfer (reinsurance, coinsurance, fronting, self-insurance) and semantic projection are **deferred** per `risk-transfer-scope.md` (W021) and W009.

## Modeling Rules

Start every contract change from the business concept:

1. Define the canonical concept in original language.
2. Decide whether it belongs in an existing contract, a role table, a classification, reference data, a lifecycle event, or a new contract.
3. Check `references/patterns/` and `references/design-decisions/` before inventing a new rule.
4. Keep source-system and target-platform details out of the canonical contract.
5. Add design rationale when the boundary is significant or likely to be revisited.

Prefer stable business concepts over source-shaped structures.

Prefer classification or reference data when subtypes only change categorization.

Prefer a specialized contract only when the subtype has durable, distinct business meaning and its own meaningful attributes or relationships.

Prefer lifecycle events for meaningful business state changes instead of overwriting history.

Prefer transaction-oriented financial modeling over one canonical contract per monetary subtype.

Prefer explicit party-role contracts over duplicating party fields across business contexts.

## Required Patterns

Use the party-role pattern when a person or organization participates in a context:

- Keep `Party` as the reusable person or organization anchor.
- Use role contracts for context-specific participation.
- Store role type, effective dates, status, and relevant relationship keys on the role contract.

Use the exposure pattern for risk basis modeling:

- Keep `Policy` as the contractual container.
- Keep `Coverage` as the protection being offered or provided.
- Keep `InsurableObject` as what may be insured.
- Keep `Exposure` as the measurable risk basis.
- Use specialized exposure contracts for vehicle, property, and workers compensation details when needed.

Use the financial transaction pattern for monetary activity:

- Model premiums, fees, taxes, surcharges, payments, reserves, recoveries, salvage, subrogation, and similar money movements as transaction classifications or dimensions unless a separate contract has clear canonical value.
- Preserve context through policy, claim, coverage, party, and accounting references.

Use lifecycle patterns for submissions, policies, and claims:

- Capture meaningful state changes as dated events.
- Keep the current status on the parent contract only when useful for current-state access.
- Preserve event type, event datetime or date, effective date where applicable, reason code, and source-neutral narrative fields.

## Naming Rules

Use singular, business-meaningful contract names:

- Good: `Policy`, `Claim`, `Coverage`, `Exposure`, `FinancialTransaction`, `InsurableObject`, `GeographicLocation`
- Avoid source-shaped or implementation-shaped names such as plural table names, prefixes, suffixes, facts, dimensions, headers, or admin-system names.

Use lowercase snake_case for physical field names. The identifier triad (per `identifier-strategy.md`) is:

- `*_uid` — immutable system-generated GUID. Primary keys are `<slug>_uid` (e.g. `policy_uid`, `claim_uid`). FK references are `<target>_uid` (e.g. `policy_uid` on `pc.claim` references `pc.policy`).
- `*_number` — business-friendly key visible to humans (e.g. `policy_number`, `claim_number`, `vin_number`). Carried alongside the GUID PK for human queries.
- `*_code` — references a codeset under `references/odcs/pc/reference-data/`. Every `*_code` field needs a `relationships:` entry pointing at a codeset contract, or `customProperties.codesetExempt: true` plus a written `codesetExemptReason` (validator C1.2).

Other field-name suffixes:

- `_date` — calendar date (no time component).
- `_datetime` — timestamp; stored UTC.
- `_amount` — monetary amount; must be paired with a sibling `*_currency_code` field unless `customProperties.amountCurrencyExempt: true` (validator C1.1).
- `_count` — integer counts.
- `_indicator` — `BOOLEAN`. Distinguish business-meaning indicators (`catastrophe_indicator`, `litigation_indicator`) from null-presence indicators (`null-semantics.md` addendum).

Do **not** use `*_id` for identifiers. The `*_id` form is a dead-letter per `identifier-strategy.md` C2 reconciliation. Avoid abbreviations unless they are widely understood in insurance or finance.

## ODCS Authoring Checklist

Each contract should include:

- `apiVersion`, `kind`, stable `id`, singular `name`, semantic `version`, lifecycle `status`.
- Original business description and business domain.
- Schema entries with field names, business names, logical types, required flags, descriptions.
- Primary keys: `*_uid` GUID PK plus the SCD2 composite component (`valid_from_datetime`) on entity and codeset contracts (per `scd2-primary-key.md`).
- Per-property `customProperties.classifications` block with `sensitivity` (`PUBLIC` / `INTERNAL` / `CONFIDENTIAL` / `RESTRICTED`) and `regulatoryTags` (`PII` / `PHI` / `FINANCIAL`) where applicable.
- Top-level `customProperties.classificationProfile` matching the maximum field-level sensitivity (validator C1.9).
- Relationships block with `targetContractId`, `sourceFields`, `targetFields` for every FK and every `*_code` codeset binding (validator C1.2 / C1.3).
- Data quality rules; at minimum, error-severity rules for must-be-true invariants (PK required, status required, SCD2 window consistent, single current row per key).
- `customProperties.adrs: [...]` listing the ADRs that govern the contract's shape. Every id must resolve to a file under `references/design-decisions/pc/` (validator C1.12).
- `customProperties.changelog` with a new entry naming the version and the change for every version bump (validator C1.11).

Use these defaults for new contracts:

- `apiVersion: v3.0.2`
- `kind: DataContract`
- `version: 0.1.0` for first drafts
- `status: draft` for new contracts (promoted to `proposed` / `approved` later via PR per `status-promotion.md`)
- `domain: property-and-casualty` for P&C contracts
- `canonicalLayer: silver`
- `contractFamily: property-and-casualty`
- `subjectArea` set to one of: `core`, `policy`, `coverage`, `product`, `exposure`, `submission`, `claims`, `financial`. Codesets always materialize to `silver_reference_data` regardless of `subjectArea`.

Use `references/odcs/templates/pc-contract-template.odcs.yaml` as the starting point.

## Versioning And Status

Use semantic versioning per `references/design-decisions/pc/versioning-policy.md`. Below `1.0.0` the contract is pre-stable; breaking changes are permitted between `0.x` minor versions but must still be recorded in the changelog. Above `1.0.0`, breaking changes require a deprecation cycle.

- `PATCH` (`x.y.Z`) — no schema impact: description / businessName fixes, status-only promotions, ADR-only edits.
- `MINOR` (`x.Y.0`) — additive: optional field, quality rule, relationship, widened codeset.
- `MAJOR` (`X.0.0`) — breaking: drop / rename field, tighten type, optional → required, narrow codeset.

The `versioning-policy.md` ADR also governs the manifest version surface (`*.fabric.yaml` `manifestVersion`), the Fabric artifact regeneration cadence, and consumer-side pinning patterns (M10.5 extension).

Allowed statuses (per `status-promotion.md`; `review` was dropped from the validator allowlist in C2):

- `draft`
- `proposed`
- `approved`
- `deprecated`
- `retired`

Promotion is gated; the status field is not advanced ad hoc. The validator enforces YAML-checkable gates on every `approved`, `deprecated`, or `retired` contract — non-empty changelog, `targetContractId` resolution, codeset binding on every `*_code`, error-severity quality rules. Process-enforced gates (steward sign-off, known consumers, codesets at least `proposed`) are confirmed by a human reviewer at promotion time. See `docs/review-checklist.md` §4 for the gate-by-gate review path.

## Target Guidance

Keep target work separate from canonical contracts.

The first and only shipped target is **Microsoft Fabric Lakehouse** (Milestone 9, complete) under `targets/fabric/`. The Fabric projection is **metadata-driven**: the canonical ODCS contract is the only insurance-aware artifact, the generated `*.fabric.yaml` manifest is the only platform-aware artifact, and DDL / Purview JSON / notebook templates are derived from the manifest. No bespoke per-contract code; no hand-authored manifests.

Generators (run from the repository root):

- `scripts/generation/generate-fabric.py` — orchestrator that runs the four sub-generators in dependency order and ends with a manifest drift validator.
- `scripts/generation/generate-fabric-manifests.py` — ODCS → `*.fabric.yaml` manifests.
- `scripts/generation/generate-fabric-purview.py` — manifests + glossary → `purview/sensitivity-labels.json` + `purview/business-glossary.json`.
- `scripts/generation/generate-fabric-ddl.py` — manifests → Spark SQL `CREATE TABLE IF NOT EXISTS` per contract.
- `scripts/generation/generate-fabric-notebooks.py` — three parameterized notebook templates (SCD2 / append / codeset) plus the lakehouse-binding template.

Validators:

- `scripts/validation/validate-contracts.py` — strengthened canonical validator (12 C1 rules + the original W005 / W019 rule set).
- `scripts/validation/validate-fabric-manifests.py --require-full-coverage` — Fabric manifest drift validator (17 checks per `targets/fabric/manifest-schema.md` §9).

Other deferred / out-of-scope targets (Databricks, Snowflake, Kafka, API, semantic projection) are not on the active path. dbt was retired (W022). Bronze ingestion and Gold aggregates are owned upstream / downstream of Silver and not generated by this repository.

Target files must not change canonical business meaning. If a target needs context the canonical contract does not provide, the gap is recorded as an open question in the relevant plan, never silently encoded into a manifest or notebook.

## Contribution Workflow

When adding or changing contracts:

1. Read `docs/contract-inventory.md` to find what exists; read the relevant README files and the cross-cutting ADRs in `references/design-decisions/pc/` (especially `identifier-strategy.md`, `temporal-modeling.md`, `record-state.md`, `event-and-transaction.md`, `codeset-strategy.md`, `data-classification.md`, `currency-convention.md`, `null-semantics.md`, `versioning-policy.md`, `status-promotion.md`, `canonical-alignment.md`).
2. Inspect nearby contracts for local conventions; the C3–C7 hardening waves established the current shape.
3. Check applicable patterns under `references/patterns/` and design decisions under `references/design-decisions/`. If a deliberate departure or deferral might apply, check `canonical-alignment.md` first.
4. Make the smallest coherent contract change.
5. Add or update design rationale when the model boundary matters. When a new ADR is introduced, follow the primacy order: ADR first, then pattern / glossary, then contracts, then validator (per `authoring-source-primacy.md`).
6. Add or update glossary terms when terminology would otherwise be ambiguous.
7. Update `customProperties.adrs: [...]` to name the ADRs that govern the contract's shape; the validator's C1.12 rule confirms each id resolves.
8. Bump version per `versioning-policy.md` and append a `customProperties.changelog` entry naming the new version and the specific change.
9. Keep private research and external provenance out of committed files.
10. Validate before finishing:
    ```
    python3 scripts/validation/validate-contracts.py
    python3 scripts/generation/generate-fabric.py        # if canonical change touches schema
    python3 scripts/generation/generate-contract-inventory.py
    python3 scripts/generation/generate-changelog.py
    ```
    A green canonical validator + green Fabric orchestrator run is the bar before opening a PR.
11. Walk through `docs/review-checklist.md` before opening or reviewing the PR. The checklist is structured by contract kind (entity / event / transaction / codeset) and covers validator gates, human-judgment gates, status-promotion review, and the Fabric impact a canonical change produces.
12. Summarize changes by business behavior, not by source inspiration.
