# Property and Casualty Glossary

Canonical business terms for the Property and Casualty contract package.

These definitions are written as original repository language and are aligned to the ODCS contracts under `references/odcs/pc/` and the design decisions under `references/design-decisions/pc/`. They are extended as contracts move from `draft` to `proposed` or `approved`.

## Term Areas

- [Cross-cutting terms](cross-cutting.md) — identifier strategy, bi-temporal modeling, record state, codesets, classification, currency, versioning, status promotion. These apply across the whole contract set.
- [Core terms](core.md) — Party, PartyRole, PartyRelationship.
- [Submission terms](submission.md) — Submission, SubmissionPartyRole, SubmissionRisk, SubmissionAssessment, SubmissionDocument, SubmissionLifecycleEvent.
- [Policy terms](policy.md) — Policy, PolicyTerm, PolicyPartyRole, PolicyLifecycleEvent, PolicyTransaction, PolicyDocument.
- [Coverage terms](coverage.md) — Product, Coverage, ProductCoverage, PolicyCoverage, PolicyLimit, PolicyDeductible.
- [Exposure terms](exposure.md) — InsurableObject, InsurableObjectClassification, Exposure, specialized exposure subtypes.
- [Claim terms](claims.md) — Claim, ClaimFeature, ClaimLifecycleEvent, ClaimCoverage, ClaimPartyRole, ClaimDocument, ClaimFinancialTransaction.
- [Financial terms](financial.md) — FinancialTransaction patterns, classifications, immutability, currency pairing.
- [Reference data terms](reference-data.md) — codesets and entity-like reference contracts.

## Authoring Rules

- Define canonical business meaning, not source-system meaning.
- Keep definitions concise, singular, and platform-neutral.
- Prefer terms that appear in contract names, field business names, relationship descriptions, quality rules, or design decisions.
- Do not copy external definitions, raw schemas, source field names, source artifact names, URLs, or private review notes.
- Add a term when it clarifies contract meaning, relationship meaning, lifecycle meaning, or coded-value use.
- When a term is shared across the whole contract set, place it in `cross-cutting.md` rather than duplicating it across area files. Area files reference cross-cutting terms by link.
