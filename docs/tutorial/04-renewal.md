# 04 — Renewal Term

> **Scenario state.** This is a separate companion scenario from the
> Acme cancellation walkthrough in parts 01-03. Beacon Foods Inc. has a
> General Liability policy that reaches the end of its first annual term
> normally. The carrier offers a renewal, the broker accepts it, and the
> PAS issues the next annual term. This part shows the core renewal
> modeling choice: keep the durable `policy_uid`, create a new
> `policy_term_uid`, and SCD2-update `pc.policy.current_policy_term_uid`.

The source snippets, code values, and UIDs below are illustrative. The
contract shape is anchored in `pc.policy`, `pc.policy-term`,
`pc.policy-party-role`, `pc.policy-lifecycle-event`, and
`pc.policy-transaction`.

## What You Will See In This Part

- A renewal keeps the same durable `policy_uid` when it is the next term
  in the same policy history.
- A renewal creates a new `policy_term_uid` for the new effective period.
- The current `pc.policy` row closes and replaces because
  `current_policy_term_uid` and current summary fields change.
- The expiring `pc.policy-term` row closes and replaces with status
  `EXPIRED`; the renewal term inserts as a new current term row.
- Term-specific broker and insured roles carry forward as new
  `pc.policy-party-role` rows for the renewal term.
- Renewal lifecycle events and the renewal transaction append without
  mutating prior rows.

---

## Running Scenario

| Item | Value |
|---|---|
| Insured | Beacon Foods Inc. |
| Broker | Aon Midwest (organization) |
| Line of business | General Liability |
| Policy number | `BEACON-GL-0107` |
| Expiring term | 2026-01-01 to 2027-01-01 |
| Renewal term | 2027-01-01 to 2028-01-01 |
| Expiring annual premium | USD 58,000 |
| Renewal annual premium | USD 64,000 |
| Source system | `NEBULA_PAS` |

Canonical identifiers used in this part:

| Concept | Canonical UID |
|---|---|
| Account (Beacon) | `ACCT-BEACON-22C1` |
| Policy | `POL-BEACON-0107` |
| Expiring policy term | `TRM-BEACON-2026` |
| Renewal policy term | `TRM-BEACON-2027` |
| Insured party | `PTY-BEACON-8821` |
| Broker party | `PTY-AON-7714` |
| Expiring broker role | `PPR-BEACON-BRK-2026` |
| Renewal broker role | `PPR-BEACON-BRK-2027` |
| Expiring insured role | `PPR-BEACON-INS-2026` |
| Renewal insured role | `PPR-BEACON-INS-2027` |

## Stage 0 - Starting Silver State

Before the renewal batch lands, Beacon's first term is issued and current.

```text
silver_policy.policy
  policy_uid                   = POL-BEACON-0107
  policy_number                = BEACON-GL-0107
  policy_status_code           = ISSUED
  policy_type_code             = NEW_BUSINESS
  current_policy_term_uid      = TRM-BEACON-2026
  prior_policy_uid             = null
  is_current_indicator         = true

silver_policy.policy_term
  policy_term_uid              = TRM-BEACON-2026
  policy_uid                   = POL-BEACON-0107
  policy_term_number           = 1
  policy_term_status_code      = ACTIVE
  term_effective_date          = 2026-01-01
  term_expiration_date         = 2027-01-01
  renewal_indicator            = false
  annualized_premium_amount    = 58000.00
  annualized_premium_currency_code = USD
  is_current_indicator         = true

silver_policy.policy_transaction
  PTX-BEACON-NB-2026           NEW_BUSINESS
  policy_term_uid              = TRM-BEACON-2026
  transaction_effective_date   = 2026-01-01
  premium_change_amount        = 58000.00
  premium_change_currency_code = USD
```

The existing broker and insured role rows are term-specific because their
`policy_term_uid` points at `TRM-BEACON-2026`.

---

## Stage 1 - Source Records

The PAS emits a renewal offer, then a renewal bind/issue package. The
important source behavior is that `policy_id` remains the same and
`current_term_id` changes to the new term.

### 1a. Policy header republish

```text
source: nebula_pas.policy
  policy_id           = 200107
  policy_no           = BEACON-GL-0107
  policy_status       = I
  policy_type         = REN
  lob                 = GL
  account_id          = ACCT-99107
  product_id          = PROD-GL-STD
  issue_dt            = 2026-12-20
  orig_eff_dt         = 2026-01-01
  current_term_id     = TERM-200107-2
  prior_policy_id     = null              -- same durable policy, new term
  description         = "Beacon GL renewal, 2027 term"
  created_ts          = 2025-12-18T10:00:00Z
  updated_ts          = 2026-12-20T16:05:00Z
```

### 1b. Policy term rows

```text
source: nebula_pas.policy_term  (expiring term republish)
  term_id             = TERM-200107-1
  policy_id           = 200107
  term_no             = 1
  term_status         = EXP
  effective_dt        = 2026-01-01
  expiration_dt       = 2027-01-01
  cancellation_dt     = null
  renewal_flag        = N
  annual_premium      = 58000.00
  currency            = USD
  updated_ts          = 2027-01-01T00:05:00Z

source: nebula_pas.policy_term  (renewal term)
  term_id             = TERM-200107-2
  policy_id           = 200107
  term_no             = 2
  term_status         = ACT
  effective_dt        = 2027-01-01
  expiration_dt       = 2028-01-01
  cancellation_dt     = null
  renewal_flag        = Y
  annual_premium      = 64000.00
  currency            = USD
  created_ts          = 2026-12-20T16:05:00Z
  updated_ts          = 2026-12-20T16:05:00Z
```

### 1c. Carried-forward term roles

```text
source: nebula_pas.policy_role  (broker, renewal term)
  role_id             = ROLE-7714-2027
  policy_id           = 200107
  term_id             = TERM-200107-2
  party_ref_type      = BROKER_ORG
  party_ref_id        = AON-7714
  role                = BROKER
  role_status         = ACTIVE
  primary_broker_flag = Y
  effective_dt        = 2027-01-01
  expiration_dt       = null

source: nebula_pas.policy_role  (named insured, renewal term)
  role_id             = ROLE-8821-2027
  policy_id           = 200107
  term_id             = TERM-200107-2
  party_ref_type      = ACCOUNT_ORG
  party_ref_id        = ORG-8821
  role                = NAMED_INSURED
  role_status         = ACTIVE
  primary_broker_flag = N
  effective_dt        = 2027-01-01
  expiration_dt       = null
```

### 1d. Renewal events and transaction

```text
source: nebula_pas.policy_event  (renewal offered)
  policy_event_id     = EVT-771401
  policy_id           = 200107
  term_id             = TERM-200107-2
  event_type          = RENEWAL_OFFERED
  event_status        = COMPLETED
  prior_status        = ISSUED
  new_status          = OFFERED
  event_ts            = 2026-11-15T13:00:00Z
  initiated_by_org_id = null
  event_text          = "Renewal offer generated"
  transaction_id      = null

source: nebula_pas.policy_event  (renewal bound)
  policy_event_id     = EVT-771402
  policy_id           = 200107
  term_id             = TERM-200107-2
  event_type          = RENEWAL_BOUND
  event_status        = COMPLETED
  prior_status        = OFFERED
  new_status          = BOUND
  event_ts            = 2026-12-20T16:05:00Z
  initiated_by_org_id = AON-7714
  event_text          = "Renewal accepted by broker"
  transaction_id      = TXN-771402

source: nebula_pas.policy_event  (renewal issued)
  policy_event_id     = EVT-771403
  policy_id           = 200107
  term_id             = TERM-200107-2
  event_type          = ISSUED
  event_status        = COMPLETED
  prior_status        = BOUND
  new_status          = ISSUED
  event_ts            = 2027-01-01T00:05:00Z
  initiated_by_org_id = null
  event_text          = "Renewal term issued and effective"
  transaction_id      = null

source: nebula_pas.policy_txn
  transaction_id      = TXN-771402
  policy_id           = 200107
  term_id             = TERM-200107-2
  policy_event_id     = EVT-771402
  transaction_type    = REN
  effective_dt        = 2027-01-01
  processed_ts        = 2026-12-20T16:05:00Z
  sequence_no         = 1
  requested_by_org_id = AON-7714
  processed_by_user_id = USR-331
  premium_delta       = 64000.00
  currency            = USD
  description         = "Annual premium for renewal term"
```

---

## Stage 2 - Source-To-Canonical Mapping

The conformance job resolves the same durable `policy_uid` and creates a
new term UID for `TERM-200107-2`.

| Source field or code | Canonical field or code | Notes |
|---|---|---|
| `policy_id = 200107` | `policy_uid = POL-BEACON-0107` | Same durable policy identity as the expiring term |
| `current_term_id = TERM-200107-2` | `current_policy_term_uid = TRM-BEACON-2027` | Policy now points at the renewal term |
| `prior_policy_id = null` | `prior_policy_uid = null` | Same durable policy; no replacement-chain policy |
| `policy_type = REN` | `policy_type_code = RENEWAL` | Current policy summary reflects the renewal processing context |
| `term_status = EXP` | `policy_term_status_code = EXPIRED` | Expiring term status |
| `term_status = ACT` | `policy_term_status_code = ACTIVE` | Renewal term status |
| `renewal_flag = Y` | `renewal_indicator = true` | Term-level renewal marker |
| `transaction_type = REN` | `transaction_type_code = RENEWAL` | Renewal transaction |

Lifecycle event `prior_status_code`, `resulting_status_code`, and
`lifecycle_event_status_code` bind to `pc.lifecycle-status`. The policy
header `policy_status_code` binds to `pc.policy-status-code`, and
`policy_term_status_code` binds to `pc.term-status-code`.

Some deployments keep `policy_type_code` as the original acquisition type
(`NEW_BUSINESS`) and rely on `pc.policy-term.renewal_indicator` for term
classification. This example uses `policy_type_code = RENEWAL` to show the
current processing context. The core renewal invariant is the same either
way: the durable `policy_uid` remains stable and the policy points to a new
`current_policy_term_uid`.

---

## Stage 3 - Canonical Bronze Feed

### 3a. `bronze.policy_raw`

```text
  policy_uid                   = POL-BEACON-0107
  source_system_code           = NEBULA_PAS
  source_natural_key           = "200107"
  policy_number                = BEACON-GL-0107
  policy_status_code           = ISSUED
  policy_type_code             = RENEWAL
  line_of_business_code        = GENERAL_LIABILITY
  account_uid                  = ACCT-BEACON-22C1
  product_uid                  = PROD-GL-STD
  original_effective_date      = 2026-01-01
  issue_date                   = 2026-12-20
  current_policy_term_uid      = TRM-BEACON-2027
  prior_policy_uid             = null
  policy_description           = "Beacon GL renewal, 2027 term"
  source_created_datetime      = 2025-12-18T10:00:00Z
  source_updated_datetime      = 2026-12-20T16:05:00Z
```

### 3b. `bronze.policy_term_raw`

```text
row 1 (expiring term republish):
  policy_term_uid              = TRM-BEACON-2026
  source_system_code           = NEBULA_PAS
  source_natural_key           = "TERM-200107-1"
  policy_uid                   = POL-BEACON-0107
  policy_term_number           = 1
  policy_term_status_code      = EXPIRED
  term_effective_date          = 2026-01-01
  term_expiration_date         = 2027-01-01
  cancellation_date            = null
  renewal_indicator            = false
  annualized_premium_amount    = 58000.00
  annualized_premium_currency_code = USD
  source_updated_datetime      = 2027-01-01T00:05:00Z

row 2 (renewal term):
  policy_term_uid              = TRM-BEACON-2027
  source_system_code           = NEBULA_PAS
  source_natural_key           = "TERM-200107-2"
  policy_uid                   = POL-BEACON-0107
  policy_term_number           = 2
  policy_term_status_code      = ACTIVE
  term_effective_date          = 2027-01-01
  term_expiration_date         = 2028-01-01
  cancellation_date            = null
  renewal_indicator            = true
  annualized_premium_amount    = 64000.00
  annualized_premium_currency_code = USD
  source_created_datetime      = 2026-12-20T16:05:00Z
  source_updated_datetime      = 2026-12-20T16:05:00Z
```

### 3c. `bronze.policy_party_role_raw`

```text
row 1 (broker, renewal term):
  policy_party_role_uid        = PPR-BEACON-BRK-2027
  source_system_code           = NEBULA_PAS
  source_natural_key           = "ROLE-7714-2027"
  policy_uid                   = POL-BEACON-0107
  policy_term_uid              = TRM-BEACON-2027
  party_uid                    = PTY-AON-7714
  role_type_code               = BROKER
  role_status_code             = ACTIVE
  primary_role_indicator       = true
  effective_date               = 2027-01-01
  expiration_date              = null

row 2 (named insured, renewal term):
  policy_party_role_uid        = PPR-BEACON-INS-2027
  source_system_code           = NEBULA_PAS
  source_natural_key           = "ROLE-8821-2027"
  policy_uid                   = POL-BEACON-0107
  policy_term_uid              = TRM-BEACON-2027
  party_uid                    = PTY-BEACON-8821
  role_type_code               = NAMED_INSURED
  role_status_code             = ACTIVE
  primary_role_indicator       = false
  effective_date               = 2027-01-01
  expiration_date              = null
```

### 3d. Append-only feed rows

```text
bronze.policy_lifecycle_event_raw
  PLE-BEACON-OFFERED-2027   RENEWAL_OFFERED   2026-11-15T13:00:00Z
  PLE-BEACON-BOUND-2027     RENEWAL_BOUND     2026-12-20T16:05:00Z
  PLE-BEACON-ISSUED-2027    ISSUED            2027-01-01T00:05:00Z

bronze.policy_transaction_raw
  PTX-BEACON-REN-2027       RENEWAL           2027-01-01   +64000.00 USD
```

---

## Stage 4 - Silver Materialization

### 4a. `silver_policy.policy` closes and replaces

The SCD2 hash for `POL-BEACON-0107` changes because
`current_policy_term_uid`, `policy_type_code`, `issue_date`, and
`source_updated_datetime` changed.

```text
POL-BEACON-0107 after renewal issue

Row 1 (closed):
  policy_type_code        = NEW_BUSINESS
  current_policy_term_uid = TRM-BEACON-2026
  record_status_code      = SUPERSEDED
  is_current_indicator    = false

Row 2 (new current):
  policy_type_code        = RENEWAL
  policy_status_code      = ISSUED
  current_policy_term_uid = TRM-BEACON-2027
  record_status_code      = ACTIVE
  is_current_indicator    = true
```

### 4b. `silver_policy.policy_term` updates the old term and inserts the new term

```text
TRM-BEACON-2026 after renewal effective date

Row 1 (closed):
  policy_term_status_code = ACTIVE
  record_status_code      = SUPERSEDED
  is_current_indicator    = false

Row 2 (new current for the same term identity):
  policy_term_status_code = EXPIRED
  term_effective_date     = 2026-01-01
  term_expiration_date    = 2027-01-01
  renewal_indicator       = false
  record_status_code      = ACTIVE
  is_current_indicator    = true

TRM-BEACON-2027
  policy_term_status_code = ACTIVE
  term_effective_date     = 2027-01-01
  term_expiration_date    = 2028-01-01
  renewal_indicator       = true
  annualized_premium_amount = 64000.00
  annualized_premium_currency_code = USD
  record_status_code      = ACTIVE
  is_current_indicator    = true
```

### 4c. Roles, events, and transaction

Because roles are term-specific in this scenario, the renewal term gets
new current role rows. The expiring term's role rows remain available for
historical term queries. A live-book query should consider both role status
and term status; an `ACTIVE` role on an `EXPIRED` term is historical, not
currently in force.

```text
silver_policy.policy_party_role
  PPR-BEACON-BRK-2026   BROKER          TRM-BEACON-2026   ACTIVE
  PPR-BEACON-INS-2026   NAMED_INSURED   TRM-BEACON-2026   ACTIVE
  PPR-BEACON-BRK-2027   BROKER          TRM-BEACON-2027   ACTIVE   <- new
  PPR-BEACON-INS-2027   NAMED_INSURED   TRM-BEACON-2027   ACTIVE   <- new

silver_policy.policy_lifecycle_event
  PLE-BEACON-OFFERED-2027   RENEWAL_OFFERED
  PLE-BEACON-BOUND-2027     RENEWAL_BOUND
  PLE-BEACON-ISSUED-2027    ISSUED

silver_policy.policy_transaction
  PTX-BEACON-NB-2026        NEW_BUSINESS   policy_term_uid = TRM-BEACON-2026   +58000.00 USD
  PTX-BEACON-REN-2027       RENEWAL   policy_term_uid = TRM-BEACON-2027   +64000.00 USD
```

---

## Renewal Query Pattern

Gold consumers usually need both current policy state and term history.
The term grain is important: premium should be grouped by
`policy_term_uid`, not only by `policy_uid`, otherwise multiple terms get
collapsed together.

```sql
-- illustrative
select
  p.policy_uid,
  p.policy_number,
  p.current_policy_term_uid,
  t.policy_term_uid,
  t.policy_term_number,
  t.policy_term_status_code,
  t.term_effective_date,
  t.term_expiration_date,
  t.renewal_indicator,
  t.annualized_premium_amount,
  txn.term_written_premium
from silver_policy.policy p
join silver_policy.policy_term t
  on t.policy_uid = p.policy_uid
 and t.is_current_indicator = true
left join (
  select
    policy_uid,
    policy_term_uid,
    sum(premium_change_amount) as term_written_premium
  from silver_policy.policy_transaction
  where correction_indicator = false
  group by policy_uid, policy_term_uid
) txn
  on txn.policy_uid = t.policy_uid
 and txn.policy_term_uid = t.policy_term_uid
where p.policy_uid = 'POL-BEACON-0107'
  and p.is_current_indicator = true
order by t.policy_term_number
;
```

Result:

```text
policy_uid        policy_term_uid    term_no  status   renewal  annualized_premium  written_premium
POL-BEACON-0107   TRM-BEACON-2026   1        EXPIRED  false    58000.00            58000.00
POL-BEACON-0107   TRM-BEACON-2027   2        ACTIVE   true     64000.00            64000.00
```

The policy's current pointer is `TRM-BEACON-2027`, but the expired term
remains queryable as a current row for that term identity. SCD2 currentness
is scoped to a logical key, not to "the currently active business term."

---

## When To Use `prior_policy_uid`

This example keeps `policy_uid = POL-BEACON-0107` across renewal because
the renewal is modeled as the next term in one durable policy history.

Use a new `policy_uid` with `prior_policy_uid` only when the business has a
new durable policy identity, such as a rewrite, replacement policy, or a
source/platform convention where each renewal is legally and operationally
issued as a new policy record. In that pattern:

```text
renewal policy_uid      = POL-BEACON-0107-R2
prior_policy_uid        = POL-BEACON-0107
current_policy_term_uid = TRM-BEACON-2027
```

Do not populate `prior_policy_uid` merely because a new term exists. The
term relationship is represented by `pc.policy-term`; `prior_policy_uid`
represents a durable-policy chain.

Continue with [05-gold-projection.md](05-gold-projection.md), where the
tutorial projects Silver rows into consumer views.
