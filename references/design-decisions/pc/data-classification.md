# Data Classification (PII, PHI, Sensitivity)

## Decision

Every field on a canonical contract carries an explicit data classification. Classification is captured at the field level via `customProperties.classifications` on each property and at the contract level via `customProperties.classificationProfile` summarizing the most-sensitive class present.

Classification dimensions:

- **Sensitivity tier**: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`.
- **Regulatory tags**: zero or more of `PII`, `PHI`, `PCI`, `SPI`, `FINANCIAL`, `JURISDICTION_RESTRICTED`.
- **Retention class** (optional): a code referencing the retention codeset where retention is governed.

## Rationale

Targets need to enforce governance — column masking, row-level security, lineage tagging, retention enforcement. Both dbt (column-level meta tags, exposures) and Microsoft Fabric / Purview (sensitivity labels, classification scans) consume field-level classification. If the canonical contract does not carry it, every target re-derives it inconsistently or skips it.

Classifying at the canonical layer makes the contract the single source of truth and makes target generation deterministic.

## Consequences

- Every property in every contract gets `customProperties.classifications` with at least a `sensitivity` tier. Where the field is non-sensitive, `sensitivity: PUBLIC` is set explicitly — silence is not classification.
- Regulatory tags are additive. A `social_security_number` is `RESTRICTED` + `PII` + `SPI`. A `diagnosis_code` is `RESTRICTED` + `PHI`. A `policy_number` is `INTERNAL` (typically not PII on its own, but treated as internal because it identifies a business relationship).
- The validator checks that every property carries a `sensitivity` value and rejects contracts with unclassified fields.
- Contract-level `classificationProfile` is the maximum sensitivity tier present, used by target generators to set the default sensitivity label on the materialized table.
- HIPAA-relevant contracts (anything carrying `PHI`) declare `customProperties.subjectToHipaa: true` at the contract level so downstream targets can branch their generation logic.

## Guidance

- Use `RESTRICTED` for any field that, if disclosed, would create regulatory or legal exposure. Use `CONFIDENTIAL` for commercial sensitivity (rates, reserves, underwriting comments).
- Free-text narrative fields default to `CONFIDENTIAL` and `PII` because they routinely contain identifiers that the schema does not enforce.
- Classifications evolve. Tightening a classification (e.g. INTERNAL → CONFIDENTIAL) is a non-breaking metadata change. Loosening one (e.g. RESTRICTED → CONFIDENTIAL) is a governance decision and must be reviewed by the data steward, even though it does not break a schema consumer.

## Related

- `references/design-decisions/pc/codeset-strategy.md`
- `references/design-decisions/pc/versioning-policy.md`
