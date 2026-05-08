# Versioning Policy

## Decision

Canonical contracts use Semantic Versioning (`MAJOR.MINOR.PATCH`) with data-contract-specific semantics:

- **MAJOR** (`X.0.0`) — breaking change for consumers.
  - Drop a field
  - Rename a field
  - Tighten a `logicalType` (e.g. `string` → `decimal`)
  - Change a field from optional to required
  - Narrow allowed values in a referenced codeset (remove or rename a code)
  - Change a primary key
  - Drop a relationship
  - Change cardinality of a relationship in a way that loses rows for any consumer

- **MINOR** (`x.Y.0`) — additive change, backward-compatible.
  - Add an optional field
  - Add a relationship
  - Add a quality rule (any severity)
  - Widen allowed values in a referenced codeset (add a code)
  - Tighten a quality rule (warning) without rejecting prior data
  - Add or refine `customProperties` that are advisory

- **PATCH** (`x.y.Z`) — no schema impact.
  - Description, businessName, or comment updates
  - Typo fixes
  - Author or steward metadata changes

Below `1.0.0` (any `0.x.y`), the contract is **pre-stable**. Breaking changes are permitted between `0.x` minor versions, but every breaking change must still be recorded in the contract's changelog and surfaced in the planning status doc. Breaking changes after `1.0.0` require a deprecation cycle (see `status-promotion.md`).

## Rationale

Without a documented policy, every author makes their own judgment about what counts as breaking. Consumers cannot pin or upgrade safely, and downstream targets (dbt, Fabric) cannot generate diff-safe migrations.

SemVer is the de facto standard. Adapting it to data-contract reality (where adding a code value or tightening a quality rule is a real consumer-visible event) gives us a precise vocabulary.

## Consequences

- Every contract carries a `version:` field (already present) and a `customProperties.changelog` array recording each version with date, change type, and brief description.
- The validator checks that the `version` is well-formed SemVer and that an unreleased breaking change to an `approved` contract bumps the major version.
- Codeset contracts version too. Adding a code value is MINOR; removing or renaming a code is MAJOR.
- Target generators use the major version to namespace materializations where appropriate (e.g. table name suffix, schema-evolution tooling).

## Guidance

- Treat the version as a contract with consumers, not a label. If you cannot articulate a breaking change without raising the major, the change probably is breaking.
- Bundle multiple non-breaking changes into a single MINOR bump rather than emitting many micro-versions.
- Pre-stable (`0.x`) is the right home for the current contract set until consumers exist. Promote to `1.0.0` only when the contract is `approved` and at least one consumer pins to it.

## Manifest Version (`*.fabric.yaml`)

The Fabric target generates a manifest per canonical contract under `targets/fabric/manifests/pc/<area>/<slug>.fabric.yaml`. Each manifest carries a top-level `manifestVersion: <semver>` field that captures the schema version of the manifest format itself, **independent of the source contract version** in `contract.version`.

Two version surfaces coexist on every manifest:

- **`contract.version`** — mirrors the source ODCS contract's `version:` field. Bumps whenever the canonical contract bumps. Governed by the canonical SemVer rules above.
- **`manifestVersion`** — schema version of the manifest format. Bumps when the manifest schema in `targets/fabric/manifest-schema.md` changes — a new role added to the field-role taxonomy in §5.2, a new `qualityRules.type`, a new top-level block, a renamed field, or any change a downstream consumer of the manifest format must adapt to.

Manifest version SemVer rules mirror the canonical rules:

- **MAJOR** — breaking change for manifest consumers. Examples: rename a top-level block, rename a column-level field, narrow the allowed-role set, change the digest algorithm, drop a `qualityRules` type.
- **MINOR** — additive change, backward-compatible. Examples: add a new role, add a new `qualityRules` type, add a new optional column-level field, add an optional metadata block.
- **PATCH** — no consumer impact. Examples: documentation tightening, type allow-list extension that does not change emitted manifests, comment-field renames in the schema document only.

The current shipped manifest format is `manifestVersion: 1.0.0`. Every manifest under `targets/fabric/manifests/pc/` carries this value. A future schema change bumps every manifest in lockstep — the manifest validator's full-coverage check confirms no manifest lags.

Notebook templates declare a compatible `manifestVersion` range; the manifest validator and the notebook runtime both enforce it. Mixing a manifest at `manifestVersion: 2.x` with a notebook expecting `1.x` is a deployment error caught at notebook-load time.

## Fabric Artifact Regeneration Cadence

A canonical contract bump produces — in lockstep — a regenerated manifest, DDL, Purview JSON, and run-summary surface. Notebook templates regenerate only when the notebook generator itself changes; they consume the manifest at runtime and adapt.

The manifest validator's `sourceContractDigest` pin makes the lockstep deterministic: every contract bump that touches schema produces a new manifest digest, and missing regen is surfaced by `validate-fabric-manifests.py --require-full-coverage`.

Three rules govern the regeneration cadence:

- **PATCH bumps** to a contract regenerate the manifest (digest), DDL (table comment), and Purview JSON (`sourceContractVersion` strings). Notebook templates are untouched. No manifest schema change.
- **MINOR bumps** regenerate the same files plus column-level changes wherever a column was added (DDL gains a column with `COMMENT`; manifest gains a column entry; Purview JSON gains a column-level entry; glossary terms refresh when descriptions change). Notebook templates remain untouched.
- **MAJOR bumps** trigger the same regeneration plus a deliberate review of consumer pinning. The manifest validator does not by itself catch consumer-pinning impact — it only catches drift within the file artifact bundle. The reviewer's job is to walk the rows of `docs/review-checklist.md` §5 and confirm the change is intentional.

The orchestrator at `scripts/generation/generate-fabric.py` runs the four sub-generators (`generate-fabric-manifests.py`, `generate-fabric-purview.py`, `generate-fabric-ddl.py`, `generate-fabric-notebooks.py`) in dependency order and ends with the manifest drift validator. A green orchestrator run is the single highest-value check on a canonical-layer PR.

## Consumer-Side Pinning Guidance

Consumers of this repository (Fabric workspaces, downstream Gold-layer ETL, AI / RAG indexes that ingest the contracts) pin against one of three surfaces. The choice depends on what the consumer cares about.

- **Pin a contract version** — a consumer that depends on a specific contract's shape pins on the `version:` field of that contract (e.g. `pc.policy@0.4.2`). The pin is broken when MAJOR bumps the contract; the consumer's CI fails the validator's version-comparison check before any breaking change ships. Use this when the consumer is contract-specific.
- **Pin a manifest version** — a consumer of the Fabric manifest format itself (e.g. a custom downstream notebook, an alternative-target generator) pins on `manifestVersion`. Independent of contract pins. Use this when the consumer cares about the manifest schema, not which contract.
- **Pin a repository tag** — a consumer that wants the entire bundle (contracts + manifests + DDL + Purview + notebooks + walkthroughs) pins a git tag. Most production deployments use this — it is the simplest path to reproducibility, since the orchestrator's output is reproducible from the contract surface at the tag.

Cross-pin combinations are valid when the consumer cares about more than one surface; for example, a Fabric deployer might pin both a repository tag (for the artifact bundle) and a manifest version range in their notebook config (so they fail loudly on a manifest-schema break).

What this section does **not** govern: workspace-level Fabric versions (Lakehouse runtime, Spark version, Delta version) — those are platform concerns owned by the deployer, not the canonical layer. Compatibility with Fabric runtime versions is tracked in `targets/fabric/conventions.md`, not here.

## Related

- `references/design-decisions/pc/status-promotion.md`
- `references/design-decisions/pc/codeset-strategy.md`
- `targets/fabric/manifest-schema.md` — manifest schema reference governed by `manifestVersion`.
- `scripts/validation/validate-fabric-manifests.py` — drift validator that enforces the `sourceContractDigest` pin.
- `docs/review-checklist.md` §5 — Fabric impact matrix used during PR review.
