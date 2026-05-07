# Fabric Manifest Schema

This document is the schema reference for the Fabric manifest. The manifest is the single intermediate artifact that drives every generated downstream file (Delta DDL, SCD2 / append / codeset notebooks at runtime, Purview sensitivity labels, business glossary). One manifest per ODCS contract.

The manifest is **always derived**, never authored. A human edits the canonical ODCS contract; the manifest generator (`scripts/generation/generate-fabric-manifests.py`, F2) reads the contract and emits the manifest. If a manifest disagrees with its source contract, the validator (`scripts/validation/validate-fabric-manifests.py`) flags drift and the generator is rerun.

Companion documents:

- `README.md` — purpose, scope, persona flow, file map.
- `conventions.md` — runtime mechanics: SCD2, append-only, codeset materialization, partitioning, V-Order, Purview projection.
- `type-mapping.md` — ODCS logical type → Spark SQL type, nullability, decimal precision, datetime semantics.

This document uses the Policy contract as the worked example. Policy is an entity contract; sections that differ for event, transaction, and codeset kinds are called out with separate examples.

---

## 1. File layout

One manifest per contract. The manifest path mirrors the source contract path:

```text
references/odcs/pc/policy/policy.odcs.yaml
        ↓
targets/fabric/manifests/pc/policy/policy.fabric.yaml
```

The slug in the file name is the same slug used as the Delta table name (`policy`, `policy_term`, `claim_lifecycle_event`, `line_of_business`).

---

## 2. Top-level shape

A manifest has six top-level keys:

```yaml
manifestVersion: 1.0.0       # schema version of the manifest itself
contract:                    # mirrors fields from the source ODCS contract
fabric:                      # platform-mechanics (lakehouse, schema, table, columns, mode)
relationships:               # FK and cross-contract relationships projected from ODCS
generation:                  # provenance: generator version, run datetime, source path, digest
```

A worked example for Policy follows. Subsequent sections document each block.

```yaml
manifestVersion: 1.0.0

contract:
  id: pc.policy
  name: Policy
  version: 0.4.2
  domain: property-and-casualty
  description: Canonical contract for durable Property and Casualty policy identity
    and current policy summary.
  classificationProfile: CONFIDENTIAL
  subjectToHipaa: false
  contractKind: entity                  # entity | event | transaction | codeset
  subjectArea: policy
  adrs:
    - authoring-source-primacy
    - canonical-alignment
    - codeset-strategy
    - data-classification
    - entity-boundaries
    - identifier-strategy
    - null-semantics
    - policy-lifecycle-modeling
    - record-state
    - scd2-primary-key
    - status-promotion
    - temporal-modeling
    - versioning-policy

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
      role: identity
      description: Immutable system-generated GUID that uniquely identifies the canonical
        policy record across snapshots and source systems.
      classifications:
        sensitivity: INTERNAL
        regulatoryTags: []
      purview:
        sensitivityLabel: Internal

    - name: source_system_code
      sparkType: STRING
      nullable: true
      role: source-attribution
      description: Identifier of the upstream system that produced or last asserted
        this record. Used for multi-source mastering and lineage.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal
      codeReference:
        codeset: pc.source-system-code
        codesetTable: silver_reference_data.source_system_code
        codesetField: code_value

    - name: source_natural_key
      sparkType: STRING
      nullable: true
      role: source-attribution
      description: Natural key assigned by the source system. Captured for provenance;
        not used as the canonical primary key.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal

    - name: policy_number
      sparkType: STRING
      nullable: false
      role: business-key
      description: Business-facing number assigned to the policy.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal

    - name: policy_status_code
      sparkType: STRING
      nullable: false
      role: code-reference
      description: Current lifecycle status of the policy.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal
      codeReference:
        codeset: pc.policy-status-code
        codesetTable: silver_reference_data.policy_status_code
        codesetField: code_value

    - name: line_of_business_code
      sparkType: STRING
      nullable: false
      role: code-reference
      description: Classification of the insurance line of business for the policy.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal
      codeReference:
        codeset: pc.line-of-business
        codesetTable: silver_reference_data.line_of_business
        codesetField: code_value

    - name: account_uid
      sparkType: STRING
      nullable: true
      role: foreign-key
      description: Identifier (GUID reference) for the commercial account the policy
        belongs to. Required for commercial-lines rollups; null for personal-lines
        policies that do not live under an account.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal
      foreignKey:
        targetContract: pc.account
        targetTable: silver_core.account
        targetField: account_uid

    - name: original_effective_date
      sparkType: DATE
      nullable: true
      role: data
      description: Date when the policy first became effective across its durable
        policy history.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal

    - name: policy_description
      sparkType: STRING
      nullable: true
      role: data
      description: Source-neutral business description of the policy when additional
        context is needed.
      classifications:
        sensitivity: CONFIDENTIAL
        regulatoryTags: [PII]
      purview:
        sensitivityLabel: Confidential

    - name: source_created_datetime
      sparkType: TIMESTAMP
      nullable: true
      role: source-time
      description: Source-system timestamp asserting when this record was created.
        Captured for late-arriving-data analysis; distinct from the SCD2 system-time
        start in valid_from_datetime.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal

    - name: source_updated_datetime
      sparkType: TIMESTAMP
      nullable: true
      role: source-time
      description: Source-system timestamp asserting when this record was last updated.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal

    - name: record_status_code
      sparkType: STRING
      nullable: false
      role: record-state
      description: Warehouse-level state of the record. References the RecordStatusCode
        codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal
      codeReference:
        codeset: pc.record-status-code
        codesetTable: silver_reference_data.record_status_code
        codesetField: code_value

    - name: valid_from_datetime
      sparkType: TIMESTAMP
      nullable: false
      primaryKey: true
      role: scd2-valid-from
      description: System-time start of the SCD2 window for this record version.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal

    - name: valid_to_datetime
      sparkType: TIMESTAMP
      nullable: true
      role: scd2-valid-to
      description: System-time end of the SCD2 window for this record version.
        Null indicates the current row.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal

    - name: is_current_indicator
      sparkType: BOOLEAN
      nullable: false
      role: scd2-is-current
      description: True for exactly one row per logical key, indicating the current
        record version.
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal

    # ... remaining columns elided for brevity ...

  scd2:
    enabled: true
    validFrom: valid_from_datetime
    validTo: valid_to_datetime
    isCurrent: is_current_indicator
    naturalKey: [policy_uid]
    deletionAware: false
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
    supersededValue: SUPERSEDED
    softDeletedValue: SOFT_DELETED

  appendOnly:
    enabled: false                       # mutually exclusive with scd2.enabled
    correctionIndicator: null
    correctsRefField: null

  qualityRules:
    - id: policy_uid_required
      type: not_null
      column: policy_uid
      severity: error
      sourceRule: policy_uid_required
    - id: single_current_row_per_key
      type: unique
      keyColumns: [policy_uid]
      filter: "is_current_indicator = true"
      severity: error
      sourceRule: single_current_row_per_key
    - id: valid_window_consistent
      type: expression
      expression: "valid_to_datetime IS NULL OR valid_to_datetime > valid_from_datetime"
      severity: error
      sourceRule: valid_window_consistent
    - id: policy_prior_policy_must_differ
      type: expression
      expression: "prior_policy_uid IS NULL OR prior_policy_uid <> policy_uid"
      severity: warning
      sourceRule: policy_prior_policy_must_differ

  bronze:
    table: bronze.policy_raw
    incrementalColumn: _ingested_at
    expectedColumns:
      - policy_uid
      - source_system_code
      - source_natural_key
      - policy_number
      - policy_status_code
      - line_of_business_code
      - account_uid
      - original_effective_date
      - policy_description
      - source_created_datetime
      - source_updated_datetime
      # ... remaining columns elided for brevity ...

relationships:
  - name: policy_to_current_policy_term
    description: Relates a policy to its current policy term when term detail is available.
    cardinality: many-to-one
    targetContract: pc.policy-term
    targetTable: silver_policy.policy_term
    sourceFields: [current_policy_term_uid]
    targetFields: [policy_term_uid]
  - name: policy_to_account
    description: Relates a policy to the commercial account the policy belongs to
      when account context is available.
    cardinality: many-to-one
    targetContract: pc.account
    targetTable: silver_core.account
    sourceFields: [account_uid]
    targetFields: [account_uid]
  # ... remaining relationships elided for brevity ...

generation:
  generatorVersion: 1.0.0
  generatedAt: 2026-05-07T00:00:00Z
  sourceContractPath: references/odcs/pc/policy/policy.odcs.yaml
  sourceContractDigest: sha256:...
```

---

## 3. `manifestVersion`

Format: semver string. The manifest schema is independently versioned from the source contract. A manifest schema bump is reserved for a real shape change (a renamed top-level key, a new required field). The source contract's version travels through the `contract.version` field and does not bump the manifest schema.

`1.0.0` is the F1 baseline.

---

## 4. `contract` block

Mirrors fields from the source ODCS contract. The generator copies these from the contract; the validator confirms they match.

| Field | Source | Notes |
|---|---|---|
| `id` | ODCS `id` | e.g. `pc.policy`. |
| `name` | ODCS `name` | e.g. `Policy`. |
| `version` | ODCS `version` | Mirrors source. The validator fails on any mismatch. |
| `domain` | ODCS `domain` | `property-and-casualty` for every contract under `references/odcs/pc/`. |
| `description` | ODCS top-level `description` | Used in DDL table comments and Purview business-glossary entries. |
| `classificationProfile` | `customProperties.classificationProfile` | One of `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`. Reflects the max field sensitivity per C2. |
| `subjectToHipaa` | `customProperties.subjectToHipaa` | Default `false`. When `true`, drives HIPAA-aware Purview labels and notebook annotations. |
| `contractKind` | Derived from contract slug and folder | One of `entity`, `event`, `transaction`, `codeset`. |
| `subjectArea` | `customProperties.subjectArea` | Drives the lakehouse schema name (`silver_<subjectArea>`). |
| `adrs` | `customProperties.adrs` | Pass-through. Used by the Purview business-glossary entries to back-link to ADR rationale. |

### 4.1 `contractKind` derivation

The generator classifies every contract into one of four kinds, in priority order:

1. **`codeset`** — file lives under `references/odcs/pc/reference-data/`.
2. **`event`** — slug ends in `-lifecycle-event`.
3. **`transaction`** — slug ends in `-transaction` or matches `financial-transaction` / `policy-financial-transaction` / `claim-financial-transaction`.
4. **`entity`** — anything else.

The classification is purely structural (no slug heuristics on column shape) so a new contract that follows the conventions classifies correctly without configuration.

---

## 5. `fabric` block

The platform-mechanics core of the manifest.

### 5.1 `fabric.lakehouse` and `fabric.schema`

Single-lakehouse override per `conventions.md`:

- `lakehouse: nebula_pc_silver` for every contract.
- `schema: silver_<subjectArea>` derived from `customProperties.subjectArea`.

### 5.2 `fabric.table`

```yaml
fabric:
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
```

| Field | Notes |
|---|---|
| `name` | snake_case slug; matches the source file name without `.odcs.yaml` and `.fabric.yaml`. |
| `delta.tableProperties` | See `conventions.md` §7. `delta.appendOnly` is `true` for `event` / `transaction` kinds, `false` otherwise. |
| `partitionedBy` | `[is_current_indicator]` for entity / codeset kinds; `[<business-time-column>]` for event / transaction kinds. |
| `zorderBy` | Advisory hint. `[*_uid]` for entities; empty for events / transactions / codesets by default. |
| `vorder` | Always `true`. |

### 5.3 `fabric.columns`

A list, one entry per column. Order matches the source contract's `properties` order.

Each column entry:

```yaml
- name: policy_uid
  sparkType: STRING
  nullable: false
  primaryKey: true                   # only on PK columns
  role: identity
  description: Immutable system-generated GUID...
  classifications:
    sensitivity: INTERNAL
    regulatoryTags: []
  purview:
    sensitivityLabel: Internal
  foreignKey: null                   # block populated only for foreign-key role
  codeReference: null                # block populated only for code-reference role
  currencyPair: null                 # block populated only for monetary-amount role
```

Field-by-field rules:

| Field | Source | Notes |
|---|---|---|
| `name` | ODCS `name` | snake_case; never renamed. |
| `sparkType` | Derived per `type-mapping.md` | One of `STRING`, `INT`, `BIGINT`, `DECIMAL(p, s)`, `BOOLEAN`, `DATE`, `TIMESTAMP`. |
| `nullable` | Derived from ODCS `required` plus the rules in `type-mapping.md` §3 | `false` for primary keys, SCD2 system-time fields, `is_current_indicator`, `record_status_code`, `correction_indicator`. |
| `primaryKey` | ODCS `primaryKey` | Present and `true` only on PK columns; omitted otherwise. |
| `role` | Derived from field name, position, and contract kind | One of the values in §5.4. |
| `description` | ODCS `description` | Pass-through; used in DDL column comments and Purview entries. |
| `classifications.sensitivity` | `customProperties.classifications.sensitivity` | `PUBLIC` / `INTERNAL` / `CONFIDENTIAL` / `RESTRICTED`. |
| `classifications.regulatoryTags` | `customProperties.classifications.regulatoryTags` | Subset of `[PII, PHI, FINANCIAL]`. Empty list when absent. |
| `purview.sensitivityLabel` | Mapped from `classifications.sensitivity` | `Public` / `Internal` / `Confidential` / `Restricted`. |
| `foreignKey` | Block populated only when role is `foreign-key`. | `targetContract`, `targetTable`, `targetField`. |
| `codeReference` | Block populated only when role is `code-reference` or when an entity has a codeset binding for `record-state`, `source-attribution`, etc. | `codeset`, `codesetTable`, `codesetField`. |
| `currencyPair` | Block populated only when role is `monetary-amount`. | `pairedColumn` naming the sibling currency code column. |

### 5.4 Field role taxonomy

The `role` field captures **how** the notebook should treat the column. It is derived from ODCS metadata, not authored. The generator computes the role per the rules below; the validator confirms exactly one role-based field exists for each required SCD2 / record-state / append-only slot.

| Role | Derivation rule | Notebook behavior |
|---|---|---|
| `identity` | `primaryKey: true` and name ends `_uid`. | SCD2 natural key; immutable; non-null. |
| `business-key` | Name ends `_number`, not the PK. | Carried through; surfaced for human queries. |
| `source-attribution` | Name in `{source_system_code, source_natural_key}`. | Captured for lineage; included in change-detection hash on entity contracts. |
| `source-time` | Name in `{source_created_datetime, source_updated_datetime}`. | Source-system time. Included in the change-detection hash on entity contracts. Forbidden on append-only contracts. |
| `scd2-valid-from` | Name `valid_from_datetime`. | Managed entirely by the merge notebook; not sourced from Bronze. |
| `scd2-valid-to` | Name `valid_to_datetime`. | Managed entirely by the merge notebook; null for the current row. |
| `scd2-is-current` | Name `is_current_indicator`. | Managed entirely by the merge notebook. |
| `record-state` | Name `record_status_code`. | Default `ACTIVE` on insert; transitions managed by the merge logic. |
| `foreign-key` | Name ends `_uid`, not the PK, and a target contract resolves. | Carried through; not joined eagerly in Silver merge. |
| `code-reference` | Name ends `_code` and a codeset contract resolves (and `customProperties.codesetExempt` is not `true`). | Carried through; emits a `codeReference` block. Post-merge assertion checks the value. |
| `monetary-amount` | logicalType `decimal` and field name has amount semantics (`*_amount`). | Triggers paired-currency assertion via the `currencyPair` block. |
| `monetary-currency` | Name ends `_currency_code` and a sibling monetary field exists. | Carried; participates in pairing assertion. Bound to `pc.currency-code` codeset. |
| `data` | Anything else. | Carried through; subject to standard hashing for change detection. |
| `event-correction-flag` | Name `correction_indicator` on event/transaction. | Drives append insert with correction handling. |
| `event-corrects-ref` | Name `corrects_*_uid` on event/transaction. | Foreign key to the corrected row; checked at write time. |
| `lifecycle-event-link` | Name `lifecycle_event_uid` on a transaction. | Cross-reference to the linked lifecycle event per the event-and-transaction ADR. |

The validator catches a column that does not match any role rule. A new role is added deliberately by extending the table here and the generator together.

### 5.5 `fabric.scd2`

Present and `enabled: true` on entity and codeset contracts. Mutually exclusive with `appendOnly.enabled`.

```yaml
scd2:
  enabled: true
  validFrom: valid_from_datetime
  validTo: valid_to_datetime
  isCurrent: is_current_indicator
  naturalKey: [policy_uid]
  deletionAware: false
  changeDetection:
    excludeFromHashing:
      - valid_from_datetime
      - valid_to_datetime
      - is_current_indicator
      - record_status_code
```

| Field | Notes |
|---|---|
| `enabled` | `true` for entity and codeset; `false` for event and transaction. |
| `validFrom` / `validTo` / `isCurrent` | Always the canonical names. The generator does not rename. |
| `naturalKey` | List with one element: the `*_uid` PK. The composite SCD2 PK is enforced by including `valid_from_datetime` in the table-level `primaryKey: true` markers, but the SCD2 *natural* key for change detection is just `*_uid`. |
| `deletionAware` | Default `false`; `true` only when the contract opts in. Codesets default to `true`. |
| `changeDetection.excludeFromHashing` | Always the four SCD2 / record-state fields above; no per-contract overrides. |

### 5.6 `fabric.recordState`

Present and `enabled: true` on entity and codeset contracts.

```yaml
recordState:
  enabled: true
  field: record_status_code
  activeValue: ACTIVE
  supersededValue: SUPERSEDED
  softDeletedValue: SOFT_DELETED
```

The values come from the `pc.record-status-code` codeset. The generator does not parameterize them per contract.

### 5.7 `fabric.appendOnly`

Present and `enabled: true` on event and transaction contracts. Mutually exclusive with `scd2.enabled`.

```yaml
# Example for pc.policy-lifecycle-event
appendOnly:
  enabled: true
  correctionIndicator: correction_indicator
  correctsRefField: corrects_policy_lifecycle_event_uid
  businessTimeField: event_datetime
  partitionExpression: "MONTH(event_datetime)"
```

| Field | Notes |
|---|---|
| `enabled` | `true` for event/transaction kinds; `false` otherwise. |
| `correctionIndicator` | Name of the `correction_indicator` column. Always present when `enabled: true`. |
| `correctsRefField` | Name of the `corrects_*_uid` column. Always present when `enabled: true`. |
| `businessTimeField` | The contract's primary business-time column (`event_datetime`, `transaction_effective_date`). Drives partitioning and append ordering. |
| `partitionExpression` | Spark SQL expression for the partition (`MONTH(event_datetime)` by default). |

For codeset contracts, `appendOnly.enabled` is `false` and the block is otherwise empty (codesets are SCD2). For entity contracts, the same.

### 5.8 `fabric.qualityRules`

Projected from the contract's `quality` block. Each rule is one of five types:

```yaml
qualityRules:
  - id: policy_uid_required
    type: not_null
    column: policy_uid
    severity: error
    sourceRule: policy_uid_required

  - id: single_current_row_per_key
    type: unique
    keyColumns: [policy_uid]
    filter: "is_current_indicator = true"
    severity: error
    sourceRule: single_current_row_per_key

  - id: valid_window_consistent
    type: expression
    expression: "valid_to_datetime IS NULL OR valid_to_datetime > valid_from_datetime"
    severity: error
    sourceRule: valid_window_consistent

  - id: building_value_currency_pair
    type: currency_pair
    amountColumn: building_value_amount
    currencyColumn: building_value_currency_code
    severity: error
    sourceRule: building_value_currency_required_with_amount

  - id: line_of_business_code_in_codeset
    type: accepted_values
    column: line_of_business_code
    codeset: pc.line-of-business
    codesetTable: silver_reference_data.line_of_business
    codesetField: code_value
    severity: error
    sourceRule: derived
```

| Type | Semantics | Generator source |
|---|---|---|
| `not_null` | Column is non-null. | Lifted from `*_required` contract rules. |
| `unique` | `keyColumns` are unique within `filter`. | Lifted from `single_*_per_key` contract rules. |
| `expression` | Arbitrary SQL boolean. | Fallback for rules that do not match a specific type. |
| `currency_pair` | Amount and currency are both null or both non-null. | Derived from monetary-amount columns with currency siblings; the source contract may not always carry an explicit rule but the generator always emits the assertion. |
| `accepted_values` | Column value exists in a codeset's current rows. | Derived from `code-reference` columns; not authored in the contract. |

`severity` mirrors the contract's severity: `error`, `warning`, or `info`. `sourceRule` records the contract rule id (or `derived` for generator-derived rules) for traceability.

### 5.9 `fabric.bronze`

Default Bronze assumption per `conventions.md` §12:

```yaml
bronze:
  table: bronze.policy_raw
  incrementalColumn: _ingested_at
  expectedColumns:
    - policy_uid
    - policy_number
    - line_of_business_code
    # ... (every column from the canonical contract that is expected to be present in Bronze)
```

Deployers override at run time via the `bronze_prefix_override` notebook parameter; the manifest is not edited.

---

## 6. `relationships` block

Projected from the contract's `relationships` list. Each relationship:

```yaml
- name: policy_to_current_policy_term
  description: Relates a policy to its current policy term when term detail is available.
  cardinality: many-to-one
  targetContract: pc.policy-term
  targetTable: silver_policy.policy_term
  sourceFields: [current_policy_term_uid]
  targetFields: [policy_term_uid]
```

| Field | Source | Notes |
|---|---|---|
| `name` | ODCS relationship `name` | Pass-through. |
| `description` | ODCS relationship `description` | Pass-through. |
| `cardinality` | ODCS `relationshipType` | `many-to-one` / `one-to-many` / `many-to-many`. |
| `targetContract` | ODCS `targetContractId` | e.g. `pc.policy-term`. |
| `targetTable` | Derived from target contract's subject area + slug | e.g. `silver_policy.policy_term`. |
| `sourceFields` / `targetFields` | ODCS `sourceFields` / `targetFields` | Pass-through. |

Relationships are documentation-only at the manifest level. The notebook does not eagerly join across relationships in the SCD2 merge; consumers join in their own queries. The Purview business-glossary entries surface relationships in the term metadata for navigation.

---

## 7. `generation` block

Provenance metadata. Used by the validator for drift detection.

```yaml
generation:
  generatorVersion: 1.0.0
  generatedAt: 2026-05-07T00:00:00Z
  sourceContractPath: references/odcs/pc/policy/policy.odcs.yaml
  sourceContractDigest: sha256:9a8f...
```

| Field | Notes |
|---|---|
| `generatorVersion` | Semver of the manifest generator. Bumped when the manifest schema changes. |
| `generatedAt` | UTC timestamp of the generator run. |
| `sourceContractPath` | Repo-relative path to the source ODCS contract. |
| `sourceContractDigest` | SHA-256 of the source contract file. The validator re-hashes the source contract and fails the manifest if the digest disagrees. |

Drift control: a contract edit invalidates the digest. The validator catches it; the generator is rerun.

---

## 8. Manifest variations by contract kind

### 8.1 Entity (`pc.policy`)

The worked example above. SCD2 enabled, append-only disabled, full SCD2 / record-state / source-time / source-attribution column set.

### 8.2 Event (`pc.policy-lifecycle-event`)

Differences from the entity shape:

```yaml
contract:
  contractKind: event

fabric:
  table:
    delta:
      tableProperties:
        delta.appendOnly: true       # event/transaction tables
      partitionedBy: [event_datetime]   # business-time month partition
  scd2:
    enabled: false
  appendOnly:
    enabled: true
    correctionIndicator: correction_indicator
    correctsRefField: corrects_policy_lifecycle_event_uid
    businessTimeField: event_datetime
    partitionExpression: "MONTH(event_datetime)"
  recordState:
    enabled: false                   # no record_status_code on append-only contracts
```

No `valid_from_datetime`, `valid_to_datetime`, `is_current_indicator`, `record_status_code`, `source_created_datetime`, or `source_updated_datetime` columns. The contract validator's C1.5 rule rejects any append-only contract that smuggles them in.

### 8.3 Transaction (`pc.financial-transaction`)

Same shape as event. Adds `monetary-amount` columns with `currencyPair` blocks:

```yaml
- name: transaction_amount
  sparkType: DECIMAL(18, 2)
  nullable: false
  role: monetary-amount
  classifications:
    sensitivity: CONFIDENTIAL
    regulatoryTags: [FINANCIAL]
  purview:
    sensitivityLabel: Confidential
  currencyPair:
    pairedColumn: transaction_currency_code

- name: transaction_currency_code
  sparkType: STRING
  nullable: false
  role: monetary-currency
  classifications:
    sensitivity: INTERNAL
  purview:
    sensitivityLabel: Internal
  codeReference:
    codeset: pc.currency-code
    codesetTable: silver_reference_data.currency_code
    codesetField: code_value
```

The notebook's `currency_pair` quality rule confirms both columns are null together or non-null together.

### 8.4 Codeset (`pc.line-of-business`)

Same shape as entity (SCD2). The `code_value` column carries `sensitivity: PUBLIC` per the C5 hygiene phase:

```yaml
contract:
  contractKind: codeset

fabric:
  scd2:
    enabled: true
    deletionAware: true              # codesets default to deletion-aware
  recordState:
    enabled: true

  columns:
    - name: line_of_business_uid
      sparkType: STRING
      nullable: false
      primaryKey: true
      role: identity
      classifications:
        sensitivity: INTERNAL
      purview:
        sensitivityLabel: Internal

    - name: code_value
      sparkType: STRING
      nullable: false
      role: data
      classifications:
        sensitivity: PUBLIC
      purview:
        sensitivityLabel: Public

    # ... remaining columns elided for brevity ...
```

A pure codeset (12-13 column shape) and a richer reference-data entity (`LineOfBusiness`, `LifecycleStatus`, etc.) share the same `contractKind: codeset` and the same notebook template. The richer entities have additional columns (parent hierarchies, business segments) but the materialization is identical.

---

## 9. Validation rules summary

`scripts/validation/validate-fabric-manifests.py` (F2) enforces:

1. **Contract correspondence.** Every manifest has a contract; every contract has a manifest (the templates folder is excluded).
2. **Path correspondence.** The manifest path mirrors the contract path under `targets/fabric/manifests/pc/`.
3. **Version match.** `contract.version` matches the source contract's version.
4. **ID match.** `contract.id` matches the source contract id and the path slug.
5. **Digest match.** `generation.sourceContractDigest` matches `sha256(<source contract bytes>)`.
6. **Kind correctness.** `contract.contractKind` matches the derivation rules in §4.1.
7. **Mutually exclusive modes.** `scd2.enabled` and `appendOnly.enabled` are not both `true`.
8. **Required SCD2 columns.** When `scd2.enabled` is `true`, `valid_from_datetime` / `valid_to_datetime` / `is_current_indicator` columns exist with the right roles.
9. **Required append-only columns.** When `appendOnly.enabled` is `true`, `correction_indicator` and `corrects_*_uid` columns exist with the right roles.
10. **Forbidden columns on append-only contracts.** No `valid_from_datetime`, `valid_to_datetime`, `is_current_indicator`, `record_status_code`, `source_created_datetime`, or `source_updated_datetime` on `event` / `transaction` contracts.
11. **Type set.** Every column's `sparkType` is in the allowed set (per `type-mapping.md` §10).
12. **Type derivation.** Every column's `sparkType` is consistent with the source contract's `logicalType`.
13. **Nullability consistency.** Per `type-mapping.md` §3.
14. **Role coverage.** Every column has exactly one role. Every required role for the contract kind is satisfied by exactly one column.
15. **Foreign-key resolution.** Every `foreign-key` role column's `targetContract` resolves to a contract that exists.
16. **Code-reference resolution.** Every `code-reference` role column's `codeset` resolves to a contract that exists.
17. **Currency-pair consistency.** Every `monetary-amount` role column has a `currencyPair` block whose `pairedColumn` is a sibling `monetary-currency` role column on the same table.

A drifted manifest fails CI. The fix is to re-run the manifest generator. The manifest is never edited by hand.

---

## 10. What the manifest does not carry

Documented for clarity:

- **No source-system schema.** Bronze schema is referenced by qualified name; the manifest does not enumerate Bronze columns or types.
- **No ingestion mechanics.** No connector configuration, no schedule, no Pipelines metadata. Bronze is upstream.
- **No workspace IDs.** Lakehouse-binding is in a separate template file with empty IDs the deployer fills in.
- **No Gold projections.** Aggregates, marts, and semantic models are downstream of Silver.
- **No PII masking rules.** Masking is a Purview / consumer concern; the manifest carries the sensitivity label so the consumer's rule engine can act.
- **No retention policy.** Delta-level VACUUM and time-travel retention are deployer concerns governed by environment policy.
- **No notebook code.** The manifest carries the metadata; the notebook templates carry the code. The two are decoupled by design.

A request to add any of the above is a contract-vs-target-vs-skill scoping conversation, not a manifest schema change.
