# 03 — Mid-Term Cancellation (With A Correction)

> **Scenario state.** It is 2026-06-01. After three months of coverage,
> Acme Manufacturing has consolidated its operations and asks Marsh to
> cancel the General Liability policy `POL-7C4D8E10` mid-term. The PAS
> records the cancellation with a pro-rata return-premium transaction of
> USD -36,000 (nine months of unearned premium). On 2026-06-03, the
> back-office discovers that the original cancel event was tagged with
> the wrong reason ("non-payment") when it should have been "voluntary
> cancellation by insured", and emits a correction row.

This part shows the SCD2 close-and-replace on the policy header, the
broker role being terminated, two append-only event rows (cancel and
its correction), one append-only transaction row (return premium), and
how an immutable correction is represented without ever updating the
original row.

## What You Will See In This Part

- The PAS republishes the policy header with `policy_status = X` (cancelled)
  and a new `updated_ts`. The SCD2 merge closes the `ISSUED` row from part
  01 and inserts a new current row with status `CANCELLED`.
- The PAS republishes the broker policy-party-role row with
  `role_status = TERMINATED` and `expiration_dt = 2026-06-01`. The SCD2
  merge closes the previous broker-role row and inserts a new current
  row.
- One lifecycle event row (`CANCELLATION`) and one transaction row
  (`CANCELLATION`, with negative premium) append.
- Two days later, a correction row appends — same lifecycle-event-type,
  but `correction_indicator = true` and a back-pointer to the original
  event row's `policy_lifecycle_event_uid`.

---

## Stage 1 — Source Records (2026-06-01 and 2026-06-03)

### 1a. Policy header republish (PAS, 2026-06-01)

```text
source: nebula_pas.policy
  policy_id           = 100042
  policy_no           = ACME-GL-2026-0042
  policy_status       = X                     -- source code for "cancelled"
  policy_type         = NB
  lob                 = GL
  issue_dt            = 2026-03-01
  orig_eff_dt         = 2026-03-01
  current_term_id     = TERM-100042-1
  description         = "Acme Mfg GL new business, 2026 term — cancelled mid-term"
  created_ts          = 2026-02-25T14:30:00Z  -- unchanged
  updated_ts          = 2026-06-01T16:45:00Z
```

### 1b. Broker role republish (PAS, 2026-06-01)

```text
source: nebula_pas.policy_role  (broker, terminated)
  role_id             = ROLE-882001
  policy_id           = 100042
  term_id             = TERM-100042-1
  party_ref_type      = BROKER_ORG
  party_ref_id        = BR-7821
  role                = BROKER
  role_status         = TERMINATED              -- changed
  primary_broker_flag = Y
  effective_dt        = 2026-03-01
  expiration_dt       = 2026-06-01              -- now populated
  updated_ts          = 2026-06-01T16:45:00Z
```

The named-insured role row republishes with the same pattern
(`role_status = TERMINATED`, `expiration_dt = 2026-06-01`) and is not
shown again.

### 1c. Cancel lifecycle event (PAS, 2026-06-01)

```text
source: nebula_pas.policy_event
  policy_event_id     = EVT-555004
  policy_id           = 100042
  term_id             = TERM-100042-1
  event_type          = CANCELLATION
  event_status        = COMPLETED
  prior_status        = I
  new_status          = X
  event_ts            = 2026-06-01T16:45:00Z
  initiated_by_org_id = ORG-31178               -- Acme initiated
  event_text          = "Cancellation, reason: non-payment"
  transaction_id      = TXN-300003
```

### 1d. Cancel transaction (PAS, 2026-06-01)

```text
source: nebula_pas.policy_txn
  transaction_id      = TXN-300003
  policy_id           = 100042
  term_id             = TERM-100042-1
  policy_event_id     = EVT-555004
  transaction_type    = CAN                     -- cancellation
  effective_dt        = 2026-06-01
  processed_ts        = 2026-06-01T16:45:00Z
  sequence_no         = 3
  requested_by_org_id = ORG-31178
  processed_by_user_id = USR-201
  premium_delta       = -36000.00               -- pro-rata return
  currency            = USD
  description         = "Pro-rata return premium for unearned 9 months"
```

### 1e. Correction event (PAS, 2026-06-03)

The cancel event was originally tagged with reason "non-payment". On
review, the back-office determines the correct reason is "voluntary
cancellation by insured". The PAS emits a *new* event row that
corrects the prior one. The original is not updated — append-only
contracts never mutate prior rows.

```text
source: nebula_pas.policy_event
  policy_event_id     = EVT-555005
  policy_id           = 100042
  term_id             = TERM-100042-1
  event_type          = CANCELLATION
  event_status        = COMPLETED
  prior_status        = I
  new_status          = X
  event_ts            = 2026-06-03T09:10:00Z      -- when correction filed
  initiated_by_org_id = ORG-31178
  event_text          = "Cancellation, reason corrected to: voluntary by insured"
  transaction_id      = TXN-300003                 -- same transaction
  correction_flag     = Y
  corrects_event_id   = EVT-555004
```

---

## Stage 2 — Raw Bronze Landing

Two batches land. The 2026-06-01 batch carries the policy header
republish, the broker role republish, the named-insured role
republish, the cancel event, and the cancel transaction. The
2026-06-03 batch carries only the correction event row.

```text
2026-06-01 batch:
  bronze_pas.policy_raw_src        <- 1 row (status = X)
  bronze_pas.policy_role_raw_src   <- 2 rows (broker terminated, insured terminated)
  bronze_pas.policy_event_raw_src  <- 1 row (EVT-555004)
  bronze_pas.policy_txn_raw_src    <- 1 row (TXN-300003)

2026-06-03 batch:
  bronze_pas.policy_event_raw_src  <- 1 row (EVT-555005, correction)
```

---

## Stage 3 — Source-To-Canonical Mapping

The conformance job applies the same lookups as parts 01 and 02 and
adds these new translations:

| Source code | Canonical code | Codeset |
|---|---|---|
| `X` (policy_status) | `CANCELLED` | `pc.policy-status-code` |
| `I` (event prior_status) | `ISSUED` | `pc.lifecycle-status` |
| `X` (event new_status) | `CANCELLED` | `pc.lifecycle-status` |
| `TERMINATED` (role_status) | `TERMINATED` | `pc.role-status-code` |
| `CAN` (transaction_type) | `CANCELLATION` | `pc.transaction-type` |
| `CANCELLATION` (event_type) | `CANCELLATION` | `pc.lifecycle-event-type` |
| `Y` (correction_flag) | `true` (boolean) | (boolean type) |

Identifier mapping for the new rows:

| Source identifier | Canonical UID |
|---|---|
| `EVT-555004` | `PLE-AABB1122` |
| `EVT-555005` | `PLE-EEFF5566` |
| `TXN-300003` | `PTX-CCDD3344` |
| `ROLE-882001` (republish) | `PPR-2F8B1C50` (existing, same UID) |

The role republish keeps the same `policy_party_role_uid`. SCD2 versioning
is by canonical UID + system time, not by emitting a new identity.

---

## Stage 4 — Canonical Bronze Feed

### 4a. `bronze.policy_raw` — one new row

```text
  policy_uid                   = POL-7C4D8E10
  source_system_code           = NEBULA_PAS
  source_natural_key           = "100042"
  policy_status_code           = CANCELLED
  policy_type_code             = NEW_BUSINESS
  line_of_business_code        = GENERAL_LIABILITY
  account_uid                  = ACCT-1F6E9A2B
  agreement_uid                = AGR-3B5F2A91
  policy_description           = "Acme Mfg GL new business, 2026 term — cancelled mid-term"
  source_created_datetime      = 2026-02-25T14:30:00Z
  source_updated_datetime      = 2026-06-01T16:45:00Z
```

### 4b. `bronze.policy_party_role_raw` — one new row (broker, plus an analogous insured row)

```text
  policy_party_role_uid        = PPR-2F8B1C50
  policy_uid                   = POL-7C4D8E10
  party_uid                    = PTY-MARSH-9E2A
  role_type_code               = BROKER
  role_status_code             = TERMINATED
  primary_role_indicator       = true
  effective_date               = 2026-03-01
  expiration_date              = 2026-06-01
  source_updated_datetime      = 2026-06-01T16:45:00Z
```

### 4c. `bronze.policy_lifecycle_event_raw` — two new rows

```text
row 1 (cancel, 2026-06-01):
  policy_lifecycle_event_uid   = PLE-AABB1122
  policy_uid                   = POL-7C4D8E10
  policy_term_uid              = TRM-7C4D8E10-2026
  lifecycle_event_type_code    = CANCELLATION
  lifecycle_event_status_code  = COMPLETED
  prior_status_code            = ISSUED
  resulting_status_code        = CANCELLED
  event_datetime               = 2026-06-01T16:45:00Z
  initiated_by_party_uid       = PTY-ACME-4D7C
  event_description            = "Cancellation, reason: non-payment"
  triggering_transaction_uid   = PTX-CCDD3344
  correction_indicator         = false
  corrects_policy_lifecycle_event_uid = null

row 2 (correction, 2026-06-03):
  policy_lifecycle_event_uid   = PLE-EEFF5566
  policy_uid                   = POL-7C4D8E10
  policy_term_uid              = TRM-7C4D8E10-2026
  lifecycle_event_type_code    = CANCELLATION
  lifecycle_event_status_code  = COMPLETED
  prior_status_code            = ISSUED
  resulting_status_code        = CANCELLED
  event_datetime               = 2026-06-03T09:10:00Z
  initiated_by_party_uid       = PTY-ACME-4D7C
  event_description            = "Cancellation, reason corrected to: voluntary by insured"
  triggering_transaction_uid   = PTX-CCDD3344
  correction_indicator         = true
  corrects_policy_lifecycle_event_uid = PLE-AABB1122
```

### 4d. `bronze.policy_transaction_raw` — one new row

```text
  policy_transaction_uid        = PTX-CCDD3344
  policy_uid                    = POL-7C4D8E10
  policy_term_uid               = TRM-7C4D8E10-2026
  policy_lifecycle_event_uid    = PLE-AABB1122
  transaction_type_code         = CANCELLATION
  transaction_effective_date    = 2026-06-01
  transaction_processed_datetime= 2026-06-01T16:45:00Z
  transaction_sequence_number   = 3
  requested_by_party_uid        = PTY-ACME-4D7C
  processed_by_party_uid        = PTY-USER-USR201
  premium_change_amount         = -36000.00
  premium_change_currency_code  = USD
  transaction_description       = "Pro-rata return premium for unearned 9 months"
  correction_indicator          = false
```

---

## Stage 5 — Silver Materialization

### 5a. SCD2 close-and-replace on `silver_policy.policy`

The merge template detects that the canonical hash for `POL-7C4D8E10`
differs from the current row (status changed `ISSUED` -> `CANCELLED`,
description changed, `source_updated_datetime` changed). It closes the
existing current row and inserts a new one. The bind-day historical
row from part 01 is untouched.

```text
silver_policy.policy after this load — three rows for POL-7C4D8E10

Row 1 (closed at part 01 issue load):
  policy_status_code   = BOUND
  record_status_code   = SUPERSEDED
  valid_from_datetime  = 2026-02-25T15:00:00Z
  valid_to_datetime    = 2026-03-01T09:00:00Z
  is_current_indicator = false

Row 2 (closed by this load):
  policy_status_code   = ISSUED
  record_status_code   = SUPERSEDED
  valid_from_datetime  = 2026-03-01T09:00:00Z
  valid_to_datetime    = 2026-06-01T17:00:00Z
  is_current_indicator = false

Row 3 (new current):
  policy_status_code   = CANCELLED
  record_status_code   = ACTIVE
  source_updated_datetime = 2026-06-01T16:45:00Z
  valid_from_datetime  = 2026-06-01T17:00:00Z
  valid_to_datetime    = null
  is_current_indicator = true
```

After the load, exactly one current row exists per natural key. The
post-write validator confirms this.

### 5b. SCD2 close-and-replace on `silver_policy.policy_party_role`

The broker role row also closes-and-replaces. Same pattern:

```text
PPR-2F8B1C50 after this load — two rows

Row 1 (closed):
  role_type_code         = BROKER
  role_status_code       = ACTIVE
  expiration_date        = null
  record_status_code     = SUPERSEDED
  valid_from_datetime    = 2026-02-25T15:00:00Z
  valid_to_datetime      = 2026-06-01T17:00:00Z
  is_current_indicator   = false

Row 2 (new current):
  role_type_code         = BROKER
  role_status_code       = TERMINATED
  expiration_date        = 2026-06-01
  primary_role_indicator = true
  record_status_code     = ACTIVE
  valid_from_datetime    = 2026-06-01T17:00:00Z
  valid_to_datetime      = null
  is_current_indicator   = true
```

The named-insured role (`PPR-9A4D7E22`) closes-and-replaces with the
same pattern. Note that the broker is still represented as
*primary_role_indicator = true* in the current row even though the
role itself is terminated. The history of who was the broker for this
term is preserved by the `valid_from`/`valid_to` window plus the role
status code.

### 5c. Append-only inserts: cancel event + correction event + cancel transaction

The append-only template inserts three new rows (two events, one
transaction). The correction row is just another row — the original
`PLE-AABB1122` is not updated.

```text
silver_policy.policy_lifecycle_event after this part — five rows

  PLE-A1B2C3D4   BOUND          2026-02-25   correction_indicator = false
  PLE-E5F6A7B8   ISSUED         2026-03-01   correction_indicator = false
  PLE-12C34D56   ENDORSEMENT    2026-04-15   correction_indicator = false
  PLE-AABB1122   CANCELLATION   2026-06-01   correction_indicator = false
  PLE-EEFF5566   CANCELLATION   2026-06-03   correction_indicator = true,
                                              corrects_policy_lifecycle_event_uid
                                              = PLE-AABB1122
```

```text
silver_policy.policy_transaction after this part — three rows

  PTX-C9D0E1F2   NEW_BUSINESS   2026-03-01    +48000.00 USD
  PTX-78E90F12   ENDORSEMENT    2026-04-15    +5000.00 USD
  PTX-CCDD3344   CANCELLATION   2026-06-01   -36000.00 USD
```

---

## How To Read A Corrected Event In A Query

Consumers that want the *current* understanding of the cancel reason
need to filter out events that have been corrected. A standard pattern
is to keep events that are not themselves the subject of a correction
back-reference:

```sql
-- illustrative
with corrected_uids as (
  select corrects_policy_lifecycle_event_uid as uid
  from silver_policy.policy_lifecycle_event
  where correction_indicator = true
    and corrects_policy_lifecycle_event_uid is not null
)
select e.*
from silver_policy.policy_lifecycle_event e
left anti join corrected_uids c on c.uid = e.policy_lifecycle_event_uid
;
```

Applied to our data, this returns the four current-truth rows
(`BOUND`, `ISSUED`, `ENDORSEMENT`, and the correction
`PLE-EEFF5566`). The original `PLE-AABB1122` is filtered out because
it has been superseded by the correction.

Audit consumers (timeline, reconciliation) keep all rows including
corrected originals, so they can show "this row was filed at
2026-06-01 16:45 then corrected at 2026-06-03 09:10".

---

## End-Of-Part-03 State Recap

| Table | Current rows | Historical rows |
|---|---|---|
| `silver_policy.policy` | 1 (status `CANCELLED`) | 2 (`BOUND`, `ISSUED`) |
| `silver_core.party` | 2 (unchanged) | 0 |
| `silver_policy.policy_party_role` | 2 (both `TERMINATED`) | 2 |
| `silver_core.agreement` | 1 (unchanged) | 0 |
| `silver_policy.policy_lifecycle_event` | 5 rows total, including 1 correction | n/a |
| `silver_policy.policy_transaction` | 3 rows total, sum +17000.00 USD | n/a |

Continue with [04-renewal.md](04-renewal.md) for a separate renewal
companion scenario, then [05-gold-projection.md](05-gold-projection.md)
to project these Silver rows into consumer views.
