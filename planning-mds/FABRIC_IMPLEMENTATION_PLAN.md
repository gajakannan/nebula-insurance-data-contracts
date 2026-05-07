# Fabric Implementation Plan

This plan defines how canonical ODCS contracts under `references/odcs/pc/` are projected into Microsoft Fabric Lakehouse artifacts. It is the detailed companion to work item **W023** in `planning-mds/STATUS.md` and to the Fabric target line in `planning-mds/IMPLEMENTATION_PLAN.md`.

This document is authoritative for the Fabric target. Generator scripts and the contents of `targets/fabric/` follow what this plan specifies; if they diverge, this plan is the source of truth and the artifacts must be regenerated.

**Precondition:** this plan assumes the canonical surface is at 0.4.x post-hardening per `planning-mds/CANONICAL_HARDENING_PLAN.md`. F1–F8 do not start until canonical hardening (Milestone 8.5, W025–W031) completes. The metadata-driven posture in §2 depends on canonical contracts being clean against the strengthened validator; running F1–F8 against the 0.2.0 surface would propagate every canonical-layer issue into manifests, DDL, notebooks, and Purview labels.

Last updated: 2026-05-06.

## 1. Intent

Project the canonical Property and Casualty contract set into a Fabric Lakehouse Silver layer using a **metadata-driven** approach: a single manifest per contract, rendered from the ODCS source of truth, drives every downstream artifact (Delta DDL, SCD2 merge notebooks, append-only event notebooks, Purview sensitivity manifests, business glossary).

The manifest is the only Fabric-aware artifact. Everything else is derived from it. The ODCS contract is the only insurance-aware artifact; the manifest is the only platform-aware artifact. No human authors at the level below the manifest.

### Success criteria

- Every canonical entity contract has a Delta table in the Silver Lakehouse with SCD2 system-time history.
- Every canonical event/transaction contract has an append-only Delta table with correction-row handling.
- Every canonical codeset has a SCD2 Delta table.
- Field-level sensitivity classifications from the ODCS contracts appear as Purview sensitivity labels on the Lakehouse Delta columns.
- A change to a canonical ODCS contract regenerates manifests, DDL, notebooks, and Purview artifacts in lockstep with no manual editing.
- A new author can read this plan plus `targets/fabric/conventions.md` and produce a contract that integrates correctly with Fabric Silver without writing platform code.

## 2. Non-Negotiable Boundaries

The following are constraints. The implementation must obey them; if a phase pulls in tension with one, the phase is wrong, not the constraint.

- **Canonical contracts are the source of truth.** ODCS YAML under `references/odcs/pc/` is not edited to suit Fabric mechanics. If Fabric needs context the contract does not provide, the gap is recorded as an open question in this plan, not silently encoded into a manifest or notebook.
- **Manifests are derived, not authored.** A human does not write `*.fabric.yaml` by hand. The generator is the only source of manifests. Any manual correction must be reflected back into the generator.
- **Notebooks are templates, not bespoke.** Per-contract notebooks are not authored. A small fixed set of parameterized notebooks reads the manifest at runtime and adapts.
- **No source-system specifics leak into the canonical layer.** Bronze schema details, ingestion mechanics, and connector configuration belong outside this repository.
- **Platform mechanics live under `targets/fabric/`.** The `references/` tree does not gain Fabric-specific fields, and the canonical contracts do not gain `customProperties` that exist solely to drive Fabric behavior. Generic `customProperties` (classifications, classification profile, changelog) are canonical and serve multiple targets.
- **Append-only contracts stay append-only.** Per the temporal-modeling and event-and-transaction ADRs, event and transaction tables must not be implemented with SCD2.
- **PHI-tagged contracts inherit HIPAA handling automatically.** The generator emits HIPAA-aware Purview labels and notebook annotations whenever `customProperties.subjectToHipaa` is true on a contract.

## 3. Architectural Posture

### 3.1 Metadata-driven engineering

```
ODCS contract (references/odcs/pc/*.odcs.yaml)
        │
        ▼  generator: scripts/generation/generate-fabric-manifests.py
Fabric manifest (targets/fabric/manifests/pc/<area>/<slug>.fabric.yaml)
        │
        ├──► targets/fabric/ddl/pc/<area>/<slug>.spark.sql       (Delta CREATE TABLE)
        ├──► consumed by targets/fabric/notebooks/silver-*-template.ipynb at runtime
        ├──► targets/fabric/purview/sensitivity-labels.json      (column sensitivity)
        └──► targets/fabric/purview/business-glossary.json       (terms from descriptions)
```

The manifest carries everything a Fabric consumer needs about one contract:

- Lakehouse, schema, and Delta table identity.
- Column list with Spark SQL types, nullability, primary key, partition role, classification, and Purview sensitivity label.
- SCD2 / append-only mode and the field names that implement it.
- Quality rules in a runtime-evaluable form.
- Codeset cross-references (where to look up `*_code` values).
- Bronze contract: expected source table, incremental key, and column expectations.

### 3.2 Reference materials

- `microsoft/skills-for-fabric` — Fabric-native authoring and consumption skills (see §3.3 for the coexistence model). Specifically referenced for `.ipynb` API requirements and medallion conventions, drawing on `skills/e2e-medallion-architecture/` and `skills/spark-authoring-cli/`.
- ADRs that govern target generation behavior:
  - `references/design-decisions/pc/identifier-strategy.md`
  - `references/design-decisions/pc/temporal-modeling.md`
  - `references/design-decisions/pc/record-state.md`
  - `references/design-decisions/pc/event-and-transaction.md`
  - `references/design-decisions/pc/codeset-strategy.md`
  - `references/design-decisions/pc/data-classification.md`
  - `references/design-decisions/pc/currency-convention.md`
  - `references/design-decisions/pc/null-semantics.md`

### 3.3 Coexistence with `microsoft/skills-for-fabric`

This repository ships a finished, source-of-truth artifact bundle: canonical insurance contracts plus everything generated from them (manifests, DDL, parameterized notebooks, Purview labels, glossary). It is intentionally **static and insurance-aware**.

The `microsoft/skills-for-fabric` repository ships a complementary, **dynamic and insurance-agnostic** capability: a collection of AI-agent skills (installed into Copilot CLI, Claude Code, Cursor, VS Code, Windsurf) that authenticate against a live Fabric workspace via Azure AD and operate it — creating Lakehouses, deploying notebooks, running queries, registering Power BI semantic models.

Neither replaces the other. They are designed to compose: this repository's outputs are operands for the skills.

#### 3.3.1 What each side owns

| Concern | This repository | `microsoft/skills-for-fabric` |
|---|---|---|
| Insurance domain modeling (entities, relationships, lifecycle, classifications) | Owns | Out of scope |
| Canonical contract authoring conventions (ADRs, validator, glossary, patterns) | Owns | Out of scope |
| Canonical-to-Fabric translation (manifest schema, type mapping, role taxonomy) | Owns | Out of scope |
| Generated `.ipynb` notebook templates (SCD2 / append / codeset) | Authors and validates | Deploys into Fabric via `spark-authoring-cli` |
| Generated Spark SQL `CREATE TABLE` DDL | Authors and validates | Applies to Lakehouse via `spark-authoring-cli` |
| Generated Purview sensitivity-label and business-glossary JSON | Authors and validates | No skill counterpart today; consumer ingests via Purview REST API |
| Workspace creation, capacity assignment, RBAC | Out of scope | Owns (skill: `spark-authoring-cli`) |
| Lakehouse provisioning and lakehouse-binding population | Leaves binding fields blank in `lakehouse-binding-template.json` | Owns the populated runtime binding |
| Notebook deployment to Fabric (REST `updateDefinition`) | Out of scope | Owns (skill: `spark-authoring-cli`) |
| Bronze ingestion (Pipelines, Copy activity, OneLake shortcuts) | Out of scope | Out of scope; covered by separate Fabric tooling |
| Silver-table query access for analysts | Out of scope | Owns (skill: `spark-consumption-cli`) |
| Gold semantic models and Power BI artifacts | Out of scope (Gold is downstream) | Owns (skills: `powerbi-authoring-cli`, `powerbi-consumption-cli`) |

#### 3.3.2 Artifact-level handoff

```
┌─────────────────────────────────────────┐
│  nebula-insurance-data-contracts        │     static / insurance-aware
│  (this repository)                      │
│                                         │
│  references/odcs/pc/*.odcs.yaml         │
│           │                             │
│           ▼  scripts/generation/...     │
│  targets/fabric/                        │
│  ├── manifests/...fabric.yaml           │
│  ├── ddl/...spark.sql                   │
│  ├── notebooks/silver-*-template.ipynb  │
│  ├── notebooks/lakehouse-binding-       │
│  │              template.json (blank)   │
│  └── purview/{sensitivity-labels,       │
│               business-glossary}.json   │
└─────────────┬───────────────────────────┘
              │  artifact handoff
              │  (file paths; no runtime coupling)
              ▼
┌─────────────────────────────────────────┐
│  microsoft/skills-for-fabric            │     dynamic / insurance-agnostic
│  (installed in the consumer's AI tool)  │
│                                         │
│  spark-authoring-cli                    │
│  ├── creates Lakehouse                  │
│  ├── applies DDL                        │
│  ├── deploys notebooks (REST)           │
│  └── populates lakehouse-binding        │
│                                         │
│  spark-consumption-cli                  │
│  └── runs Spark SQL against Silver      │
│                                         │
│  powerbi-authoring-cli (Gold layer)     │
│  powerbi-consumption-cli (Gold layer)   │
└─────────────┬───────────────────────────┘
              │
              ▼
       Live Fabric workspace
       (Azure AD authenticated)
```

The boundary is the artifact layer: this repository writes files; the skills read those files (or REST-deploy them) into a real workspace. There is no library import, no runtime dependency, no shared state.

#### 3.3.3 Persona workflow

The end-to-end workflow spans three personas; each persona uses one side of the boundary.

| Step | Persona | Repository / tool | Activity |
|---|---|---|---|
| 1 | Insurance data architect | This repository | Author or update an ODCS contract under `references/odcs/pc/`. Run `scripts/validation/validate-contracts.py`. Commit. |
| 2 | This repository's CI / local generator run | This repository | `scripts/generation/generate-fabric.py` regenerates manifests, DDL, notebooks, Purview JSON. `validate-fabric-manifests.py` confirms no drift. |
| 3 | Platform engineer | `spark-authoring-cli` skill (in their AI tool) | Point the skill at the generated artifacts. Skill creates / updates the Lakehouse, applies DDL, deploys notebooks, populates lakehouse binding. |
| 4 | Platform engineer or operator | Fabric workspace UI or pipeline | Schedule the deployed notebooks against Bronze. Bronze ingestion is owned upstream of this repository. |
| 5 | Analyst | `spark-consumption-cli` skill | Query the Silver tables produced by the SCD2 / append / codeset notebooks. |
| 6 | Analyst (Gold) | `powerbi-authoring-cli` / `powerbi-consumption-cli` | Build and consume Power BI semantic models atop Silver. Out of scope for this repository's milestone. |

Step 3 is the only step where the two repositories meet. Steps 1–2 are this repository's domain; steps 4–6 are the skills' (and the live workspace's) domain.

#### 3.3.4 Conventions this repository inherits from `skills-for-fabric`

The skills are insurance-agnostic but they encode platform-level conventions that the generator must respect so that handoff at step 3 works without manual fixup:

- **`.ipynb` shape.** Every code cell carries `"outputs": []` and `"execution_count": null`. Notebook generator validates this shape (per §10.3 and the F6 acceptance criteria).
- **Lakehouse-binding placeholder pattern.** Generator emits `lakehouse-binding-template.json` with empty `default_lakehouse`, `default_lakehouse_name`, `default_lakehouse_workspace_id` fields; the skill fills these at deployment time. Generator never invents workspace IDs.
- **Medallion layering.** Bronze / Silver / Gold separation. This repository targets the Silver layer only; Bronze and Gold sit outside the artifact bundle but inside the skills' operational scope.
- **Single-lakehouse override.** The skills' default is one workspace and one lakehouse per layer; this repository overrides to a single Silver Lakehouse (per §4) and the override is documented so the skill's templates do not contradict it.

#### 3.3.5 Independence guarantees

- **This repository runs without the skills installed.** Generators are pure Python plus PyYAML; validators are pure Python. No skill-runtime is invoked at generation or validation time.
- **The skills run without this repository present.** They operate on any conformant Fabric artifact bundle; this repository's outputs are one such bundle, but a hand-authored bundle would also work.
- **No shared schema or library.** Manifest schema (§5) is internal to this repository. Skills consume the file types Fabric expects (`.ipynb`, `.sql`, `.json`) — not the manifest. The manifest is the generator's intermediate representation, not a public interface.
- **Versioning is independent.** This repository's contracts version per `versioning-policy.md`. The skills version per their own marketplace. A consumer pinning one does not constrain the other; the only compatibility surface is the file types Fabric accepts.

#### 3.3.6 What this means for §19 (Out of Scope)

Several items in §19 are "out of scope here, in scope for the skills." The §19 list explicitly cross-references the skill that handles each item, so a reader does not mistake a deferral for a gap.

## 4. Lakehouse and Workspace Topology

The skills-for-fabric default is one workspace and one lakehouse per medallion layer. This plan targets only the Silver layer, and the user has chosen a **single-lakehouse** layout for the canonical Silver.

| Concern | Decision |
|---|---|
| Workspace | Single workspace, name parameterized (e.g. `nebula-pc-silver-{env}`) |
| Lakehouse | Single Silver Lakehouse, name `nebula_pc_silver` |
| Schema (folder) inside Lakehouse | One schema per ODCS subject area: `silver_core`, `silver_policy`, `silver_coverage`, `silver_product`, `silver_exposure`, `silver_submission`, `silver_claims`, `silver_financial`, `silver_reference_data` |
| Delta table name | snake_case slug of the contract (e.g. `policy`, `policy_term`, `claim_lifecycle_event`) |
| Bronze | Assumed to exist outside this repository. Manifests reference Bronze tables by qualified name via a configurable prefix (e.g. `bronze.<source>_<table>`). |
| Gold | Out of scope for this milestone. Power BI / Direct Lake consumption is downstream of Silver and not generated here. |

The single-lakehouse choice is captured as an explicit override of the skills-for-fabric default; trade-offs (looser RBAC isolation between ingestion and engineering) are accepted for this milestone.

## 5. Manifest Schema

The manifest is YAML. One file per ODCS contract, mirroring the source path:

```text
references/odcs/pc/policy/policy.odcs.yaml
        ↓
targets/fabric/manifests/pc/policy/policy.fabric.yaml
```

### 5.1 Top-level shape

```yaml
manifestVersion: 1.0.0
contract:
  id: pc.policy                        # source ODCS contract id
  name: Policy
  version: 0.2.0                       # mirrors source contract version
  domain: property-and-casualty
  classificationProfile: INTERNAL      # from contract customProperties
  subjectToHipaa: false
  contractKind: entity                 # entity | event | transaction | codeset
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
      vorder: true
  columns:
    - name: policy_uid
      sparkType: STRING
      nullable: false
      primaryKey: true
      role: identity                    # identity | business-key | source-attribution
                                         # | scd2-valid-from | scd2-valid-to
                                         # | scd2-is-current | record-state
                                         # | foreign-key | code-reference
                                         # | monetary-amount | monetary-currency
                                         # | data | event-correction-flag
                                         # | event-corrects-ref | lifecycle-event-link
      description: Immutable system-generated GUID...
      classifications:
        sensitivity: INTERNAL
        regulatoryTags: []
      purview:
        sensitivityLabel: Internal
      foreignKey: null
      codeReference: null
      currencyPair: null
    - name: policy_number
      sparkType: STRING
      nullable: false
      role: business-key
      description: Business-friendly identifier...
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal
    - name: line_of_business_code
      sparkType: STRING
      nullable: false
      role: code-reference
      description: ...
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal
      codeReference:
        codeset: pc.line-of-business
        codesetTable: silver_reference_data.line_of_business
        codesetField: code_value
    - name: annualized_premium_amount
      sparkType: DECIMAL(18, 2)
      nullable: true
      role: monetary-amount
      description: ...
      classifications:
        sensitivity: CONFIDENTIAL
        regulatoryTags: [FINANCIAL]
      purview:
        sensitivityLabel: Confidential
      currencyPair:
        pairedColumn: premium_currency_code
  scd2:
    enabled: true
    validFrom: valid_from_datetime
    validTo: valid_to_datetime
    isCurrent: is_current_indicator
    naturalKey: [policy_uid]
    changeDetection:
      excludeFromHashing:
        - valid_from_datetime
        - valid_to_datetime
        - is_current_indicator
        - record_status_code
  recordState:
    enabled: true
    field: record_status_code
    activeValue: ACTIVE
    softDeletedValue: SOFT_DELETED
    supersededValue: SUPERSEDED
  appendOnly:
    enabled: false                     # mutually exclusive with scd2.enabled
    correctionIndicator: null
    correctsRefField: null
  qualityRules:
    - id: policy_uid_required
      type: not_null
      column: policy_uid
      severity: error
      sourceRule: policy_uid_required
    - id: policy_prior_policy_must_differ
      type: expression
      expression: prior_policy_uid IS NULL OR prior_policy_uid <> policy_uid
      severity: warning
      sourceRule: policy_prior_policy_must_differ
  bronze:
    table: bronze.policy_raw           # parameterized; consumer overrides
    incrementalColumn: _ingested_at
    expectedColumns:
      - policy_uid
      - policy_number
      - ...
relationships:
  - name: policy_to_current_policy_term
    description: ...
    cardinality: many-to-one
    targetContract: pc.policy-term
    targetTable: silver_policy.policy_term
    sourceFields: [current_policy_term_uid]
    targetFields: [policy_term_uid]
generation:
  generatorVersion: 1.0.0
  generatedAt: 2026-05-05T00:00:00Z
  sourceContractPath: references/odcs/pc/policy/policy.odcs.yaml
  sourceContractDigest: sha256:...
```

### 5.2 Field role taxonomy

The `role` field on a column captures *how* the notebook should treat the column. It is derived from ODCS metadata, not authored.

| Role | Source signal | Notebook behavior |
|---|---|---|
| `identity` | `primaryKey: true` and name ends `_uid` | Used as the SCD2 natural key; not nullable; immutable |
| `business-key` | Field named `*_number` and not the PK | Carried through; surfaced for human queries |
| `source-attribution` | `source_system_code`, `source_natural_key` | Captured for lineage; not part of change detection |
| `scd2-valid-from` / `scd2-valid-to` / `scd2-is-current` | Standard SCD2 fields | Managed entirely by the merge notebook; not sourced from Bronze |
| `record-state` | `record_status_code` | Default `ACTIVE` on insert; transitions managed by deletion / supersession logic |
| `foreign-key` | Field name ends `_uid` and is not the PK | Carried through; not joined eagerly in Silver merge |
| `code-reference` | Field name ends `_code` and a codeset contract exists | Carried through; emits a `codeReference` block for downstream joins |
| `monetary-amount` | logicalType `decimal` and field name has amount semantics | Triggers paired-currency assertion |
| `monetary-currency` | Field name ends `_currency_code` and a sibling monetary field exists | Carried; participates in pairing assertion |
| `data` | Anything else | Carried through; subject to standard hashing for change detection |
| `event-correction-flag` | `correction_indicator` on event/transaction | Drives append insert with correction handling |
| `event-corrects-ref` | `corrects_*_uid` on event/transaction | Foreign key to the corrected row |
| `lifecycle-event-link` | `lifecycle_event_uid` on transaction | Cross-reference to the linked lifecycle event |

### 5.3 Manifest validation

A second validator script (`scripts/validation/validate-fabric-manifests.py`) checks:

- Every manifest has a corresponding contract in `references/odcs/pc/`.
- Every contract has a manifest unless explicitly excluded (the templates folder is excluded).
- The manifest's `contract.version` matches the source contract's version.
- The manifest's `contract.id` matches the source contract id and the path.
- The `sourceContractDigest` matches the SHA-256 of the source contract.
- Exactly one role-based field exists for each required SCD2 / record-state / append-only slot, given the contract kind.
- Spark SQL types are within the allowed type set.

This validator runs as part of CI (or whatever local check workflow exists); a manifest that drifts from its contract fails. Drift is fixed by re-running the generator, never by editing the manifest.

## 6. Type Mapping

ODCS logical types map to Spark SQL / Delta types. Decisions reflect the canonical layer's intent rather than what is most compact in storage; consumers can downcast in Gold if they need to.

| ODCS logicalType | Spark SQL type | Notes |
|---|---|---|
| `string` | `STRING` | Default. Used for all `*_uid`, `*_code`, `*_number`, narratives. |
| `integer` | `INT` | For sequence numbers, term numbers, counts. Use `BIGINT` when documented as large; default `INT` otherwise. |
| `decimal` | `DECIMAL(18, 2)` | Default for monetary amounts. Manifest may override scale where the contract description warrants (e.g. rates). |
| `boolean` | `BOOLEAN` | For all `*_indicator` fields. |
| `date` | `DATE` | For all `*_date` fields. |
| `datetime` | `TIMESTAMP` | For all `*_datetime` fields including SCD2 system-time. Stored as UTC; consumers convert for display. |
| `timestamp` | `TIMESTAMP` | Synonym for `datetime`. |
| `uuid` | `STRING` | Canonical layer keeps GUIDs as strings to avoid driver-specific UUID handling. |

The full table including precision overrides lives in `targets/fabric/type-mapping.md` and is read by the generator at run time.

## 7. SCD2 Implementation for Entity Contracts

### 7.1 Strategy

Entity contracts (every contract not in the event/transaction or codeset set) use Delta `MERGE INTO` with the standard SCD2 expansion:

- New row from Bronze, no current row in Silver: insert with `valid_from_datetime = now()`, `valid_to_datetime = null`, `is_current_indicator = true`, `record_status_code = 'ACTIVE'`.
- Bronze row matches a current Silver row by natural key, no change to non-system columns: no-op.
- Bronze row matches a current Silver row by natural key, change detected: close the existing row (`valid_to_datetime = now()`, `is_current_indicator = false`, `record_status_code = 'SUPERSEDED'`), insert a new current row.
- Bronze row missing a key that exists as current in Silver, deletion-aware mode: close the existing row with `record_status_code = 'SOFT_DELETED'` and `is_current_indicator = false`. Default behavior is non-deletion-aware unless the manifest opts in.

### 7.2 Change detection

Manifest emits a `scd2.changeDetection.excludeFromHashing` list with the SCD2 system-time fields and `record_status_code`. The merge notebook computes a SHA-256 hash over the remaining columns; equal hash means no change.

### 7.3 Partition strategy

Silver entity tables partition by `is_current_indicator` (small, two-valued partition) so current-state queries scan only the current partition. This is in tension with classic date-based partitioning, but most analytical queries on Silver entity tables filter by `is_current_indicator = true`, so the current-state partition stays hot.

ZORDER on the `*_uid` primary key for point lookups. Skipping ZORDER on small tables (< 1M rows estimated) is acceptable; the manifest carries it advisorily.

### 7.4 V-Order and Optimize Write

V-Order and Optimize Write are enabled on every Silver Delta table via `delta.autoOptimize.optimizeWrite: true` and the Spark session config in the merge notebook:

```python
spark.conf.set("spark.sql.parquet.vorder.default", "true")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.optimizeWrite.binSize", "1g")
```

## 8. Append-Only Implementation for Event and Transaction Contracts

Event and transaction contracts (`*LifecycleEvent`, `*Transaction`, plus `FinancialTransaction` and `ClaimFinancialTransaction`) are append-only.

- Bronze rows are inserted directly into Silver with `valid_from_datetime = now()`. No update logic.
- Correction rows are inserted with `correction_indicator = true` and `corrects_*_uid` referring to the corrected row. The merge notebook does not update or delete the corrected row.
- Default partition: `valid_from_datetime` truncated to month (`MONTH(valid_from_datetime)`). Aligns with high-volume time-series query patterns.
- Quality assertion: `correction_indicator` non-null; `corrects_*_uid` is non-null whenever `correction_indicator` is true and references a row that exists in the same Silver table.

A separate template notebook handles append-only contracts; reuses the same manifest schema with `appendOnly.enabled: true`.

## 9. Codeset Implementation

Codeset contracts (the 13 generated codesets plus `LineOfBusiness`, `LifecycleStatus`, `LifecycleEventType`, `TransactionType`) are SCD2 entity contracts in form. Per the codeset-strategy ADR, code values version through history.

- Default load mode: full refresh from Bronze codeset table, with SCD2 wrapping per the entity merge logic. Codesets are small and a full snapshot per load is acceptable.
- Optional incremental mode: when the Bronze codeset arrives as a change feed rather than a full snapshot, the manifest opts into incremental mode. Default is full refresh.
- A separate template notebook handles codeset loads; reuses the same manifest schema with `contractKind: codeset`.

## 10. Notebook Architecture

Three template notebooks under `targets/fabric/notebooks/`:

| Notebook | Drives | Reads manifest? |
|---|---|---|
| `silver-scd2-merge-template.ipynb` | All entity contracts (non-codeset, non-event) | Yes; manifest path is a parameter cell |
| `silver-append-template.ipynb` | All event and transaction contracts | Yes; manifest path is a parameter cell |
| `silver-codeset-load-template.ipynb` | All codeset contracts | Yes; manifest path is a parameter cell |

### 10.1 Parameterization

Each notebook starts with a Fabric parameter cell:

```python
# PARAMETERS
manifest_path = "targets/fabric/manifests/pc/policy/policy.fabric.yaml"
load_mode = "incremental"          # incremental | full | catchup
as_of_datetime = None              # optional override; default is current run datetime
```

Fabric notebook parameters use the standard `# PARAMETERS` cell tag and override the values when the notebook is invoked via REST API or pipeline activity.

### 10.2 Notebook structure

Every template notebook has the same cell layout:

1. Parameter cell.
2. Imports and Spark session config (V-Order, Optimize Write).
3. Manifest load and schema validation (Pydantic-style structural check).
4. Bronze read (with the incremental column predicate from the manifest).
5. Quality pre-assertions (rules with severity `error` that should fail before write).
6. Merge / append / codeset-load body, derived from the manifest.
7. Post-write validation (row counts, current-row uniqueness check, SCD2 window non-overlap check).
8. Optional `OPTIMIZE` and `ZORDER` calls based on manifest hints.
9. Run summary printed for orchestration to capture (rows in, rows inserted, rows superseded, rows soft-deleted, assertion results).

### 10.3 Fabric .ipynb requirements

Per skills-for-fabric:

- Every code cell must include `"outputs": []` and `"execution_count": null` in the `.ipynb` JSON.
- Notebooks emitted by the generator must include `metadata.dependencies.lakehouse` with `default_lakehouse`, `default_lakehouse_name`, and `default_lakehouse_workspace_id` slots that are intentionally left as empty strings; the consumer fills them in at deployment time. The generator does not invent workspace IDs.
- Notebook deployment (Fabric REST API `updateDefinition`) is a consumer concern. This repository ships the notebook content; consumers deploy.

### 10.4 Lakehouse binding metadata

Generator emits a small companion file alongside each generated artifact set:

`targets/fabric/notebooks/lakehouse-binding-template.json` — empty IDs, populated by the consumer.

`targets/fabric/conventions.md` documents how to bind locally and via REST API.

## 11. DDL Generation

Generator emits one Spark SQL `CREATE TABLE` statement per contract under `targets/fabric/ddl/pc/<area>/<slug>.spark.sql`. Each file:

- Declares the Delta table with explicit columns and Spark SQL types from the manifest.
- Sets Delta table properties: `delta.autoOptimize.optimizeWrite`, `delta.autoOptimize.autoCompact`, optional `delta.enableChangeDataFeed`, optional `delta.appendOnly` for event/transaction tables.
- Declares partitioning and ZORDER hints in comments (Spark `OPTIMIZE ... ZORDER` is a runtime concern).
- Includes column comments derived from the ODCS field descriptions.
- Includes a table comment derived from the ODCS contract description plus `Source: pc.<contract-id> v<version>` for traceability.

DDL is provided as a convenience for consumers who wire up an external schema management workflow (e.g. one-off bootstrap, CI checks, schema diffing). The merge notebook does not require pre-existing tables; it creates them on first run if absent. DDL is the audit-friendly representation.

## 12. Purview Integration

Two artifacts under `targets/fabric/purview/`:

### 12.1 sensitivity-labels.json

A JSON manifest in Microsoft Purview's sensitivity label import format. One entry per Delta column with classification, structured as:

```json
{
  "schemaVersion": "1.0",
  "labels": [
    {
      "fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_policy/policy/policy_uid",
      "sensitivityLabel": "Internal",
      "regulatoryTags": [],
      "sourceContract": "pc.policy",
      "sourceContractVersion": "0.2.0"
    },
    {
      "fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_core/party/birth_date",
      "sensitivityLabel": "Restricted",
      "regulatoryTags": ["PII"],
      "sourceContract": "pc.party",
      "sourceContractVersion": "0.2.0"
    }
  ]
}
```

The consumer ingests this file via the Purview REST API or imports it through the Purview UI. The generator does not call Purview; it emits the manifest.

### 12.2 business-glossary.json

A JSON manifest of canonical terms in Purview's business glossary import format. Terms are extracted from the glossary files under `references/glossary/pc/` and from contract / field descriptions. Each term includes:

- Canonical term name.
- Definition.
- Source path (e.g. `references/glossary/pc/policy.md#Policy`).
- Optional list of column FQNs the term applies to.

This artifact is regenerated whenever glossary or contract descriptions change.

### 12.3 HIPAA-aware handling

When a contract has `customProperties.subjectToHipaa: true`, the generator:

- Adds `regulatoryTags: ["PHI"]` to every column whose classification carries `PHI`.
- Annotates the table-level entry with a `complianceProfile: HIPAA` flag.
- Includes a `# HIPAA: requires masking` comment in the merge notebook for columns tagged `PHI`.

## 13. Quality Assertion Strategy

Quality rules in ODCS contracts are projected into the manifest as runtime-evaluable assertions:

- `not_null` rules: implemented in the notebook as a `df.filter(col.isNull()).count() == 0` check.
- `unique` rules (e.g. `single_current_row_per_key`): implemented as a `df.groupBy(key).count().filter("count > 1").count() == 0` check.
- `expression` rules: arbitrary SQL boolean expression evaluated against the dataframe.
- `currency_pair` rules: checked via the manifest's `currencyPair` metadata; whenever the amount column is non-null, the paired currency column must be non-null.
- `accepted_values` rules: derived from codeset cross-references; the value must exist in the referenced codeset's current rows.

Assertion outcomes are captured per rule into a structured run-result dictionary that the notebook prints at the end. Severity `error` fails the run (the notebook raises). Severity `warning` records to the run summary but does not fail. Severity `info` records to the run summary.

The Bronze→Silver run does not write to Silver if any error-severity pre-assertion fails. Post-write assertions run after the merge and a failure marks the run as failed but does not roll back the write; the merge is idempotent and a re-run after a fix produces a clean state.

## 14. Bronze Assumption

The plan assumes Bronze tables exist. The plan does not specify how data lands in Bronze (Fabric Pipelines, Copy activity, OneLake shortcuts, or other ingestion mechanisms — that is upstream).

Default assumptions captured in every manifest's `bronze` block:

- Bronze table name: `bronze.<source>_<table>` with a configurable prefix.
- Incremental column: `_ingested_at` of type `TIMESTAMP`.
- Expected columns: every column in the canonical contract is expected to be present in Bronze with the same name. Columns missing from Bronze are filled with `NULL` if optional and raise a notebook error if required.
- Bronze schema is allowed to carry additional columns; they are dropped at the merge boundary.

The `bronze.table` value in each manifest is a default that the consumer can override via notebook parameters. Manifests are not edited; the override is at run time.

## 15. Generators

### 15.1 generate-fabric-manifests.py

Location: `scripts/generation/generate-fabric-manifests.py`.

Reads: `references/odcs/pc/**/*.odcs.yaml`.

Emits: `targets/fabric/manifests/pc/<area>/<slug>.fabric.yaml`.

Behavior:

- Determines `contractKind` from contract slug (event/transaction list; codeset list; otherwise entity).
- Maps ODCS columns to manifest columns, computing the field role per the role taxonomy.
- Maps ODCS quality rules to manifest assertions, lifting `not_null` and `unique` rules to typed forms where the rule name follows the standard pattern, and falling back to `expression` for the rest.
- Maps `customProperties.classifications` to `purview.sensitivityLabel` using a small allowed-value map (`PUBLIC → Public`, `INTERNAL → Internal`, `CONFIDENTIAL → Confidential`, `RESTRICTED → Restricted`).
- Computes the SHA-256 of the source contract and embeds it as `generation.sourceContractDigest`.
- Idempotent: rerunning produces no diff if no contracts changed.

### 15.2 generate-fabric-ddl.py

Location: `scripts/generation/generate-fabric-ddl.py`.

Reads: `targets/fabric/manifests/pc/**/*.fabric.yaml`.

Emits: `targets/fabric/ddl/pc/<area>/<slug>.spark.sql`.

Behavior:

- Renders one `CREATE TABLE IF NOT EXISTS` statement per manifest.
- Sets Delta table properties from manifest `fabric.table.delta.tableProperties`.
- Emits column comments from manifest column descriptions.
- Emits table comment with source contract id and version.

### 15.3 generate-fabric-purview.py

Location: `scripts/generation/generate-fabric-purview.py`.

Reads: `targets/fabric/manifests/pc/**/*.fabric.yaml` plus `references/glossary/pc/**/*.md`.

Emits:
- `targets/fabric/purview/sensitivity-labels.json` (single consolidated file across the entire contract set).
- `targets/fabric/purview/business-glossary.json` (single consolidated file).

### 15.4 generate-fabric-notebooks.py

Location: `scripts/generation/generate-fabric-notebooks.py`.

Reads: a small set of internal templates under the same script directory.

Emits:
- `targets/fabric/notebooks/silver-scd2-merge-template.ipynb`
- `targets/fabric/notebooks/silver-append-template.ipynb`
- `targets/fabric/notebooks/silver-codeset-load-template.ipynb`
- `targets/fabric/notebooks/lakehouse-binding-template.json`

The notebook generator is intentionally separate from the manifest generator: notebooks do not change per contract, only when the runtime logic changes.

### 15.5 Orchestrator

A thin top-level script `scripts/generation/generate-fabric.py` calls the four generators in order and produces a summary report.

## 16. Manifest Validator

Location: `scripts/validation/validate-fabric-manifests.py`.

Checks listed in section 5.3. Returns non-zero exit code on any drift.

This validator runs alongside the existing `scripts/validation/validate-contracts.py` whenever the canonical surface is changed, so manifests cannot silently drift from contracts.

## 17. Phasing

Each phase ends with a green validator run and a documented checkpoint.

Phase ordering rationale: the data-classification ADR's payoff materializes only when sensitivity labels reach the materialized columns. Purview manifest generation is therefore moved ahead of DDL and notebook work — once manifests exist (F3), the highest-leverage deliverable is sensitivity labels (F4), then DDL (F5), then notebooks (F6). DDL and notebooks both consume the same manifest set, but Purview integration unlocks classification enforcement that DDL and notebooks cannot replace.

### Phase F1 — Conventions and type mapping (docs only)

Deliverables:
- `targets/fabric/README.md`
- `targets/fabric/type-mapping.md`
- `targets/fabric/conventions.md`
- `targets/fabric/manifest-schema.md` (worked schema reference for one example)

Acceptance criteria:
- A new contributor can read these four files and understand the projection without running any tooling.
- All decisions in this plan are reflected.

Estimated scope: 4 documents, ~200-400 lines each.

### Phase F2 — Manifest generator and one example

Deliverables:
- `scripts/generation/generate-fabric-manifests.py`
- `scripts/validation/validate-fabric-manifests.py`
- `targets/fabric/manifests/pc/policy/policy.fabric.yaml` (one manifest emitted as the golden example)

Acceptance criteria:
- Generator runs and produces a manifest that matches the schema in section 5.
- Validator passes the emitted manifest.
- The manifest is human-readable and has no Fabric-specific information that contradicts the source ODCS contract.

Pause for review here. Confirm the manifest shape with the user before generating all 54.

### Phase F3 — Manifest generation for the full contract set

Deliverables:
- 54 manifests under `targets/fabric/manifests/pc/`.

Acceptance criteria:
- All 54 manifests pass the manifest validator.
- All `contractKind` values are correctly classified.
- Spot-checks on at least one contract per kind (entity, codeset, event, transaction) confirm correct field-role assignment.

### Phase F4 — Purview manifests

Deliverables:
- `scripts/generation/generate-fabric-purview.py`
- `targets/fabric/purview/sensitivity-labels.json`
- `targets/fabric/purview/business-glossary.json`

Acceptance criteria:
- Sensitivity manifest has one entry per column across the entire Lakehouse.
- HIPAA-tagged contracts produce PHI-tagged column entries.
- Glossary manifest covers the cross-cutting glossary terms plus area-specific entries with FQN references where applicable.

### Phase F5 — DDL generation

Deliverables:
- `scripts/generation/generate-fabric-ddl.py`
- 54 Spark SQL files under `targets/fabric/ddl/pc/`.

Acceptance criteria:
- Every DDL file is a valid Spark SQL `CREATE TABLE IF NOT EXISTS` statement.
- Column types, nullability, partition keys, and table properties match the manifests.
- DDL files include source-contract traceability comments.

### Phase F6 — Notebook templates

Deliverables:
- Three template notebooks under `targets/fabric/notebooks/`.
- `targets/fabric/notebooks/lakehouse-binding-template.json`.
- `scripts/generation/generate-fabric-notebooks.py`.

Acceptance criteria:
- Each notebook conforms to Fabric `.ipynb` requirements (every code cell has `outputs: []` and `execution_count: null`).
- Each notebook has the canonical cell layout described in section 10.2.
- Notebooks read the manifest path as a parameter and adapt to any contract of the relevant kind.
- A peer review confirms the notebooks would execute on Fabric Spark with a real Bronze input (real execution is a downstream verification).

### Phase F7 — Worked example walkthrough

Deliverables:
- `targets/fabric/examples/end-to-end-policy.md` walks Policy + PolicyTerm + PolicyCoverage + PolicyStatusCode through the full persona flow defined in §3.3.3:
  1. **Architect** edits `references/odcs/pc/policy/policy.odcs.yaml`; validator passes.
  2. **Generator** (`scripts/generation/generate-fabric.py`) regenerates manifest, Purview entries, DDL, and notebook templates; manifest validator confirms no drift.
  3. **Platform engineer** points `spark-authoring-cli` (or an equivalent Fabric deployment tool) at `targets/fabric/`; the skill creates the Silver Lakehouse, applies the four DDL files, deploys the SCD2 / append / codeset notebooks, and populates the lakehouse-binding fields.
  4. **Operator** schedules the deployed notebooks; Bronze data arrives; Silver tables fill.
  5. **Analyst** queries the Silver `policy` and `policy_term` tables via `spark-consumption-cli`.
  6. **Governance** ingests `sensitivity-labels.json` into Purview via REST; classification labels appear on the Lakehouse columns.
- One worked-out merge notebook execution trace (or a structured stub if real execution is not available locally).
- A clear callout that step 3 is consumer-driven: this repository ships the artifacts; `spark-authoring-cli` is one common deployment path; alternatives (Fabric REST API directly, Azure DevOps pipelines, manual notebook upload) are equally valid and the worked example documents the contract Nebula owes the deployer rather than mandating a specific tool.

Acceptance criteria:
- A reader can follow the example and understand each artifact's role and which persona owns each step.
- Each cross-reference resolves to an actual file in the repository.
- The boundary in §3.3 is concrete: the example shows exactly which Nebula files step 3 consumes, and exactly which live-workspace state step 3 produces.

### Phase F8 — Status, planning, validator (closeout)

Deliverables:
- `planning-mds/STATUS.md` updated for W023 closure.
- `planning-mds/IMPLEMENTATION_PLAN.md` updated to reference the completed Fabric milestone.
- `scripts/validation/validate-contracts.py` and `validate-fabric-manifests.py` linked from documentation.
- Top-level `README.md` Modeling References section updated with Fabric target pointers.

Acceptance criteria:
- `planning-mds/STATUS.md` reflects the post-milestone state and lists open follow-ups.
- A new contributor can navigate from the root README to the Fabric target and back.

## 18. Open Questions and Pending Decisions

Decisions deferred until they bite:

1. **Bronze table prefix convention.** Currently `bronze.<source>_<table>`. If multiple Bronze sources land in the same Lakehouse, the prefix may need a source-system component (`bronze.{source_system}.{table}`). Resolved when the consumer wires Bronze.
2. **Catastrophe / large-event correlation across claims.** The current `catastrophe_code` field on `Claim` is a free string. If catastrophes deserve their own canonical entity, this is an ADR follow-up, not a Fabric concern.
3. **Cross-currency reporting in Gold.** Out of scope here; Gold is downstream. Captured for visibility.
4. **Partitioning on event/transaction tables.** Default is `MONTH(valid_from_datetime)`. For very high volume tables, sub-month partitioning may be needed; not chosen until measured.
5. **Notebook idempotency under late-arriving Bronze rows.** Default merge logic handles late arrivals via the SCD2 hash check, but ordering of multiple late events for the same logical key is not guaranteed across runs; documented behavior is "last write wins by `valid_from_datetime`."
6. **Streaming ingestion into Silver.** Out of scope for this milestone; batch only.

## 19. Out of Scope for This Milestone

Per the boundary established in §3.3, several items below are out of scope for *this repository* but are within scope for `microsoft/skills-for-fabric` or upstream Fabric tooling. Each entry is annotated so a reader does not mistake a deliberate boundary for a gap.

- **Gold layer** — aggregates, marts, semantic models, Power BI artifacts. Owned downstream of Silver. Consumers may use `powerbi-authoring-cli` and `powerbi-consumption-cli` from `skills-for-fabric` to author and query Gold artifacts atop the Silver tables this repository's notebooks produce.
- **Bronze ingestion** — connectors, Copy activities, scheduling. Owned upstream of Silver and outside both this repository and the skills repository. Typically handled via Fabric Pipelines, OneLake shortcuts, or third-party ETL.
- **Fabric Warehouse projection (T-SQL native).** Out of scope for this milestone. If a future milestone projects to Warehouse, `sqldw-authoring-cli` from `skills-for-fabric` would be the natural deployment path; the canonical contracts would not change.
- **dbt projection** — canceled per the Fabric-only decision.
- **Semantic projection** — RDF, OWL, knowledge graph. Deferred per W009.
- **Reinsurance, coinsurance, self-insurance, fronting** — deferred per `risk-transfer-scope.md`.
- **Streaming ingestion.** Batch only for this milestone.
- **Real Fabric workspace deployment automation.** This repository ships artifacts; deployment is a consumer responsibility. The intended deployment path is `spark-authoring-cli` from `skills-for-fabric` (and `powerbi-authoring-cli` for any Gold work that follows), but consumers may equally use the Fabric REST API directly, Azure DevOps pipelines, or manual upload. The artifacts conform to Fabric's expected file shapes; the deployment mechanism is not prescribed.
- **Live-workspace operations** (Lakehouse creation, RBAC, capacity assignment, notebook scheduling, Purview REST ingestion). Out of scope here; covered by `skills-for-fabric` skills authenticating via Azure AD.
- **Analyst-facing query tooling.** Out of scope here; covered by `spark-consumption-cli` (Lakehouse) and `powerbi-consumption-cli` (semantic models) from `skills-for-fabric`.
- **Cost or capacity SKU recommendations.** Out of scope.

## 20. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Manifest drift from canonical contracts | `validate-fabric-manifests.py` runs in CI; SHA-256 digest pinning; manifests are never edited by hand |
| Generator produces invalid `.ipynb` | Notebook generator emits and validates the JSON shape; integration smoke test asserts cells contain `outputs: []` and `execution_count: null` |
| Spark SQL type drift across Fabric runtime versions | Type mapping is centralized in one document; quarterly review noted as a follow-up |
| Bronze schema does not match expectations | Quality assertions in the merge notebook fail loudly with column-level diff before any write |
| Codeset values reference unknown codes | Post-merge assertion checks every `code-reference` value exists in the referenced codeset's current rows |
| Lakehouse-binding metadata diverges per environment | Generator leaves the IDs blank; `lakehouse-binding-template.json` is filled per environment; binding choice is captured in environment config, not in this repo |
| Notebooks become stale when canonical conventions evolve | Notebook generator is regenerated when conventions change; templates carry their own `templateVersion` annotation that the manifest validator checks |

## 21. Reference Implementation Index

When the milestone is complete the following file map describes the Fabric target:

```text
targets/fabric/
  README.md                                  # purpose, scope, navigation
  type-mapping.md                            # ODCS → Spark SQL types
  conventions.md                             # naming, materialization, runtime conventions
  manifest-schema.md                         # full manifest schema reference
  manifests/
    pc/
      <area>/<slug>.fabric.yaml              # 54 manifests
  ddl/
    pc/
      <area>/<slug>.spark.sql                # 54 DDL files
  notebooks/
    silver-scd2-merge-template.ipynb         # entity contract merge
    silver-append-template.ipynb             # event/transaction append
    silver-codeset-load-template.ipynb       # codeset load
    lakehouse-binding-template.json          # consumer fills in IDs
  purview/
    sensitivity-labels.json                  # column-level Purview manifest
    business-glossary.json                   # canonical terms manifest
  examples/
    end-to-end-policy.md                     # worked walkthrough

scripts/
  generation/
    generate-fabric.py                       # orchestrator
    generate-fabric-manifests.py             # ODCS → manifests
    generate-fabric-ddl.py                   # manifests → DDL
    generate-fabric-notebooks.py             # template notebooks
    generate-fabric-purview.py               # manifests + glossary → Purview JSON
  validation/
    validate-fabric-manifests.py             # drift detection
```
