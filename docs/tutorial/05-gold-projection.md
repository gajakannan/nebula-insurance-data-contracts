# 05 — Gold Projection

> **Scenario state.** Parts 01-03 have populated the Silver canonical
> tables for one full lifecycle of policy `POL-7C4D8E10` (Acme/Marsh).
> Part 04 has populated a renewal companion scenario for
> `POL-BEACON-0107` (Beacon/Aon). This part builds Gold consumer views
> from both Silver states. The Silver tables remain untouched — Gold is
> projection only.

Gold is owned by downstream data products, not by this repo. The SQL
shown here is illustrative; production Gold layers may be built in
dbt, a semantic layer, an API service, or a curated lakehouse. The
queries below are written against the Silver schemas defined in parts
01-04 so the reader can trace each output column back to a specific
Silver row.

## What You Will See In This Part

- A `policy_360` view joining the current `pc.policy` row with current
  party, role, agreement, and term-level aggregates from the
  append-only event and transaction tables.
- A `broker_book` view that lists each policy a given party currently
  holds a `BROKER` role on, with current premium and status.
- A `policy_activity_timeline` view that combines lifecycle events and
  transactions into a single chronological feed, with corrections
  filtered out.
- A `policy_term_history` view for the Beacon renewal companion,
  showing why renewal analytics group premium and status by
  `policy_term_uid`, not only by `policy_uid`.

The Acme values returned below match the Silver state recorded at the
end of part 03. The Beacon values match the Silver state recorded in
part 04.

---

## Gold View 1 — `policy_360`

A `policy_360` row gives a single self-contained snapshot of a policy:
identity, business attributes, current parties, current premium, and
the most recent lifecycle event. It joins one current `pc.policy` row
with current rows from related tables and aggregates from append-only
tables.

### 1a. Illustrative query

```sql
-- illustrative — production policy_360 should be a curated dbt model
-- or semantic layer object owned by the downstream data product.
select
  p.policy_uid,
  p.policy_number,
  p.policy_status_code        as current_status,
  p.policy_type_code,
  p.line_of_business_code,
  p.original_effective_date,
  p.issue_date,

  -- insured party (current row)
  ins.party_uid               as insured_party_uid,
  ins.party_display_name      as insured_name,

  -- broker party (current row)
  brk.party_uid               as broker_party_uid,
  brk.party_display_name      as broker_name,
  brk_role.role_status_code   as broker_role_status,

  -- broker-of-record agreement
  agr.agreement_number        as broker_of_record_agreement,
  agr.agreement_status_code   as bor_status,

  -- premium aggregates from append-only transactions
  txn.term_written_premium,
  txn.most_recent_transaction_type,
  txn.most_recent_transaction_effective_date,

  -- most recent non-corrected lifecycle event
  evt.last_event_type,
  evt.last_event_datetime
from silver_policy.policy p
left join silver_policy.policy_party_role insured_role
  on insured_role.policy_uid = p.policy_uid
 and insured_role.role_type_code = 'NAMED_INSURED'
 and insured_role.is_current_indicator = true
left join silver_core.party ins
  on ins.party_uid = insured_role.party_uid
 and ins.is_current_indicator = true
left join silver_policy.policy_party_role brk_role
  on brk_role.policy_uid = p.policy_uid
 and brk_role.role_type_code = 'BROKER'
 and brk_role.primary_role_indicator = true
 and brk_role.is_current_indicator = true
left join silver_core.party brk
  on brk.party_uid = brk_role.party_uid
 and brk.is_current_indicator = true
left join silver_core.agreement agr
  on agr.agreement_uid = p.agreement_uid
 and agr.is_current_indicator = true
left join (
  select
    policy_uid,
    sum(premium_change_amount)                                  as term_written_premium,
    max(transaction_processed_datetime)                         as last_processed,
    max_by(transaction_type_code, transaction_processed_datetime) as most_recent_transaction_type,
    max_by(transaction_effective_date, transaction_processed_datetime)
                                                                as most_recent_transaction_effective_date
  from silver_policy.policy_transaction
  where correction_indicator = false
  group by policy_uid
) txn on txn.policy_uid = p.policy_uid
left join (
  select
    e.policy_uid,
    max_by(e.lifecycle_event_type_code, e.event_datetime) as last_event_type,
    max(e.event_datetime)                                 as last_event_datetime
  from silver_policy.policy_lifecycle_event e
  left anti join (
    select corrects_policy_lifecycle_event_uid as uid
    from silver_policy.policy_lifecycle_event
    where correction_indicator = true
      and corrects_policy_lifecycle_event_uid is not null
  ) c on c.uid = e.policy_lifecycle_event_uid
  group by e.policy_uid
) evt on evt.policy_uid = p.policy_uid
where p.is_current_indicator = true
  and p.policy_uid = 'POL-7C4D8E10'
;
```

### 1b. Resulting row for Acme/Marsh

```text
policy_uid                              = POL-7C4D8E10
policy_number                           = ACME-GL-2026-0042
current_status                          = CANCELLED
policy_type_code                        = NEW_BUSINESS
line_of_business_code                   = GENERAL_LIABILITY
original_effective_date                 = 2026-03-01
issue_date                              = 2026-03-01

insured_party_uid                       = PTY-ACME-4D7C
insured_name                            = "Acme Manufacturing Inc."

broker_party_uid                        = PTY-MARSH-9E2A
broker_name                             = "Marsh Northeast"
broker_role_status                      = TERMINATED

broker_of_record_agreement              = BOR-MARSH-ACME-2024
bor_status                              = ACTIVE

term_written_premium                    = 17000.00          -- 48000 + 5000 - 36000
most_recent_transaction_type            = CANCELLATION
most_recent_transaction_effective_date  = 2026-06-01

last_event_type                         = CANCELLATION
last_event_datetime                     = 2026-06-03T09:10:00Z   -- correction wins
```

The broker-of-record agreement is still `ACTIVE` even though the
broker role on this policy is terminated. The agreement governs the
broker's relationship with Acme; cancelling one policy mid-term does
not cancel the broker-of-record letter.

`term_written_premium` of USD 17,000 is what Acme paid net of return
premium: nine months of unearned premium on the original USD 48,000
annual policy was returned (-USD 36,000), but the +USD 5,000 mid-term
endorsement is fully retained, so net = 48000 + 5000 - 36000 = 17000.
A real Gold model may want a separate "earned premium" metric for
this slice.

`last_event_datetime` is 2026-06-03 (the correction), not 2026-06-01,
because the original cancel event row was filtered out by the
correction back-reference subquery.

---

## Gold View 2 — `broker_book` (For Marsh Northeast)

A `broker_book` row lists every policy a broker currently holds a
primary `BROKER` role on. In our data, only one policy has a Marsh
role row, but the projection generalizes to a broker's full book.

### 2a. Illustrative query

```sql
-- illustrative
select
  brk.party_uid                  as broker_party_uid,
  brk.party_display_name         as broker_name,
  p.policy_uid,
  p.policy_number,
  p.policy_status_code           as policy_status,
  p.line_of_business_code,
  p.original_effective_date,
  brk_role.role_status_code      as broker_role_status,
  brk_role.effective_date        as broker_role_effective,
  brk_role.expiration_date       as broker_role_expiration,
  agr.agreement_number           as broker_of_record_agreement,
  txn.term_written_premium
from silver_core.party brk
join silver_policy.policy_party_role brk_role
  on brk_role.party_uid = brk.party_uid
 and brk_role.role_type_code = 'BROKER'
 and brk_role.primary_role_indicator = true
 and brk_role.is_current_indicator = true
join silver_policy.policy p
  on p.policy_uid = brk_role.policy_uid
 and p.is_current_indicator = true
left join silver_core.agreement agr
  on agr.agreement_uid = p.agreement_uid
 and agr.is_current_indicator = true
left join (
  select policy_uid, sum(premium_change_amount) as term_written_premium
  from silver_policy.policy_transaction
  where correction_indicator = false
  group by policy_uid
) txn on txn.policy_uid = p.policy_uid
where brk.is_current_indicator = true
  and brk.party_uid = 'PTY-MARSH-9E2A'
order by p.original_effective_date desc
;
```

### 2b. Resulting rows for Marsh Northeast

```text
broker_party_uid             = PTY-MARSH-9E2A
broker_name                  = "Marsh Northeast"
policy_uid                   = POL-7C4D8E10
policy_number                = ACME-GL-2026-0042
policy_status                = CANCELLED
line_of_business_code        = GENERAL_LIABILITY
original_effective_date      = 2026-03-01
broker_role_status           = TERMINATED
broker_role_effective        = 2026-03-01
broker_role_expiration       = 2026-06-01
broker_of_record_agreement   = BOR-MARSH-ACME-2024
term_written_premium         = 17000.00
```

The cancelled policy still appears in the broker's book because the
broker role is still the *current* row — it was closed-and-replaced
with `role_status_code = TERMINATED`, not soft-deleted. A "live book"
view would add `where brk_role.role_status_code = 'ACTIVE'` and a
"historical book" view would query the SCD2 historical rows by
`valid_from_datetime`/`valid_to_datetime` window. The Silver layer
preserves the raw history; Gold chooses the framing.

---

## Gold View 3 — `policy_activity_timeline`

The timeline merges lifecycle events and policy transactions into a
single chronological view per policy, filtering out lifecycle events
that have been corrected. This is the consumer surface for activity
panels in a UI or for time-windowed analytics.

### 3a. Illustrative query

```sql
-- illustrative
with corrected_event_uids as (
  select corrects_policy_lifecycle_event_uid as uid
  from silver_policy.policy_lifecycle_event
  where correction_indicator = true
    and corrects_policy_lifecycle_event_uid is not null
),
events as (
  select
    e.policy_uid,
    e.event_datetime              as activity_datetime,
    'EVENT'                       as activity_kind,
    e.lifecycle_event_type_code   as activity_type,
    e.lifecycle_event_status_code as activity_status,
    cast(null as decimal(18,2))   as premium_change_amount,
    e.event_description           as activity_description,
    e.policy_lifecycle_event_uid  as activity_uid,
    case when e.correction_indicator then e.corrects_policy_lifecycle_event_uid end
                                  as supersedes_uid
  from silver_policy.policy_lifecycle_event e
  left anti join corrected_event_uids c
    on c.uid = e.policy_lifecycle_event_uid
),
transactions as (
  select
    t.policy_uid,
    t.transaction_processed_datetime as activity_datetime,
    'TRANSACTION'                    as activity_kind,
    t.transaction_type_code          as activity_type,
    cast(null as string)             as activity_status,
    t.premium_change_amount,
    t.transaction_description        as activity_description,
    t.policy_transaction_uid         as activity_uid,
    case when t.correction_indicator then t.corrects_policy_transaction_uid end
                                     as supersedes_uid
  from silver_policy.policy_transaction t
  where t.correction_indicator = false
)
select *
from (
  select * from events
  union all
  select * from transactions
) activity
order by
  activity_datetime,
  case activity_kind when 'EVENT' then 0 else 1 end,
  activity_uid
;
```

### 3b. Resulting timeline for `POL-7C4D8E10`

```text
2026-02-25T14:30:00Z   EVENT        BOUND          $   --       "Policy bound at $48,000 annual premium"
2026-02-25T14:30:00Z   TRANSACTION  NEW_BUSINESS   +48000.00    "Annual premium for new business term"
2026-03-01T08:00:00Z   EVENT        ISSUED         $   --       "Policy issued and effective"
2026-04-15T11:20:00Z   EVENT        ENDORSEMENT    $   --       "Add Building C — 220 Riverside Drive, Albany NY"
2026-04-15T11:20:00Z   TRANSACTION  ENDORSEMENT    + 5000.00    "Add Building C to scheduled premises"
2026-06-01T16:45:00Z   TRANSACTION  CANCELLATION   -36000.00    "Pro-rata return premium for unearned 9 months"
2026-06-03T09:10:00Z   EVENT        CANCELLATION   $   --       "Cancellation, reason corrected to: voluntary by insured"
                                                                supersedes_uid = PLE-AABB1122
```

Notable points:

- The original cancel event (`PLE-AABB1122`, "non-payment") is absent
  because the correction back-reference filtered it out. The
  correction row carries `supersedes_uid = PLE-AABB1122` so audit
  consumers can still join back to the original.
- The cancel transaction (`PTX-CCDD3344`) appears even though the
  event that triggered it was corrected. Transactions and events are
  separate append-only contracts; correction of one does not imply
  correction of the other. If the back-office had decided the
  transaction also needed to be restated, the PAS would have emitted
  a separate transaction correction row.
- The bind event sits at 2026-02-25 14:30 alongside the new-business
  transaction (which was processed at the same timestamp). The query
  keeps ordering deterministic by sorting on `activity_datetime`,
  `activity_kind`, and `activity_uid`.

---

## Gold View 4 — `policy_term_history` (Beacon Renewal)

Part 04 introduced the renewal modeling convention: the durable
`policy_uid` stays stable while a new `policy_term_uid` represents the
renewal period. A term-history projection makes that explicit for
analytics and UI surfaces that need to show prior and current terms
side by side.

### 4a. Illustrative query

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
  t.annualized_premium_currency_code,
  txn.term_written_premium,
  txn.term_transaction_count,
  evt.last_term_event_type,
  evt.last_term_event_datetime
from silver_policy.policy p
join silver_policy.policy_term t
  on t.policy_uid = p.policy_uid
 and t.is_current_indicator = true
left join (
  select
    policy_uid,
    policy_term_uid,
    sum(premium_change_amount) as term_written_premium,
    count(*)                   as term_transaction_count
  from silver_policy.policy_transaction
  where correction_indicator = false
  group by policy_uid, policy_term_uid
) txn
  on txn.policy_uid = t.policy_uid
 and txn.policy_term_uid = t.policy_term_uid
left join (
  select
    policy_uid,
    policy_term_uid,
    max_by(lifecycle_event_type_code, event_datetime) as last_term_event_type,
    max(event_datetime)                               as last_term_event_datetime
  from silver_policy.policy_lifecycle_event
  where correction_indicator = false
  group by policy_uid, policy_term_uid
) evt
  on evt.policy_uid = t.policy_uid
 and evt.policy_term_uid = t.policy_term_uid
where p.policy_uid = 'POL-BEACON-0107'
  and p.is_current_indicator = true
order by t.policy_term_number
;
```

### 4b. Resulting rows for Beacon/Aon

```text
policy_uid                 = POL-BEACON-0107
policy_number              = BEACON-GL-0107
current_policy_term_uid    = TRM-BEACON-2027

term 1:
  policy_term_uid          = TRM-BEACON-2026
  policy_term_number       = 1
  policy_term_status_code  = EXPIRED
  term_effective_date      = 2026-01-01
  term_expiration_date     = 2027-01-01
  renewal_indicator        = false
  annualized_premium       = 58000.00 USD
  term_written_premium     = 58000.00
  term_transaction_count   = 1
  last_term_event_type     = null
  last_term_event_datetime = null

term 2:
  policy_term_uid          = TRM-BEACON-2027
  policy_term_number       = 2
  policy_term_status_code  = ACTIVE
  term_effective_date      = 2027-01-01
  term_expiration_date     = 2028-01-01
  renewal_indicator        = true
  annualized_premium       = 64000.00 USD
  term_written_premium     = 64000.00
  term_transaction_count   = 1
  last_term_event_type     = ISSUED
  last_term_event_datetime = 2027-01-01T00:05:00Z
```

The current policy row points to `TRM-BEACON-2027`, but both current
term identities are returned because `is_current_indicator = true` is
evaluated per `policy_term_uid`. `TRM-BEACON-2026` is the current
version of an expired business term, while `TRM-BEACON-2027` is the
current version of the active renewal term.

This is why renewal Gold models should aggregate premium by
`policy_uid, policy_term_uid`. Grouping only by `policy_uid` would
collapse the original and renewal terms into one USD 122,000 number
and hide the renewal boundary.

---

## How Downstream Products Build On This

The views above are *one* way to project Silver. Realistic
downstream products typically:

- Materialize Gold tables in dbt or a curated lakehouse, refreshed on
  a schedule, with their own contract that documents grain, metrics,
  and SLAs.
- Build a semantic model (Power BI, Looker, Cube, dbt Semantic Layer)
  on top of the Silver canonical tables so analysts join by
  conformed natural keys (`policy_uid`, `party_uid`, `agreement_uid`)
  without needing to know SCD2 mechanics.
- Expose REST or GraphQL APIs that wrap the same Silver-side joins
  with `is_current_indicator = true` filters baked in.
- Stream events into AI/ML feature stores keyed on canonical UIDs,
  using the append-only event stream as the system of record for
  state changes.

In every case, Silver remains the single source of truth and Gold
remains projection. If a consumer needs a column that Silver does
not carry, the right move is to add that column to the canonical
contract (with versioning), not to pile it into a Gold model where
it cannot be reused.

---

## Tutorial Wrap-Up

Across parts 01-05, you have followed:

- One Acme policy through new business, endorsement, cancellation,
  correction, and Gold current-state/activity projections.
- One Beacon policy through renewal, term-history materialization, and
  Gold term-history projection.

The common flow is:

1. **Source records** emitted by PAS, agency portal, and broker
   systems on bind day, issue day, endorsement day, cancel day,
   correction day, and renewal day.
2. **Raw Bronze** — source-shaped, immutable, with ingestion
   metadata.
3. **Source-to-canonical conformance** — code translations, UID
   resolution, and the broker-source-row split into party + role +
   agreement.
4. **Canonical Bronze feed** — the boundary at which the contracts in
   this repo take ownership.
5. **Silver materialization** — SCD2 close-and-replace for durable
   entities, append-only inserts for events and transactions, with
   correction rows captured immutably.
6. **Gold projection** — example queries that demonstrate how
   consumers compose the Silver tables into product-shaped views,
   choosing whether to surface live state, historical state, or both.

For deeper detail on any single contract, return to its ODCS file
under `references/odcs/pc/`. For deeper detail on the SCD2 merge or
append-only template, see the notebooks under
`targets/fabric/notebooks/`. The validators under `scripts/validation/`
are the authoritative source on what a Silver row must look like at
load time.
