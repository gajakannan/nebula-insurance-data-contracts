# Fabric Target

This folder is the Fabric target for the canonical Property and Casualty data contracts under `references/odcs/pc/`. It defines how those canonical contracts project into a Microsoft Fabric Lakehouse Silver layer through a **metadata-driven** approach.

The authoritative plan for the Fabric target is `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md`. This README and its three sibling documents are the F1 deliverables of that plan: documentation only, no generated artifacts, no platform code. They give a contributor enough context to understand the projection without running any tooling.

---

## What this folder is for

A canonical contract describes a business concept in source-neutral, platform-neutral terms. A Fabric Lakehouse needs concrete artifacts: Delta tables with Spark SQL types, partition strategies, SCD2 merge logic, append-only correction handling, codeset lookups, Purview sensitivity labels, business glossary entries, and `.ipynb` notebooks that conform to Fabric's runtime expectations.

This folder is the bridge. It does two jobs:

1. **Documents the projection.** The four F1 docs explain the rules: how an ODCS field becomes a Spark column, how an entity contract becomes an SCD2 Delta table, how an event contract becomes an append-only Delta table, how a codeset becomes a small lookup table, how a `customProperties.classifications` block becomes a Purview sensitivity label.
2. **Holds generated artifacts.** Later phases (F2 onward) populate `manifests/`, `ddl/`, `notebooks/`, `purview/`, and `examples/` from the canonical contracts via generators in `scripts/generation/`. Those folders are derived; if a manifest disagrees with its source contract, the generator is rerun, never the manifest hand-edited.

The folder is intentionally **static and insurance-aware**. It ships finished artifacts that a Fabric platform engineer can deploy. It does not authenticate against a Fabric workspace, create Lakehouses, or run notebooks; that is the job of `microsoft/skills-for-fabric` (see "Coexistence" below).

---

## What this folder is not

- **Not the canonical layer.** Canonical insurance modeling lives under `references/odcs/pc/`. Files here describe how that layer materializes in Fabric, not what it means.
- **Not a Fabric workspace.** Nothing in this folder calls Fabric APIs, creates resources, or holds workspace identifiers. Lakehouse-binding metadata is left blank for the deployer to fill at runtime.
- **Not Bronze.** Bronze ingestion (Pipelines, Copy activity, OneLake shortcuts, third-party ETL) is upstream of this repository. The manifests reference Bronze tables by qualified name and assume they exist; the generator never specifies how Bronze is loaded.
- **Not Gold.** Aggregates, marts, semantic models, and Power BI artifacts are downstream of Silver and outside this milestone's scope. A future milestone may add a Gold target, but this folder targets the Silver layer only.
- **Not platform code in the canonical layer.** Fabric mechanics live here, not under `references/`. The canonical contracts do not gain Fabric-specific `customProperties`; generic ones (classifications, classification profile, changelog, ADR back-links) serve multiple targets.

---

## The four F1 documents

Read these in order. Each document is self-contained but the order builds context.

| # | Document | Scope |
|---|---|---|
| 1 | `README.md` (this file) | Purpose, scope, persona flow, reading order, file map. |
| 2 | `conventions.md` | Lakehouse and schema naming, materialization strategy per contract kind, SCD2 / append-only / codeset implementation, partitioning, V-Order, Purview projection, HIPAA handling, lakehouse binding. |
| 3 | `type-mapping.md` | ODCS logical type → Spark SQL / Delta type. Decimal precision rules, datetime semantics, GUID handling, nullability, type-mapping edge cases. |
| 4 | `manifest-schema.md` | The Fabric manifest file format, with the Policy contract worked end-to-end as the reference example. The manifest is the single intermediate artifact that drives every generated downstream file. |

A new contributor who reads these four files in order should be able to:

- Locate the canonical source for any Fabric artifact.
- Predict what a manifest, DDL file, notebook, or Purview entry looks like for any contract.
- Identify which canonical change (a field rename, a sensitivity bump, a new codeset) triggers regeneration of which Fabric artifact.
- Hand off generated artifacts to a Fabric platform engineer without ambiguity about the contract Nebula owes the deployer.

---

## Generation flow at a glance

```text
references/odcs/pc/<area>/<slug>.odcs.yaml          (canonical, hand-authored)
        │
        ▼  scripts/generation/generate-fabric-manifests.py        (F2)
targets/fabric/manifests/pc/<area>/<slug>.fabric.yaml             (one per contract)
        │
        ├──► scripts/generation/generate-fabric-ddl.py            (F5)
        │      └──► targets/fabric/ddl/pc/<area>/<slug>.spark.sql
        │
        ├──► scripts/generation/generate-fabric-purview.py        (F4)
        │      ├──► targets/fabric/purview/sensitivity-labels.json
        │      └──► targets/fabric/purview/business-glossary.json
        │
        └──► consumed at runtime by:
             targets/fabric/notebooks/silver-scd2-merge-template.ipynb       (F6)
             targets/fabric/notebooks/silver-append-template.ipynb           (F6)
             targets/fabric/notebooks/silver-codeset-load-template.ipynb     (F6)
             (plus targets/fabric/notebooks/lakehouse-binding-template.json)
```

The orchestrator script `scripts/generation/generate-fabric.py` runs the four generators in order and produces a summary report. A drift validator (`scripts/validation/validate-fabric-manifests.py`) catches any manifest that has fallen out of sync with its source contract.

The manifest is the only intermediate representation. Every generated artifact downstream of the manifest is mechanical. The ODCS contract is the only insurance-aware artifact; the manifest is the only platform-aware artifact. No human authors at the level below the manifest.

---

## Persona flow

End-to-end, Fabric delivery spans three personas. This repository owns steps 1 and 2; `microsoft/skills-for-fabric` (or any other Fabric deployment tooling the consumer prefers) owns step 3 onward.

| Step | Persona | Tool / repo | Activity |
|---|---|---|---|
| 1 | Insurance data architect | This repository | Author or update an ODCS contract under `references/odcs/pc/`. Run `scripts/validation/validate-contracts.py`. Commit. |
| 2 | CI or local generator run | This repository | `scripts/generation/generate-fabric.py` regenerates manifests, DDL, notebooks, Purview JSON. `validate-fabric-manifests.py` confirms no drift. |
| 3 | Platform engineer | `spark-authoring-cli` skill (or Fabric REST API directly, Azure DevOps pipeline, manual upload) | Point the deployer at `targets/fabric/`. The deployer creates / updates the Silver Lakehouse, applies DDL, deploys notebooks, populates lakehouse-binding fields. |
| 4 | Operator | Fabric workspace UI or pipeline | Schedule the deployed notebooks against Bronze. Bronze ingestion is owned upstream. |
| 5 | Analyst | `spark-consumption-cli` (or any Spark / SQL client) | Query the Silver tables produced by the SCD2 / append / codeset notebooks. |
| 6 | Analyst (Gold) | `powerbi-authoring-cli` / `powerbi-consumption-cli` | Build and consume Power BI semantic models atop Silver. Out of scope for this milestone. |

Step 3 is the only step where this repository and a deployment tool meet. Steps 1–2 are this repository's domain; steps 4–6 are the deployer's (and the live workspace's) domain.

---

## Coexistence with `microsoft/skills-for-fabric`

The skills repository ships AI-agent skills (for Copilot CLI, Claude Code, Cursor, VS Code, Windsurf) that authenticate against a live Fabric workspace via Azure AD and operate it: creating Lakehouses, deploying notebooks, running queries, registering Power BI semantic models. It is intentionally **dynamic and insurance-agnostic**.

This repository is intentionally **static and insurance-aware**. It ships canonical insurance contracts plus everything generated from them.

Neither replaces the other. The boundary is the artifact layer: this repository writes files; the skills read those files (or REST-deploy them) into a real workspace. There is no library import, no runtime dependency, no shared state.

| Concern | This repository | `microsoft/skills-for-fabric` |
|---|---|---|
| Insurance domain modeling | Owns | Out of scope |
| Canonical-to-Fabric translation (manifest, type mapping, role taxonomy) | Owns | Out of scope |
| Generated `.ipynb` notebook templates | Authors and validates | Deploys to Fabric (`spark-authoring-cli`) |
| Generated Spark SQL DDL | Authors and validates | Applies to Lakehouse (`spark-authoring-cli`) |
| Generated Purview JSON | Authors and validates | Consumer ingests via Purview REST API |
| Workspace creation, capacity, RBAC | Out of scope | Owns (`spark-authoring-cli`) |
| Lakehouse provisioning and binding | Leaves IDs blank | Owns the populated runtime binding |
| Bronze ingestion | Out of scope | Out of scope (separate Fabric tooling) |
| Silver query access | Out of scope | Owns (`spark-consumption-cli`) |
| Gold semantic models | Out of scope (Gold is downstream) | Owns (`powerbi-authoring-cli`, `powerbi-consumption-cli`) |

Conventions this repository inherits from `skills-for-fabric` (so that handoff at step 3 works without manual fixup):

- **`.ipynb` shape.** Every code cell carries `"outputs": []` and `"execution_count": null`. Notebook generator validates this shape.
- **Lakehouse-binding placeholder.** Generator emits `lakehouse-binding-template.json` with empty `default_lakehouse`, `default_lakehouse_name`, `default_lakehouse_workspace_id` fields; the deployer fills them at deployment time.
- **Medallion layering.** Bronze / Silver / Gold separation. This repository targets the Silver layer only.
- **Single-lakehouse override.** The skills' default is one workspace and one lakehouse per layer; this repository overrides to a single Silver Lakehouse (per `conventions.md`).

This repository runs without the skills installed; the skills run without this repository present. Versioning is independent. The only compatibility surface is the file types Fabric accepts (`.ipynb`, `.sql`, `.json`).

---

## Non-negotiable boundaries

The Fabric implementation plan codifies a small set of constraints. Every F1 document is consistent with them; every F2+ artifact must obey them.

- **Canonical contracts are the source of truth.** ODCS YAML under `references/odcs/pc/` is not edited to suit Fabric mechanics. If Fabric needs context the contract does not provide, the gap is recorded as an open question, not silently encoded into a manifest or notebook.
- **Manifests are derived, not authored.** A human does not write `*.fabric.yaml` by hand. The generator is the only source of manifests. Any manual correction must be reflected back into the generator.
- **Notebooks are templates, not bespoke.** Per-contract notebooks are not authored. A small fixed set of parameterized notebooks reads the manifest at runtime and adapts.
- **No source-system specifics leak into the canonical layer.** Bronze schema details, ingestion mechanics, and connector configuration belong outside this repository.
- **Platform mechanics live under `targets/fabric/`.** The `references/` tree does not gain Fabric-specific fields. Generic `customProperties` (classifications, classification profile, changelog, ADR back-links) are canonical and serve multiple targets.
- **Append-only contracts stay append-only.** Per the temporal-modeling and event-and-transaction ADRs, event and transaction tables must not be implemented with SCD2.
- **HIPAA handling is automatic.** When a contract has `customProperties.subjectToHipaa: true`, the generator emits HIPAA-aware Purview labels and notebook annotations; the contract author does not maintain a parallel list.

---

## Canonical surface this folder targets

The Fabric target is gated on canonical hardening (Milestone 8.5, W025–W031) being complete. As of the F1 deliverable, the canonical surface is **85 contracts at version 0.4.x**, distributed across these subject areas:

| Subject area | Folder | Notes |
|---|---|---|
| Core | `references/odcs/pc/core/` | Party, Account, Agreement and their relationship / role contracts. Spine of commercial-lines rollups. |
| Policy | `references/odcs/pc/policy/` | Policy and its term, role, lifecycle event, transaction, document children. |
| Coverage | `references/odcs/pc/coverage/` | Coverage, ProductCoverage M:N, PolicyCoverage, PolicyLimit, PolicyDeductible, Product. |
| Exposure | `references/odcs/pc/exposure/` | InsurableObject and its classification / role children, plus Exposure and three subtype contracts (Property, Vehicle, Workers Comp). |
| Submission | `references/odcs/pc/submission/` | Submission and its role / risk / assessment / document / lifecycle children. |
| Claims | `references/odcs/pc/claims/` | Claim and its role / coverage / feature / lifecycle / financial / document children, plus Occurrence and Catastrophe. |
| Financial | `references/odcs/pc/financial/` | FinancialTransaction and PolicyFinancialTransaction (claim-side ClaimFinancialTransaction lives under `claims/`). |
| Reference data | `references/odcs/pc/reference-data/` | 42 codeset and reference-data contracts. |

By contract kind:

- **Entity contracts** (SCD2): every contract that is not a codeset, event, or transaction. Carries `valid_from_datetime`, `valid_to_datetime`, `is_current_indicator`, `record_status_code`. Composite primary key on `(*_uid, valid_from_datetime)`.
- **Event contracts** (append-only): the `*-lifecycle-event` family. Carries `correction_indicator` and `corrects_*_uid`. No SCD2 fields. No source-time fields (source-time is forbidden on append-only contracts per the temporal-modeling ADR).
- **Transaction contracts** (append-only): the `*-transaction` family plus `financial-transaction`, `policy-financial-transaction`, `claim-financial-transaction`. Same shape as event contracts.
- **Codeset contracts** (SCD2): pure codesets and richer reference-data entities under `reference-data/`. Same SCD2 mechanics as entities; primary key is `*_uid`; codeset cross-references join on `code_value`.

`conventions.md` documents the materialization rules per kind. `manifest-schema.md` shows the manifest fields that distinguish them.

---

## File map

This is the target end state once F2–F8 land. F1 only ships the four documents at the top.

```text
targets/fabric/
  README.md                                  # this file
  conventions.md                             # naming, materialization, runtime conventions
  type-mapping.md                            # ODCS → Spark SQL types
  manifest-schema.md                         # full manifest schema reference

  manifests/
    pc/
      <area>/<slug>.fabric.yaml              # 85 manifests, F2–F3

  ddl/
    pc/
      <area>/<slug>.spark.sql                # 85 DDL files, F5

  notebooks/
    silver-scd2-merge-template.ipynb         # entity contract merge, F6
    silver-append-template.ipynb             # event/transaction append, F6
    silver-codeset-load-template.ipynb       # codeset load, F6
    lakehouse-binding-template.json          # consumer fills in IDs, F6

  purview/
    sensitivity-labels.json                  # column-level Purview manifest, F4
    business-glossary.json                   # canonical terms manifest, F4

  examples/
    end-to-end-policy.md                     # worked walkthrough, F7

scripts/
  generation/
    generate-fabric.py                       # orchestrator, F2+
    generate-fabric-manifests.py             # ODCS → manifests, F2
    generate-fabric-ddl.py                   # manifests → DDL, F5
    generate-fabric-notebooks.py             # template notebooks, F6
    generate-fabric-purview.py               # manifests + glossary → Purview JSON, F4
  validation/
    validate-fabric-manifests.py             # drift detection, F2
```

---

## Where to go next

- **Conventions and runtime mechanics** → `conventions.md`.
- **Type mapping rules** → `type-mapping.md`.
- **Manifest schema reference** → `manifest-schema.md`.
- **The implementation plan** (authoritative; this README is its companion) → `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md`.
- **The canonical contracts** → `references/odcs/pc/`.
- **The ADRs that govern target generation behavior** → `references/design-decisions/pc/` (especially `temporal-modeling.md`, `record-state.md`, `event-and-transaction.md`, `codeset-strategy.md`, `data-classification.md`, `currency-convention.md`, `null-semantics.md`, `scd2-primary-key.md`).
