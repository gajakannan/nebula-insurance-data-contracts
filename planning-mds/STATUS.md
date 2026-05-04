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
| W004 | Create ODCS authoring template | Done | Template lives at `references/odcs/templates/pc-contract-template.odcs.yaml`. |
| W005 | Add contract validation tooling | Done | `scripts/validation/validate-contracts.py` validates YAML shape, required metadata, naming, primary keys, descriptions, custom properties, and source-neutrality guardrails. |
| W006 | Author first milestone contracts | In progress | `Party`, `PartyRole`, and `PartyRelationship` are complete and pass validation. Policy, Coverage, Exposure, Claim, and FinancialTransaction remain placeholders. |
| W007 | Add glossary starter set | Not started | Canonical terms only, written in original language. |
| W008 | Add target type mapping guidance | Not started | Start with Fabric and dbt after canonical contracts stabilize. |
| W009 | Define semantic and ontology projection approach | Not started | Treat ontology as derived semantic view, not as the canonical source of truth. |
| W010 | Add missing `Coverage` placeholder | Done | Roadmap and first milestone now align to `references/odcs/pc/coverage/coverage.odcs.yaml`. |

## Next Recommended Step

Complete `Policy` next, using the core identity contracts as relationship anchors. The policy contract should pass `python3 scripts/validation/validate-contracts.py references/odcs/pc/policy/policy.odcs.yaml` before broader full-repo validation is expected to pass.
