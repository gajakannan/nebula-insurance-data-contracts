# 01 — Bind And Issue

> **Scenario state.** A submission was created on 2026-02-15 for Acme
> Manufacturing's new General Liability policy. On 2026-02-25 the broker (Marsh
> Northeast) accepted the quote and the policy was bound. On 2026-03-01 the
> policy was issued and is now in force. This part traces the records that
> the policy admin system, agency portal, and broker systems emit across
> these dates — through Bronze, the source-to-canonical mapping, and into
> Silver as durable SCD2 entities and append-only events.

For the running scenario values (account, party, agreement, term identifiers
and source-side IDs), see the [tutorial README](README.md#running-scenario).

## What You Will See In This Part

- The PAS publishes a policy header, two party rows (broker, insured), two
  policy-party-role rows, a broker-of-record agreement, two lifecycle event
  rows (`BOUND`, `ISSUED`), and one policy-transaction row (`NEW_BUSINESS`).
- These records land in raw Bronze in their source shape, then a conformance
  job reshapes them into canonical Bronze feed rows.
- Generated Fabric notebooks consume the canonical feed and materialize
  Silver rows: SCD2 rows for policy / party / role / agreement; append-only
  rows for the lifecycle events and the transaction.
- The first SCD2 notebook run produces one current row per durable identity.

---

## Stage 1 — Source Records

Source records are not canonical. Different source systems use their own
field names and code values. Below are the records emitted on bind day
(2026-02-25) and on issue day (2026-03-01).

### 1a. Policy header (PAS, 2026-02-25 — emitted at bind)

```text
source: nebula_pas.policy
  policy_id           = 100042
  policy_no           = ACME-GL-2026-0042
  policy_status       = B                 -- source code for "bound"
  policy_type         = NB
  lob                 = GL
  account_id          = ACCT-44213
  agreement_id        = AGRMT-77
  product_id          = PROD-GL-STD
  issue_dt            = null              -- not yet issued
  orig_eff_dt         = 2026-03-01
  current_term_id     = TERM-100042-1
  prior_policy_id     = null              -- no prior policy for new business
  description         = "Acme Mfg GL new business, 2026 term"
  created_ts          = 2026-02-25T14:30:00Z
  updated_ts          = 2026-02-25T14:30:00Z
```

### 1b. Policy header republish (PAS, 2026-03-01 — emitted at issue)

```text
source: nebula_pas.policy
  policy_id           = 100042
  ...
  policy_status       = I                 -- source code for "issued"
  issue_dt            = 2026-03-01
  updated_ts          = 2026-03-01T08:00:00Z
  -- all other fields unchanged
```

The source system republishes the full policy row whenever any field
changes. The mapper does not need to compute deltas; the SCD2 loader
detects no-op republishes by hashing canonical columns.

### 1c. Broker organization (Agency portal, broker side)

```text
source: nebula_agy.broker_org
  broker_org_id       = BR-7821
  broker_name         = "Marsh Northeast"
  broker_legal_name   = "Marsh & McLennan Companies, NE Region"
  broker_type         = BROKERAGE
  broker_status       = ACTIVE
  created_ts          = 2018-04-12T09:00:00Z
  updated_ts          = 2024-09-22T17:14:00Z
```

### 1d. Insured organization (PAS account record)

```text
source: nebula_pas.account_org
  org_id              = ORG-31178
  org_name            = "Acme Manufacturing Inc."
  org_legal_name      = "Acme Manufacturing Incorporated"
  org_type            = CORP
  status              = ACTIVE
  created_ts          = 2017-08-30T11:21:00Z
  updated_ts          = 2025-12-04T10:02:00Z
```

### 1e. Policy-party roles (PAS)

```text
source: nebula_pas.policy_role  (broker)
  role_id             = ROLE-882001
  policy_id           = 100042
  term_id             = TERM-100042-1
  party_ref_type      = BROKER_ORG
  party_ref_id        = BR-7821
  role                = BROKER
  role_status         = ACTIVE
  primary_broker_flag = Y
  effective_dt        = 2026-03-01
  expiration_dt       = null
  created_ts          = 2026-02-25T14:30:00Z
  updated_ts          = 2026-02-25T14:30:00Z

source: nebula_pas.policy_role  (named insured)
  role_id             = ROLE-882002
  policy_id           = 100042
  term_id             = TERM-100042-1
  party_ref_type      = ACCOUNT_ORG
  party_ref_id        = ORG-31178
  role                = NAMED_INSURED
  role_status         = ACTIVE
  primary_broker_flag = N
  effective_dt        = 2026-03-01
  expiration_dt       = null
```

### 1f. Broker-of-record agreement (Agency portal — pre-existing)

```text
source: nebula_agy.broker_agreement
  agreement_id        = AGRMT-77
  agreement_no        = BOR-MARSH-ACME-2024
  agreement_name      = "Acme / Marsh Broker of Record"
  agreement_type      = BOR
  agreement_status    = ACTIVE
  account_id          = ACCT-44213
  broker_org_id       = BR-7821
  effective_dt        = 2024-01-15
  expiration_dt       = null
```

The agreement was created in 2024 and is unchanged at bind. The mapping
job re-reads its current row when it processes this policy.

### 1g. Policy lifecycle events (PAS)

```text
source: nebula_pas.policy_event  (bind, 2026-02-25)
  policy_event_id     = EVT-555001
  policy_id           = 100042
  term_id             = TERM-100042-1
  event_type          = BOUND
  event_status        = COMPLETED
  prior_status        = Q
  new_status          = B
  event_ts            = 2026-02-25T14:30:00Z
  initiated_by_org_id = BR-7821
  event_text          = "Policy bound at $48,000 annual premium"
  transaction_id      = TXN-300001

source: nebula_pas.policy_event  (issue, 2026-03-01)
  policy_event_id     = EVT-555002
  policy_id           = 100042
  term_id             = TERM-100042-1
  event_type          = ISSUED
  event_status        = COMPLETED
  prior_status        = B
  new_status          = I
  event_ts            = 2026-03-01T08:00:00Z
  initiated_by_org_id = null               -- system-initiated
  event_text          = "Policy issued and effective"
  transaction_id      = null
```

### 1h. Policy transaction (PAS, booked at bind)

```text
source: nebula_pas.policy_txn
  transaction_id      = TXN-300001
  policy_id           = 100042
  term_id             = TERM-100042-1
  policy_event_id     = EVT-555001
  transaction_type    = NB                  -- new business
  effective_dt        = 2026-03-01
  processed_ts        = 2026-02-25T14:30:00Z
  sequence_no         = 1
  requested_by_org_id = BR-7821
  processed_by_user_id = USR-101
  premium_delta       = 48000.00
  currency            = USD
  description         = "Annual premium for new business term"
```

---

## Stage 2 — Raw Bronze Landing

The ingestion platform writes each source record into a source-shaped
Bronze table without renaming or normalizing fields. It only adds
ingestion metadata (`_ingested_at`, `_source_file`, `_payload_hash`).

```text
bronze_pas.policy_raw_src           <- 2 rows (bind, issue republish)
bronze_pas.account_org_raw_src      <- 1 row
bronze_pas.policy_role_raw_src      <- 2 rows (broker, named insured)
bronze_pas.policy_event_raw_src     <- 2 rows (BOUND, ISSUED)
bronze_pas.policy_txn_raw_src       <- 1 row (NB)
bronze_agy.broker_org_raw_src       <- 1 row (Marsh Northeast)
bronze_agy.broker_agreement_raw_src <- 1 row (BOR-MARSH-ACME-2024)
```

Raw Bronze keeps source codes (`B`, `I`, `BOR`, `Y`/`N`), source ID
formats, and source field names. It is replayable and fully auditable.

---

## Stage 3 — Source-To-Canonical Mapping

A conformance job, owned by the implementation outside this repo, reads
the raw Bronze tables and writes canonical-shaped feed tables. This is
the most interesting reshape: it resolves canonical `*_uid` keys,
translates field names, normalizes codes, and splits source rows that
carry multiple canonical concepts.

### 3a. Field-level mapping

For the policy header:

| Source field (raw Bronze) | Canonical field (feed) | Transformation |
|---|---|---|
| `policy_id` | `policy_uid` | UID lookup or generation; here `100042` -> `POL-7C4D8E10` |
| (constant) | `source_system_code` | Set to `NEBULA_PAS` for this feed |
| `policy_id` | `source_natural_key` | Preserved as string `"100042"` |
| `policy_no` | `policy_number` | Direct copy |
| `policy_status` | `policy_status_code` | Code translation: `B` -> `BOUND`, `I` -> `ISSUED` |
| `policy_type` | `policy_type_code` | Code translation: `NB` -> `NEW_BUSINESS` |
| `lob` | `line_of_business_code` | Code translation: `GL` -> `GENERAL_LIABILITY` |
| `account_id` | `account_uid` | UID lookup: `ACCT-44213` -> `ACCT-1F6E9A2B` |
| `agreement_id` | `agreement_uid` | UID lookup: `AGRMT-77` -> `AGR-3B5F2A91` |
| `product_id` | `product_uid` | UID lookup |
| `orig_eff_dt` | `original_effective_date` | Direct copy |
| `issue_dt` | `issue_date` | Direct copy (null at bind, populated at issue) |
| `current_term_id` | `current_policy_term_uid` | UID lookup |
| `prior_policy_id` | `prior_policy_uid` | UID lookup when present; null for this new-business policy |
| `description` | `policy_description` | Direct copy |
| `created_ts` | `source_created_datetime` | Direct copy (source-system time) |
| `updated_ts` | `source_updated_datetime` | Direct copy |
| (none) | `issuing_jurisdiction_code` | Resolved from policy term jurisdiction (`US-NY`) |

The `account_uid` and term UIDs above are foreign-key context. This tutorial
does not load `pc.account` or `pc.policy-term`; it assumes those canonical
rows already exist, or are loaded by adjacent pipelines, before the policy
feed is validated.

For the broker source row, the mapping splits one source record into
canonical rows in two different contracts:

| Source field (broker_org) | Canonical destination | Transformation |
|---|---|---|
| `broker_org_id` | `pc.party.party_uid` (broker row) | UID lookup: `BR-7821` -> `PTY-MARSH-9E2A` |
| `broker_name` | `pc.party.party_display_name` | Direct copy |
| `broker_legal_name` | `pc.party.legal_name` | Direct copy |
| `broker_status` | `pc.party.party_status_code` | Direct copy |
| (constant) | `pc.party.party_type_code` | Set to `ORGANIZATION` |
| `broker_type` | `pc.party.organization_type_code` | Code translation: `BROKERAGE` -> `AGENCY` |

The conformance job emits one `pc.party` row for Marsh Northeast and a
separate `pc.party` row for Acme Manufacturing (split from the source
account org), then emits two `pc.policy-party-role` rows linking each
party to the policy:

| Source row | Canonical role row | role_type_code | party_uid |
|---|---|---|---|
| `policy_role` (broker) | `policy_party_role_uid = PPR-2F8B1C50` | `BROKER` | `PTY-MARSH-9E2A` |
| `policy_role` (named insured) | `policy_party_role_uid = PPR-9A4D7E22` | `NAMED_INSURED` | `PTY-ACME-4D7C` |

Code translation cheat-sheet for this part:

| Source code | Canonical code | Codeset |
|---|---|---|
| `policy_status = B` | `BOUND` | `pc.policy-status-code` |
| `policy_status = I` | `ISSUED` | `pc.policy-status-code` |
| `prior_status` / `new_status = Q` | `QUOTED` | `pc.lifecycle-status` |
| `prior_status` / `new_status = B` | `BOUND` | `pc.lifecycle-status` |
| `prior_status` / `new_status = I` | `ISSUED` | `pc.lifecycle-status` |
| `NB` (policy_type) | `NEW_BUSINESS` | `pc.policy-type-code` |
| `NB` (transaction_type) | `NEW_BUSINESS` | `pc.transaction-type` |
| `GL` | `GENERAL_LIABILITY` | `pc.line-of-business` |
| `BOR` | `BROKER_OF_RECORD` | `pc.agreement-type-code` (deployment-extended) |
| `BROKERAGE` | `AGENCY` | `pc.organization-type` (deployment-defined) |
| `BOUND` (event_type) | `BOUND` | `pc.lifecycle-event-type` |
| `ISSUED` (event_type) | `ISSUED` | `pc.lifecycle-event-type` |
| `Y` / `N` (broker_flag) | `true` / `false` | (boolean type) |

---

## Stage 4 — Canonical Bronze Feed

The mapping job writes one row per canonical entity into the feed
tables consumed by the generated notebooks. The feed is in canonical
vocabulary; the notebooks no longer need to know about the source.

### 4a. `bronze.policy_raw` — two rows

```text
row 1 (from bind republish, 2026-02-25):
  policy_uid                   = POL-7C4D8E10
  source_system_code           = NEBULA_PAS
  source_natural_key           = "100042"
  policy_number                = ACME-GL-2026-0042
  policy_status_code           = BOUND
  policy_type_code             = NEW_BUSINESS
  line_of_business_code        = GENERAL_LIABILITY
  account_uid                  = ACCT-1F6E9A2B
  agreement_uid                = AGR-3B5F2A91
  product_uid                  = PROD-GL-STD
  issuing_jurisdiction_code    = US-NY
  original_effective_date      = 2026-03-01
  issue_date                   = null
  current_policy_term_uid      = TRM-7C4D8E10-2026
  prior_policy_uid             = null
  policy_description           = "Acme Mfg GL new business, 2026 term"
  source_created_datetime      = 2026-02-25T14:30:00Z
  source_updated_datetime      = 2026-02-25T14:30:00Z

row 2 (from issue republish, 2026-03-01):
  policy_uid                   = POL-7C4D8E10
  ...
  policy_status_code           = ISSUED
  issue_date                   = 2026-03-01
  source_updated_datetime      = 2026-03-01T08:00:00Z
  -- all other fields unchanged
```

### 4b. `bronze.party_raw` — two rows

```text
row 1 (broker):
  party_uid                    = PTY-MARSH-9E2A
  source_system_code           = NEBULA_AGY
  source_natural_key           = "BR-7821"
  party_type_code              = ORGANIZATION
  party_display_name           = "Marsh Northeast"
  legal_name                   = "Marsh & McLennan Companies, NE Region"
  organization_name            = "Marsh Northeast"
  organization_type_code       = AGENCY
  party_status_code            = ACTIVE
  effective_date               = 2018-04-12
  expiration_date              = null
  source_created_datetime      = 2018-04-12T09:00:00Z
  source_updated_datetime      = 2024-09-22T17:14:00Z

row 2 (insured):
  party_uid                    = PTY-ACME-4D7C
  source_system_code           = NEBULA_PAS
  source_natural_key           = "ORG-31178"
  party_type_code              = ORGANIZATION
  party_display_name           = "Acme Manufacturing Inc."
  legal_name                   = "Acme Manufacturing Incorporated"
  organization_name            = "Acme Manufacturing Inc."
  organization_type_code       = CORPORATION
  party_status_code            = ACTIVE
  effective_date               = 2017-08-30
  expiration_date              = null
  source_created_datetime      = 2017-08-30T11:21:00Z
  source_updated_datetime      = 2025-12-04T10:02:00Z
```

### 4c. `bronze.policy_party_role_raw` — two rows

```text
row 1 (broker role):
  policy_party_role_uid        = PPR-2F8B1C50
  source_system_code           = NEBULA_PAS
  source_natural_key           = "ROLE-882001"
  policy_uid                   = POL-7C4D8E10
  policy_term_uid              = TRM-7C4D8E10-2026
  party_uid                    = PTY-MARSH-9E2A
  role_type_code               = BROKER
  role_status_code             = ACTIVE
  primary_role_indicator       = true
  effective_date               = 2026-03-01
  expiration_date              = null
  source_created_datetime      = 2026-02-25T14:30:00Z
  source_updated_datetime      = 2026-02-25T14:30:00Z

row 2 (named insured role):
  policy_party_role_uid        = PPR-9A4D7E22
  ...
  party_uid                    = PTY-ACME-4D7C
  role_type_code               = NAMED_INSURED
  primary_role_indicator       = false
```

### 4d. `bronze.agreement_raw` — one row

```text
  agreement_uid                = AGR-3B5F2A91
  source_system_code           = NEBULA_AGY
  source_natural_key           = "AGRMT-77"
  agreement_number             = BOR-MARSH-ACME-2024
  agreement_name               = "Acme / Marsh Broker of Record"
  agreement_type_code          = BROKER_OF_RECORD
  agreement_status_code        = ACTIVE
  account_uid                  = ACCT-1F6E9A2B
  counterparty_party_uid       = PTY-MARSH-9E2A
  effective_date               = 2024-01-15
  expiration_date              = null
  agreement_description        = "Master broker-of-record letter on file"
```

### 4e. `bronze.policy_lifecycle_event_raw` — two rows

```text
row 1 (BOUND):
  policy_lifecycle_event_uid   = PLE-A1B2C3D4
  policy_uid                   = POL-7C4D8E10
  policy_term_uid              = TRM-7C4D8E10-2026
  lifecycle_event_type_code    = BOUND
  lifecycle_event_status_code  = COMPLETED
  prior_status_code            = QUOTED
  resulting_status_code        = BOUND
  event_datetime               = 2026-02-25T14:30:00Z
  initiated_by_party_uid       = PTY-MARSH-9E2A
  event_description            = "Policy bound at $48,000 annual premium"
  triggering_transaction_uid   = PTX-C9D0E1F2
  correction_indicator         = false
  corrects_policy_lifecycle_event_uid = null

row 2 (ISSUED):
  policy_lifecycle_event_uid   = PLE-E5F6A7B8
  policy_uid                   = POL-7C4D8E10
  policy_term_uid              = TRM-7C4D8E10-2026
  lifecycle_event_type_code    = ISSUED
  lifecycle_event_status_code  = COMPLETED
  prior_status_code            = BOUND
  resulting_status_code        = ISSUED
  event_datetime               = 2026-03-01T08:00:00Z
  initiated_by_party_uid       = null
  event_description            = "Policy issued and effective"
  triggering_transaction_uid   = null
  correction_indicator         = false
```

### 4f. `bronze.policy_transaction_raw` — one row

```text
  policy_transaction_uid        = PTX-C9D0E1F2
  policy_uid                    = POL-7C4D8E10
  policy_term_uid               = TRM-7C4D8E10-2026
  policy_lifecycle_event_uid    = PLE-A1B2C3D4
  transaction_type_code         = NEW_BUSINESS
  transaction_effective_date    = 2026-03-01
  transaction_processed_datetime= 2026-02-25T14:30:00Z
  transaction_sequence_number   = 1
  requested_by_party_uid        = PTY-MARSH-9E2A
  processed_by_party_uid        = PTY-USER-USR101
  premium_change_amount         = 48000.00
  premium_change_currency_code  = USD
  transaction_description       = "Annual premium for new business term"
  correction_indicator          = false
```

---

## Stage 5 — Silver Materialization (SCD2 Path)

Generated Fabric notebooks consume the canonical feed tables and apply
the SCD2 merge or append-only template. The same template covers every
SCD2 entity in this part (policy, party, policy-party-role, agreement);
the manifest tells the template which natural key, validity columns, and
hashing rules to use.

### 5a. Illustrative manifest snippet (`pc.policy`)

```yaml
# illustrative — actual file at targets/fabric/manifests/pc/policy/policy.fabric.yaml
contractId: pc.policy
contractVersion: 0.4.x
kind: entity
silver:
  schema: silver_policy
  table: policy
bronze:
  schema: bronze
  table: policy_raw
  incrementalColumn: _ingested_at
scd2:
  enabled: true
  validFrom: valid_from_datetime
  validTo: valid_to_datetime
  isCurrent: is_current_indicator
  naturalKey: [policy_uid]
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
columns:
  - name: policy_uid
    role: identity
    type: string
  - name: policy_number
    role: business-key
    type: string
  - name: policy_status_code
    role: code-reference
    codeset: pc.policy-status-code
  - name: policy_type_code
    role: code-reference
    codeset: pc.policy-type-code
  # ... remaining columns omitted in this illustration
```

### 5b. Illustrative DDL snippet (`silver_policy.policy`)

```sql
-- illustrative — actual file at targets/fabric/ddl/pc/policy/policy.spark.sql
CREATE TABLE IF NOT EXISTS silver_policy.policy (
  policy_uid                STRING    NOT NULL,
  source_system_code        STRING    NOT NULL,
  source_natural_key        STRING    NOT NULL,
  policy_number             STRING    NOT NULL,
  policy_status_code        STRING    NOT NULL,
  policy_type_code          STRING,
  line_of_business_code     STRING,
  account_uid               STRING,
  agreement_uid             STRING,
  -- ...
  source_created_datetime   TIMESTAMP,
  source_updated_datetime   TIMESTAMP,
  record_status_code        STRING    NOT NULL,
  valid_from_datetime       TIMESTAMP NOT NULL,
  valid_to_datetime         TIMESTAMP,
  is_current_indicator      BOOLEAN   NOT NULL,
  CONSTRAINT pk_policy PRIMARY KEY (policy_uid, valid_from_datetime)
)
USING DELTA
PARTITIONED BY (is_current_indicator)
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);
```

### 5c. Illustrative SCD2 merge logic (`silver-scd2-merge-template`)

```python
# illustrative pseudocode — actual notebook at
# targets/fabric/notebooks/silver-scd2-merge-template.ipynb
manifest = load_manifest("pc.policy")           # reads scd2 + recordState config
incoming = read_feed("bronze.policy_raw")       # canonical-shape rows

# 1. Hash everything except SCD2 system-time and record-state columns
hash_cols = [c for c in incoming.columns if c not in manifest.scd2.excludeFromHashing]
incoming  = incoming.withColumn("_row_hash", sha2_concat(hash_cols))

current   = read_silver("silver_policy.policy").where("is_current_indicator = true")

# 2. Find natural keys whose hash differs from the current row
to_close  = current.join(incoming, on=manifest.scd2.naturalKey, how="inner") \
                   .where("current._row_hash <> incoming._row_hash")

# 3. Close superseded rows
update silver_policy.policy
   set valid_to_datetime  = run_timestamp,
       is_current_indicator = false,
       record_status_code = 'SUPERSEDED'
 where (policy_uid, valid_from_datetime) in to_close

# 4. Insert the new current rows (or initial inserts)
insert into silver_policy.policy
select incoming.*,
       'ACTIVE'      as record_status_code,
       run_timestamp as valid_from_datetime,
       null          as valid_to_datetime,
       true          as is_current_indicator
  from incoming
 where natural_key not in already_current_with_same_hash

# 5. Post-write validation
assert one_current_row_per_natural_key("silver_policy.policy")
assert codeset_values_accepted("silver_policy.policy.policy_status_code",
                                "pc.policy-status-code")
```

### 5d. Resulting Silver rows after Stage 5

The notebook run on bind day inserts the first current row for every
SCD2 entity. The next run on issue day (with the republished policy
header in the feed) detects a change to `policy_status_code` and
`source_updated_datetime` for `POL-7C4D8E10`, closes the bind-day row,
and inserts a new current row.

#### `silver_policy.policy`

```text
After bind-day load:
  policy_uid          = POL-7C4D8E10
  policy_status_code  = BOUND
  issue_date          = null
  source_updated_datetime = 2026-02-25T14:30:00Z
  record_status_code  = ACTIVE
  valid_from_datetime = 2026-02-25T15:00:00Z   -- load timestamp
  valid_to_datetime   = null
  is_current_indicator = true

After issue-day load:
  Row 1 (bind-day row, now closed):
    policy_uid          = POL-7C4D8E10
    policy_status_code  = BOUND
    record_status_code  = SUPERSEDED
    valid_from_datetime = 2026-02-25T15:00:00Z
    valid_to_datetime   = 2026-03-01T09:00:00Z
    is_current_indicator = false

  Row 2 (issue-day row, new current):
    policy_uid          = POL-7C4D8E10
    policy_status_code  = ISSUED
    issue_date          = 2026-03-01
    source_updated_datetime = 2026-03-01T08:00:00Z
    record_status_code  = ACTIVE
    valid_from_datetime = 2026-03-01T09:00:00Z
    valid_to_datetime   = null
    is_current_indicator = true
```

#### `silver_core.party` — two current rows (one per party)

```text
party_uid = PTY-MARSH-9E2A
  party_display_name      = "Marsh Northeast"
  organization_type_code  = AGENCY
  party_status_code       = ACTIVE
  record_status_code      = ACTIVE
  valid_from_datetime     = 2026-02-25T15:00:00Z
  is_current_indicator    = true

party_uid = PTY-ACME-4D7C
  party_display_name      = "Acme Manufacturing Inc."
  organization_type_code  = CORPORATION
  party_status_code       = ACTIVE
  record_status_code      = ACTIVE
  is_current_indicator    = true
```

#### `silver_policy.policy_party_role` — two current rows

```text
policy_party_role_uid = PPR-2F8B1C50
  policy_uid              = POL-7C4D8E10
  party_uid               = PTY-MARSH-9E2A
  role_type_code          = BROKER
  primary_role_indicator  = true
  is_current_indicator    = true

policy_party_role_uid = PPR-9A4D7E22
  policy_uid              = POL-7C4D8E10
  party_uid               = PTY-ACME-4D7C
  role_type_code          = NAMED_INSURED
  is_current_indicator    = true
```

#### `silver_core.agreement` — one current row

```text
agreement_uid = AGR-3B5F2A91
  agreement_number        = BOR-MARSH-ACME-2024
  agreement_type_code     = BROKER_OF_RECORD
  agreement_status_code   = ACTIVE
  account_uid             = ACCT-1F6E9A2B
  counterparty_party_uid  = PTY-MARSH-9E2A
  is_current_indicator    = true
```

---

## Stage 6 — Silver Materialization (Append-Only Path)

Lifecycle events and policy transactions never SCD2-version. Each row
is an immutable fact about a moment in time. The append-only template
inserts new rows and rejects duplicates by `*_uid`.

### 6a. Illustrative manifest snippet (`pc.policy-lifecycle-event`)

```yaml
# illustrative — actual file at
# targets/fabric/manifests/pc/policy/policy-lifecycle-event.fabric.yaml
contractId: pc.policy-lifecycle-event
kind: append-only
silver:
  schema: silver_policy
  table: policy_lifecycle_event
bronze:
  schema: bronze
  table: policy_lifecycle_event_raw
  incrementalColumn: _ingested_at
appendOnly:
  enabled: true
  identityColumn: policy_lifecycle_event_uid
  correctionIndicator: correction_indicator
  correctsReference: corrects_policy_lifecycle_event_uid
columns:
  - name: policy_lifecycle_event_uid
    role: identity
  - name: lifecycle_event_type_code
    role: code-reference
    codeset: pc.lifecycle-event-type
  # ...
```

### 6b. Illustrative append-only logic (`silver-append-template`)

```python
# illustrative pseudocode — actual notebook at
# targets/fabric/notebooks/silver-append-template.ipynb
manifest = load_manifest("pc.policy-lifecycle-event")
incoming = read_feed("bronze.policy_lifecycle_event_raw")
existing = read_silver("silver_policy.policy_lifecycle_event")

# 1. Drop rows whose identity already exists in Silver (idempotency)
new_rows = incoming.join(existing, on=manifest.appendOnly.identityColumn,
                         how="left_anti")

# 2. Validate correction references resolve when correction_indicator = true
assert all(
    row.corrects_policy_lifecycle_event_uid is not None
    for row in new_rows.where("correction_indicator = true")
)
assert correction_targets_exist(new_rows, existing)

# 3. Insert
insert into silver_policy.policy_lifecycle_event
select * from new_rows

# 4. Post-write codeset validation
assert codeset_values_accepted(
    "silver_policy.policy_lifecycle_event.lifecycle_event_type_code",
    "pc.lifecycle-event-type")
```

### 6c. Resulting Silver rows after Stage 6

#### `silver_policy.policy_lifecycle_event` — two rows

```text
PLE-A1B2C3D4  (BOUND, 2026-02-25T14:30:00Z, prior=QUOTED, resulting=BOUND,
               initiated_by=PTY-MARSH-9E2A, triggering_transaction=PTX-C9D0E1F2)
PLE-E5F6A7B8  (ISSUED, 2026-03-01T08:00:00Z, prior=BOUND, resulting=ISSUED,
               initiated_by=null, triggering_transaction=null)
```

#### `silver_policy.policy_transaction` — one row

```text
PTX-C9D0E1F2  (NEW_BUSINESS, effective=2026-03-01,
               processed=2026-02-25T14:30:00Z, sequence=1,
               premium_change_amount=48000.00, currency=USD,
               policy_lifecycle_event_uid = PLE-A1B2C3D4)
```

---

## Validation Highlights From This Part

- **SCD2 current-row uniqueness.** After the issue-day load, the SCD2 merge
  template asserts exactly one `is_current_indicator = true` row per
  `policy_uid`. The bind-day row is now closed and counts as historical.
- **Codeset accepted-values check.** Post-write, the notebook checks every
  `*_code` column against its bound codeset. `policy_status_code = ISSUED`
  must exist as a current row in `silver_reference.policy_status_code`.
- **Required-fields check.** `policy_uid`, `source_system_code`,
  `policy_status_code`, and the SCD2 fields are non-nullable. The
  pre-write validator rejects the load if any are missing.
- **Append-only idempotency.** Re-running the lifecycle-event load with the
  same source rows is a no-op: rows whose `policy_lifecycle_event_uid`
  already exists are filtered out before insert.

---

## End-Of-Part-01 State Recap

After parts 01a-01h are loaded, Silver contains:

| Table | Current rows | Historical (SCD2 closed) rows |
|---|---|---|
| `silver_policy.policy` | 1 (`POL-7C4D8E10`, status `ISSUED`) | 1 (status `BOUND`) |
| `silver_core.party` | 2 (Marsh, Acme) | 0 |
| `silver_policy.policy_party_role` | 2 (broker, insured) | 0 |
| `silver_core.agreement` | 1 (`AGR-3B5F2A91`) | 0 |
| `silver_policy.policy_lifecycle_event` | 2 (`BOUND`, `ISSUED`) | n/a (append-only) |
| `silver_policy.policy_transaction` | 1 (`NEW_BUSINESS`) | n/a (append-only) |

Continue with [02-endorsement.md](02-endorsement.md), where the policy is
mid-term and an endorsement adds Building C to the schedule.
