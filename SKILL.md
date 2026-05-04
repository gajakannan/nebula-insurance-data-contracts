---
name: nebula-insurance-data-contracts
description: "Work on Nebula's platform-neutral canonical insurance data contracts. Use when designing, editing, validating, documenting, or generating ODCS v3 YAML contracts, modeling patterns, design decisions, glossary terms, or target-specific implementation guidance for this repository."
compatibility: ["manual-orchestration-contract"]
metadata:
  allowed-tools: "Read Write Edit Bash(git:*) Bash(rg:*) Bash(find:*) Bash(sed:*) Bash(python3:*)"
  version: "0.1.0"
  author: "Nebula Framework Team"
  tags: ["insurance", "data-contracts", "odcs", "canonical-modeling"]
  last_updated: "2026-05-04"
---

# Nebula Insurance Data Contracts

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

Use this initial modeling spine unless the user explicitly asks for a different scope:

- Core: `Party`, `PartyRole`, `PartyRelationship`, `Account`, `Agreement`
- Submission: `Submission`, `SubmissionPartyRole`, `SubmissionRisk`, `SubmissionAssessment`, `SubmissionDocument`, `SubmissionLifecycleEvent`
- Policy: `Policy`, `PolicyTerm`, `PolicyPartyRole`, `PolicyLifecycleEvent`, `PolicyTransaction`, `PolicyDocument`
- Coverage: `Product`, `Coverage`, `PolicyCoverage`, `PolicyLimit`, `PolicyDeductible`
- Exposure: `InsurableObject`, `InsurableObjectClassification`, `Exposure`, `VehicleExposure`, `PropertyExposure`, `WorkersCompExposure`
- Claims: `Claim`, `ClaimEvent`, `ClaimCoverage`, `ClaimPartyRole`, `ClaimDocument`
- Financial: `FinancialTransaction`, `PolicyFinancialTransaction`, `ClaimFinancialTransaction`, `FinancialTransactionClassification`
- Reference data: `GeographicLocation`, `LocationAddress`, `LineOfBusiness`, `TransactionType`, `LifecycleStatus`, `LifecycleEventType`
- Assessment: `Assessment`, `RiskAssessment`, `UnderwritingAssessment`

Add new P&C contracts under the closest folder in `references/odcs/pc/`. Create a new folder only when the concept does not fit the existing domain areas.

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

Use lowercase snake_case for physical field names:

- `_id` for identifiers.
- `_code` for coded values.
- `_date` for dates.
- `_datetime` or `_timestamp` only when time precision matters.
- `_amount` for monetary amounts.
- `_count` for counts.
- `_indicator` for yes/no or true/false business indicators.

Avoid abbreviations unless they are widely understood in insurance or finance.

## ODCS Authoring Checklist

Each contract should include:

- `apiVersion`
- `kind`
- Stable `id`
- Singular `name`
- Semantic `version`
- Lifecycle `status`
- Original business description
- Business domain
- Schema entries
- Field names, business names, logical types, required flags, and descriptions
- Primary keys where applicable
- Relationships where applicable
- Data quality rules where meaningful
- Ownership or support metadata when known
- Custom properties for canonical layer and contract family

Use these defaults unless repository conventions later replace them:

- `apiVersion: v3.0.2`
- `kind: DataContract`
- `version: 0.1.0` for first drafts
- `status: draft` for new contracts
- `domain: property-and-casualty` for P&C contracts
- `canonicalLayer: silver`
- `contractFamily: property-and-casualty`

## Versioning And Status

Use semantic versioning where practical:

- `PATCH` for documentation, metadata, or non-breaking clarification.
- `MINOR` for additive, backward-compatible fields or rules.
- `MAJOR` for breaking schema, meaning, or compatibility changes.

Use these statuses:

- `draft`
- `review`
- `approved`
- `deprecated`
- `retired`

## Target Guidance

Keep target work separate from canonical contracts.

When the user requests a platform implementation, place guidance or generated artifacts under the relevant target folder:

- `targets/fabric/`
- `targets/databricks/`
- `targets/snowflake/`
- `targets/dbt/`
- `targets/kafka/`
- `targets/api/`

Target files may define type mappings, naming conventions, deployment patterns, table or view generation, model generation, topic or schema generation, API schema generation, and semantic model guidance.

Target files must not change canonical business meaning.

## Contribution Workflow

When adding or changing contracts:

1. Read the relevant README files.
2. Inspect nearby contracts for local conventions.
3. Check applicable patterns and design decisions.
4. Make the smallest coherent contract change.
5. Add or update design rationale when the model boundary matters.
6. Add or update glossary terms when terminology would otherwise be ambiguous.
7. Keep private research and external provenance out of committed files.
8. Validate ODCS files before finishing when validation tooling exists.
9. Summarize changes by business behavior, not by source inspiration.

If validation tooling does not exist yet, do a manual structural review and state that automated validation was unavailable.
