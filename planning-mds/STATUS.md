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
- First ODCS contract files are placeholders rather than complete ODCS contracts.
- Validation and generation script folders exist but do not yet contain tooling.
- Target folders exist but do not yet contain target guidance.
- Glossary folders exist but do not yet contain canonical terms.
- The policy placeholder path has been moved from the core area to the policy area.

## Active Work Items

| ID | Work Item | Status | Notes |
| --- | --- | --- | --- |
| W001 | Fix policy placeholder path mismatch | Done | `Policy` now lives under `references/odcs/pc/policy/`. |
| W002 | Add planning tracker | Done | This file tracks execution status. |
| W003 | Add implementation plan | Done | See `planning-mds/IMPLEMENTATION_PLAN.md`. |
| W004 | Create ODCS authoring template | Not started | Needed before scaling contract authoring. |
| W005 | Add contract validation tooling | Not started | Validate YAML shape, required metadata, naming, and source-neutrality checks. |
| W006 | Author first milestone contracts | Not started | Party, Policy, Coverage, Exposure, Claim, FinancialTransaction. |
| W007 | Add glossary starter set | Not started | Canonical terms only, written in original language. |
| W008 | Add target type mapping guidance | Not started | Start with Fabric and dbt after canonical contracts stabilize. |
| W009 | Define semantic and ontology projection approach | Not started | Treat ontology as derived semantic view, not as the canonical source of truth. |

## Next Recommended Step

Create the ODCS authoring template and validation checklist, then replace the `Party` placeholder with the first complete contract. `Party` should go first because role, policy, claim, account, and relationship contracts depend on it.
