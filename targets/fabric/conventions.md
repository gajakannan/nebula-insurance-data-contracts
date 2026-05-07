# Fabric Conventions

This document is the runtime-mechanics reference for the Fabric target. It defines lakehouse and schema layout, materialization strategy per contract kind (entity / event / transaction / codeset), partitioning and Delta optimizations, Purview projection, HIPAA handling, lakehouse binding, and the conventions inherited from `microsoft/skills-for-fabric`.

Companion documents:

- `README.md` — purpose, scope, persona flow, file map.
- `type-mapping.md` — ODCS logical type → Spark SQL type, nullability, decimal precision, datetime semantics.
- `manifest-schema.md` — manifest format, with Policy worked end-to-end.

The authoritative plan is `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md`. Where this document and the plan disagree, the plan wins and this document is rewritten to match.

---

## 1. Lakehouse and workspace topology

The skills-for-fabric default is one workspace and one lakehouse per medallion layer. This Fabric target overrides the default to a **single Silver Lakehouse** for the canonical P&C contract set.

| Concern | Decision |
|---|---|
| Workspace | One workspace; name parameterized at deployment time (e.g. `nebula-pc-silver-{env}` for dev / test / prod). |
| Lakehouse | One Silver Lakehouse named `nebula_pc_silver`. |
| Schema (folder) | One schema per ODCS subject area: `silver_core`, `silver_policy`, `silver_coverage`, `silver_exposure`, `silver_submission`, `silver_claims`, `silver_financial`, `silver_reference_data`. |
| Delta table | snake_case slug of the contract id, with the `pc.` prefix dropped (e.g. `pc.policy` → `policy`, `pc.policy-term` → `policy_term`, `pc.claim-lifecycle-event` → `claim_lifecycle_event`). |
| Bronze | Assumed to exist outside this repository. Manifests reference Bronze tables by qualified name with a configurable prefix (e.g. `bronze.policy_raw`); the deployer overrides the prefix per environment via notebook parameters. |
| Gold | Out of scope for this milestone. Power BI / Direct Lake consumption is downstream of Silver and not generated here. |

The single-lakehouse choice is captured as an explicit override of the skills-for-fabric default. Trade-offs (looser RBAC isolation between ingestion and engineering than a dedicated-lakehouse layout would offer) are accepted for this milestone. A future milestone may revisit the layout if RBAC requirements change.

Schema names follow `silver_<subject_area>` to leave room for a future Gold layer (`gold_<subject_area>`) in the same lakehouse without naming collisions.

---

## 2. Naming conventions

| Artifact | Convention | Example |
|---|---|---|
| Lakehouse | snake_case, single lakehouse | `nebula_pc_silver` |
| Schema (folder) | `silver_<subject_area>` | `silver_policy` |
| Delta table name | snake_case slug of contract (no `pc.` prefix) | `policy`, `policy_term`, `claim_lifecycle_event`, `line_of_business` |
| Column name | exact name from the ODCS contract, lowercase snake_case | `policy_uid`, `valid_from_datetime`, `policy_status_code` |
| DDL file | `<slug>.spark.sql` under `targets/fabric/ddl/pc/<area>/` | `targets/fabric/ddl/pc/policy/policy.spark.sql` |
| Manifest file | `<slug>.fabric.yaml` under `targets/fabric/manifests/pc/<area>/` | `targets/fabric/manifests/pc/policy/policy.fabric.yaml` |
| Notebook (template) | `silver-<mode>-template.ipynb` under `targets/fabric/notebooks/` | `silver-scd2-merge-template.ipynb` |
| Manifest path used as parameter | absolute path from repo root | `targets/fabric/manifests/pc/policy/policy.fabric.yaml` |

Column naming is canonical; the manifest never renames a column for Fabric reasons. If a Fabric runtime word is reserved (the canonical layer's chosen names — `valid_from_datetime`, `record_status_code`, `correction_indicator` — are not Spark reserved words), the convention is to escape with backticks at DDL generation time, not to rename.

---

## 3. Materialization by contract kind

The manifest's `contractKind` field tells the generator and the runtime notebook which template to apply. Four kinds map onto three notebook templates.

| Kind | How identified | Notebook template | Materialization |
|---|---|---|---|
| `entity` | Default for any contract not in the lists below. | `silver-scd2-merge-template.ipynb` | SCD2 with `valid_from_datetime` / `valid_to_datetime` / `is_current_indicator` and `record_status_code`. |
| `event` | Slug ends in `-lifecycle-event`. | `silver-append-template.ipynb` | Append-only with `correction_indicator` + `corrects_*_uid`. No SCD2 fields. |
| `transaction` | Slug ends in `-transaction` or matches `financial-transaction` / `policy-financial-transaction` / `claim-financial-transaction`. | `silver-append-template.ipynb` | Append-only, same shape as event. |
| `codeset` | Located under `references/odcs/pc/reference-data/`. | `silver-codeset-load-template.ipynb` | SCD2 with full-refresh load mode by default; incremental opt-in. |

Three materialization shapes, one manifest schema. The schema fields that change per kind are documented in `manifest-schema.md`.

---

## 4. SCD2 strategy for entity contracts

Entity contracts use Delta `MERGE INTO` with a standard SCD2 expansion. The merge notebook follows these rules per Bronze row:

| Bronze row state | Action |
|---|---|
| New row, no current row in Silver matches the natural key. | Insert with `valid_from_datetime = current_timestamp()`, `valid_to_datetime = NULL`, `is_current_indicator = TRUE`, `record_status_code = 'ACTIVE'`. |
| Bronze matches a current Silver row by natural key, no change to non-system columns. | No-op. |
| Bronze matches a current Silver row by natural key, change detected. | Close the existing row (`valid_to_datetime = current_timestamp()`, `is_current_indicator = FALSE`, `record_status_code = 'SUPERSEDED'`); insert a new current row. |
| Bronze missing a key that exists as current in Silver, deletion-aware mode opted in. | Close the existing row with `record_status_code = 'SOFT_DELETED'`, `is_current_indicator = FALSE`. |

Default behavior is **non-deletion-aware**: if Bronze sends a partial snapshot, missing keys are not interpreted as deletions. Deletion-aware mode is opt-in per manifest (`scd2.deletionAware: true`) and is intended for sources that always send the full population.

Composite primary key: `(*_uid, valid_from_datetime)` per the scd2-primary-key ADR. The `*_uid` alone is unique only among current rows (where `is_current_indicator = TRUE`); across history a single `*_uid` may appear many times with disjoint validity windows.

Natural key for SCD2 merge: just `*_uid`. The manifest emits `scd2.naturalKey: [policy_uid]` etc.

### 4.1 Change detection

Change detection uses a SHA-256 hash over the non-system columns. The manifest's `scd2.changeDetection.excludeFromHashing` block lists the fields to ignore:

- `valid_from_datetime`
- `valid_to_datetime`
- `is_current_indicator`
- `record_status_code`

Hash equality means no change; the merge skips inserting a new row. Hash inequality triggers the close-old / insert-new path.

Source-time fields (`source_created_datetime`, `source_updated_datetime`) **are** included in the hash. A source-time change without any other field change is a meaningful signal (the source restated the row); the merge captures it as a new SCD2 version.

### 4.2 Record-state semantics

The `record_status_code` column carries the warehouse-level state of each record version. Allowed values come from the `pc.record-status-code` codeset:

- `ACTIVE` — current, observable, authoritative.
- `SUPERSEDED` — replaced by a newer version of the same `*_uid`.
- `SOFT_DELETED` — removed from the current population without physical deletion.
- `RESTATED` — corrected after the original version was superseded.
- `MERGED` — folded into another `*_uid`'s history.

The merge notebook manages `ACTIVE` and `SUPERSEDED` automatically. `SOFT_DELETED` requires deletion-aware mode. `RESTATED` and `MERGED` are operational concerns handled by separate operator-driven scripts; the standard merge does not produce them.

### 4.3 Source-attribution

Entity contracts carry `source_system_code` and `source_natural_key` for lineage. These are sourced from Bronze, included in the hash (so a source switch generates a new SCD2 version), and not used as part of the natural key. Multi-source mastering is upstream of Silver; the canonical contract carries one `source_system_code` per row reflecting the asserting source at that point.

---

## 5. Append-only strategy for event and transaction contracts

Event and transaction contracts are immutable: each row represents a fact in time, and corrections are emitted as **new rows** that reference the corrected row. Per the temporal-modeling and event-and-transaction ADRs, these contracts do **not** carry SCD2 fields.

### 5.1 Insert behavior

The merge notebook for append-only contracts is simpler than the SCD2 path:

| Bronze row state | Action |
|---|---|
| `correction_indicator = FALSE`, no row in Silver with the same `*_uid`. | Insert. |
| `correction_indicator = FALSE`, row in Silver with the same `*_uid` already exists. | No-op (idempotent re-run). |
| `correction_indicator = TRUE`, `corrects_*_uid` references a row that exists in Silver. | Insert the correction row. The corrected row is **not** updated or deleted. |
| `correction_indicator = TRUE`, `corrects_*_uid` references a row that does **not** exist in Silver. | Quality assertion fails (severity `error`); abort the run. |

There is no update logic and no soft-delete. A correction is a new fact; the original row is preserved for audit.

### 5.2 No SCD2 fields, no source-time fields

Append-only contracts:

- Do not carry `valid_from_datetime` / `valid_to_datetime` / `is_current_indicator` / `record_status_code`.
- Do not carry `source_created_datetime` / `source_updated_datetime` (these are forbidden on append-only contracts; the contract validator's C1.5 rule enforces this).
- The system-time the row landed is captured by ingestion metadata upstream of Silver and is not modeled as a canonical column.

The append-only contract carries:

- The fact's identity (`*_uid`).
- The fact's business time (`event_datetime`, `transaction_effective_date`, `transaction_posted_date`, etc.) — sourced from Bronze.
- The fact's payload (parties, amounts, references).
- The correction pair (`correction_indicator`, `corrects_*_uid`).

Querying "what was the state at time T" on an append-only table is a fold over rows up to T; no system-time machinery is needed because each row is its own immutable version.

### 5.3 Partition strategy

Default partitioning for append-only tables: month of business time, derived from the contract's primary business datetime field.

| Slug pattern | Business-time field | Partition |
|---|---|---|
| `*-lifecycle-event` | `event_datetime` | `MONTH(event_datetime)` |
| `*-transaction` | `transaction_effective_date` | `MONTH(transaction_effective_date)` |
| `financial-transaction` family | `transaction_effective_date` | `MONTH(transaction_effective_date)` |

The manifest emits `fabric.table.delta.partitionedBy` with the derived column. For very high volume tables, sub-month partitioning may be needed; that is a deferred decision and not chosen until measured (open question in the plan).

### 5.4 Quality rules at append time

The append notebook runs the contract's quality rules before write. Two rules are universal for append-only contracts:

- `correction_indicator` is non-null.
- `corrects_*_uid` is non-null whenever `correction_indicator` is true and references a row that exists in the same Silver table.

Violation of either fails the run.

---

## 6. Codeset strategy

Codeset contracts (the `*-code` and `*-type` reference-data contracts plus the richer reference-data entities like `LineOfBusiness`, `LifecycleStatus`, `LifecycleEventType`, `TransactionType`) are **SCD2 entity contracts in form**. Per the codeset-strategy ADR, code values version through history.

### 6.1 Load mode

Default load mode is **full refresh from Bronze** with SCD2 wrapping. Codesets are small (typically tens to low thousands of rows); a full snapshot per load is acceptable and simplifies the merge.

| Manifest field | Default | Override |
|---|---|---|
| `codeset.loadMode` | `full` | `incremental` when Bronze emits a change feed rather than a full snapshot. |

In full-refresh mode, missing codes from Bronze are interpreted as soft-deletions (the merge transitions them to `SOFT_DELETED` with `is_current_indicator = FALSE`). This is the only contract kind where deletion-awareness is on by default; code values do retire over time and the canonical layer needs to record that.

### 6.2 Codeset cross-references from entity contracts

When an entity contract has a `*_code` field bound to a codeset, the manifest emits a `codeReference` block on that column:

```yaml
- name: line_of_business_code
  sparkType: STRING
  nullable: false
  role: code-reference
  codeReference:
    codeset: pc.line-of-business
    codesetTable: silver_reference_data.line_of_business
    codesetField: code_value
```

The post-merge assertion in the entity notebook checks that every non-null `line_of_business_code` exists in the current rows of `silver_reference_data.line_of_business` joined on `code_value`. A missing reference fails the run.

The codeset target is always `code_value` per the codeset-strategy ADR; the foreign key from the entity is the `*_code` value, not the codeset's `*_uid`. This keeps codeset references portable across snapshots even when codesets retire and recreate `*_uid` values.

### 6.3 Codeset-exempt fields

Two narrow exceptions, marked at the contract level via `customProperties.codesetExempt: true`:

- Long-tail carrier or industry codes (carrier-product identifiers, accounting periods like `YYYYNN`) where defining a canonical codeset adds noise without value.
- Two-value enumerations (DR / CR) policed by an inline quality rule.

Exempt fields skip the `codeReference` block in the manifest and the post-merge referential check in the notebook. The `codesetExempt: true` flag carries a written `codesetExemptReason` so the exemption is auditable.

---

## 7. Delta table properties

Every Silver Delta table carries the following Delta table properties, set in the DDL and in the merge notebook:

```sql
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true',
  'delta.appendOnly' = 'false'   -- 'true' for event/transaction tables
)
```

V-Order is enabled at session level in the notebook:

```python
spark.conf.set("spark.sql.parquet.vorder.default", "true")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.optimizeWrite.binSize", "1g")
```

Partitioning and ZORDER:

| Contract kind | Partition | ZORDER hint (advisory) |
|---|---|---|
| Entity | `is_current_indicator` (small two-valued partition; current-state queries scan only the current partition). | `*_uid` for point lookups. |
| Event / transaction | `MONTH(<business-time field>)`. | None by default. |
| Codeset | None (small tables). | None. |

ZORDER is emitted as a hint in the DDL comments rather than executed; `OPTIMIZE ... ZORDER` is a runtime concern handled by the deployer's maintenance schedule. Tables under 1M rows skip ZORDER entirely.

---

## 8. DDL generation

The DDL generator (`scripts/generation/generate-fabric-ddl.py`, F5) emits one Spark SQL `CREATE TABLE IF NOT EXISTS` statement per contract under `targets/fabric/ddl/pc/<area>/<slug>.spark.sql`. Each file:

- Declares the Delta table with explicit columns and Spark SQL types from the manifest.
- Sets the table properties listed in §7.
- Declares partitioning per §7.
- Includes a column comment for every column, derived from the ODCS field description.
- Includes a table comment with `Source: pc.<contract-id> v<version>` for traceability.
- Carries a header comment that names the manifest file and the source contract path.

DDL is provided as a convenience for consumers who wire up an external schema-management workflow (one-off bootstrap, CI checks, schema diffing). The merge notebook does not require pre-existing tables; it creates them on first run if absent. DDL is the audit-friendly representation of the same shape.

ZORDER is documented in DDL comments rather than executed, since `OPTIMIZE ... ZORDER` is a runtime command, not part of `CREATE TABLE`.

---

## 9. Notebook architecture

Three template notebooks under `targets/fabric/notebooks/`. Each reads the manifest path as a parameter and adapts to any contract of its kind.

| Notebook | Drives | Manifest read at runtime |
|---|---|---|
| `silver-scd2-merge-template.ipynb` | All entity contracts (non-codeset, non-event, non-transaction) | Yes |
| `silver-append-template.ipynb` | All event and transaction contracts | Yes |
| `silver-codeset-load-template.ipynb` | All codeset contracts | Yes |

### 9.1 Parameterization

Every notebook starts with a Fabric parameter cell:

```python
# PARAMETERS
manifest_path = "targets/fabric/manifests/pc/policy/policy.fabric.yaml"
load_mode = "incremental"          # incremental | full | catchup
as_of_datetime = None              # optional override; default is current run datetime
bronze_prefix_override = None      # optional; if set, rewrites manifest's bronze.table prefix
```

Fabric notebook parameters use the standard `# PARAMETERS` cell tag and are overridden when the notebook is invoked via REST API or pipeline activity.

### 9.2 Cell layout

Every template notebook has the same nine-cell layout:

1. Parameter cell.
2. Imports and Spark session config (V-Order, Optimize Write, UTC timezone).
3. Manifest load and structural validation.
4. Bronze read (with the incremental column predicate from the manifest).
5. Quality pre-assertions (severity `error` rules that must pass before write).
6. Merge / append / codeset-load body, derived from the manifest.
7. Post-write validation (row counts, current-row uniqueness check, SCD2 window non-overlap check, codeset reference check).
8. Optional `OPTIMIZE` and `ZORDER` calls based on manifest hints.
9. Run summary (rows in, rows inserted, rows superseded, rows soft-deleted, assertion results) printed for orchestration to capture.

### 9.3 Fabric .ipynb requirements

Per the conventions inherited from `microsoft/skills-for-fabric`:

- Every code cell must include `"outputs": []` and `"execution_count": null` in the `.ipynb` JSON.
- Notebooks emitted by the generator include `metadata.dependencies.lakehouse` with `default_lakehouse`, `default_lakehouse_name`, and `default_lakehouse_workspace_id` slots intentionally left as empty strings; the deployer fills them in. The generator never invents workspace IDs.
- Notebook deployment (Fabric REST API `updateDefinition`) is a deployer concern. This repository ships notebook content; deployers deploy.

The notebook generator validates these shape rules; an emitted notebook that fails them is a generator bug.

### 9.4 Lakehouse binding

The generator emits one companion file: `targets/fabric/notebooks/lakehouse-binding-template.json` with empty `default_lakehouse`, `default_lakehouse_name`, and `default_lakehouse_workspace_id` fields. The deployer populates the file at deployment time, per environment.

Two binding paths are supported by the deployer (this repository is agnostic between them):

- **`spark-authoring-cli` skill.** The skill discovers the workspace and lakehouse via Azure AD authentication and writes the populated binding into the deployed notebooks as part of `updateDefinition`.
- **Manual or REST-driven.** The deployer fills the template in by hand or via a CI step and uploads to Fabric; this repository's notebooks accept the populated binding without modification.

---

## 10. Quality assertion strategy

ODCS quality rules are projected into the manifest as runtime-evaluable assertions. The notebook evaluates them per their type:

| Manifest assertion type | Notebook implementation |
|---|---|
| `not_null` | `df.filter(col.isNull()).count() == 0` |
| `unique` (e.g. `single_current_row_per_key`) | `df.groupBy(key).count().filter("count > 1").count() == 0` |
| `expression` | Arbitrary SQL boolean expression evaluated against the dataframe. |
| `currency_pair` | When the amount is non-null, the paired currency must be non-null. Manifest carries the pair via `currencyPair` metadata. |
| `accepted_values` | Derived from codeset cross-references. The value must exist in the referenced codeset's current rows. |

### 10.1 Severity

Three severity levels follow the ODCS contract:

- `error` — fails the run. The notebook raises after recording the failure to the run summary. Pre-assertions of this severity prevent the write; post-assertions of this severity mark the run as failed but do not roll back the write (the merge is idempotent, and a re-run after a fix produces a clean state).
- `warning` — recorded to the run summary; does not fail the run.
- `info` — recorded to the run summary.

### 10.2 Pre-assertion vs post-assertion

- **Pre-assertions** run on the Bronze read before any write. Examples: `policy_uid_required`, `correction_indicator_required`, `valid_from_datetime_required`. These prevent malformed data from entering Silver.
- **Post-assertions** run on the Silver dataframe after the merge. Examples: `single_current_row_per_key`, codeset reference checks, SCD2 window non-overlap. These catch inconsistencies that only manifest after the merge.

The `Bronze→Silver` run does not write to Silver if any error-severity pre-assertion fails. Post-write assertions log failures and mark the run as failed without rolling back.

---

## 11. Purview integration

Two artifacts under `targets/fabric/purview/` (generated in F4):

### 11.1 `sensitivity-labels.json`

A JSON manifest in Microsoft Purview's sensitivity-label import format. One entry per Delta column across the entire Lakehouse. Format:

```json
{
  "schemaVersion": "1.0",
  "labels": [
    {
      "fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_policy/policy/policy_uid",
      "sensitivityLabel": "Internal",
      "regulatoryTags": [],
      "sourceContract": "pc.policy",
      "sourceContractVersion": "0.4.2"
    },
    {
      "fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_core/party/birth_date",
      "sensitivityLabel": "Restricted",
      "regulatoryTags": ["PII"],
      "sourceContract": "pc.party",
      "sourceContractVersion": "0.4.x"
    }
  ]
}
```

Sensitivity values map from canonical to Purview names:

| Canonical sensitivity | Purview sensitivity label |
|---|---|
| `PUBLIC` | `Public` |
| `INTERNAL` | `Internal` |
| `CONFIDENTIAL` | `Confidential` |
| `RESTRICTED` | `Restricted` |

Regulatory tags pass through unchanged: `PII`, `PHI`, `FINANCIAL`.

The deployer ingests this file via the Purview REST API or imports it through the Purview UI. The generator does not call Purview; it emits the manifest.

### 11.2 `business-glossary.json`

A JSON manifest of canonical terms in Purview's business-glossary import format. Terms are extracted from `references/glossary/pc/` and from contract / field descriptions. Each term carries:

- Canonical term name.
- Definition.
- Source path (e.g. `references/glossary/pc/policy.md#Policy`).
- Optional list of column FQNs the term applies to.

Regenerated whenever glossary or contract descriptions change.

### 11.3 HIPAA-aware handling

When a contract has `customProperties.subjectToHipaa: true`, the generator:

- Adds `regulatoryTags: ["PHI"]` to every column whose classification carries `PHI`.
- Annotates the table-level entry with a `complianceProfile: HIPAA` flag.
- Includes a `# HIPAA: requires masking` comment in the merge notebook for columns tagged `PHI`.

The contract author flips one boolean; the generator does the rest. There is no parallel HIPAA-tracking list maintained by hand.

---

## 12. Bronze assumption

The plan and this folder assume Bronze tables exist; how data lands in Bronze (Fabric Pipelines, Copy activity, OneLake shortcuts, third-party ETL) is upstream and outside this repository.

Default assumptions captured in every manifest's `bronze` block:

- Bronze table name: `bronze.<source>_<table>` with a configurable prefix.
- Incremental column: `_ingested_at` of type `TIMESTAMP`.
- Expected columns: every column in the canonical contract is expected to be present in Bronze with the same name.
  - Columns missing from Bronze are filled with `NULL` if optional.
  - Columns missing from Bronze are a notebook error if required.
- Bronze is allowed to carry additional columns; they are dropped at the merge boundary.

The `bronze.table` value in each manifest is a default. Deployers override at run time via the `bronze_prefix_override` parameter; manifests are not edited.

---

## 13. Drift control

`scripts/validation/validate-fabric-manifests.py` (F2) catches manifest drift:

- Every manifest has a corresponding contract in `references/odcs/pc/`.
- Every contract has a manifest (the templates folder is excluded).
- The manifest's `contract.version` matches the source contract's version.
- The manifest's `contract.id` matches the source contract id and the path.
- The `sourceContractDigest` matches the SHA-256 of the source contract.
- Exactly one role-based field exists for each required SCD2 / record-state / append-only slot, given the contract kind.
- Spark SQL types are within the allowed type set.

The validator runs alongside `validate-contracts.py` whenever the canonical surface changes. A drifted manifest fails CI; the fix is to re-run the generator, never to edit the manifest.

---

## 14. Open questions

Documented in `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` §18. Summarized here for visibility:

1. **Bronze table prefix convention.** Currently `bronze.<source>_<table>`. If multiple Bronze sources share the lakehouse, the prefix may need a source-system component. Resolved when Bronze is wired.
2. **Catastrophe / large-event correlation across claims.** Now closed: the canonical hardening C4 phase shipped a dedicated `pc.catastrophe` contract; `pc.claim.catastrophe_uid` references it.
3. **Cross-currency reporting in Gold.** Out of scope here; Gold is downstream.
4. **Partitioning on event/transaction tables.** Default `MONTH(<business-time>)`. Sub-month partitioning may be needed for very high volume; not chosen until measured.
5. **Notebook idempotency under late-arriving Bronze rows.** Default merge logic handles late arrivals via the SCD2 hash check; ordering of multiple late events for the same logical key is "last write wins by `valid_from_datetime`."
6. **Streaming ingestion into Silver.** Out of scope for this milestone; batch only.
