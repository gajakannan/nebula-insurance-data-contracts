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

The repo already has the right shape:

- `references/odcs/` for canonical contracts.
- `references/patterns/` for reusable modeling patterns.
- `references/design-decisions/` for rationale.
- `references/glossary/` for canonical terms.
- `targets/` for target-specific implementation guidance.
- `scripts/` for validation, generation, linting, and inspection.
- `docs/` for authoring guidance, roadmap, examples, and usage docs.

The main gap is implementation depth. Most contract files are placeholders, scripts are empty, target folders are empty, and glossary content has not started.

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

Goal: represent claim intake, lifecycle, coverage association, parties, documents, and claim activity.

Contracts:

- `Claim`
- `ClaimEvent`
- `ClaimCoverage`
- `ClaimPartyRole`
- `ClaimDocument`

Key decisions:

- Claim is tied to loss and policy context where available.
- Claim lifecycle events preserve operational history.
- Claim party roles should follow the party-role pattern.
- Claim coverage should connect claim handling to policy coverage and exposure where known.

Deliverables:

- Complete ODCS contracts.
- Claim lifecycle pattern if needed.
- Claim glossary terms.

Acceptance criteria:

- Loss notice, claim open, assignment, reserve change, payment, recovery, litigation, close, and reopen can be represented.
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

## Milestone 9: Target Implementation Guidance

Goal: make contracts usable across platforms without changing canonical meaning.

Target areas:

- Fabric
- Databricks
- Snowflake
- dbt
- Kafka
- API
- Semantic

Tasks:

- Define logical-to-target type mappings.
- Define naming conventions.
- Define table/view generation rules.
- Define dbt model conventions.
- Define Kafka and API schema projection rules.
- Define semantic projection rules.

Acceptance criteria:

- Target guidance adapts mechanics only.
- Canonical field meaning, relationships, lifecycle semantics, and quality rules stay unchanged.
- At least one target has a worked example generated from a completed contract.

## Milestone 10: Examples, Docs, And Release Governance

Goal: make the library usable and governable.

Tasks:

- Add example walkthroughs.
- Add contract inventory documentation.
- Add changelog or release notes.
- Define review checklist.
- Define versioning and compatibility rules.
- Mark mature contracts as `review` or `approved`.

Acceptance criteria:

- A new contributor can author a contract using docs and templates.
- A reviewer can verify structure, naming, relationships, quality rules, and provenance boundaries.
- Users can understand which contracts are stable enough to implement.

## First Execution Order

1. Add ODCS template and validation script.
2. Complete `Party`.
3. Complete `PartyRole` and `PartyRelationship`.
4. Complete `Policy`.
5. Complete `Coverage` and `PolicyCoverage`.
6. Complete `Exposure`.
7. Complete `Claim`.
8. Complete `FinancialTransaction`.
9. Fill in dependent contracts around the first milestone spine.
10. Add target and semantic projections after the canonical spine passes validation.

## Definition Of Done For First Usable Release

- All first milestone contracts are complete ODCS YAML.
- All first milestone contracts pass validation.
- Each contract has primary keys, required fields, descriptions, relationships, quality rules, and custom properties.
- Glossary contains first milestone terms.
- Design decisions explain significant boundaries.
- At least one target guidance path is documented.
- Semantic projection approach is documented.
- No tracked file leaks private source names, URLs, copied definitions, raw schemas, raw ontology exports, or source review notes.
