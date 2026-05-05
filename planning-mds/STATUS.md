# Status

Last updated: 2026-05-05

## Current Goal

Lock the canonical P&C ODCS contract set against a complete, governed set of cross-cutting design decisions, then move to target implementation guidance.

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
- Cross-cutting design decisions are now complete and indexed in `references/design-decisions/README.md` (identifier strategy, bi-temporal modeling, record state, codeset strategy, separation-and-nesting, currency, null semantics, data classification, versioning, status promotion, claims modeling, product-coverage M:N, risk-transfer scope, event-and-transaction).
- The tracked P&C ODCS contract files pass current repository validation.
- Validation tooling exists; a refresh is required to enforce the new conventions (W014).
- All entity contracts will be refactored to align with the new ADRs (W015).
- Target folders exist but do not yet contain target guidance.
- Glossary starter terms exist for the completed Property and Casualty contract areas.

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
| W008 | Add target type mapping guidance | Not started | Start with dbt and Microsoft Fabric after canonical contracts stabilize against the new ADRs. |
| W009 | Define semantic and ontology projection approach | Not started | Treat ontology as derived semantic view, not as the canonical source of truth. |
| W010 | Add missing `Coverage` placeholder | Done | Roadmap and first milestone now align to `references/odcs/pc/coverage/coverage.odcs.yaml`. |
| W011 | Add missing referenced and dependent contracts | Done | Reference data plus `PolicyTerm`, `Product`, `PolicyLimit`, `PolicyDeductible`, `InsurableObject`, and `InsurableObjectClassification` are complete and pass validation. |
| W012 | Add submission contract set | Done | `Submission`, `SubmissionPartyRole`, `SubmissionRisk`, `SubmissionAssessment`, `SubmissionDocument`, and `SubmissionLifecycleEvent` are complete and pass validation. |
| W013 | Add policy lifecycle detail contracts | Done | `PolicyPartyRole`, `PolicyLifecycleEvent`, `PolicyTransaction`, and `PolicyDocument` are complete and pass validation. |
| W014 | Author cross-cutting design decisions | Done | Fourteen ADRs added/refined under `references/design-decisions/pc/` and indexed in the design-decisions README. |
| W015 | Bulk YAML refactor to align with new ADRs | In progress | Add `*_uid` GUIDs, retain business keys, add SCD2 fields, add `record_status_code`, add classifications, and audit currency pairing across all entity contracts. |
| W016 | Add `ProductCoverage` M:N junction contract | Not started | Per `product-coverage-modeling.md`. |
| W017 | Add missing codeset contracts | Not started | Add codeset contracts for every `*_code` field referenced from entity contracts (PolicyStatusCode, PolicyTypeCode, CoverageBasisCode, CoverageLevelCode, CoverageStatusCode, TermStatusCode, RecordStatusCode, PartyTypeCode, PartyRoleTypeCode, ClaimStatusCode, CauseOfLossCode, JurisdictionCode, CurrencyCode, and any others uncovered during refactor). |
| W018 | Fill in claims contract set | Not started | `ClaimPartyRole`, `ClaimLifecycleEvent`, `ClaimFeature`, `ClaimCoverage`, `ClaimDocument`, `ClaimFinancialTransaction` per `claims-modeling.md`. |
| W019 | Update validator to enforce new conventions | Not started | Validator must check `*_uid` PK, SCD2 fields, `record_status_code`, classifications presence, codeset references for `*_code` fields, and SemVer well-formedness. |
| W020 | Update authoring guide and patterns to reference new ADRs | Not started | Cross-link `docs/authoring-guide.md` and `references/patterns/pc/*` to the new ADRs. |
| W021 | Risk-transfer contract family (deferred scope) | Deferred | Reinsurance, coinsurance, self-insurance, and fronting are deferred per `risk-transfer-scope.md`. Tracked here so the deferral does not get lost. |
| W022 | Author target guidance for dbt | Not started | First target. Generate dbt sources, staging models, snapshots, and column-level meta from the canonical contracts. |
| W023 | Author target guidance for Microsoft Fabric | Not started | Second target. Generate Lakehouse Delta tables with SCD2, Purview sensitivity labels from classifications, and column-level masking where required. |

## Next Recommended Step

Complete W015 (bulk YAML refactor) and W016–W018 (new contracts) so that the canonical surface matches the ADRs. Then refresh the validator (W019) and confirm all contracts pass. Targets (W022, W023) follow once the canonical surface is locked.
