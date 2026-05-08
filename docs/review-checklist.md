# PR Review Checklist

This page is the structured checklist a reviewer runs against every pull request that changes a canonical ODCS contract, an ADR, a target manifest, or any generated artifact under `targets/fabric/`. It codifies what the validators check and what the C7 single-contract cleanups taught us, organized by contract surface area.

**Order of operations:** start at §1 and only proceed to §2–§6 once the §1 automation is green. Most failure modes are caught mechanically; the human reviewer's job is to judge the ones that are not.

---

## 1. Pre-review automation (must be green before review begins)

The reviewer should expect these checks to pass before opening the diff. If any fails, send the PR back rather than reading the contract changes.

| Check | Command | What it covers |
|---|---|---|
| Canonical validator | `python3 scripts/validation/validate-contracts.py` | The 12 C1 hardening rules + the original W005 / W019 rule set. Zero findings on every PR. |
| Validator unit tests | `python3 -m pytest scripts/validation/tests/ -q` | 40 tests covering the C1.1–C1.12 rules plus the original gates. |
| Fabric manifest drift | `python3 scripts/validation/validate-fabric-manifests.py --require-full-coverage` | All 17 drift checks from `targets/fabric/manifest-schema.md` §9 across all 85 manifests. |
| Inventory drift | `python3 scripts/generation/generate-contract-inventory.py --check` | `docs/contract-inventory.md` regenerates byte-identically. |
| Changelog drift | `python3 scripts/generation/generate-changelog.py --check` | `CHANGELOG.md` regenerates byte-identically. |
| Generators idempotent | `python3 scripts/generation/generate-fabric.py` followed by `git diff --exit-code targets/fabric/` | Re-running the orchestrator produces no diff when the canonical layer has not changed. |

The orchestrator at `scripts/generation/generate-fabric.py` runs the four sub-generators and the manifest validator in dependency order. A green orchestrator run is the single highest-value check on a canonical-layer PR.

If a PR introduces a new validator rule, the unit-test count should increase by at least one fixture per branch (pass + fail).

---

## 2. By contract kind

Each subsection lists the structural and semantic checks that apply to that kind. Items marked with **(validator)** are mechanically enforced; items marked with **(human)** require reviewer judgment.

### 2.1 Entity contracts (`silver_<area>.<table>`, SCD2-merged)

- **Primary key is `<slug>_uid`** with `logicalType: string` and a separate `*_uid` field per natural key. **(validator: identifier-strategy)**
- **Composite SCD2 PK on (`*_uid`, `valid_from_datetime`).** Both fields carry `primaryKey: true`. **(validator: scd2-primary-key)**
- **SCD2 fields present:** `valid_from_datetime`, `valid_to_datetime`, `is_current_indicator`. Required where applicable. **(validator: temporal-modeling)**
- **`record_status_code` present** with `required: true`, classification `INTERNAL`, and a relationship to `pc.record-status-code`. **(validator: record-state)**
- **Codeset binding on every `*_code` field**, or `customProperties.codesetExempt: true` plus `codesetExemptReason`. **(validator: C1.2 codeset-strategy)**
- **`*_amount` paired with `*_currency_code`** in the same `properties:` array, or `customProperties.amountCurrencyExempt: true` with rationale. **(validator: C1.1 currency-convention)**
- **No mutable record timestamps.** `created_datetime` / `updated_datetime` are renamed to `source_created_datetime` / `source_updated_datetime` per the C7.4 cleanup. **(validator: C1.5)**
- **Description names the canonical concept**, not the source-system shape. The first sentence should read "Canonical contract for …". **(human)**
- **Quality rules at error severity** are stated for the must-be-true invariants — primary key required, status required, key business-time fields present, SCD2 window consistent, single current row per key. Warning-severity rules cover advisory checks. **(human)**
- **Relationships are explicit** with `targetContractId` resolving to a tracked contract id. Every FK named `<thing>_uid` should have a corresponding `relationships:` entry unless the target is intentionally external. **(validator: C1.3 + human)**

### 2.2 Event contracts (`<thing>-lifecycle-event`, append-only)

- **Append-only mode mutually exclusive with SCD2.** Manifest's `appendOnly.enabled = true` and `scd2.enabled = false`. **(validator)**
- **`correction_indicator` and `corrects_<slug>_uid` paired.** When `correction_indicator` is present, the `corrects_*_uid` field must also be present. **(validator: C1.4)**
- **`event_datetime` present** as the business-time field. The append template partitions Bronze reads on it. **(validator)**
- **No `created_datetime` / `updated_datetime` / `source_created_datetime` / `source_updated_datetime`.** Append-only rows are immutable; an "updated" timestamp is incoherent regardless of whether it captures canonical or source time. **(validator: C1.5)**
- **No SCD2 fields, no `record_status_code`** — append-only contracts do not carry warehouse-level state. **(validator)**
- **`lifecycle_event_type_code` codeset binding** to `pc.lifecycle-event-type`. **(validator: C1.2)**
- **`correction_indicator_required` quality rule at error severity.** **(human)**
- **Description names the event family** the contract carries (FNOL received, assigned, reserve change, payment, closed, reopened, denied, withdrawn, etc.). **(human)**

### 2.3 Transaction contracts (`<thing>-transaction`, `*-financial-transaction`, append-only)

- All event checks above (append-only, correction handling, no SCD2, no record-state, no mutable timestamps).
- **`lifecycle_event_uid` cross-reference** when relevant. The role taxonomy emits `lifecycle-event-link`; the manifest validator additionally checks the FK target is an event contract. **(validator)**
- **Currency pairing on every `*_amount`** field. **(validator: C1.1)**
- **`transaction_classification_code` bound to `pc.financial-transaction-classification`** when the transaction participates in cross-policy/claim rollups. **(validator: C1.2 + human for classification choice)**
- **`transaction_effective_date` present** as the business-time field; the append template partitions Bronze reads on it. **(human — name varies; verify the manifest's `appendOnly.businessTimeField` is set)**
- **Description distinguishes transaction from event.** A transaction is processed activity (premium written, payment made, reserve changed); an event is a state change (issued, bound, paid, closed). The two are complementary per `event-and-transaction.md`. **(human)**

### 2.4 Codeset contracts (under `references/odcs/pc/reference-data/`)

- **`code_value` and `code_label` fields present** at minimum; `code_description`, `external_standard_code`, `external_standard_name` optional. **(validator)**
- **`classificationProfile: PUBLIC`** for pure codesets (single `code_value` / `code_label` shape) and `INTERNAL` for richer reference-data entities (`pc.line-of-business`, `pc.lifecycle-status`, `pc.lifecycle-event-type`, `pc.transaction-type`, `pc.geographic-location`, `pc.location-address`). **(human — choice anchored in `codeset-strategy.md` addendum)**
- **All field sensitivities `PUBLIC`** when `classificationProfile: PUBLIC`. The classification profile must match the maximum field sensitivity. **(validator: C1.9)**
- **No `_uid` foreign keys back into entity contracts.** Codesets are joined to entities through `code_value`, never through the codeset's internal `*_uid`. **(human)**
- **Codeset-bound `*_code` fields on the codeset itself self-reference.** The codeset's own `record_status_code` references `pc.record-status-code` (per the C5.8 self-reference note in `codeset-strategy.md`). **(validator: C1.2)**
- **`subjectArea` reflects domain ownership**, not Spark schema. All codesets land in `silver_reference_data` regardless of `subjectArea` value (per F3 closeout). **(human)**

---

## 3. Cross-cutting checks (apply to every contract regardless of kind)

- **`customProperties.adrs: [...]` present** and every id resolves to a file under `references/design-decisions/pc/`. **(validator: C1.12)**
- **Every version bump has a matching `customProperties.changelog` entry** naming the new version. **(validator: C1.11)**
- **`classificationProfile` matches max field sensitivity.** Profile cannot be `INTERNAL` if any field is `CONFIDENTIAL` or higher. **(validator: C1.9)**
- **Narrative free-text classified `CONFIDENTIAL + PII`** — fields ending in `_description` / `_notes` / `_narrative` / `_text` / `_summary`, unless `customProperties.classifications.narrativeException: true`. **(validator: C1.7)**
- **Status / period / territory codes are not over-classified.** Fields whose name contains `_status_code` / `_result_code` / `_period_code` / `_territory_code` / `_region_code` / `_accounting_*` should not carry `RESTRICTED + PII`. **(validator: C1.8 warning)**
- **Source attribution fields present** on entity and codeset contracts: `source_system_code` (bound to `pc.source-system-code`) and `source_natural_key`. Per the C7.5 amendment to `identifier-strategy.md`, multi-source provenance is an MDM concern outside the canonical layer. **(validator)**
- **`apiVersion: v3.0.2`, `kind: DataContract`, `domain: property-and-casualty`** present at the top of every file. **(validator)**
- **YAML anchors expanded.** No `&anchor` / `*alias` references in committed files (per C3.8). **(human — anchors in raw YAML are a regression)**

---

## 4. Status-promotion review

When the PR changes `status:`, verify the gate the transition crosses per `references/design-decisions/pc/status-promotion.md`. The validator enforces the YAML-checkable gates; the reviewer enforces the rest.

### 4.1 `draft → proposed`

- **(validator)** Contract passes the strengthened canonical validator with zero findings.
- **(validator)** `customProperties.changelog` contains at least one entry.
- **(human)** PR description names the contract owner.
- **(human)** PR cross-references the relevant patterns and design-decision docs.

### 4.2 `proposed → approved`

- **(validator: C1.3)** Every relationship's `targetContractId` resolves to a contract id that exists in the canonical surface.
- **(validator: C1.2)** Every `*_code` field has a `relationships:` entry pointing at a reference-data contract, or carries `customProperties.codesetExempt: true` plus `codesetExemptReason`.
- **(validator)** All quality rules at severity `error` are stated for must-be-true invariants.
- **(human)** Domain steward sign-off recorded in the PR or in `customProperties.stewardApproval`.
- **(human)** At least one downstream consumer or target use case identified — logged in `customProperties.knownConsumers` or in the PR description. The Fabric worked examples (`targets/fabric/examples/end-to-end-policy.md`, `end-to-end-claims.md`) are valid downstream consumers; an internal pattern reference is not.
- **(human)** All `*_code` fields reference codeset contracts that are themselves at least `proposed`. Promote in cohorts where contracts depend on each other.

### 4.3 `approved → deprecated`

- **(validator)** `customProperties.deprecation` (or equivalent changelog entry) names the effective date and replacement reference.
- **(human)** A successor contract or successor major version is at least `proposed`.
- **(human)** At least one minor-version notice period elapses before retirement is permitted.

### 4.4 `deprecated → retired`

- **(validator)** Contract retains its file, schema, and changelog; `status: retired` is set.
- **(human)** At least one major version has elapsed since deprecation.
- **(human)** No remaining known consumers — verified through `knownConsumers` and any registered downstream targets.

---

## 5. Fabric impact when canonical contract field shape changes

When a PR changes a contract's properties, relationships, classifications, or quality rules, the Fabric artifact bundle regenerates. The reviewer reads the regenerated diff to confirm the change flowed through cleanly.

| Canonical change | Manifest diff | DDL diff | Purview JSON diff | Notebook diff | Run-summary diff |
|---|---|---|---|---|---|
| Patch bump (description / businessName fix) | `contract.version` + `sourceContractDigest` | Table comment `Source: pc.<id> v<new>` | `sourceContractVersion` strings | None | None |
| Add optional field | All of the above + new column entry | New column with `COMMENT` | New column-level entry | None | None |
| Add quality rule (any severity) | New entry in `qualityRules:` | None | None | None | New `assertions[]` row |
| Add relationship | New entry in `relationships:` | None | None | None | None (advisory FK check only) |
| Widen codeset (add code value) | None on the entity manifest; codeset manifest digest changes | None on the entity DDL; codeset DDL table comment changes | Codeset's `sourceContractVersion` updates | None | Next codeset load: `rowsInserted` increases by 1 |
| Drop/rename field (MAJOR) | Column removed/renamed in manifest | Column removed/renamed in DDL | Column-level entries removed/renamed | None | Next merge: every consumer pinned to old shape breaks |
| Tighten type | Manifest column `sparkType` changes | DDL column type changes | None | None | Next merge: column-level type cast may fail |

The manifest validator's digest pin makes this deterministic: every contract bump that touches schema produces a new manifest digest, and missing regen is surfaced by the validator. Notebooks regenerate only when the notebook generator itself changes — not per contract.

Cross-link to the worked traces:

- `targets/fabric/examples/end-to-end-policy.md` §9 — reverse-blast-radius trace for a codeset value deletion in policy.
- `targets/fabric/examples/end-to-end-claims.md` §9 — reverse-blast-radius trace for a codeset value rename in financial-transaction-classification.

If a PR's canonical change does not match any row above and the manifest validator passes, double-check the manifest is not a stale-digest false negative. The fix path is always to re-run the orchestrator, never to hand-edit a manifest. Manifests are not authored — if a manifest needs editing, the generator is wrong.

---

## 6. Source-neutrality boundary

Per `planning-mds/IMPLEMENTATION_PLAN.md` §"Non-Negotiable Boundaries", tracked files do not name external reference models, source URLs, source-document identifiers, copied class hierarchies, or scratch mappings. Verify on every PR:

- **No external source names** in contract descriptions, glossary entries, ADRs, planning docs, or commit messages. ACORD, NAIC, ISO, and similar may be referenced as *external standards* in codeset `external_standard_name` columns; they may not be referenced as the *source* of canonical decisions.
- **No source URLs** in any tracked file.
- **No source-document identifiers** (proprietary source-system table names, document IDs from carrier-specific systems, etc.).
- **No copied class hierarchies or scratch mappings.** Research and comparison work belong in ignored local folders (`_private-research/`, `_external-sources/`, `_source-review/`, `_scratch/` per `.gitignore`).
- **No raw schemas, raw ontology exports, or source review notes** committed.

If a PR description references private research, the reviewer asks whether that research stays in the local folder. The contract change itself stands on its own as an original canonical artifact.

---

## 7. When something doesn't fit

If a PR is structurally clean against §1–§6 but the change still feels wrong, check it against `references/design-decisions/pc/canonical-alignment.md`. The canonical-alignment ADR documents every deliberate departure from the recommended modeling defaults — identifier compactness, composite SCD2 PK, no generic `PartyRole`, polyclass exposure subtypes, the C4.5 commercial-lines reversal, the `codesetExempt` long tail, and deferrals (risk-transfer, litigation, full assessment hierarchy, semantic projection, additional targets, bronze).

If the proposed change conflicts with one of those documented departures, the right response is to reopen the ADR, not to land the PR. Per `authoring-source-primacy.md`, the precedence order when sources disagree is **ADR > pattern > glossary > contract > validator** — the more authoritative source wins, and the less authoritative one updates.

---

## 8. Cross-references

| Need | File |
|---|---|
| Canonical validator | `scripts/validation/validate-contracts.py` |
| Validator unit tests | `scripts/validation/tests/` |
| Fabric manifest validator | `scripts/validation/validate-fabric-manifests.py` |
| Fabric orchestrator | `scripts/generation/generate-fabric.py` |
| Inventory generator | `scripts/generation/generate-contract-inventory.py` |
| Changelog generator | `scripts/generation/generate-changelog.py` |
| Authoring guide | `docs/authoring-guide.md` |
| Status promotion gates | `references/design-decisions/pc/status-promotion.md` |
| Versioning rules | `references/design-decisions/pc/versioning-policy.md` |
| Canonical alignment (deliberate departures) | `references/design-decisions/pc/canonical-alignment.md` |
| Authoring source primacy (ADR > pattern > glossary > contract > validator) | `references/design-decisions/pc/authoring-source-primacy.md` |
| Worked example: SCD2 + codeset | `targets/fabric/examples/end-to-end-policy.md` |
| Worked example: append-only event + transaction + C4.5 | `targets/fabric/examples/end-to-end-claims.md` |
| Manifest schema reference | `targets/fabric/manifest-schema.md` |
| M10 plan | `planning-mds/MILESTONE_10_PLAN.md` |
