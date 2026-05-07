# Design Decisions

Records of canonical modeling choices. Each decision states the position, the rationale, the consequences for contract authors, and pointers to related decisions and patterns.

## Property and Casualty

### Modeling structure

- `pc/entity-boundaries.md` — when a concept earns a contract vs. an attribute or classification.
- `pc/separation-and-nesting.md` — when a concept becomes its own contract vs. nested attributes on a parent.
- `pc/role-modeling.md` — Party identity vs. contextual role participation.
- `pc/submission-modeling.md` — submissions as first-class, not incomplete policies.
- `pc/policy-lifecycle-modeling.md` — explicit lifecycle vs. overwriting policy history.
- `pc/exposure-modeling.md` — exposure as a first-class concept in the spine.
- `pc/financial-modeling.md` — transaction-oriented financial activity.
- `pc/product-coverage-modeling.md` — Product and Coverage as many-to-many via `ProductCoverage`.
- `pc/claims-modeling.md` — claim contract symmetry with policy and submission.
- `pc/risk-transfer-scope.md` — reinsurance, coinsurance, self-insurance, fronting deferred (with rationale).

### Identity, time, and record state

- `pc/identifier-strategy.md` — `*_uid` GUID identity column plus a business-friendly key.
- `pc/temporal-modeling.md` — bi-temporal model with SCD2 system-time fields.
- `pc/scd2-primary-key.md` — composite logical PK `(*_uid, valid_from_datetime)` for SCD2 contracts.
- `pc/record-state.md` — record-level status (soft delete, supersession, merge).
- `pc/event-and-transaction.md` — lifecycle events and transactions are complementary, with linkage rules.

### Field-level conventions

- `pc/null-semantics.md` — what null means and when to use codeset sentinels instead.
- `pc/codeset-strategy.md` — every `*_code` references a governed codeset contract.
- `pc/currency-convention.md` — monetary amount paired with transactional currency code; no house currency.
- `pc/data-classification.md` — field-level sensitivity, PII, PHI, and other regulatory tags.

### Governance

- `pc/versioning-policy.md` — SemVer with data-contract-specific semantics for MAJOR/MINOR/PATCH.
- `pc/status-promotion.md` — `draft → proposed → approved → deprecated → retired` with explicit gates.
- `pc/canonical-alignment.md` — register of deliberate departures from recommended modeling defaults, plus the list of concepts deliberately deferred from the current canonical surface.
- `pc/authoring-source-primacy.md` — primacy order ADR > pattern > glossary > contract > validator; documents which artifact to update first when something changes.
