# End-to-End Walkthrough: Claim + ClaimFeature + ClaimLifecycleEvent + ClaimFinancialTransaction + ClaimStatusCode + FinancialTransactionClassification

This walkthrough traces six canonical contracts — `pc.claim` (entity), `pc.claim-feature` (entity), `pc.claim-lifecycle-event` (append-only event), `pc.claim-financial-transaction` (append-only transaction), `pc.claim-status-code` (codeset), and `pc.financial-transaction-classification` (codeset / richer reference data) — through every step of the Fabric persona flow from `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` §3.3.3.

The point of this example is to make the canonical-to-Fabric flow concrete on the **append-only** side of the canonical surface. The companion policy walkthrough (`end-to-end-policy.md`) covers SCD2 entity merges and codeset SCD2 loads. This walkthrough adds:

- An append-only **event** table (`claim_lifecycle_event`) with `correction_indicator` / `corrects_*_uid` semantics.
- An append-only **transaction** table (`claim_financial_transaction`) that cross-references the event table via `lifecycle_event_uid` (the `lifecycle-event-link` role from `targets/fabric/manifest-schema.md` §5.2).
- A child entity (`claim_feature`) that partitions a claim into independent handling streams — exercising a non-trivial entity dependency that is not a simple lookup.
- The C4.5 commercial-lines spine showing as one-hop FK paths from `claim` (`account_uid` from C4.5; `occurrence_uid` and `catastrophe_uid` from C4.1 / C4.2; `insurable_object_uid` from C4.4). The walkthrough does not load the spine entities, but it does show how queries traverse them.

Together the six contracts exercise SCD2 entity merge, codeset SCD2 load, append-only event insert with correction handling, append-only transaction insert with cross-reference resolution, and Purview projection on FINANCIAL-tagged amounts and PII-tagged narratives — the parts of the Silver surface the policy walkthrough deliberately leaves out.

---

## 1. Persona flow at a glance

| Step | Persona | Tool / repo | Outcome |
|---|---|---|---|
| 1 | Insurance data architect | This repo | Edit ODCS contract, run validator, commit. |
| 2 | CI or local generator run | This repo | Regenerate manifest + DDL + Purview JSON; manifest validator confirms no drift. |
| 3 | Platform engineer | Deployer's choice (`spark-authoring-cli`, Fabric REST API, Azure DevOps pipeline, manual upload) | Create / update Lakehouse, apply DDL, deploy notebooks, populate lakehouse binding. |
| 4 | Operator | Fabric workspace UI or pipeline | Schedule deployed notebooks against Bronze; Silver tables fill. |
| 5 | Analyst | Spark / SQL client (`spark-consumption-cli` or any) | Query the Silver tables produced by the SCD2 / append / codeset notebooks. |
| 6 | Governance | Purview UI or REST API | Ingest `sensitivity-labels.json` and `business-glossary.json`; classification labels appear on the Lakehouse columns. |

The persona flow is identical to the policy walkthrough — only the contracts and the materialization shapes differ. Step 3 is the only step where this repository and a deployment tool meet.

---

## 2. The six contracts

| Contract | Path | Kind | Version | Spark table | Schema |
|---|---|---|---|---|---|
| Claim | `references/odcs/pc/claims/claim.odcs.yaml` | entity | 0.4.2 | `claim` | `silver_claims` |
| ClaimFeature | `references/odcs/pc/claims/claim-feature.odcs.yaml` | entity | 0.3.1 | `claim_feature` | `silver_claims` |
| ClaimLifecycleEvent | `references/odcs/pc/claims/claim-lifecycle-event.odcs.yaml` | event (append-only) | 0.1.1 | `claim_lifecycle_event` | `silver_claims` |
| ClaimFinancialTransaction | `references/odcs/pc/claims/claim-financial-transaction.odcs.yaml` | transaction (append-only) | 0.1.1 | `claim_financial_transaction` | `silver_claims` |
| ClaimStatusCode | `references/odcs/pc/reference-data/claim-status-code.odcs.yaml` | codeset | 0.4.0 | `claim_status_code` | `silver_reference_data` |
| FinancialTransactionClassification | `references/odcs/pc/reference-data/financial-transaction-classification.odcs.yaml` | codeset | 0.1.1 | `financial_transaction_classification` | `silver_reference_data` |

Note the schema choice: even though `pc.financial-transaction-classification` carries `customProperties.subjectArea: financial`, every codeset materialises to `silver_reference_data` per the F3 closeout decision. The `silver_financial` schema is reserved for non-codeset financial contracts (`financial_transaction`, `policy_financial_transaction`).

Dependency graph the deployer sees in Silver:

```text
silver_reference_data.claim_status_code (codeset)              silver_reference_data.financial_transaction_classification (codeset)
        ▲                                                                    ▲
        │ codeReference: claim_status_code → code_value                      │ codeReference: transaction_classification_code → code_value
        │                                                                    │
silver_claims.claim ─────────► silver_claims.claim_feature ────►  silver_claims.claim_lifecycle_event (append-only)
                                                                              ▲
                                                                              │ lifecycle_event_uid (lifecycle-event-link role)
                                                                              │
                                                                              silver_claims.claim_financial_transaction (append-only)

(out-of-scope sibling FKs from claim: pc.policy, pc.policy-coverage, pc.exposure, pc.insurable-object,
 pc.occurrence, pc.catastrophe, pc.account, pc.geographic-location)
```

Two patterns the policy walkthrough did not surface:

- **Append-only contracts have no SCD2 fields.** `claim_lifecycle_event` and `claim_financial_transaction` carry `correction_indicator` and `corrects_*_uid`; they do not carry `valid_from_datetime` / `valid_to_datetime` / `is_current_indicator`. A correction is a new row, not an SCD2 close-and-insert.
- **Cross-reference between event and transaction.** `claim_financial_transaction.lifecycle_event_uid` is the `lifecycle-event-link` role per the `event-and-transaction.md` ADR — a transaction is the processed-activity counterpart of the lifecycle event that authorized it. Post-write assertions check that the link resolves whenever populated.

---

## 3. Step 1 — Architect edits the canonical contract

The architect is the only persona who hand-authors files in this flow. Everything below the ODCS layer is generated.

A representative Step 1 change: adding a new financial-transaction classification `LITIGATION_EXPENSE_RESERVE` to support a defense-counsel-specific reserve bucket that the carrier wants to track separately from generic `RESERVE_EXPENSE`.

```yaml
# references/odcs/pc/reference-data/financial-transaction-classification.odcs.yaml
# (excerpt — the field list does not change because codesets carry rows, not new columns)

description: Canonical codeset for the secondary classification of financial transactions, used by
  analytics and reporting to roll up transactions across policy and claim sides (INDEMNITY, EXPENSE_ALAE,
  EXPENSE_ULAE, RESERVE_INDEMNITY, RESERVE_EXPENSE, LITIGATION_EXPENSE_RESERVE, WRITTEN_PREMIUM,
  EARNED_PREMIUM, COMMISSION_BASE, etc.).
version: 0.1.2
customProperties:
  changelog:
  - '0.1.2: Added LITIGATION_EXPENSE_RESERVE classification for defense-counsel reserves tracked
    separately from generic expense reserves (architect, 2026-05-07).'
```

The architect does not invent a Spark table, a Purview label, or a notebook. The contract layer carries `description`, `version`, `changelog`, `classifications`, and `adrs`; everything Fabric-specific is derived.

After saving, the architect runs the canonical validator:

```bash
python scripts/validation/validate-contracts.py
```

Expected output: `0 errors`, `0 warnings`, `85 contracts validated`. A failure here blocks the rest of the flow; the architect fixes the contract before moving on.

The change is a MINOR-level addition under `versioning-policy.md` (widening allowed values in a referenced codeset), but the contract is at `0.1.x` so the patch-bump form `0.1.1 → 0.1.2` is what actually ships — pre-stable contracts version more loosely, with breaking changes still recorded in the changelog. M10.5 codifies the manifest-version surface alongside this rule.

---

## 4. Step 2 — Generators regenerate every Fabric artifact

The orchestrator runs every generator in dependency order:

```bash
python scripts/generation/generate-fabric.py
```

Or, if the deployer wants to run the four steps individually for diagnostics:

```bash
python scripts/generation/generate-fabric-manifests.py
python scripts/generation/generate-fabric-purview.py
python scripts/generation/generate-fabric-ddl.py
python scripts/generation/generate-fabric-notebooks.py
python scripts/validation/validate-fabric-manifests.py --require-full-coverage
```

Each generator is idempotent: re-running with no canonical change produces no diff. The drift validator at the end catches every form of manifest-vs-contract mismatch (path, id, version, digest, kind, role coverage, type allow-list, FK and codeReference resolution, currency-pair consistency, ADR id resolution).

### 4.1 Manifest excerpts

Three manifests are worth showing in detail because they exercise the three materialization shapes the policy walkthrough did not.

**Append-only event manifest** (`silver_claims.claim_lifecycle_event`):

```yaml
# targets/fabric/manifests/pc/claims/claim-lifecycle-event.fabric.yaml (excerpt)
manifestVersion: 1.0.0
contract:
  id: pc.claim-lifecycle-event
  name: ClaimLifecycleEvent
  version: 0.1.1
  contractKind: event
  classificationProfile: CONFIDENTIAL
  subjectToHipaa: false
fabric:
  lakehouse: nebula_pc_silver
  schema: silver_claims
  table:
    name: claim_lifecycle_event
    delta:
      tableProperties:
        delta.appendOnly: true                # append-only mode is mutually exclusive with SCD2
        delta.autoOptimize.optimizeWrite: true
        delta.autoOptimize.autoCompact: true
        delta.enableChangeDataFeed: true
      partitionedBy: [event_datetime]         # business time, not SCD2 system time
      zorderBy: []                            # not emitted on append-only tables
  columns:
    - {name: claim_lifecycle_event_uid, sparkType: STRING, role: identity, primaryKey: true}
    - {name: claim_uid, sparkType: STRING, role: foreign-key,
       foreignKey: {targetContract: pc.claim, targetTable: silver_claims.claim, targetField: claim_uid}}
    - {name: claim_feature_uid, sparkType: STRING, role: foreign-key,
       foreignKey: {targetContract: pc.claim-feature, targetTable: silver_claims.claim_feature,
                    targetField: claim_feature_uid}}
    - {name: lifecycle_event_type_code, sparkType: STRING, role: code-reference,
       codeReference: {codeset: pc.lifecycle-event-type,
                       codesetTable: silver_reference_data.lifecycle_event_type,
                       codesetField: code_value}}
    - {name: event_datetime, sparkType: TIMESTAMP, role: data}    # business time, not SCD2 system time
    - {name: event_narrative, sparkType: STRING, role: data,
       classifications: {sensitivity: CONFIDENTIAL, regulatoryTags: [PII]},
       purview: {sensitivityLabel: Confidential}}
    - {name: correction_indicator, sparkType: BOOLEAN, role: event-correction-flag, nullable: false}
    - {name: corrects_claim_lifecycle_event_uid, sparkType: STRING, role: event-corrects-ref,
       nullable: true}
    # ... 4 more columns
  scd2: {enabled: false}                      # mutually exclusive with appendOnly
  recordState: {enabled: false}               # not present on append-only contracts
  appendOnly:
    enabled: true
    correctionIndicator: correction_indicator
    correctsRefField: corrects_claim_lifecycle_event_uid
    businessTimeField: event_datetime
    partitionExpression: MONTH(event_datetime)
  bronze: {table: bronze.claim_lifecycle_event_raw, incrementalColumn: _ingested_at}
generation:
  sourceContractDigest: sha256:6112eb049b9137bb1dbbbf5fb3d155c48d755fe3128cde33af0834695424ce04
```

**Append-only transaction manifest with lifecycle-event-link** (`silver_claims.claim_financial_transaction`):

```yaml
# targets/fabric/manifests/pc/claims/claim-financial-transaction.fabric.yaml (excerpt)
manifestVersion: 1.0.0
contract:
  id: pc.claim-financial-transaction
  name: ClaimFinancialTransaction
  version: 0.1.1
  contractKind: transaction
  classificationProfile: CONFIDENTIAL
fabric:
  lakehouse: nebula_pc_silver
  schema: silver_claims
  table:
    name: claim_financial_transaction
    delta:
      tableProperties:
        delta.appendOnly: true
        delta.enableChangeDataFeed: true
      partitionedBy: [transaction_effective_date]
  columns:
    - {name: claim_financial_transaction_uid, sparkType: STRING, role: identity, primaryKey: true}
    - {name: claim_uid, sparkType: STRING, role: foreign-key,
       foreignKey: {targetContract: pc.claim, targetTable: silver_claims.claim,
                    targetField: claim_uid}}
    - {name: claim_feature_uid, sparkType: STRING, role: foreign-key,
       foreignKey: {targetContract: pc.claim-feature,
                    targetTable: silver_claims.claim_feature,
                    targetField: claim_feature_uid}}
    - {name: transaction_type_code, sparkType: STRING, role: code-reference,
       codeReference: {codeset: pc.transaction-type,
                       codesetTable: silver_reference_data.transaction_type,
                       codesetField: code_value}}
    - {name: transaction_classification_code, sparkType: STRING, role: code-reference,
       codeReference: {codeset: pc.financial-transaction-classification,
                       codesetTable: silver_reference_data.financial_transaction_classification,
                       codesetField: code_value}}
    - {name: transaction_amount, sparkType: DECIMAL(18, 2), role: monetary-amount,
       classifications: {sensitivity: CONFIDENTIAL, regulatoryTags: [FINANCIAL]},
       purview: {sensitivityLabel: Confidential},
       currencyPair: {pairedColumn: transaction_currency_code}}
    - {name: transaction_currency_code, sparkType: STRING, role: monetary-currency,
       codeReference: {codeset: pc.currency-code,
                       codesetTable: silver_reference_data.currency_code,
                       codesetField: code_value}}
    - {name: lifecycle_event_uid, sparkType: STRING, role: lifecycle-event-link,
       foreignKey: {targetContract: pc.claim-lifecycle-event,
                    targetTable: silver_claims.claim_lifecycle_event,
                    targetField: claim_lifecycle_event_uid}}
    - {name: correction_indicator, sparkType: BOOLEAN, role: event-correction-flag, nullable: false}
    - {name: corrects_claim_financial_transaction_uid, sparkType: STRING,
       role: event-corrects-ref, nullable: true}
    # ... 6 more columns including transaction_narrative (Confidential + PII)
  appendOnly:
    enabled: true
    correctionIndicator: correction_indicator
    correctsRefField: corrects_claim_financial_transaction_uid
    businessTimeField: transaction_effective_date
generation:
  sourceContractDigest: sha256:a542b8ede5d57aa9879d11b044997ba4fede56d0b266d7007da981e6df70989a
```

The `lifecycle-event-link` role on `lifecycle_event_uid` is the same FK shape as `foreign-key`, but the manifest validator additionally requires the target to be an event contract — a transaction can link an event but not another transaction. This was C1's contribution to the role taxonomy.

**Entity manifest with C4.5 + C4.1 + C4.2 + C4.4 FKs** (`silver_claims.claim`):

```yaml
# targets/fabric/manifests/pc/claims/claim.fabric.yaml (excerpt)
manifestVersion: 1.0.0
contract: {id: pc.claim, version: 0.4.2, contractKind: entity, classificationProfile: CONFIDENTIAL}
fabric:
  lakehouse: nebula_pc_silver
  schema: silver_claims
  table: {name: claim}
  columns:
    - {name: claim_uid, role: identity, primaryKey: true}
    - {name: policy_uid, role: foreign-key,
       foreignKey: {targetContract: pc.policy, targetTable: silver_policy.policy}}
    - {name: policy_coverage_uid, role: foreign-key,
       foreignKey: {targetContract: pc.policy-coverage, targetTable: silver_coverage.policy_coverage}}
    - {name: exposure_uid, role: foreign-key,
       foreignKey: {targetContract: pc.exposure, targetTable: silver_exposure.exposure}}
    - {name: insurable_object_uid, role: foreign-key,                  # C4.4: one-hop to insured object
       foreignKey: {targetContract: pc.insurable-object,
                    targetTable: silver_exposure.insurable_object}}
    - {name: occurrence_uid, role: foreign-key,                        # C4.1
       foreignKey: {targetContract: pc.occurrence, targetTable: silver_claims.occurrence}}
    - {name: catastrophe_uid, role: foreign-key,                       # C4.2 (replaces free-string code)
       foreignKey: {targetContract: pc.catastrophe, targetTable: silver_claims.catastrophe}}
    - {name: account_uid, role: foreign-key,                           # C4.5: one-hop to account
       foreignKey: {targetContract: pc.account, targetTable: silver_core.account}}
    - {name: claim_description, sparkType: STRING, role: data,
       classifications: {sensitivity: CONFIDENTIAL, regulatoryTags: [PII]}}
    # ... SCD2 + record-state + claim-specific data fields
  scd2: {enabled: true, naturalKey: [claim_uid], deletionAware: false}
  recordState: {enabled: true, field: record_status_code,
                activeValue: ACTIVE, supersededValue: SUPERSEDED, softDeletedValue: SOFT_DELETED}
generation:
  sourceContractDigest: sha256:0971f733fa4d0fa2a010e22f8990a1c20673f89ae3ddba7f4673f3319c64734e
```

The remaining three manifests in this walkthrough (`claim_feature`, `claim_status_code`, `financial_transaction_classification`) follow the same patterns — `claim_feature` is an SCD2 entity with one FK to `claim` and codeReferences for `feature_status_code` and `cause_of_loss_code`; the two codesets are pure SCD2 reference data with `code_value` / `code_label` plus the standard SCD2 + recordState blocks.

Files emitted for the six contracts:

```text
targets/fabric/manifests/pc/claims/claim.fabric.yaml
targets/fabric/manifests/pc/claims/claim-feature.fabric.yaml
targets/fabric/manifests/pc/claims/claim-lifecycle-event.fabric.yaml
targets/fabric/manifests/pc/claims/claim-financial-transaction.fabric.yaml
targets/fabric/manifests/pc/reference-data/claim-status-code.fabric.yaml
targets/fabric/manifests/pc/reference-data/financial-transaction-classification.fabric.yaml
```

### 4.2 DDL excerpt for an append-only event

The append-only DDL is the most distinctive output of this walkthrough; the SCD2 entity DDL has the same shape the policy walkthrough already showed. The key differences from the entity DDL are `delta.appendOnly = 'true'`, `PARTITIONED BY (event_datetime)`, and the absence of any `OPTIMIZE … ZORDER BY` advisory comment.

```sql
-- targets/fabric/ddl/pc/claims/claim-lifecycle-event.spark.sql (excerpt)
CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_claims.claim_lifecycle_event (
  claim_lifecycle_event_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID...',
  claim_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the claim associated with the event.',
  claim_feature_uid STRING COMMENT 'Identifier (GUID reference) for the claim feature...',
  lifecycle_event_type_code STRING NOT NULL COMMENT 'Classification of the lifecycle event...',
  event_datetime TIMESTAMP NOT NULL COMMENT 'Datetime when the event occurred or was recognized.',
  effective_date DATE COMMENT 'Business-effective date for the event...',
  actor_party_uid STRING COMMENT 'Identifier (GUID reference) for the party that performed or owned the event...',
  reason_code STRING COMMENT 'Classification of the reason for the event when applicable.',
  event_narrative STRING COMMENT 'Source-neutral narrative describing the event when additional context is needed.',
  triggering_transaction_uid STRING COMMENT 'Optional reference to the transaction that produced this lifecycle event...',
  correction_indicator BOOLEAN NOT NULL COMMENT 'True when this row corrects a previously emitted row...',
  corrects_claim_lifecycle_event_uid STRING COMMENT 'Reference to the prior row that this row corrects...'
)
USING DELTA
PARTITIONED BY (event_datetime)
COMMENT 'Append-only canonical record of a business-meaningful state change in the claim history... Source: pc.claim-lifecycle-event v0.1.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- (no OPTIMIZE ... ZORDER advisory; per conventions.md §7, ZORDER is skipped on append-only tables.)
```

`claim_financial_transaction.spark.sql` follows the same shape, partitioned by `transaction_effective_date`.

Files emitted for the six contracts:

```text
targets/fabric/ddl/pc/claims/claim.spark.sql
targets/fabric/ddl/pc/claims/claim-feature.spark.sql
targets/fabric/ddl/pc/claims/claim-lifecycle-event.spark.sql
targets/fabric/ddl/pc/claims/claim-financial-transaction.spark.sql
targets/fabric/ddl/pc/reference-data/claim-status-code.spark.sql
targets/fabric/ddl/pc/reference-data/financial-transaction-classification.spark.sql
```

### 4.3 Purview JSON excerpt

The two consolidated Purview files cover all 85 contracts (1235 column entries + 85 table entries + 308 glossary terms). The excerpts below are filtered to the six tables in this walkthrough:

```jsonc
// targets/fabric/purview/sensitivity-labels.json (filtered)
{
  "schemaVersion": "1.0",
  "lakehouse": "nebula_pc_silver",
  "tables": [
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_claims/claim",
     "purviewLabel": "Confidential", "classificationProfile": "CONFIDENTIAL",
     "sourceContract": "pc.claim", "sourceContractVersion": "0.4.2"},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_claims/claim_feature",
     "purviewLabel": "Internal", "classificationProfile": "INTERNAL",
     "sourceContract": "pc.claim-feature", "sourceContractVersion": "0.3.1"},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_claims/claim_lifecycle_event",
     "purviewLabel": "Confidential", "classificationProfile": "CONFIDENTIAL",
     "sourceContract": "pc.claim-lifecycle-event", "sourceContractVersion": "0.1.1"},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_claims/claim_financial_transaction",
     "purviewLabel": "Confidential", "classificationProfile": "CONFIDENTIAL",
     "sourceContract": "pc.claim-financial-transaction", "sourceContractVersion": "0.1.1"},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_reference_data/claim_status_code",
     "purviewLabel": "Public", "classificationProfile": "PUBLIC",
     "sourceContract": "pc.claim-status-code", "sourceContractVersion": "0.4.0"},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_reference_data/financial_transaction_classification",
     "purviewLabel": "Public", "classificationProfile": "PUBLIC",
     "sourceContract": "pc.financial-transaction-classification", "sourceContractVersion": "0.1.2"}
  ],
  "labels": [
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_claims/claim/claim_uid",
     "sensitivityLabel": "Internal", "regulatoryTags": []},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_claims/claim/claim_description",
     "sensitivityLabel": "Confidential", "regulatoryTags": ["PII"]},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_claims/claim_lifecycle_event/event_narrative",
     "sensitivityLabel": "Confidential", "regulatoryTags": ["PII"]},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_claims/claim_financial_transaction/transaction_amount",
     "sensitivityLabel": "Confidential", "regulatoryTags": ["FINANCIAL"]},
    {"fullyQualifiedName": "Lakehouse://nebula_pc_silver/Tables/silver_claims/claim_financial_transaction/transaction_narrative",
     "sensitivityLabel": "Confidential", "regulatoryTags": ["PII"]}
    // ... ~80 more column entries for these six tables
  ]
}
```

Three of the six tables are CONFIDENTIAL — `claim` (because of `claim_description` PII), `claim_lifecycle_event` (`event_narrative` PII), `claim_financial_transaction` (`transaction_amount` FINANCIAL plus `transaction_narrative` PII). `claim_feature` is INTERNAL — no narrative, no monetary amount. The two codesets are PUBLIC.

`subjectToHipaa` is false for all six contracts; no `complianceProfile: HIPAA` flag, no PHI columns. The wiring is in place if a future contract flips the flag.

The glossary entry for `Source System Code` lists 38 column FQNs across the lakehouse, including `silver_claims/claim/source_system_code`, `silver_claims/claim_feature/source_system_code`, and `silver_claims/claim_financial_transaction/source_system_code`. The Purview UI shows the term linked to those columns automatically once the JSON is ingested.

### 4.4 Notebook templates

For this walkthrough the deployer uses all three template notebooks:

| Contract | Template |
|---|---|
| `pc.claim`, `pc.claim-feature` | `silver-scd2-merge-template.ipynb` |
| `pc.claim-lifecycle-event`, `pc.claim-financial-transaction` | `silver-append-template.ipynb` |
| `pc.claim-status-code`, `pc.financial-transaction-classification` | `silver-codeset-load-template.ipynb` |

A single deployed copy of each template runs against every contract of its kind. The append template's mechanic — insert with `correction_indicator` resolution — is the same regardless of whether it is fed an event or a transaction; the manifest's `appendOnly.businessTimeField` and `correctsRefField` are the per-contract knobs.

### 4.5 Drift control

The closing step of the generator run:

```bash
$ python scripts/validation/validate-fabric-manifests.py --require-full-coverage
Validated 85 manifests across 8 schemas: 0 errors.
```

For the codeset edit in §3, the `claim-financial-transaction.fabric.yaml` digest is recomputed (because every transaction whose `transaction_classification_code` may now reference `LITIGATION_EXPENSE_RESERVE` shares an `accepted_values` rule against `pc.financial-transaction-classification@0.1.2`); the manifest's `contract.version` for `pc.financial-transaction-classification` updates to `0.1.2`; the codeset's own `sourceContractDigest` recomputes. No other manifest moves.

---

## 5. Step 3 — Platform engineer deploys to Fabric

Step 3 is consumer-driven, identical to the policy walkthrough. The artifact bundle for the six-contract walkthrough:

```text
# DDL applied to the Lakehouse:
targets/fabric/ddl/pc/reference-data/claim-status-code.spark.sql
targets/fabric/ddl/pc/reference-data/financial-transaction-classification.spark.sql
targets/fabric/ddl/pc/claims/claim.spark.sql
targets/fabric/ddl/pc/claims/claim-feature.spark.sql
targets/fabric/ddl/pc/claims/claim-lifecycle-event.spark.sql
targets/fabric/ddl/pc/claims/claim-financial-transaction.spark.sql

# Notebooks deployed (one copy of each template):
targets/fabric/notebooks/silver-codeset-load-template.ipynb
targets/fabric/notebooks/silver-scd2-merge-template.ipynb
targets/fabric/notebooks/silver-append-template.ipynb

# Lakehouse binding the deployer fills in:
targets/fabric/notebooks/lakehouse-binding-template.json

# Purview JSON ingested via Purview REST API or UI:
targets/fabric/purview/sensitivity-labels.json
targets/fabric/purview/business-glossary.json
```

Common deployment paths: `spark-authoring-cli` (`microsoft/skills-for-fabric`); Fabric REST API directly; Azure DevOps pipeline; manual upload. The deployer-choice matrix from `end-to-end-policy.md` §5 applies unchanged. This repository ships file artifacts; the deployment mechanism is not prescribed.

---

## 6. Step 4 — Operator runs the loads

Run order matters more here than in the policy walkthrough because the dependency graph has more edges. The six-step order:

```text
1. silver-codeset-load-template.ipynb     manifest_path=.../claim-status-code.fabric.yaml
2. silver-codeset-load-template.ipynb     manifest_path=.../financial-transaction-classification.fabric.yaml
3. silver-scd2-merge-template.ipynb       manifest_path=.../claim.fabric.yaml
4. silver-scd2-merge-template.ipynb       manifest_path=.../claim-feature.fabric.yaml
5. silver-append-template.ipynb           manifest_path=.../claim-lifecycle-event.fabric.yaml
6. silver-append-template.ipynb           manifest_path=.../claim-financial-transaction.fabric.yaml
```

Why this order:

- Codesets load first so the entity merges' post-write `accepted_values` assertions resolve.
- `claim` loads before `claim_feature` because `claim_feature.claim_uid` references `claim.claim_uid`.
- `claim_lifecycle_event` loads before `claim_financial_transaction` because `claim_financial_transaction.lifecycle_event_uid` references `claim_lifecycle_event.claim_lifecycle_event_uid` (the `lifecycle-event-link` role).

All six runs use the same parameter cell shape:

```python
# PARAMETERS
manifest_path = "targets/fabric/manifests/pc/claims/claim_lifecycle_event.fabric.yaml"
load_mode = "incremental"          # incremental | full | catchup
as_of_datetime = None              # default is current run datetime
bronze_prefix_override = None      # default uses manifest's bronze.table prefix
run_optimize = False
optimize_min_rows = 1000000
```

### 6.1 Worked-out execution traces (structured stubs)

Real Spark execution is a downstream verification, not a generation-time step. The traces below are the structured run-summary shapes the notebook prints to stdout at the end of cell 11 — the same `SHARED_RUN_SUMMARY_SOURCE` from `scripts/generation/generate-fabric-notebooks.py` that the policy walkthrough exercises. The orchestrator parses the same JSON regardless of contract.

Step 6.1 — load `claim_status_code` (codeset, full refresh):

```jsonc
{
  "contractId": "pc.claim-status-code",
  "contractKind": "codeset",
  "table": "nebula_pc_silver.silver_reference_data.claim_status_code",
  "loadMode": "full",
  "rowsRead": 7, "rowsInserted": 7,
  "rowsSuperseded": 0, "rowsSoftDeleted": 0, "rowsCorrected": 0,
  "assertions": [
    {"id": "claim_status_code_uid_required",  "type": "not_null",   "ok": true, "severity": "error"},
    {"id": "code_value_required",             "type": "not_null",   "ok": true, "severity": "error"},
    {"id": "single_current_row_per_key",      "type": "unique",     "ok": true, "severity": "error"},
    {"id": "valid_window_consistent",         "type": "expression", "ok": true, "severity": "error"}
  ],
  "status": "ok"
}
```

Step 6.2 — load `financial_transaction_classification` (codeset, full refresh). The new `LITIGATION_EXPENSE_RESERVE` row from the architect's Step 1 edit lights up here:

```jsonc
{
  "contractId": "pc.financial-transaction-classification",
  "contractKind": "codeset",
  "loadMode": "full",
  "rowsRead": 12, "rowsInserted": 1,        // 11 prior rows already current; 1 new row
  "rowsSuperseded": 0, "rowsSoftDeleted": 0, "rowsCorrected": 0,
  "assertions": [
    {"id": "code_value_required",        "type": "not_null", "ok": true, "severity": "error"},
    {"id": "single_current_row_per_key", "type": "unique",   "ok": true, "severity": "error"}
  ],
  "status": "ok",
  "note": "1 new row: LITIGATION_EXPENSE_RESERVE"
}
```

Step 6.3 — merge `claim` (entity, incremental). Standard SCD2 close-and-insert for any claim with a status change since the last run:

```jsonc
{
  "contractId": "pc.claim",
  "contractKind": "entity",
  "table": "nebula_pc_silver.silver_claims.claim",
  "loadMode": "incremental",
  "rowsRead": 4218, "rowsInserted": 3915,    // 3667 brand-new + 248 SCD2 changes
  "rowsSuperseded": 248,                     // closed by the change-detection hash
  "rowsSoftDeleted": 0, "rowsCorrected": 0,
  "assertions": [
    {"id": "claim_status_code_in_codeset",            "type": "accepted_values", "ok": true, "severity": "error"},
    {"id": "claim_type_code_in_codeset",              "type": "accepted_values", "ok": true, "severity": "error"},
    {"id": "claim_closed_date_not_before_opened_date","type": "expression",      "ok": true, "severity": "error"},
    {"id": "claim_insurable_object_path_consistent",  "type": "expression",      "ok": true, "severity": "error"},
    {"id": "claim_reported_datetime_not_before_loss_date", "type": "expression", "ok": true, "severity": "warning"}
  ],
  "status": "ok"
}
```

Step 6.4 — merge `claim_feature` (entity, incremental). Same shape; smaller volume because most claims have a single feature.

Step 6.5 — append `claim_lifecycle_event` (event, incremental). One correction row in this batch — a prior `RESERVE_CHANGE` event is being corrected because the original feature attribution was wrong:

```jsonc
{
  "contractId": "pc.claim-lifecycle-event",
  "contractKind": "event",
  "table": "nebula_pc_silver.silver_claims.claim_lifecycle_event",
  "loadMode": "incremental",
  "rowsRead": 8412, "rowsInserted": 8412,
  "rowsSuperseded": 0, "rowsSoftDeleted": 0,
  "rowsCorrected": 1,                        // one row carries correction_indicator = true
  "assertions": [
    {"id": "claim_lifecycle_event_claim_uid_required",  "type": "not_null", "ok": true, "severity": "error"},
    {"id": "claim_lifecycle_event_type_code_required",  "type": "not_null", "ok": true, "severity": "error"},
    {"id": "lifecycle_event_type_code_in_codeset",      "type": "accepted_values", "ok": true, "severity": "error"},
    {"id": "correction_indicator_required",             "type": "not_null", "ok": true, "severity": "error"},
    {"id": "corrects_claim_lifecycle_event_uid_resolves",
     "type": "expression", "ok": true, "severity": "error",
     "note": "1 correction row; corrects_claim_lifecycle_event_uid resolves to a prior row in the table."}
  ],
  "status": "ok"
}
```

Append-only mechanics worth highlighting: `rowsRead` and `rowsInserted` are equal (no SCD2 supersession on append-only tables), and the correction row is counted under `rowsCorrected` independently of `rowsInserted`. The original (corrected) row is **not** updated — append-only rows are immutable. Downstream consumers reconstruct the latest claimed view by filtering `correction_indicator = false UNION (correction_indicator = true and is the latest correction for the corrected uid)`.

Step 6.6 — append `claim_financial_transaction` (transaction, incremental). One transaction in this batch carries `transaction_classification_code = 'LITIGATION_EXPENSE_RESERVE'` (the new code from Step 1), and one transaction is a correction:

```jsonc
{
  "contractId": "pc.claim-financial-transaction",
  "contractKind": "transaction",
  "table": "nebula_pc_silver.silver_claims.claim_financial_transaction",
  "loadMode": "incremental",
  "rowsRead": 12653, "rowsInserted": 12653,
  "rowsSuperseded": 0, "rowsSoftDeleted": 0, "rowsCorrected": 1,
  "assertions": [
    {"id": "claim_financial_transaction_amount_required",  "type": "not_null", "ok": true, "severity": "error"},
    {"id": "claim_financial_transaction_currency_required","type": "not_null", "ok": true, "severity": "error"},
    {"id": "transaction_amount_currency_pair",
     "type": "currency_pair", "ok": true, "severity": "error"},
    {"id": "transaction_type_code_in_codeset",
     "type": "accepted_values", "ok": true, "severity": "error"},
    {"id": "transaction_classification_code_in_codeset",
     "type": "accepted_values", "ok": true, "severity": "error",
     "note": "1 row references LITIGATION_EXPENSE_RESERVE; resolved against silver_reference_data.financial_transaction_classification"},
    {"id": "transaction_currency_code_in_codeset",
     "type": "accepted_values", "ok": true, "severity": "error"},
    {"id": "lifecycle_event_uid_resolves",
     "type": "expression", "ok": true, "severity": "error",
     "note": "8217 rows have lifecycle_event_uid populated; all resolve to a row in silver_claims.claim_lifecycle_event."}
  ],
  "status": "ok"
}
```

The `lifecycle_event_uid_resolves` post-write assertion is the unique post-write check this walkthrough adds beyond the policy walkthrough: every populated `lifecycle_event_uid` must point to a row that already exists in the lifecycle event table. Because the run order loads events before transactions, the assertion resolves cleanly.

### 6.2 Worked failure mode: transaction arrives before its lifecycle event

If the operator runs `claim_financial_transaction` *before* `claim_lifecycle_event`, the `lifecycle_event_uid_resolves` assertion fires post-write: any transaction with a populated `lifecycle_event_uid` cannot find its target row in `silver_claims.claim_lifecycle_event`. The notebook records the failure in the run summary and raises:

```jsonc
{
  "contractId": "pc.claim-financial-transaction",
  "rowsRead": 12653, "rowsInserted": 12653,                  // the insert succeeded
  "rowsCorrected": 1,
  "assertions": [
    {"id": "lifecycle_event_uid_resolves",
     "type": "expression", "ok": false, "severity": "error",
     "note": "8217 rows have lifecycle_event_uid populated; 8217 do NOT resolve. Fix: load claim_lifecycle_event then re-run."}
  ],
  "status": "failed"
}
```

Append-only mechanics make this recoverable: the transaction rows already wrote, but the post-write assertion failure does not roll them back. After the operator loads `claim_lifecycle_event` and re-runs `claim_financial_transaction` in `incremental` mode, no new rows are inserted (Bronze has not advanced since the failed run), the post-write assertion runs again, and clears.

The same shape applies to the codeset-before-entity failure mode the policy walkthrough described — the recovery is a re-run after the prerequisite catches up; nothing is rolled back.

---

## 7. Step 5 — Analyst queries Silver

The analyst answers a question that exercises every kind of join in the walkthrough: "for every open claim, what is the most recent reserve change and the most recent payment, with human-readable status and classification labels?"

```sql
WITH recent_reserve_change AS (
  SELECT
    cft.claim_uid,
    MAX(cft.transaction_effective_date) AS last_reserve_date
  FROM nebula_pc_silver.silver_claims.claim_financial_transaction AS cft
  WHERE cft.transaction_type_code = 'RESERVE_CHANGE'
    AND cft.correction_indicator = FALSE        -- ignore corrections in the rollup
  GROUP BY cft.claim_uid
),
recent_payment AS (
  SELECT
    cft.claim_uid,
    MAX(cft.transaction_effective_date) AS last_payment_date,
    SUM(CASE WHEN cft.transaction_type_code = 'PAYMENT' THEN cft.transaction_amount ELSE 0 END) AS total_paid_amount
  FROM nebula_pc_silver.silver_claims.claim_financial_transaction AS cft
  WHERE cft.transaction_type_code = 'PAYMENT'
    AND cft.correction_indicator = FALSE
  GROUP BY cft.claim_uid
)
SELECT
  c.claim_uid,
  c.claim_number,
  cs.code_label                                    AS claim_status_label,
  c.claim_type_code,
  c.opened_date,
  rrc.last_reserve_date,
  rp.last_payment_date,
  rp.total_paid_amount
FROM nebula_pc_silver.silver_claims.claim AS c
JOIN nebula_pc_silver.silver_reference_data.claim_status_code AS cs
  ON cs.code_value = c.claim_status_code
 AND cs.is_current_indicator = TRUE
LEFT JOIN recent_reserve_change AS rrc ON rrc.claim_uid = c.claim_uid
LEFT JOIN recent_payment        AS rp  ON rp.claim_uid  = c.claim_uid
WHERE c.is_current_indicator = TRUE
  AND c.record_status_code   = 'ACTIVE'
  AND c.claim_status_code IN ('OPEN', 'REOPENED');
```

Three patterns the analyst should know that did not surface in the policy walkthrough:

- **Append-only tables filter by business time, not SCD2.** `claim_financial_transaction` is filtered by `transaction_effective_date` (and `correction_indicator = FALSE` to ignore correction rows during a rollup). There is no `is_current_indicator` on append-only tables.
- **Correction rows are filtered out of rollups.** The append template's run summary counts them under `rowsCorrected`; analytic queries that compute totals must exclude them. A reconciliation query that needs to account for corrections includes them and joins `corrects_claim_financial_transaction_uid` back to the original.
- **Codeset joins are still through `code_value`.** The codeset's `*_uid` is internal; entity contracts never store it. `cs.code_value = c.claim_status_code` is the canonical join shape.

Time-travel works on the entity tables and codesets exactly as in the policy walkthrough (replace `is_current_indicator = TRUE` with an SCD2 window predicate). It does not apply to append-only tables — those are time-series; you filter by `event_datetime` or `transaction_effective_date` directly.

A loss-runs-by-account query exercises the C4.5 commercial-lines spine:

```sql
SELECT
  c.account_uid,
  COUNT(*)                                         AS claim_count,
  SUM(rp.total_paid_amount)                        AS account_paid_amount
FROM nebula_pc_silver.silver_claims.claim AS c
LEFT JOIN recent_payment AS rp ON rp.claim_uid = c.claim_uid
WHERE c.is_current_indicator = TRUE
  AND c.account_uid IS NOT NULL
GROUP BY c.account_uid
ORDER BY account_paid_amount DESC NULLS LAST;
```

This is the one-hop path C4.5 unlocked — `account_uid` is on `claim` directly, so the rollup does not have to traverse `policy → policy_account_path` to land at the account.

---

## 8. Step 6 — Governance ingests Purview JSON

The governance team imports the same two consolidated Purview files. After ingest, the new state in the Purview UI for the six-contract walkthrough:

| What governance sees | Source on this repo |
|---|---|
| Six tables under `nebula_pc_silver`, three of them `Confidential`. | `sensitivity-labels.json.tables[]`. |
| `silver_claims/claim/claim_description` flagged `Confidential` + `PII`. | The ODCS contract's `customProperties.classifications` block on `claim_description`. |
| `silver_claims/claim_lifecycle_event/event_narrative` flagged `Confidential` + `PII`. | Same shape on the event contract. |
| `silver_claims/claim_financial_transaction/transaction_amount` flagged `Confidential` + `FINANCIAL`. | Same shape on the transaction contract. |
| `silver_claims/claim_financial_transaction/transaction_narrative` flagged `Confidential` + `PII`. | Same shape on the transaction contract. |
| `silver_claims/claim_financial_transaction/payee_party_role_uid` flagged `Confidential` + `PII`. | Inherited via the canonical-alignment ADR — payee identity is sensitive even when only the role uid is stored. |
| `LITIGATION_EXPENSE_RESERVE` glossary term linked to `silver_claims/claim_financial_transaction/transaction_classification_code`. | `business-glossary.json.terms[]`, harvested from the codeset's description. |

The C7.4 `source_*_datetime` rename means the late-arriving-data analysis fields on `claim` (`source_created_datetime`, `source_updated_datetime`) appear next to the SCD2 system-time fields (`valid_from_datetime`, `valid_to_datetime`) in the Purview UI without the prior naming collision the original `created_datetime` / `updated_datetime` caused.

Governance owns retention, masking, and audit downstream of the labels. This repository is the source of the labels; the Purview workspace is the system of record once the labels are in.

---

## 9. What changes when the architect changes the contract

A reverse trace of Step 1 — the architect renames `LITIGATION_EXPENSE_RESERVE` to `DEFENSE_COUNSEL_RESERVE` because legal review prefers the latter term. What changes downstream:

| Layer | Change |
|---|---|
| ODCS contract (`pc.financial-transaction-classification`) | `description` updated; `version` bumped to `0.2.0` (rename of an allowed code value is MAJOR per `versioning-policy.md`, but at `0.x` we use a MINOR bump and record the breaking change in the changelog); changelog entry names the rename. |
| Manifest (`financial-transaction-classification.fabric.yaml`) | `contract.version` bumped to `0.2.0`; `sourceContractDigest` recomputed; column shape unchanged. |
| Manifest (`claim-financial-transaction.fabric.yaml`) | `codeReference.codeset` is unchanged (still points at `pc.financial-transaction-classification`); the manifest does not embed code values, so no diff. |
| DDL (`financial-transaction-classification.spark.sql`) | Table comment updated to `Source: pc.financial-transaction-classification v0.2.0`. Column shape identical. |
| Purview JSON | `sourceContractVersion` strings update for the two table-level entries that reference the codeset and for the column-level entries. |
| Notebook templates | No change — templates are decoupled from any specific contract. |
| Codeset load notebook run | Next run: the row whose `code_value = 'LITIGATION_EXPENSE_RESERVE'` is deletion-detected (full-refresh mode), closed with `record_status_code = 'SOFT_DELETED'`, and a new `code_value = 'DEFENSE_COUNSEL_RESERVE'` row inserts as the current row. The renamed code is two SCD2 rows, not one. |
| Append notebook runs (transaction) | Next run: any transaction Bronze row carrying the old `LITIGATION_EXPENSE_RESERVE` value fails the `transaction_classification_code_in_codeset` post-write assertion. The architect either backfills the upstream system to use the new code, or restores the codeset entry. |
| Analyst queries | A query that filters `transaction_classification_code = 'LITIGATION_EXPENSE_RESERVE'` returns historical rows only; the same query rewritten to use `DEFENSE_COUNSEL_RESERVE` returns the new rows. A union across both, joined to the codeset by SCD2 window, recovers the full series. |

The blast radius of a single contract edit is two regenerated manifests, two small DDL diffs, one Purview JSON diff, and a behaviour change at the next codeset-load run. The mechanical fan-out from one ODCS edit is what the metadata-driven posture buys.

---

## 10. Cross-references

| Need | File |
|---|---|
| Plan that governs every step here | `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` |
| Plan that governs M10 deliverables | `planning-mds/MILESTONE_10_PLAN.md` |
| Persona flow definition | `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` §3.3.3, mirrored in `targets/fabric/README.md` |
| Lakehouse / schema / table conventions | `targets/fabric/conventions.md` |
| Manifest field reference | `targets/fabric/manifest-schema.md` (field-role taxonomy in §5.2 includes `event-correction-flag`, `event-corrects-ref`, `lifecycle-event-link`) |
| ODCS → Spark type mapping | `targets/fabric/type-mapping.md` |
| Companion walkthrough (SCD2 entity + codeset side) | `targets/fabric/examples/end-to-end-policy.md` |
| Claim lifecycle pattern | `references/patterns/pc/claim-lifecycle-pattern.md` |
| Event-and-transaction ADR | `references/design-decisions/pc/event-and-transaction.md` |
| Claims-modeling ADR | `references/design-decisions/pc/claims-modeling.md` |
| Account / commercial-lines spine ADR (C4.5) | `references/design-decisions/pc/canonical-alignment.md`; pattern in `references/patterns/pc/account-pattern.md` |
| Currency-convention ADR | `references/design-decisions/pc/currency-convention.md` |
| Data-classification ADR | `references/design-decisions/pc/data-classification.md` |
| Canonical contracts referenced in this walkthrough | `references/odcs/pc/claims/claim.odcs.yaml`, `claim-feature.odcs.yaml`, `claim-lifecycle-event.odcs.yaml`, `claim-financial-transaction.odcs.yaml`, `references/odcs/pc/reference-data/claim-status-code.odcs.yaml`, `financial-transaction-classification.odcs.yaml` |
| Manifests referenced | `targets/fabric/manifests/pc/claims/claim.fabric.yaml`, `claim-feature.fabric.yaml`, `claim-lifecycle-event.fabric.yaml`, `claim-financial-transaction.fabric.yaml`, `targets/fabric/manifests/pc/reference-data/claim-status-code.fabric.yaml`, `financial-transaction-classification.fabric.yaml` |
| DDL referenced | `targets/fabric/ddl/pc/claims/claim.spark.sql`, `claim-feature.spark.sql`, `claim-lifecycle-event.spark.sql`, `claim-financial-transaction.spark.sql`, `targets/fabric/ddl/pc/reference-data/claim-status-code.spark.sql`, `financial-transaction-classification.spark.sql` |
| Purview JSON referenced | `targets/fabric/purview/sensitivity-labels.json`, `targets/fabric/purview/business-glossary.json` |
| Notebook templates referenced | `targets/fabric/notebooks/silver-scd2-merge-template.ipynb`, `silver-append-template.ipynb`, `silver-codeset-load-template.ipynb` |
| Lakehouse binding | `targets/fabric/notebooks/lakehouse-binding-template.json` |
| Manifest validator | `scripts/validation/validate-fabric-manifests.py` |
| Manifest generator | `scripts/generation/generate-fabric-manifests.py` |
| DDL generator | `scripts/generation/generate-fabric-ddl.py` |
| Purview generator | `scripts/generation/generate-fabric-purview.py` |
| Notebook generator | `scripts/generation/generate-fabric-notebooks.py` |
| Orchestrator | `scripts/generation/generate-fabric.py` |
