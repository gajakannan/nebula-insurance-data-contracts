# Layered Data Flow Tutorial

A row-level walkthrough of how P&C policies move from source systems
through Bronze, canonical Silver, generated Fabric artifacts, and Gold
consumption. Parts 01-03 share one new-business-through-cancellation
scenario, so the same policy, broker, account, term, and party identifiers
can be traced across stages. Part 04 is a separate renewal companion
scenario focused on `policy_uid` and `policy_term_uid` behavior. Part 05
projects the tutorial state into Gold-style consumer views.

This is illustrative material, not a new contract source. The authoritative
contracts remain under `references/odcs/pc/`, the authoritative manifests and
generated artifacts remain under `targets/fabric/`, and the validators in
`scripts/` remain the source of truth for what a Silver row must look like.
The snippets in these parts are tagged "illustrative" wherever they show a
manifest, DDL, or notebook fragment — they are written for clarity and may
omit detail you would see in the real generated files.

## Reading Order

| Part | What it covers |
|---|---|
| [01-bind-and-issue.md](01-bind-and-issue.md) | Source rows from PAS, agency, and submission portals; raw Bronze landing; source-to-canonical mapping; canonical Bronze feed; first Silver SCD2 rows for the policy, broker party, role, and broker-of-record agreement; bind and issue lifecycle events and the new-business transaction. |
| [02-endorsement.md](02-endorsement.md) | A mid-term endorsement that adds coverage and a positive premium delta. Shows the append-only path: lifecycle event row and transaction row land in Silver while the SCD2 policy row is unchanged because the policy header did not materially change. |
| [03-cancellation.md](03-cancellation.md) | Cancellation event, return-premium transaction, the SCD2 close-and-replace on the policy row when its status changes from `ISSUED` to `CANCELLED`, the role row closing, and a correction-row example showing append-only correction semantics. |
| [04-renewal.md](04-renewal.md) | Separate renewal companion scenario showing durable `policy_uid`, new `policy_term_uid`, `current_policy_term_uid` SCD2 update, term expiration, carried-forward roles, and renewal term-history queries. |
| [05-gold-projection.md](05-gold-projection.md) | Example consumer queries against the Silver tables built up across parts 01-04: Acme `policy_360`, `broker_book`, and activity timeline views, plus a Beacon renewal `policy_term_history` view. |

## Running Scenario For Parts 01-03

| Item | Value |
|---|---|
| Insured | Acme Manufacturing Inc. |
| Broker | Marsh Northeast (organization) |
| Line of business | General Liability |
| Policy number | `ACME-GL-2026-0042` |
| Term | 2026-03-01 to 2027-03-01 |
| Initial annual premium | USD 48,000 |
| Source system | `NEBULA_PAS` (policy admin system) |

| Date | Event |
|---|---|
| 2026-02-15 | Submission created in agency portal |
| 2026-02-25 | Quote accepted, policy bound |
| 2026-03-01 | Policy issued and effective; initial transaction posted |
| 2026-04-15 | Endorsement adds Building C; +USD 5,000 premium |
| 2026-06-01 | Policy cancelled mid-term; pro-rata return of premium |

Canonical identifiers used throughout parts 01-03 (illustrative GUIDs):

| Concept | Canonical UID |
|---|---|
| Account (Acme) | `ACCT-1F6E9A2B` |
| Policy | `POL-7C4D8E10` |
| Policy term | `TRM-7C4D8E10-2026` |
| Insured party | `PTY-ACME-4D7C` |
| Broker party | `PTY-MARSH-9E2A` |
| Broker-of-record agreement | `AGR-3B5F2A91` |
| Broker policy-party-role | `PPR-2F8B1C50` |
| Insured policy-party-role | `PPR-9A4D7E22` |

The account and policy term identifiers are referenced context in parts
01-03. Those parts carry `account_uid`, `policy_term_uid`, and
`current_policy_term_uid` as foreign keys, but do not materialize
`pc.account` or `pc.policy-term` rows. Part 04 materializes
`pc.policy-term` rows to show renewal behavior.

Source-side identifiers (from PAS):

| Concept | Source identifier |
|---|---|
| `policy_id` | `100042` |
| `policy_no` | `ACME-GL-2026-0042` |
| `account_id` | `ACCT-44213` |
| `broker_org_id` | `BR-7821` |
| `insured_org_id` | `ORG-31178` |

## Stage Map

```text
Source Systems              Raw Bronze                Canonical Bronze         Silver Canonical            Gold Consumers
(PAS, agency,               (source-shaped,           Feed (canonical          (this repo's contracts)     (downstream)
 submission, billing)        immutable, with          vocabulary, prepared
                             ingestion metadata)      for generated notebooks)

policy/broker/event   --->  bronze_pas.policy_raw_src     --->  bronze.policy_raw           --->  silver_policy.policy            --->  policy_360
records emitted by          bronze_pas.policy_term_       bronze.policy_term_raw            silver_policy.policy_term             broker_book
source applications         raw_src                       bronze.party_raw                  silver_core.party                     activity timeline
                            bronze_agency.broker_org_     bronze.policy_party_role_raw      silver_policy.policy_party_role       marts, semantic
                            raw_src                       bronze.agreement_raw              silver_core.agreement                 models, APIs
                            bronze_pas.policy_event_      bronze.policy_lifecycle_event_raw silver_policy.policy_lifecycle_event
                            raw_src
                            bronze_pas.transaction_       bronze.policy_transaction_raw     silver_policy.policy_transaction
                            raw_src
                                       |                            |                                 |                                 |
                          ingestion metadata        source-to-canonical             generated Fabric                  projection,
                          appended (_ingested_at,   conformance job                 notebooks (SCD2                   aggregation,
                          _source_file,             (resolves *_uid keys,           merge or append-only              semantic
                          _payload_hash)            normalizes codes,               with codeset and                  modeling
                                                    splits broker into              quality validation)
                                                    party + role + optional
                                                    agreement)
```

## Ownership Map

| Stage | Shape | Owner |
|---|---|---|
| Source systems | Source-native policy, party, broker, event, and transaction records | Policy admin, submission, agency, claims, billing, or vendor systems |
| Raw Bronze | Immutable source-shaped landing tables with ingestion metadata | Ingestion platform outside this repo |
| Source-to-canonical mapping | Raw source fields mapped to canonical fields and keys | Data engineering implementation outside this repo |
| Canonical Bronze feed | Canonical-shaped feed tables consumed by generated Fabric notebooks | Platform implementation guided by this repo |
| Silver contracts | ODCS canonical contracts and generated Silver table metadata | This repo |
| Fabric artifacts | Manifests, DDL, notebooks, Purview JSON | Generated by scripts in this repo |
| Gold consumption | Policy 360, broker book, activity timelines, marts, semantic models, APIs | Downstream data products |

## Reshape Responsibilities

| Reshape | Component | What changes |
|---|---|---|
| Source to raw Bronze | Ingestion outside this repo | Preserves source shape, adds ingestion metadata, does not canonicalize business meaning |
| Raw Bronze to canonical Bronze feed | Source-to-canonical mapper outside this repo | Resolves canonical identifiers, translates field names, normalizes codes, splits overloaded source records into canonical entities and events |
| ODCS contract to Fabric manifest | `scripts/generation/generate-fabric-manifests.py` | Projects contract fields to Spark types, role tags, codeset bindings, SCD2 or append-only behavior, quality rules, Bronze table defaults |
| Manifest to DDL | `scripts/generation/generate-fabric-ddl.py` | Emits Spark SQL table definitions for the Silver tables |
| Manifest to notebook templates | `scripts/generation/generate-fabric-notebooks.py` | Emits generic SCD2, append-only, and codeset loaders driven by manifests |
| Manifest to governance metadata | `scripts/generation/generate-fabric-purview.py` | Emits sensitivity labels and glossary bindings |
| Silver to Gold | Downstream model, dbt, semantic layer, API, or notebook implementation | Joins and projects canonical tables into consumption-specific views |

## Fabric Artifact View

For each canonical contract used in this tutorial, generation produces the
same family of artifacts.

| Contract | Manifest path | DDL path | Runtime notebook template |
|---|---|---|---|
| `pc.policy` | `targets/fabric/manifests/pc/policy/policy.fabric.yaml` | `targets/fabric/ddl/pc/policy/policy.spark.sql` | `silver-scd2-merge-template.ipynb` |
| `pc.policy-term` | `targets/fabric/manifests/pc/policy/policy-term.fabric.yaml` | `targets/fabric/ddl/pc/policy/policy-term.spark.sql` | `silver-scd2-merge-template.ipynb` |
| `pc.party` | `targets/fabric/manifests/pc/core/party.fabric.yaml` | `targets/fabric/ddl/pc/core/party.spark.sql` | `silver-scd2-merge-template.ipynb` |
| `pc.policy-party-role` | `targets/fabric/manifests/pc/policy/policy-party-role.fabric.yaml` | `targets/fabric/ddl/pc/policy/policy-party-role.spark.sql` | `silver-scd2-merge-template.ipynb` |
| `pc.agreement` | `targets/fabric/manifests/pc/core/agreement.fabric.yaml` | `targets/fabric/ddl/pc/core/agreement.spark.sql` | `silver-scd2-merge-template.ipynb` |
| `pc.policy-lifecycle-event` | `targets/fabric/manifests/pc/policy/policy-lifecycle-event.fabric.yaml` | `targets/fabric/ddl/pc/policy/policy-lifecycle-event.spark.sql` | `silver-append-template.ipynb` |
| `pc.policy-transaction` | `targets/fabric/manifests/pc/policy/policy-transaction.fabric.yaml` | `targets/fabric/ddl/pc/policy/policy-transaction.spark.sql` | `silver-append-template.ipynb` |

## Validation Points

| Point | What is checked | Tool or component |
|---|---|---|
| Contract authoring | Required ODCS fields, naming, SCD2 fields, append-only shape, codeset relationships, classification rules, ADR references | `scripts/validation/validate-contracts.py` |
| Manifest drift | Manifest path, contract id, digest, kind, Spark types, nullability, role tags, FK and codeset references, currency pairs | `scripts/validation/validate-fabric-manifests.py --require-full-coverage` |
| Artifact generation | Manifests, Purview JSON, DDL, notebook templates, then drift validation | `scripts/generation/generate-fabric.py` |
| Runtime pre-write | Required fields, uniqueness, expressions, currency pairs before Silver write | Generated Fabric notebooks |
| Runtime post-write | Codeset accepted-values checks, SCD2 current-row uniqueness, SCD2 window consistency | Generated Fabric notebooks |
| Gold consumption | Product-specific quality, mart grain, metric definitions, semantic joins | Downstream implementation |

## A Note on Code Values

Codesets such as `pc.policy-status-code`, `pc.term-status-code`,
`pc.lifecycle-status`, `pc.lifecycle-event-type`, and
`pc.transaction-type` are defined as canonical lookup-table contracts
whose accepted code values are populated per deployment. The codes used in
this tutorial (`BOUND`, `ISSUED`, `CANCELLED`, `ENDORSEMENT`, `BROKER`,
`BROKER_OF_RECORD`, etc.) follow the canonical examples called out in
each codeset's description. Real deployments may use slightly different
spellings or extend these sets. Treat the code values here as illustrative
and check the codeset rows in your environment for the authoritative list.

Status values appear in two canonical contexts. Policy header
`policy_status_code` binds to `pc.policy-status-code`; lifecycle event
`prior_status_code`, `resulting_status_code`, and
`lifecycle_event_status_code` bind to `pc.lifecycle-status`; policy term
`policy_term_status_code` binds to `pc.term-status-code`.

## Practical Reading Order Of The Underlying Contracts

To pair this tutorial with the canonical contracts themselves:

1. `references/odcs/pc/policy/policy.odcs.yaml`
2. `references/odcs/pc/policy/policy-term.odcs.yaml`
3. `references/odcs/pc/core/party.odcs.yaml`
4. `references/odcs/pc/policy/policy-party-role.odcs.yaml`
5. `references/odcs/pc/core/agreement.odcs.yaml`
6. `references/odcs/pc/policy/policy-lifecycle-event.odcs.yaml`
7. `references/odcs/pc/policy/policy-transaction.odcs.yaml`
8. `targets/fabric/manifests/pc/policy/policy.fabric.yaml`
9. `targets/fabric/manifests/pc/policy/policy-term.fabric.yaml`
10. `targets/fabric/notebooks/silver-scd2-merge-template.ipynb`
11. `targets/fabric/notebooks/silver-append-template.ipynb`
