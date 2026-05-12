# 02 — Mid-Term Endorsement

> **Scenario state.** It is 2026-04-15. The policy `POL-7C4D8E10` has been
> in force since 2026-03-01. Acme Manufacturing has opened a new operating
> location and the broker requests a mid-term endorsement to extend the
> General Liability coverage to that location. Underwriting approves and
> the PAS records an endorsement at +USD 5,000 premium.

This part is shorter than part 01. The policy header does not materially
change, so no new SCD2 row is created for `silver_policy.policy`. Two
append-only rows land: one lifecycle event and one transaction. The
template details introduced in part 01 are not repeated here.

## What You Will See In This Part

- The PAS emits one new lifecycle event row (`ENDORSEMENT`) and one new
  transaction row (`ENDORSEMENT`) tied to the existing policy and term.
- The conformance job maps these into the canonical feed.
- The append-only notebook template inserts the two new Silver rows. The
  SCD2 merge runs but is a no-op for the policy row, because the policy
  header was not republished.

---

## Stage 1 — Source Records (2026-04-15)

The PAS emits only the event and transaction. It does not republish the
policy header for an endorsement that does not change policy-level
attributes such as status, term, or insured.

### 1a. Endorsement lifecycle event (PAS)

```text
source: nebula_pas.policy_event
  policy_event_id     = EVT-555003
  policy_id           = 100042
  term_id             = TERM-100042-1
  event_type          = ENDORSEMENT
  event_status        = COMPLETED
  prior_status        = I             -- still issued
  new_status          = I             -- still issued
  event_ts            = 2026-04-15T11:20:00Z
  initiated_by_org_id = BR-7821       -- Marsh requested it
  event_text          = "Add Building C — 220 Riverside Drive, Albany NY"
  transaction_id      = TXN-300002
```

### 1b. Endorsement transaction (PAS)

```text
source: nebula_pas.policy_txn
  transaction_id      = TXN-300002
  policy_id           = 100042
  term_id             = TERM-100042-1
  policy_event_id     = EVT-555003
  transaction_type    = END           -- endorsement
  effective_dt        = 2026-04-15
  processed_ts        = 2026-04-15T11:20:00Z
  sequence_no         = 2             -- second transaction on this term
  requested_by_org_id = BR-7821
  processed_by_user_id = USR-104
  premium_delta       = 5000.00
  currency            = USD
  description         = "Add Building C to scheduled premises"
```

---

## Stage 2 — Raw Bronze Landing

```text
bronze_pas.policy_event_raw_src   <- 1 row (EVT-555003)
bronze_pas.policy_txn_raw_src     <- 1 row (TXN-300002)
```

No other raw Bronze tables are written for this endorsement. The policy
header table is untouched because PAS did not republish.

---

## Stage 3 — Source-To-Canonical Mapping

Only the event and transaction are mapped. The lookups for `policy_uid`,
`policy_term_uid`, and `party_uid` reuse the keys established in part 01.

| Source field | Canonical field | Transformation |
|---|---|---|
| `policy_event_id` | `policy_lifecycle_event_uid` | UID lookup or generation: `EVT-555003` -> `PLE-12C34D56` |
| `event_type = ENDORSEMENT` | `lifecycle_event_type_code` | Direct code: `ENDORSEMENT` |
| `event_status = COMPLETED` | `lifecycle_event_status_code` | Direct code: `COMPLETED` |
| `prior_status = I` | `prior_status_code` | Code translation: `I` -> `ISSUED` |
| `new_status = I` | `resulting_status_code` | Code translation: `I` -> `ISSUED` |
| `transaction_id` | `triggering_transaction_uid` | UID lookup: `TXN-300002` -> `PTX-78E90F12` |
| `transaction_type = END` | `transaction_type_code` | Code translation: `END` -> `ENDORSEMENT` |
| `premium_delta = 5000.00` | `premium_change_amount` | Direct copy |
| `currency = USD` | `premium_change_currency_code` | Direct copy |
| `initiated_by_org_id = BR-7821` | `initiated_by_party_uid` | UID lookup: `BR-7821` -> `PTY-MARSH-9E2A` |
| `requested_by_org_id = BR-7821` | `requested_by_party_uid` | Same UID lookup |
| `processed_by_user_id = USR-104` | `processed_by_party_uid` | UID lookup of internal user party |

Notice that `prior_status_code` and `resulting_status_code` are both
`ISSUED`. An endorsement does not change policy status, only policy
content. This is normal for endorsement events. These event status fields
bind to `pc.lifecycle-status`; the policy header's `policy_status_code`
binds separately to `pc.policy-status-code`.

---

## Stage 4 — Canonical Bronze Feed

### 4a. `bronze.policy_lifecycle_event_raw` — one new row

```text
  policy_lifecycle_event_uid   = PLE-12C34D56
  policy_uid                   = POL-7C4D8E10
  policy_term_uid              = TRM-7C4D8E10-2026
  lifecycle_event_type_code    = ENDORSEMENT
  lifecycle_event_status_code  = COMPLETED
  prior_status_code            = ISSUED
  resulting_status_code        = ISSUED
  event_datetime               = 2026-04-15T11:20:00Z
  initiated_by_party_uid       = PTY-MARSH-9E2A
  event_description            = "Add Building C — 220 Riverside Drive, Albany NY"
  triggering_transaction_uid   = PTX-78E90F12
  correction_indicator         = false
  corrects_policy_lifecycle_event_uid = null
```

### 4b. `bronze.policy_transaction_raw` — one new row

```text
  policy_transaction_uid        = PTX-78E90F12
  policy_uid                    = POL-7C4D8E10
  policy_term_uid               = TRM-7C4D8E10-2026
  policy_lifecycle_event_uid    = PLE-12C34D56
  transaction_type_code         = ENDORSEMENT
  transaction_effective_date    = 2026-04-15
  transaction_processed_datetime= 2026-04-15T11:20:00Z
  transaction_sequence_number   = 2
  requested_by_party_uid        = PTY-MARSH-9E2A
  processed_by_party_uid        = PTY-USER-USR104
  premium_change_amount         = 5000.00
  premium_change_currency_code  = USD
  transaction_description       = "Add Building C to scheduled premises"
  correction_indicator          = false
```

---

## Stage 5 — Silver Materialization

The orchestrator runs both templates on every batch, but in this batch
only the append-only template has work to do.

### 5a. Append-only template inserts two new rows

The `silver-append-template` (introduced in [01-bind-and-issue.md](01-bind-and-issue.md#6b-illustrative-append-only-logic-silver-append-template))
joins incoming feed rows against existing Silver rows on
`policy_lifecycle_event_uid` and `policy_transaction_uid`. Both UIDs
are new, so both rows pass the anti-join filter and insert into Silver.

After the load:

```text
silver_policy.policy_lifecycle_event  -- now 3 rows
  PLE-A1B2C3D4   BOUND          2026-02-25T14:30:00Z
  PLE-E5F6A7B8   ISSUED         2026-03-01T08:00:00Z
  PLE-12C34D56   ENDORSEMENT    2026-04-15T11:20:00Z   <- new

silver_policy.policy_transaction     -- now 2 rows
  PTX-C9D0E1F2   NEW_BUSINESS   2026-03-01    +48000.00 USD
  PTX-78E90F12   ENDORSEMENT    2026-04-15    +5000.00 USD   <- new
```

### 5b. SCD2 template runs, but produces no new policy row

The orchestrator also runs `silver-scd2-merge-template` against
`bronze.policy_raw`. There are no new feed rows for `POL-7C4D8E10`
(PAS did not republish the policy header), so the join in step 2 of
the template (recall part 01, stage 5c) returns no rows for that
natural key, and no SCD2 work happens for the policy.

```text
silver_policy.policy   -- unchanged from part 01
  POL-7C4D8E10   policy_status_code = ISSUED   is_current_indicator = true
                  valid_from_datetime = 2026-03-01T09:00:00Z
                  valid_to_datetime   = null
```

This is the intended behavior. The policy header is durable identity
plus current summary; an endorsement that adds coverage to a *child*
contract (such as `pc.policy-coverage` or `pc.policy-location`) does
not need to disturb the policy header row. Coverage and location
contracts have their own SCD2 rows; those are out of scope for this
tutorial slice.

---

## Why The Endorsement Did Not Drive A Policy SCD2 Update

The decision is driven by what the source emits, not by the canonical
loader. The general rule is:

| Source republishes... | Canonical SCD2 effect |
|---|---|
| Nothing on the policy header | No SCD2 work for `pc.policy` |
| The policy header with no canonical-column changes | No-op detected by hash; no new row |
| The policy header with at least one canonical-column change | Close current row, insert new current row |

In part 01, the issue-day republish changed `policy_status_code`,
`issue_date`, and `source_updated_datetime` — the hash differed from the
bind-day row, so SCD2 produced a new current row. In this part, the PAS
sends nothing for the policy header, so the hash comparison never runs
and the existing current row stays untouched.

---

## End-Of-Part-02 State Recap

| Table | Current rows | Historical rows |
|---|---|---|
| `silver_policy.policy` | 1 (status `ISSUED`, unchanged) | 1 (`BOUND`) |
| `silver_core.party` | 2 (unchanged) | 0 |
| `silver_policy.policy_party_role` | 2 (unchanged) | 0 |
| `silver_core.agreement` | 1 (unchanged) | 0 |
| `silver_policy.policy_lifecycle_event` | 3 (added `ENDORSEMENT`) | n/a |
| `silver_policy.policy_transaction` | 2 (added `ENDORSEMENT`, +5000.00) | n/a |

Total premium activity to date for the term: 48000.00 + 5000.00 =
USD 53000.00 written. This number will be useful when we project the
policy_360 view in [05-gold-projection.md](05-gold-projection.md).

Continue with [03-cancellation.md](03-cancellation.md), where the policy
is cancelled mid-term and an SCD2 close-and-replace lands.
