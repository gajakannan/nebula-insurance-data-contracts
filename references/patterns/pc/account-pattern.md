# Account Pattern

Use the account pattern to model commercial-lines master customer relationships, agreement-driven coverage programs, and account-level rollups for premium, financial activity, and loss runs.

## Intent

In commercial Property and Casualty insurance, a single customer relationship typically owns multiple policies across different lines of business, sometimes under master agreements that govern shared terms, pricing, billing, and service-level commitments. Without an account spine, every account-level question (total exposure, master-program rollup, billing aggregation, loss runs across the customer) becomes a multi-table reconstruction.

The Account pattern lifts that spine into the canonical layer. Personal-lines policies can leave `account_uid` and `agreement_uid` null; commercial-lines policies populate them and gain a one-hop path to account context.

## Recommended Contracts

```text
Account
AccountRelationship
AccountPartyRole
Agreement
```

`Account` is the master customer entity. `AccountRelationship` carries the corporate-hierarchy and program-structure relationships that the simple `parent_account_uid` self-FK on Account cannot fully express (billing parent ≠ underwriting parent ≠ ultimate parent). `AccountPartyRole` carries account-scoped party participations (account manager, billing contact, key insured contact). `Agreement` carries the master legal or program contract that governs how policies are issued under the account.

## Modeling Guidance

### Account hierarchy

The Account contract carries a `parent_account_uid` self-FK for the **primary** parent in a corporate hierarchy. This handles the 90% case ("give me the immediate parent of this account") with a single join.

For richer cases — multiple parents, time-bounded restructurings, mergers, demergers, master-program enrollments distinct from the corporate hierarchy — use `AccountRelationship`. The relationship type code distinguishes parent-child variants:

```text
PARENT
BILLING_PARENT
UNDERWRITING_PARENT
ULTIMATE_PARENT
MASTER_PROGRAM
MERGED_INTO
DEMERGED_FROM
```

Both shapes coexist: consumers needing the simple parent walk the self-FK; consumers needing multi-relationship semantics walk `AccountRelationship`. Denormalized views (e.g. `ultimate_parent_account_uid`) are a target-side concern, not a canonical-layer column.

### Agreement

`Agreement` represents the master legal or program contract between insurer and an account, broker, MGA, or program administrator. One agreement can spawn many policies; one policy can reference at most one agreement. Examples:

```text
MASTER_PROGRAM        # large account or association master program
BROKER_AUTHORITY      # binding authority granted to a broker
MGA_AUTHORITY         # binding authority granted to an MGA
SERVICE_AGREEMENT     # account-level service-level agreement
BINDER_AGREEMENT      # binder issued before policy issue
```

Agreement is a separate contract from Policy because it has its own lifecycle (negotiation, signing, renewal, termination) independent of the policies it spawns, and because aggregation at agreement level (program performance, broker authority utilization) is a primary commercial-lines query.

### FK propagation

Contracts that gain an `account_uid` direct FK for one-hop rollups:

- `Policy` — `account_uid` and `agreement_uid` (both nullable; populated for commercial)
- `Submission` — `account_uid` and `agreement_uid` (commercial submissions land at account level, often before any policy is quoted)
- `Claim` — `account_uid` only (loss runs by account in one hop; agreement reachable via policy when needed)
- `PolicyFinancialTransaction` — `account_uid` and `agreement_uid` (account-level financial rollups, master-program billing, account-level commission accruals)

Personal-lines instances leave the FKs null. The validator does not require population; it requires that when populated, the values resolve.

### What is *not* in this pattern

- **`AgreementPartyRole`** — agreement-level parties are usually the two counterparties (captured directly on Agreement) plus one-time signatories (captured on documents). The role contract pattern earns its weight where a context has many distinct parties evolving over time; agreements do not fit that shape strongly. Add later if a use case bites.
- **`AgreementRelationship`** — agreements rarely have parent-child structure; the hierarchy lives at Account.
- **`AgreementCoverage`** — pre-bound coverage flow from master programs is real but defers cleanly. Once `Coverage` is well-shaped and a use case bites, this is a thin junction add.
- **`InsuredAccount`** — variant of Account; modeled via `account_type_code` (e.g. `INSURED_LARGE`, `INSURED_MIDMARKET`) rather than as a separate contract.

## Related

- `references/design-decisions/pc/role-modeling.md` — Party identity vs. contextual role participation, including account-level roles.
- `references/design-decisions/pc/entity-boundaries.md` — when a concept earns a contract vs. an attribute.
- `references/design-decisions/pc/identifier-strategy.md` — `*_uid` GUID identity and `*_number` business keys.
- `references/patterns/pc/party-role-pattern.md` — the broader party-role pattern that AccountPartyRole instantiates.
