# End-to-End Walkthrough: Policy + PolicyTerm + PolicyCoverage + PolicyStatusCode

This walkthrough traces four canonical contracts — `pc.policy` (entity), `pc.policy-term` (entity), `pc.policy-coverage` (entity), and `pc.policy-status-code` (codeset) — through every step of the Fabric persona flow from `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` §3.3.3.

The point of this example is not to teach SCD2 or Spark. It is to make concrete the contract Nebula owes the Fabric deployer: which artifacts ship from this repository, what they look like, who consumes each one, and which steps live outside the boundary entirely.

The four contracts are picked because they cover the three materialization shapes a deployer will encounter in the same dependency tree:

- A standalone entity (`Policy`) that other entities reference.
- A child entity (`PolicyTerm`) that holds the policy's term-level state and is referenced by `Policy.current_policy_term_uid`.
- A junction entity (`PolicyCoverage`) that joins `Policy` and `PolicyTerm` to coverage selection.
- A codeset (`PolicyStatusCode`) that supplies allowed values for `Policy.policy_status_code`.

Together they exercise SCD2 entity merge, codeset SCD2 load, foreign-key validation, codeset reference checks, currency-pair assertions, and Purview projection — the full mechanic surface of Silver.

---

## 1. Persona flow at a glance

| Step | Persona | Tool / repo | Outcome |
|---|---|---|---|
| 1 | Insurance data architect | This repo | Edit ODCS contract, run validator, commit. |
| 2 | CI or local generator run | This repo | Regenerate manifest + DDL + Purview JSON; manifest validator confirms no drift. |
| 3 | Platform engineer | Deployer's choice (`spark-authoring-cli`, Fabric REST API, Azure DevOps pipeline, manual upload) | Create / update Lakehouse, apply DDL, deploy notebooks, populate lakehouse binding. |
| 4 | Operator | Fabric workspace UI or pipeline | Schedule deployed notebooks against Bronze; Silver tables fill. |
| 5 | Analyst | Spark / SQL client (`spark-consumption-cli` or any) | Query the Silver tables produced by the SCD2 / codeset notebooks. |
| 6 | Governance | Purview UI or REST API | Ingest `sensitivity-labels.json` and `business-glossary.json`; classification labels appear on the Lakehouse columns. |

Step 3 is the only step where this repository and a deployment tool meet. Steps 1–2 are this repository's domain; steps 4–6 are the deployer's (and the live workspace's) domain.

---

## 2. The four contracts

| Contract | Path | Kind | Version | Spark table | Schema |
|---|---|---|---|---|---|
| Policy | `references/odcs/pc/policy/policy.odcs.yaml` | entity | 0.4.2 | `policy` | `silver_policy` |
| PolicyTerm | `references/odcs/pc/policy/policy-term.odcs.yaml` | entity | 0.4.1 | `policy_term` | `silver_policy` |
| PolicyCoverage | `references/odcs/pc/coverage/policy-coverage.odcs.yaml` | entity | 0.4.1 | `policy_coverage` | `silver_coverage` |
| PolicyStatusCode | `references/odcs/pc/reference-data/policy-status-code.odcs.yaml` | codeset | 0.4.0 | `policy_status_code` | `silver_reference_data` |

Dependency graph the deployer sees in Silver:

```text
silver_reference_data.policy_status_code (codeset)
        ▲
        │ codeReference: policy_status_code → code_value
        │
silver_policy.policy ──┬────────────► silver_policy.policy_term
                       │              (Policy.current_policy_term_uid → policy_term_uid)
                       │
                       ▼
silver_coverage.policy_coverage ───► silver_policy.policy_term
                                     (PolicyCoverage.policy_term_uid)
                                     silver_policy.policy
                                     (PolicyCoverage.policy_uid)
                                     silver_coverage.coverage
                                     (PolicyCoverage.coverage_uid; out of scope here)
```

The codeset must be loaded first; an entity merge that runs before its codeset is loaded fails its post-merge `accepted_values` assertion. `silver_coverage.coverage` is an out-of-scope sibling for this walkthrough — `PolicyCoverage` references it, but the example focuses on the four contracts above.

---

## 3. Step 1 — Architect edits the canonical contract

The architect is the only persona who hand-authors files in this flow. Everything below the ODCS layer is generated.

A representative Step 1 change: adding a new policy lifecycle status `IN_FORCE_PENDING_AUDIT` to the codeset.

```yaml
# references/odcs/pc/reference-data/policy-status-code.odcs.yaml
# (excerpt — the field list does not change because codesets carry rows, not new columns)

description: Canonical codeset for policy lifecycle status values such as quoted, bound,
  issued, in-force, in-force-pending-audit, cancelled, lapsed, expired, and reinstated.
version: 0.4.1
customProperties:
  changelog:
  - '0.4.1: Added IN_FORCE_PENDING_AUDIT for audit-paused in-force policies (architect, 2026-05-07).'
```

The architect does not invent a Spark table, a Purview label, or a notebook. The contract layer carries `description`, `version`, `changelog`, `classifications`, and `adrs`; everything Fabric-specific is derived.

After saving, the architect runs the canonical validator:

```bash
python scripts/validation/validate-contracts.py
```

Expected output: `0 errors`, `0 warnings`, `85 contracts validated`. A failure here blocks the rest of the flow; the architect fixes the contract before moving on.

---

## 4. Step 2 — Generators regenerate every Fabric artifact

A single orchestrator script will run all four generators in dependency order. Until the orchestrator wrapper lands (F8 closeout), the deployer runs them by hand:

```bash
python scripts/generation/generate-fabric-manifests.py
python scripts/generation/generate-fabric-ddl.py
python scripts/generation/generate-fabric-purview.py
python scripts/generation/generate-fabric-notebooks.py
python scripts/validation/validate-fabric-manifests.py --require-full-coverage
```

Each generator is idempotent: re-running with no canonical change produces no diff. The drift validator at the end catches every form of manifest-vs-contract mismatch (path, id, version, digest, kind, role coverage, type allow-list, FK and codeReference resolution, currency-pair consistency).

### 4.1 Manifest

The manifest is the only Fabric-aware artifact that humans read. It is the intermediate representation that drives DDL, Purview, and notebooks.

```yaml
# targets/fabric/manifests/pc/policy/policy.fabric.yaml (excerpt)
manifestVersion: 1.0.0
contract:
  id: pc.policy
  name: Policy
  version: 0.4.2
  contractKind: entity
  classificationProfile: CONFIDENTIAL
  subjectToHipaa: false
fabric:
  lakehouse: nebula_pc_silver
  schema: silver_policy
  table:
    name: policy
    delta:
      tableProperties:
        delta.appendOnly: false
        delta.autoOptimize.optimizeWrite: true
        delta.autoOptimize.autoCompact: true
        delta.enableChangeDataFeed: true
      partitionedBy: [is_current_indicator]
      zorderBy: [policy_uid]
  columns:
    - {name: policy_uid, sparkType: STRING, role: identity, primaryKey: true}
    - {name: policy_status_code, sparkType: STRING, role: code-reference,
       codeReference: {codeset: pc.policy-status-code,
                       codesetTable: silver_reference_data.policy_status_code,
                       codesetField: code_value}}
    - {name: current_policy_term_uid, sparkType: STRING, role: foreign-key,
       foreignKey: {targetContract: pc.policy-term,
                    targetTable: silver_policy.policy_term,
                    targetField: policy_term_uid}}
    # ... 19 more columns, one per ODCS property
  scd2: {enabled: true, naturalKey: [policy_uid], deletionAware: false}
  recordState: {enabled: true, field: record_status_code,
                activeValue: ACTIVE, supersededValue: SUPERSEDED, softDeletedValue: SOFT_DELETED}
  bronze: {table: bronze.policy_raw, incrementalColumn: _ingested_at}
generation:
  sourceContractDigest: sha256:83d23562ae5949fe15d150fc48a07da5df359ed0945cc929f57a4e439f8983e8
```

The manifest for `pc.policy-coverage` has the same structure, with `silver_coverage` as the schema and seven foreign-key columns (`policy_uid`, `coverage_uid`, `policy_term_uid`, `exposure_uid`, `policy_limit_uid`, `policy_deductible_uid`, `record_status_code`'s codeReference). The manifest for `pc.policy-term` adds `currencyPair` metadata on `annualized_premium_amount` paired with `annualized_premium_currency_code`. The manifest for `pc.policy-status-code` is the simplest — ten columns, no foreign keys, no codeReferences (it is the codeset; entities reference it).

Files emitted:

```text
targets/fabric/manifests/pc/policy/policy.fabric.yaml
targets/fabric/manifests/pc/policy/policy-term.fabric.yaml
targets/fabric/manifests/pc/coverage/policy-coverage.fabric.yaml
targets/fabric/manifests/pc/reference-data/policy-status-code.fabric.yaml
```

### 4.2 DDL

```sql
-- targets/fabric/ddl/pc/policy/policy.spark.sql (excerpt)
CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_policy.policy (
  policy_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID...',
  policy_number STRING NOT NULL COMMENT 'Business-facing number assigned to the policy.',
  policy_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the policy.',
  current_policy_term_uid STRING COMMENT 'Identifier (GUID reference) for the current policy term...',
  policy_description STRING COMMENT 'Source-neutral business description...',
  -- ... 17 more columns
  record_status_code STRING NOT NULL COMMENT '...',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window...',
  valid_to_datetime TIMESTAMP COMMENT '...',
  is_current_indicator BOOLEAN NOT NULL COMMENT '...'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for durable Property and Casualty policy identity... Source: pc.policy v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_policy.policy ZORDER BY (policy_uid);
```

Files emitted:

```text
targets/fabric/ddl/pc/policy/policy.spark.sql
targets/fabric/ddl/pc/policy/policy-term.spark.sql
targets/fabric/ddl/pc/coverage/policy-coverage.spark.sql
targets/fabric/ddl/pc/reference-data/policy-status-code.spark.sql
```

DDL is a convenience for deployers wiring CI schema diffing or one-shot bootstrap; the merge notebooks create tables on first run if absent. DDL changes when manifest column shape changes — never as a hand edit.

### 4.3 Purview JSON

Two consolidated files (one per repository, not per contract):

```text
targets/fabric/purview/sensitivity-labels.json     (1235 column entries + 85 table entries)
targets/fabric/purview/business-glossary.json      (308 terms)
```

Excerpts for the four tables in this walkthrough:

```jsonc
// targets/fabric/purview/sensitivity-labels.json (filtered)
{
  "schemaVersion": "1.0",
  "lakehouse": "nebula_pc_silver",
  "tables": [
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_policy/policy",
     "purviewLabel": "Confidential", "classificationProfile": "CONFIDENTIAL",
     "sourceContract": "pc.policy", "sourceContractVersion": "0.4.2"},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_policy/policy_term",
     "purviewLabel": "Confidential", "classificationProfile": "CONFIDENTIAL",
     "sourceContract": "pc.policy-term", "sourceContractVersion": "0.4.1"},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_coverage/policy_coverage",
     "purviewLabel": "Internal", "classificationProfile": "INTERNAL",
     "sourceContract": "pc.policy-coverage", "sourceContractVersion": "0.4.1"},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_reference_data/policy_status_code",
     "purviewLabel": "Public", "classificationProfile": "PUBLIC",
     "sourceContract": "pc.policy-status-code", "sourceContractVersion": "0.4.0"}
  ],
  "labels": [
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_policy/policy/policy_uid",
     "sensitivityLabel": "Internal", "regulatoryTags": [],
     "sourceContract": "pc.policy", "sourceContractVersion": "0.4.2"},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_policy/policy/policy_description",
     "sensitivityLabel": "Confidential", "regulatoryTags": ["PII"],
     "sourceContract": "pc.policy", "sourceContractVersion": "0.4.2"},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_policy/policy_term/annualized_premium_amount",
     "sensitivityLabel": "Confidential", "regulatoryTags": ["FINANCIAL"],
     "sourceContract": "pc.policy-term", "sourceContractVersion": "0.4.1"}
    // ... 29 more column entries for these four tables
  ]
}
```

Two table entries are CONFIDENTIAL (`Policy` because it has the PII narrative `policy_description`; `PolicyTerm` because it has the FINANCIAL `annualized_premium_amount`). `PolicyCoverage` is INTERNAL — no sensitive narrative, no monetary amount. `PolicyStatusCode` is PUBLIC — every column is a public code value.

`subjectToHipaa` is false for all four contracts; no `complianceProfile: HIPAA` flag, no PHI columns, no `# HIPAA: requires masking` notebook annotations. The wiring is in place if a future contract flips the flag.

The glossary entry for `Source System Code` lists 38 column FQNs across the lakehouse — including the `source_system_code` columns on `silver_policy.policy` and `silver_policy.policy_term`. The Purview UI shows the glossary term linked to those columns automatically once the JSON is ingested.

### 4.4 Notebook templates

Three template notebooks plus the binding template are emitted unchanged on every generator run; they are decoupled from any specific contract:

```text
targets/fabric/notebooks/silver-scd2-merge-template.ipynb
targets/fabric/notebooks/silver-append-template.ipynb
targets/fabric/notebooks/silver-codeset-load-template.ipynb
targets/fabric/notebooks/lakehouse-binding-template.json
```

For this walkthrough the deployer uses two of them:

| Contract | Template |
|---|---|
| `pc.policy`, `pc.policy-term`, `pc.policy-coverage` | `silver-scd2-merge-template.ipynb` |
| `pc.policy-status-code` | `silver-codeset-load-template.ipynb` |

A single deployed copy of each template runs against every contract of its kind; the manifest path is the only per-contract parameter.

### 4.5 Drift control

The closing step of the generator run:

```bash
$ python scripts/validation/validate-fabric-manifests.py --require-full-coverage
Validated 85 manifests across 8 schemas: 0 errors.
```

Every check from `manifest-schema.md` §9 passes (path, id, version, digest, kind, mode-exclusion, role coverage, type allow-list, FK and codeReference resolution, currency-pair consistency, ADR id resolution). A drift in any of these 17 checks means the architect's contract change did not flow cleanly into the manifest; the fix is to re-run the generator, never to edit the manifest.

---

## 5. Step 3 — Platform engineer deploys to Fabric

Step 3 is consumer-driven. This repository ships file artifacts that conform to Fabric's expected file shapes (`.sql`, `.ipynb`, `.json`); the deployment mechanism is not prescribed.

Common deployment paths:

| Path | What it does | When to choose it |
|---|---|---|
| **`spark-authoring-cli` (`microsoft/skills-for-fabric`)** | AI-agent skill that authenticates against Fabric via Azure AD, creates the Lakehouse, applies DDL files, deploys notebooks via REST `updateDefinition`, and populates the lakehouse-binding fields per environment. | Default for interactive deployments where the deployer has the skills installed in their AI tool. |
| **Fabric REST API directly** | Custom script or pipeline calls Fabric REST endpoints to create the Lakehouse, run DDL, and `updateDefinition` notebooks. | When the deployer prefers an in-house deployer, or wants tight integration with an existing CI/CD platform. |
| **Azure DevOps pipeline** | YAML pipeline that runs `az` and Fabric REST calls for repeatable per-environment deployments. | Production deployments where everything must run from CI. |
| **Manual upload** | Deployer copies notebooks into the Fabric workspace by hand and runs DDL through the SQL endpoint. | One-off bootstrap or trial deployments. |

The contract Nebula owes the deployer in step 3 is the artifact bundle, not a particular tool. Whichever path the deployer chooses, they consume exactly these files for the four-contract walkthrough:

```text
# DDL applied to the Lakehouse:
targets/fabric/ddl/pc/reference-data/policy-status-code.spark.sql
targets/fabric/ddl/pc/policy/policy.spark.sql
targets/fabric/ddl/pc/policy/policy-term.spark.sql
targets/fabric/ddl/pc/coverage/policy-coverage.spark.sql

# Notebooks deployed (one copy of each template; the deployer typically clones
# them per contract or parameterizes them per pipeline run):
targets/fabric/notebooks/silver-codeset-load-template.ipynb
targets/fabric/notebooks/silver-scd2-merge-template.ipynb

# Lakehouse binding the deployer fills in:
targets/fabric/notebooks/lakehouse-binding-template.json

# Purview JSON ingested via Purview REST API or UI:
targets/fabric/purview/sensitivity-labels.json
targets/fabric/purview/business-glossary.json
```

`spark-authoring-cli` is one common path among many; it is not the only path and not a runtime dependency of this repository. The boundary in `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` §3.3 holds: this repository writes files; the deployer reads those files (or REST-deploys them) into a real workspace. There is no library import, no shared state, no version coupling.

The deployer fills `lakehouse-binding-template.json` per environment:

```json
{
  "default_lakehouse": "<lakehouse-id>",
  "default_lakehouse_name": "nebula_pc_silver",
  "default_lakehouse_workspace_id": "<workspace-id>"
}
```

The empty values that ship from this repository are intentional — workspace and lakehouse IDs are environment-specific and never committed.

---

## 6. Step 4 — Operator runs the loads

The operator schedules the deployed notebooks against Bronze. Bronze ingestion (Pipelines, Copy activity, OneLake shortcuts, third-party ETL) is owned upstream of this repository and is assumed to be in place.

Run order matters: the codeset must populate before the entity merges so the entities' post-write `accepted_values` assertions can resolve.

```text
1. silver-codeset-load-template.ipynb  manifest_path=targets/fabric/manifests/pc/reference-data/policy-status-code.fabric.yaml
2. silver-scd2-merge-template.ipynb    manifest_path=targets/fabric/manifests/pc/policy/policy-term.fabric.yaml
3. silver-scd2-merge-template.ipynb    manifest_path=targets/fabric/manifests/pc/policy/policy.fabric.yaml
4. silver-scd2-merge-template.ipynb    manifest_path=targets/fabric/manifests/pc/coverage/policy-coverage.fabric.yaml
```

Why this order:

- `policy_status_code` rows must exist before `policy.policy_status_code` is validated against the codeset.
- `policy_term` rows must exist before `policy.current_policy_term_uid` resolves cleanly. (FK validation is advisory; the merge does not block on a missing term.)
- `policy_coverage` references both `policy` and `policy_term` and rolls last.

Each notebook starts with a parameter cell that the operator overrides at run time:

```python
# PARAMETERS
manifest_path = "targets/fabric/manifests/pc/policy/policy.fabric.yaml"
load_mode = "incremental"          # incremental | full | catchup
as_of_datetime = None              # default is current run datetime
bronze_prefix_override = None      # default uses manifest's bronze.table prefix
run_optimize = False               # default false; deployer's maintenance schedule owns OPTIMIZE
optimize_min_rows = 1000000        # threshold below which OPTIMIZE is skipped
```

### 6.1 Worked-out merge notebook execution trace (structured stub)

A real Spark execution is not available locally; the trace below is the structured run-summary the notebook prints to stdout at the end of cell 11. The shape is canonical (defined in `scripts/generation/generate-fabric-notebooks.py` as `SHARED_RUN_SUMMARY_SOURCE`) — an orchestrator parses the same JSON regardless of contract.

Step 4.1 — load `policy_status_code` (codeset, full refresh, deletion-aware):

```jsonc
{
  "contractId": "pc.policy-status-code",
  "contractKind": "codeset",
  "table": "nebula_pc_silver.silver_reference_data.policy_status_code",
  "loadMode": "full",
  "runDatetime": "2026-05-07T03:14:22.011Z",
  "rowsRead": 9,
  "rowsInserted": 9,
  "rowsSuperseded": 0,
  "rowsSoftDeleted": 0,
  "rowsCorrected": 0,
  "assertions": [
    {"id": "policy_status_code_uid_required", "type": "not_null", "ok": true,  "severity": "error"},
    {"id": "code_value_required",             "type": "not_null", "ok": true,  "severity": "error"},
    {"id": "code_label_required",             "type": "not_null", "ok": true,  "severity": "error"},
    {"id": "valid_from_datetime_required",    "type": "not_null", "ok": true,  "severity": "error"},
    {"id": "valid_window_consistent",         "type": "expression", "ok": true, "severity": "error"},
    {"id": "single_current_row_per_key",      "type": "unique",   "ok": true,  "severity": "error"},
    {"id": "record_status_code_required",     "type": "not_null", "ok": true,  "severity": "error"}
  ],
  "status": "ok"
}
```

Step 4.2 — merge `policy_term` (entity, incremental):

```jsonc
{
  "contractId": "pc.policy-term",
  "contractKind": "entity",
  "table": "nebula_pc_silver.silver_policy.policy_term",
  "loadMode": "incremental",
  "rowsRead": 1432,
  "rowsInserted": 1228,    // 1140 brand-new + 88 SCD2 changes
  "rowsSuperseded": 88,    // closed by the change-detection hash
  "rowsSoftDeleted": 0,
  "rowsCorrected": 0,
  "assertions": [
    {"id": "annualized_premium_amount_currency_pair", "type": "currency_pair",   "ok": true, "severity": "error"},
    {"id": "policy_term_status_code_in_codeset",      "type": "accepted_values", "ok": true, "severity": "error"},
    {"id": "annualized_premium_currency_code_in_codeset", "type": "accepted_values", "ok": true, "severity": "error"}
    // ... 12 more assertions, all ok
  ],
  "status": "ok"
}
```

Step 4.3 — merge `policy` (entity, incremental). The new codeset value `IN_FORCE_PENDING_AUDIT` from the architect's Step 1 edit lights up here — 13 Bronze rows arrive carrying that status; the post-merge `policy_status_code_in_codeset` assertion finds them in `silver_reference_data.policy_status_code` and passes.

```jsonc
{
  "contractId": "pc.policy",
  "contractKind": "entity",
  "table": "nebula_pc_silver.silver_policy.policy",
  "loadMode": "incremental",
  "rowsRead": 2014,
  "rowsInserted": 1841,
  "rowsSuperseded": 173,
  "rowsSoftDeleted": 0,
  "rowsCorrected": 0,
  "assertions": [
    {"id": "policy_status_code_in_codeset", "type": "accepted_values", "ok": true, "severity": "error",
     "note": "13 row(s) reference IN_FORCE_PENDING_AUDIT; resolved against silver_reference_data.policy_status_code"},
    {"id": "policy_prior_policy_must_differ", "type": "expression", "ok": true, "severity": "warning"}
    // ... 14 more assertions, all ok
  ],
  "status": "ok"
}
```

Step 4.4 — merge `policy_coverage` (entity, incremental):

```jsonc
{
  "contractId": "pc.policy-coverage",
  "contractKind": "entity",
  "table": "nebula_pc_silver.silver_coverage.policy_coverage",
  "loadMode": "incremental",
  "rowsRead": 6122,
  "rowsInserted": 5847,
  "rowsSuperseded": 275,
  "rowsSoftDeleted": 0,
  "rowsCorrected": 0,
  "assertions": [
    {"id": "policy_coverage_effective_date_not_after_expiration_date", "type": "expression", "ok": true, "severity": "error"},
    {"id": "coverage_status_code_in_codeset",  "type": "accepted_values", "ok": true, "severity": "error"},
    {"id": "single_current_row_per_key",       "type": "unique", "ok": true, "severity": "error"}
    // ... 11 more assertions, all ok
  ],
  "status": "ok"
}
```

Failure mode worth understanding: if the operator runs `policy` *before* the codeset load, the `policy_status_code_in_codeset` assertion fails post-write — `IN_FORCE_PENDING_AUDIT` is missing from `silver_reference_data.policy_status_code`. The notebook records the failure in the run summary (`status: "failed"`) and raises after printing. The merge itself is idempotent; once the codeset catches up, a re-run clears the failure without rolling back any Silver rows.

---

## 7. Step 5 — Analyst queries Silver

The analyst joins the four tables to answer "for every active policy, what is the term context, the coverage selection, and the human-readable policy status?":

```sql
SELECT
  p.policy_uid,
  p.policy_number,
  ps.code_label                               AS policy_status_label,
  pt.policy_term_number,
  pt.term_effective_date,
  pt.term_expiration_date,
  pt.annualized_premium_amount,
  pt.annualized_premium_currency_code,
  pc.coverage_uid,
  pc.coverage_status_code,
  pc.effective_date                           AS coverage_effective_date
FROM nebula_pc_silver.silver_policy.policy AS p
JOIN nebula_pc_silver.silver_reference_data.policy_status_code AS ps
  ON ps.code_value = p.policy_status_code
 AND ps.is_current_indicator = TRUE
LEFT JOIN nebula_pc_silver.silver_policy.policy_term AS pt
  ON pt.policy_term_uid = p.current_policy_term_uid
 AND pt.is_current_indicator = TRUE
LEFT JOIN nebula_pc_silver.silver_coverage.policy_coverage AS pc
  ON pc.policy_uid = p.policy_uid
 AND pc.policy_term_uid = p.current_policy_term_uid
 AND pc.is_current_indicator = TRUE
WHERE p.is_current_indicator = TRUE
  AND p.record_status_code = 'ACTIVE';
```

Two patterns the analyst should know:

- **Always filter `is_current_indicator = TRUE` for current-state queries.** The Silver tables are SCD2; without the filter, the query returns every historical version. The `is_current_indicator` partition makes this filter cheap.
- **Codeset joins always go through `code_value`, never the codeset's `*_uid`.** Per the codeset-strategy ADR, `code_value` is the foreign key from the entity to the codeset. The codeset's `*_uid` is internal; entity contracts never store it.

Time-travel is available natively. To see the policy as it stood on 2026-04-01, the analyst replaces the `is_current_indicator = TRUE` filter with an SCD2 window predicate:

```sql
WHERE p.valid_from_datetime <= TIMESTAMP '2026-04-01 00:00:00 UTC'
  AND (p.valid_to_datetime IS NULL OR p.valid_to_datetime > TIMESTAMP '2026-04-01 00:00:00 UTC')
```

The same shape works on `policy_term`, `policy_coverage`, and `policy_status_code` — all four tables share the SCD2 system-time axis.

---

## 8. Step 6 — Governance ingests Purview JSON

The governance team (or an automated CI step) imports `targets/fabric/purview/sensitivity-labels.json` and `targets/fabric/purview/business-glossary.json` into Microsoft Purview via the REST API or the UI. The flat-file shape is exactly what Purview's import endpoints expect; this repository does not hold a Purview SDK or call the REST API directly.

After ingest, in the Purview UI:

| What governance sees | Source on this repo |
|---|---|
| Lakehouse-level entry `nebula_pc_silver` with 85 tables. | `sensitivity-labels.json.tables[]`. |
| Each Silver column tagged with its sensitivity (`Public` / `Internal` / `Confidential` / `Restricted`) and regulatory tags. | `sensitivity-labels.json.labels[]`. |
| `silver_policy.policy.policy_description` flagged `Confidential` + `PII`. | The ODCS contract's `customProperties.classifications` block on `policy_description`. |
| `silver_policy.policy_term.annualized_premium_amount` flagged `Confidential` + `FINANCIAL`. | Same — on `annualized_premium_amount`. |
| 308 business-glossary terms; "Source System Code" linked to 38 columns lakehouse-wide. | `business-glossary.json.terms[]`. |

Governance owns retention, masking, and audit downstream of the labels. This repository is the source of the labels; the Purview workspace is the system of record once the labels are in.

---

## 9. What changes when the architect changes the contract

A reverse trace of Step 1 — the architect deletes the `IN_FORCE_PENDING_AUDIT` value from the codeset (it was a misjudgment). What changes downstream:

| Layer | Change |
|---|---|
| ODCS contract | Codeset `description` and `changelog` updated; `version` bumped to 0.4.2. |
| Manifest | `contract.version` bumped to 0.4.2; `sourceContractDigest` recomputed; everything else unchanged (the contract carries no row-level data). |
| DDL | `Source: pc.policy-status-code v0.4.2.` table comment updated. Column shape is identical. |
| Purview JSON | Two `sourceContractVersion` strings update (one in `tables[]`, ten in `labels[]`). |
| Notebook templates | No change — the templates are decoupled from any specific contract. |
| Codeset load notebook run | Next run: 1 row missing from Bronze (the deleted code) → soft-deleted in Silver. |
| Entity merge notebook runs | Next runs: any policy still carrying the deleted code value as `policy_status_code` fails the `policy_status_code_in_codeset` post-write assertion. The architect either backfills those policies upstream or restores the codeset value. |

The blast radius of a single contract edit is a regenerated manifest, a small DDL diff, and a small Purview JSON diff. Nothing else moves. The mechanical fan-out from one ODCS edit is the entire payoff of the metadata-driven posture.

---

## 10. Cross-references

| Need | File |
|---|---|
| Plan that governs every step here | `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` |
| Persona flow definition | `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` §3.3.3, mirrored in `targets/fabric/README.md` |
| Lakehouse / schema / table conventions | `targets/fabric/conventions.md` |
| Manifest field reference | `targets/fabric/manifest-schema.md` |
| ODCS → Spark type mapping | `targets/fabric/type-mapping.md` |
| ADRs that govern target generation | `references/design-decisions/pc/temporal-modeling.md`, `record-state.md`, `event-and-transaction.md`, `codeset-strategy.md`, `data-classification.md`, `currency-convention.md`, `null-semantics.md`, `scd2-primary-key.md` |
| Canonical contracts referenced in this walkthrough | `references/odcs/pc/policy/policy.odcs.yaml`, `references/odcs/pc/policy/policy-term.odcs.yaml`, `references/odcs/pc/coverage/policy-coverage.odcs.yaml`, `references/odcs/pc/reference-data/policy-status-code.odcs.yaml` |
| Manifests referenced | `targets/fabric/manifests/pc/policy/policy.fabric.yaml`, `targets/fabric/manifests/pc/policy/policy-term.fabric.yaml`, `targets/fabric/manifests/pc/coverage/policy-coverage.fabric.yaml`, `targets/fabric/manifests/pc/reference-data/policy-status-code.fabric.yaml` |
| DDL referenced | `targets/fabric/ddl/pc/policy/policy.spark.sql`, `targets/fabric/ddl/pc/policy/policy-term.spark.sql`, `targets/fabric/ddl/pc/coverage/policy-coverage.spark.sql`, `targets/fabric/ddl/pc/reference-data/policy-status-code.spark.sql` |
| Purview JSON referenced | `targets/fabric/purview/sensitivity-labels.json`, `targets/fabric/purview/business-glossary.json` |
| Notebook templates referenced | `targets/fabric/notebooks/silver-scd2-merge-template.ipynb`, `targets/fabric/notebooks/silver-codeset-load-template.ipynb` |
| Lakehouse binding | `targets/fabric/notebooks/lakehouse-binding-template.json` |
| Manifest validator | `scripts/validation/validate-fabric-manifests.py` |
| Manifest generator | `scripts/generation/generate-fabric-manifests.py` |
| DDL generator | `scripts/generation/generate-fabric-ddl.py` |
| Purview generator | `scripts/generation/generate-fabric-purview.py` |
| Notebook generator | `scripts/generation/generate-fabric-notebooks.py` |
