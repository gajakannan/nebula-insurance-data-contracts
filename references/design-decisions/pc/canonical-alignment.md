# Canonical Alignment — Deliberate Departures and Deferrals

## Decision

The canonical P&C contract surface is **source-informed but not source-derived**, and it intentionally departs from several modeling defaults that a textbook-correct or vendor-aligned model might apply. This ADR is the single place a reviewer can look to find every deliberate departure from the recommended modeling defaults, plus every concept that has been deliberately deferred from the current canonical surface.

It complements the cross-cutting ADRs (each of which states the rule for one convention) by explaining where the canonical surface intentionally diverges from those defaults — and why. When a contract carries `customProperties.adrs: [..., canonical-alignment, ...]`, a reviewer can read this ADR to understand which deliberate choice is at play.

This ADR does not replace per-decision ADRs. Each departure cross-references the ADR that owns the rule, and each deferral cross-references the ADR that documents the deferred concept where one exists.

## Rationale

Without a single alignment register, deliberate departures look indistinguishable from oversights. New contributors do not know whether `Account` is missing because the modeling team forgot it or because it was deliberately deferred and then reversed; they do not know whether `_uid` is a casual choice or a documented one; they do not know whether the assessment family is intentionally narrow or accidentally narrow. Inevitably someone re-litigates a closed decision, or worse, "fixes" a deliberate departure as if it were a bug.

Maintaining one alignment register makes the canonical layer navigable for new contributors without prior context. It also makes governance reviews tractable: the reviewer scans this ADR plus the per-contract `customProperties.adrs` back-links and immediately knows where to focus.

## Deliberate departures from recommended defaults

### Identifier and key conventions

- **`*_uid` rather than `*_identifier`.** The canonical layer uses the compact `*_uid` suffix on every system-generated GUID identity column. A textbook-correct convention might be `*_identifier`. The compact form was chosen for column-name density at the silver layer where these columns appear in every join and projection. Documented in `identifier-strategy.md`.
- **Composite SCD2 primary key `(*_uid, valid_from_datetime)` rather than dual identity.** A dual-identity model would split the `*_uid` business identity from a separate `*_version_uid` per row version. The composite key keeps both faces of the row in one column pair and avoids a second GUID per record version. Documented in `scd2-primary-key.md`. Re-evaluation is open if a downstream target (Fabric, future targets, MDM) prefers dual-identity.
- **`_id` is reserved.** The validator rejects new non-PK `_id` fields. The historical `_id` column appears only on a small set of legacy migrated fields and is not a canonical pattern.

### Entity boundaries

- **Submission as a first-class entity, not an "incomplete policy".** A vendor-aligned model often treats submission state as a partial policy row that promotes to a full policy on bind. The canonical layer keeps submission and policy as separate contracts because their lifecycles, party participation, and data quality concerns differ in ways that a single contract cannot represent cleanly. Documented in `submission-modeling.md`.
- **`PolicyFinancialTransaction` and `ClaimFinancialTransaction` rather than a single polymorphic `FinancialTransaction`.** A pure transaction-pattern model emits one polymorphic transaction contract. The canonical layer keeps `FinancialTransaction` as the abstract pattern but ships `PolicyFinancialTransaction` and `ClaimFinancialTransaction` because the policy-side and claim-side lifecycles have enough independent structure to warrant separate contracts. The shared classification taxonomy lives in `pc.financial-transaction-classification`. Documented in `financial-modeling.md`; landed in canonical hardening C4.6.
- **Exposure subtype contracts (`vehicle-exposure`, `property-exposure`, `workers-comp-exposure`) rather than a single polymorphic `Exposure`.** A purely abstract model would carry `Exposure` plus an `exposure_type_code` and a polymorphic key. The canonical layer keeps `Exposure` as the abstract spine but also ships subtype contracts because the line-of-business-specific fields (VIN, building value, payroll) are too distinct to share one schema. Documented in `exposure-modeling.md`.
- **Generic `PartyRole` is not shipped.** The polymorphic `context_type_code + context_uid` shape that a generic role contract would require cannot be validated by ODCS, and every shipped use case maps to one of the five context-specific role contracts (`SubmissionPartyRole`, `PolicyPartyRole`, `ClaimPartyRole`, `InsurableObjectPartyRole`, `AccountPartyRole`). Documented in `role-modeling.md` and `references/patterns/pc/party-role-pattern.md`.
- **`Account`, `AccountRelationship`, `AccountPartyRole`, `Agreement` shipped (commercial-lines reversal).** The original C4.5 default was to amend — defer the account/agreement layer until commercial-line scope expanded. The reversal landed during canonical hardening C4 because the user-driven scope expansion brought commercial-lines into the first wave. Documented in `entity-boundaries.md` and `references/patterns/pc/account-pattern.md`.
- **Coverage Group rendered as a codeset rather than a separate hierarchy entity.** The vendor-style model would carry a `CoverageGroup` entity with parent/child links to `Coverage`. The canonical layer treats coverage grouping as a classification on `Coverage` and `PolicyCoverage` because the grouping is presentation-oriented and does not carry independent lifecycle. Re-evaluate if a use case bites that needs the group as a first-class entity.
- **Policy Amount rendered as a transaction-classification rather than a separate `Amount` entity.** The vendor-style model would carry an `Amount` entity that joins to the policy. The canonical layer carries amount semantics on `PolicyFinancialTransaction` rows classified by `pc.financial-transaction-classification`. The transaction-oriented model gives consumers a queryable money-flow without an extra join.
- **`InsurableObjectClassification` lives under `exposure/`, not its own subject area.** The contract is a classification of insurable objects rather than a separate spine entity, so it shares the exposure subject area.
- **`LocationAddress` and `GeographicLocation` live under `reference-data/`, not their own subject area.** These are governed reference-data entities rather than subject-area spine entities. Both follow the reference-data-entity shape (richer than a pure codeset) per `codeset-strategy.md`'s C5.3 addendum.

### Codeset and reference-data conventions

- **Two reference-data shapes are recognized: pure codeset and reference-data entity.** Pure codesets carry the standard codeset shape (`*_code_uid`, `code_value`, `code_label`, `code_description`, external-standard mappings, SCD2, `record_status_code`) at `classificationProfile: PUBLIC`. Reference-data entities carry the codeset identity columns plus richer business attributes (subject classification, parent/child hierarchy, regulatory mappings) at `classificationProfile: INTERNAL`. The validator's C1.2 codeset-binding rule treats both shapes as valid codeset targets. Documented in `codeset-strategy.md` (C5.3 addendum).
- **`record-status-code` self-reference is intentional.** The codeset carries a `record_status_code` field that references the same codeset; it bootstraps with `ACTIVE` and uses its own values for subsequent supersession marks. Documented in `codeset-strategy.md` (C5.8 addendum).
- **Some `*_code` fields are deliberately exempted from canonical codeset binding.** Carrier-product taxonomies (e.g. `vehicle_use_code`, `coverage_type_code`, `product_type_code`), industry-library codes (e.g. `construction_type_code`, `form_code`), carrier-internal identifiers (e.g. `accounting_period_code`, `company_catastrophe_code`), and two-value enumerations (e.g. `debit_credit_code`) carry `customProperties.codesetExempt: true` plus `codesetExemptReason: ...` rather than a canonical codeset binding. The full list is in `scripts/refactor/apply-hardening-c5.py` (`EXEMPT_FIELDS`).

### Field-shape conventions

- **No house currency.** Every `*_amount` is paired with a sibling `*_currency_code`. The canonical layer does not pre-convert to a single house currency. Documented in `currency-convention.md`.
- **`source_natural_key` carries primary source key only.** Multi-source provenance is treated as an MDM concern outside the canonical layer; the slot is a single string. To be revisited in canonical hardening C7 if a use case bites that needs the multi-source shape.
- **Universal business-window convention.** Business-effective windows on entity contracts use `effective_*` / `expiration_*` field pairs; system-time windows use `valid_from_datetime` / `valid_to_datetime`. The two are deliberately not collapsed. Documented in `temporal-modeling.md`.

### Assessment scope

- **Only `submission-assessment` ships in the assessment family.** The full assessment subtype hierarchy (underwriting assessment, risk assessment, claim assessment, audit assessment) is deferred. The submission-side assessment is the only one that bites in the first wave; the rest are deferred to a future milestone rather than authored speculatively.

## Deferrals (out of scope for the current canonical surface)

- **Risk-transfer family.** Reinsurance, coinsurance, fronting, self-insurance, retention structures. Recognized canonical concepts; deferred from the first wave. Documented in `risk-transfer-scope.md`. Recoveries that flow through carrier financials can be represented as `FinancialTransaction` rows with appropriate transaction-type classifications until the structural risk-transfer family is added.
- **Litigation and arbitration as first-class entities.** Currently modeled as a `litigation_indicator: boolean` on `Claim`. Acceptable for the first wave; promotion to first-class `Litigation` / `Arbitration` entities is a future milestone.
- **Full assessment subtype hierarchy.** `submission-assessment` is the only assessment contract; `underwriting-assessment`, `risk-assessment`, and the remainder of the assessment family are deferred.
- **Semantic projection (RDF / OWL / SKOS / knowledge graph).** Tracked in the planning STATUS doc as W009; deferred until a downstream consumer pulls.
- **Additional targets beyond Microsoft Fabric.** Databricks, Snowflake, dbt, Kafka, and API targets are reserved as future scope; only Fabric is in scope for the current implementation milestone.
- **Bronze / ingestion / connector concerns.** This repository defines the silver canonical contract layer. Bronze landing schemas, source connectors, and streaming ingestion are outside the scope of this layer.
- **Streaming ingestion.** Out of scope.
- **Generic `PartyRole`.** Documented above as a deliberate departure rather than a deferral; the polymorphic shape is not a future plan.

## Consequences

- A new contributor who reads this ADR has a single, exhaustive register of deliberate departures and deferrals. They can identify whether a perceived gap is intentional, scoped for a future milestone, or a real bug.
- A reviewer reading a contract that carries `canonical-alignment` in its `customProperties.adrs` knows the contract is part of a surface whose deliberate departures are documented; the reviewer reaches for this ADR rather than re-deriving the rationale.
- This ADR is the right place to update when a deliberate departure is reversed (as the C4.5 commercial-lines reversal of `Account` / `Agreement` was) or when a deferral is brought into scope. Both events should also update the planning STATUS doc.
- This ADR is **not** the right place to record the rule for a single convention. Per-convention ADRs (identifier-strategy, temporal-modeling, codeset-strategy, etc.) own the rule statements; this ADR cross-references them.

## Guidance

- When you author or change a contract that participates in a deliberate departure listed above, add the relevant per-convention ADR plus `canonical-alignment` to `customProperties.adrs`. The validator's C1.12 rule confirms each id resolves.
- When you propose a new departure or a new deferral, raise it in the planning STATUS doc, add an entry here, and cross-reference the per-convention ADR that owns the rule.
- When you reverse a departure or bring a deferral into scope, update both this ADR and the per-convention ADR. Note the reversal in the contract's changelog with a specific reference to the ADR(s) that drove the change.

## Related

- `references/design-decisions/pc/authoring-source-primacy.md` — which artifact to update first when something changes.
- `references/design-decisions/README.md` — full ADR index.
- `references/patterns/README.md` — full pattern index.
- `planning-mds/STATUS.md` — deferral and scope-expansion tracking.
- `planning-mds/CANONICAL_HARDENING_PLAN.md` — the milestone plan that landed the canonical surface in its current shape.
