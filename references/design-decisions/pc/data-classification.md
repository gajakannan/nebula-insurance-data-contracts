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

## Narrative free-text default

Narrative free-text fields — properties whose name ends in `_description`, `_notes`, `_narrative`, `_text`, or `_summary` — default to **`CONFIDENTIAL` plus at least one regulatory tag** (`PII` is the typical default; `PHI` for medical narrative; `FINANCIAL` for financial narrative). Free-text routinely contains identifiers, regulated content, or commercially sensitive information that the schema does not enforce, so the default leans conservative.

Authors who need to opt out of this default classify the field with `customProperties.classifications.narrativeException: true` plus a `narrativeExceptionReason` string explaining why the classification is lower than the default. The validator enforces the default and accepts the exception form.

The default does **not** apply to codeset `code_value`, `code_label`, and `code_description` fields on contracts under `references/odcs/pc/reference-data/`. Codeset reference data is `PUBLIC` by design — the values are the same enumerations every consumer sees and they carry no PII / PHI / financial content. The validator carves codeset and reference-data contracts out of the narrative heuristic by path.

## Guidance

- Use `RESTRICTED` for any field that, if disclosed, would create regulatory or legal exposure. Use `CONFIDENTIAL` for commercial sensitivity (rates, reserves, underwriting comments).
- Apply the narrative default above to every new free-text field; document the exception only when there is a real, written reason.
- Status / period / territory / accounting fields (`_status_code`, `_result_code`, `_period_code`, `_territory_code`, `_region_code`, `accounting_*`) are typically `INTERNAL` with no PII tag — they describe lifecycle / classification metadata, not personal information. The validator emits a warning when these patterns appear at `RESTRICTED + PII` so reviewers can confirm the tagging is intentional.
- Classifications evolve. Tightening a classification (e.g. INTERNAL → CONFIDENTIAL) is a non-breaking metadata change. Loosening one (e.g. RESTRICTED → CONFIDENTIAL) is a governance decision and must be reviewed by the data steward, even though it does not break a schema consumer.

## Related

- `references/design-decisions/pc/codeset-strategy.md`
- `references/design-decisions/pc/versioning-policy.md`
