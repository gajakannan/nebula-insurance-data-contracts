# Status

Last updated: 2026-05-04

## Current Goal

Complete the repository intent: a platform-neutral canonical insurance data contract library, authored in ODCS v3 YAML, with Property and Casualty as the first domain package.

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
- The tracked P&C ODCS contract files pass current repository validation, and authored relationship targets resolve to tracked contracts.
- Validation tooling exists; generation and target implementation folders still need content.
- Target folders exist but do not yet contain target guidance.
- Submission and reference-data ODCS folders now contain starter contract sets.
- Glossary folders exist but do not yet contain canonical terms.
- The policy placeholder path has been moved from the core area to the policy area.

## Active Work Items

| ID | Work Item | Status | Notes |
| --- | --- | --- | --- |
| W001 | Fix policy placeholder path mismatch | Done | `Policy` now lives under `references/odcs/pc/policy/`. |
| W002 | Add planning tracker | Done | This file tracks execution status. |
| W003 | Add implementation plan | Done | See `planning-mds/IMPLEMENTATION_PLAN.md`. |
| W004 | Create ODCS authoring template | Done | Template lives at `references/odcs/templates/pc-contract-template.odcs.yaml`. |
| W005 | Add contract validation tooling | Done | `scripts/validation/validate-contracts.py` validates YAML shape, required metadata, naming, primary keys, descriptions, custom properties, and source-neutrality guardrails. |
| W006 | Author first milestone contracts | Done | `Party`, `PartyRole`, `PartyRelationship`, `Policy`, `Coverage`, `PolicyCoverage`, `Exposure`, exposure subtypes, `Claim`, and `FinancialTransaction` are complete and pass validation. |
| W007 | Add glossary starter set | Not started | Canonical terms only, written in original language. |
| W008 | Add target type mapping guidance | Not started | Start with Fabric and dbt after canonical contracts stabilize. |
| W009 | Define semantic and ontology projection approach | Not started | Treat ontology as derived semantic view, not as the canonical source of truth. |
| W010 | Add missing `Coverage` placeholder | Done | Roadmap and first milestone now align to `references/odcs/pc/coverage/coverage.odcs.yaml`. |
| W011 | Add missing referenced and dependent contracts | Done | Reference data plus `PolicyTerm`, `Product`, `PolicyLimit`, `PolicyDeductible`, `InsurableObject`, and `InsurableObjectClassification` are complete and pass validation. |
| W012 | Add submission contract set | Done | `Submission`, `SubmissionPartyRole`, `SubmissionRisk`, `SubmissionAssessment`, `SubmissionDocument`, and `SubmissionLifecycleEvent` are complete and pass validation. |

## Next Recommended Step

Add the glossary starter set next, using canonical terms from the completed contracts. After glossary terms are in place, continue with remaining backlog contracts such as account, agreement, policy lifecycle detail, claim event detail, and financial transaction classification.
