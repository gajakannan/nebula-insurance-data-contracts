# ODCS to Spark SQL Type Mapping

This document is the type-mapping reference for the Fabric target. It defines how every ODCS `logicalType` projects to a Spark SQL / Delta type, what nullability rules apply, and how special cases (decimal scale, datetime semantics, GUID handling, codeset references, currency-paired amounts) are resolved.

Companion documents:

- `README.md` — purpose, scope, persona flow, file map.
- `conventions.md` — runtime mechanics: SCD2, append-only, codeset materialization, partitioning, V-Order, Purview projection.
- `manifest-schema.md` — manifest format, with Policy worked end-to-end.

The manifest generator reads this table at run time. If a mapping changes, this document is the single source of truth; the generator is updated to match.

---

## 1. Why types are explicit and centralized

ODCS contracts express types in domain-aligned terms (`string`, `decimal`, `date`, `datetime`, `boolean`, `integer`). Spark SQL needs concrete physical types with precision and timezone semantics. Centralizing the mapping prevents drift across generators (manifest, DDL, notebook), keeps the rules auditable, and makes type changes a one-line edit.

The mapping decisions reflect the canonical layer's intent (preserve business meaning, support analytics) rather than what is most compact in storage. Consumers that need narrower types (`SMALLINT`, `FLOAT`, `INT` over `BIGINT`) can downcast in the Gold layer; Silver does not optimize for storage at the cost of expressiveness.

The Fabric runtime version targeted is the Spark 3.5 / Delta 3.x baseline that Fabric Lakehouse provides as of 2026. Quarterly review of this table is a documented follow-up; a runtime upgrade may add types (e.g. `VARIANT`) but is not allowed to silently change existing mappings.

---

## 2. Primary mapping table

| ODCS `logicalType` | Spark SQL type | Nullable default | Notes |
|---|---|---|---|
| `string` | `STRING` | follows `required` | Default for all `*_uid`, `*_code`, `*_number`, narrative fields. |
| `integer` | `INT` | follows `required` | Sequence numbers, term numbers, counts. Use `BIGINT` only when the contract description explicitly warrants it. |
| `decimal` | `DECIMAL(18, 2)` | follows `required` | Default for monetary amounts. Manifest may override scale per the precision rules in §4. |
| `boolean` | `BOOLEAN` | follows `required` | All `*_indicator` fields. |
| `date` | `DATE` | follows `required` | All `*_date` fields. Date-only, no time component. |
| `datetime` | `TIMESTAMP` | follows `required` | All `*_datetime` fields. Stored as UTC; consumers convert for display. See §5. |
| `timestamp` | `TIMESTAMP` | follows `required` | Synonym for `datetime`. The canonical layer uses `datetime`; either is accepted from upstream. |
| `uuid` | `STRING` | follows `required` | Canonical layer keeps GUIDs as strings (see §6). |

The full set of ODCS logical types used in the canonical surface is the eight rows above. Anything outside this set (e.g. nested `array`, `map`, `struct`) is rejected by the manifest validator until the type-mapping table is extended deliberately.

---

## 3. Nullability

Nullability in the manifest is derived from the ODCS field's `required` flag:

| ODCS `required` | Manifest `nullable` | Spark SQL |
|---|---|---|
| `true` | `false` | `NOT NULL` |
| `false` (or omitted) | `true` | omitted (Spark default is nullable) |

Rules that override the default:

- **Primary keys.** Any field with ODCS `primaryKey: true` is non-null in the manifest, regardless of `required`. The validator flags a contradiction (a PK marked `required: false`) before manifest generation.
- **SCD2 system-time fields.** `valid_from_datetime` is non-null on every entity contract. `valid_to_datetime` is nullable (null indicates the current row). `is_current_indicator` is non-null. These rules come from the temporal-modeling ADR and are enforced by the contract validator before any manifest is written.
- **`record_status_code`.** Non-null on every entity contract. The merge notebook defaults it to `ACTIVE` on insert; transitions to `SUPERSEDED` and `SOFT_DELETED` are managed by the merge logic, never sourced from Bronze.
- **Correction fields.** `correction_indicator` is non-null on every event/transaction contract. `corrects_*_uid` is nullable (populated only when `correction_indicator` is true).
- **Source-attribution fields.** `source_system_code` and `source_natural_key` are nullable on entity contracts; the canonical contract makes them optional and the manifest follows. They are forbidden on append-only contracts per the temporal-modeling ADR.
- **Source-time fields.** `source_created_datetime` and `source_updated_datetime` are nullable on entity contracts. They are forbidden on append-only contracts.

Spark SQL `NOT NULL` constraints are emitted in the DDL. The merge notebook does not attempt to repair null values for required columns; a quality pre-assertion (severity `error`) catches the violation and aborts the run.

---

## 4. Decimal precision

The canonical default for `decimal` is `DECIMAL(18, 2)`, which fits most monetary amounts in the supported jurisdictions and avoids Spark's default `DECIMAL(38, 18)` which is wider than needed.

Per-field overrides are allowed in two circumstances:

1. **Rates and ratios.** Premium rates, factors, weights, and similar dimensionless quantities use `DECIMAL(18, 6)`. The manifest carries the override on the column entry; the contract description must call out the rate semantics so the override is auditable.
2. **High-precision amounts.** Reinsurance premium share factors and similarly fine-grained financial values may use `DECIMAL(18, 8)`. As of the F1 baseline no canonical field requires this; the override stays available for future contracts.

Override resolution rule: the manifest generator looks at field name plus `customProperties.decimalPrecision` (if present) and emits the override. If neither signal is present, the default `DECIMAL(18, 2)` applies. The current canonical surface has no contracts setting `customProperties.decimalPrecision`; all `decimal` fields use the default.

Edge cases:

- **Counts that look like amounts.** Fields like `number_of_employees`, `vehicle_count` are `integer` in ODCS, not `decimal`, and map to `INT`. The naming convention (`*_count`, `*_number`, `*_quantity` for whole numbers) keeps these unambiguous.
- **Percentages.** Stored as decimal fractions, not as integers. A 12.5% rate is `0.125` with `DECIMAL(18, 6)`; the contract description names the unit explicitly.
- **Negative amounts.** Permitted. The merge notebook does not enforce sign; the contract's quality rules (where present) carry domain-specific assertions.

---

## 5. Datetime semantics

All `datetime` fields map to Spark SQL `TIMESTAMP`. The canonical layer treats datetimes as UTC instants; the upstream data must arrive in UTC or be converted at the Bronze→Silver boundary.

Rules:

- **Storage timezone.** UTC. Spark `TIMESTAMP` is timezone-naive on the wire but interpreted as UTC by the merge notebook's session config (`spark.sql.session.timeZone = "UTC"`).
- **Display timezone.** Consumer responsibility. The Silver layer does not localize; Gold or Power BI applies user / report timezone.
- **Daylight saving.** Not relevant at the Silver layer because storage is UTC. Bronze data that arrives in local time must be converted before Silver merge; that is upstream of this repository.
- **`valid_from_datetime` / `valid_to_datetime`.** System time. Set by the merge notebook as `current_timestamp()` at run time. Never sourced from Bronze. The temporal-modeling ADR is authoritative.
- **`source_created_datetime` / `source_updated_datetime`.** Source-system time. Sourced from Bronze. Captured for late-arriving-data analysis. Distinct from system time; a row may have a recent `valid_from_datetime` (because it just landed) and an old `source_created_datetime` (because the source created it months ago).
- **`event_datetime` / `transaction_*_date`.** Business time. Sourced from Bronze. The append-only notebook uses `event_datetime` (or the equivalent transaction date) for partition pruning.

`date` fields map to `DATE`, which has no time component and no timezone. Date arithmetic (effective date, expiration date, occurrence date) operates on calendar days in the policy's governing jurisdiction; the canonical layer does not adjust dates across timezones.

Bi-temporal queries (system time + business time) are explicitly supported. The merge notebook's SCD2 expansion preserves both axes: `valid_from_datetime` / `valid_to_datetime` on the row records when Silver knew the version; the contract's business dates (`effective_date`, `expiration_date`, `event_datetime`) record when the business meant the value to apply. A third axis (source time, via `source_created_datetime` / `source_updated_datetime`) records when the source asserted it.

---

## 6. GUID handling

ODCS `uuid` and `string` fields named `*_uid` both map to Spark `STRING`. The canonical layer chose strings over Spark's nominal UUID handling for portability:

- Avoids driver-specific UUID rendering across JDBC, ODBC, and PySpark.
- Preserves exact lexicographic ordering for human inspection.
- Sidesteps Hive Metastore inconsistencies in older Fabric runtimes.
- Allows the merge notebook to hash GUIDs in the same SHA-256 pipeline as other string fields, with no per-type branching.

The trade-off (16 bytes of UUID become 36 bytes of canonical hyphenated string) is accepted at Silver. Gold may project to UUID or BINARY for indexing payoff.

GUID format expectations:

- Canonical hyphenated form: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`, lowercase, 36 characters.
- The contract validator does not currently enforce GUID format; that is a follow-up if GUID drift is observed in Bronze.
- The merge notebook does not validate GUID format; quality rules in the contract may add an assertion when the source is known to emit non-canonical forms.

---

## 7. Codeset reference fields

Fields that end in `_code` and bind to a codeset contract are still typed `STRING` in Spark, but the manifest carries an additional `codeReference` block that the notebook uses to validate values against the referenced codeset.

Type mapping is unchanged: `STRING NOT NULL` (or nullable per the field's `required` flag). The codeset binding is a manifest-level concern, not a Spark type concern. See `manifest-schema.md` for the `codeReference` block; see `conventions.md` for the post-merge assertion that confirms every code value exists in the referenced codeset's current rows.

The codeset target field is always `code_value` per the codeset-strategy ADR; the foreign key from the entity is the `*_code` value, not the codeset's `*_uid`.

Two narrow exceptions, both surfaced via `customProperties.codesetExempt: true` on the source contract:

- Long-tail carrier codes (carrier-product, accounting period) where a canonical codeset is not warranted.
- Two-value enumerations (DR / CR) policed by inline quality rules.

Exempt fields still map to `STRING`; they simply do not get a `codeReference` block in the manifest, and the notebook skips the referential check for them.

---

## 8. Currency-paired amounts

Per the currency-convention ADR, every monetary `*_amount` field has a sibling `*_currency_code` field. The pairing is enforced at the contract level (the validator catches an amount without a currency); the manifest projects the pairing as a `currencyPair` block on the amount column.

Type mapping:

- `*_amount` → `DECIMAL(18, 2)` (or override per §4).
- `*_currency_code` → `STRING` with a codeset binding to `pc.currency-code`.

The notebook's quality rules check that whenever the amount is non-null, the currency is non-null; manifest-level `currencyPair` metadata makes this assertion mechanical without reading the contract description.

A small set of contracts (`policy-deductible`, `product-coverage`) carry bound amounts under a single shared currency rather than a per-field currency. The contract carries `customProperties.currencyExempt: true` with a written rationale; the manifest emits the `currencyPair` block targeting the shared currency column on the same row.

---

## 9. Reserved column names

The Fabric materialization adds no Silver-side audit columns to the canonical schema. The manifest emits exactly the columns the canonical contract defines, plus the SCD2 / append-only fields the contract already includes.

Reserved names that the generator never writes and that Bronze data must not provide:

- `_silver_inserted_at`
- `_silver_run_id`
- `_silver_source_file`

If a future audit requirement needs these, the addition is planned as a contract-level change (because it propagates to all entity contracts) rather than a Fabric-only override. Adding them as Fabric-only columns would violate the "no platform mechanics in the canonical layer" boundary.

Bronze schema is allowed to carry additional columns; they are dropped at the merge boundary. The notebook reads only the columns named in the manifest's column list and `bronze.expectedColumns`.

---

## 10. Type validation

`scripts/validation/validate-fabric-manifests.py` runs three checks relevant to types:

1. **Allowed Spark types.** Every column's `sparkType` must be in the set `{STRING, INT, BIGINT, DECIMAL(p, s), BOOLEAN, DATE, TIMESTAMP}` for the explicit-precision form. Anything outside is a hard error.
2. **Type derivation correctness.** The Spark type must match the ODCS `logicalType` per §2 (or per a documented override per §4). The validator reads the source contract and re-derives; a manifest with a different type from what the rules produce fails.
3. **Nullability consistency.** The manifest's `nullable` flag must match the rules in §3. A primary key marked nullable, a `valid_from_datetime` marked nullable, a `correction_indicator` marked nullable — all hard errors.

Drift in any of the three is fixed by re-running the manifest generator. The manifest is never edited by hand to bypass the validator.

---

## 11. Type mapping by contract kind

The mapping table in §2 applies uniformly. The contract kind affects which fields are present, not how each field maps:

- **Entity contracts.** All eight ODCS types may appear. SCD2 system-time fields are `TIMESTAMP`; `is_current_indicator` is `BOOLEAN`; `record_status_code` is `STRING` with a binding to `pc.record-status-code`.
- **Event contracts.** Generally `STRING` and `TIMESTAMP`-heavy. `correction_indicator` is `BOOLEAN`. No SCD2 fields, no source-time fields.
- **Transaction contracts.** Same as event contracts plus `DECIMAL(18, 2)` amounts and their paired currency codes.
- **Codeset contracts.** Mostly `STRING`, with optional `effective_date` / `expiration_date` (`DATE`) and the standard SCD2 system-time fields. `code_value` is `STRING NOT NULL`.

The manifest's `contractKind` field tells the notebook which template to use; the type mapping itself does not branch.

---

## 12. Open questions

Documented for visibility; not blockers for F1.

- **`VARIANT` for source-attribution metadata.** Fabric's Spark runtime is gaining `VARIANT` support. If a future contract carries semi-structured source-system metadata (lineage payloads, raw event envelopes), `VARIANT` is the natural type. As of F1 no canonical field uses it.
- **Date-time precision.** Spark `TIMESTAMP` is microsecond-precision. The canonical layer does not currently rely on sub-second precision; if a future contract does (e.g. high-frequency event streams), a `TIMESTAMP_NTZ` or `TIMESTAMP_LTZ` distinction may be needed.
- **Negative-scale decimals.** Not used; not supported. If a future contract needs them, the type-mapping table is extended deliberately rather than the generator inferring.
