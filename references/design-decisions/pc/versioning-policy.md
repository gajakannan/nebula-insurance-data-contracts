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

## Related

- `references/design-decisions/pc/status-promotion.md`
- `references/design-decisions/pc/codeset-strategy.md`
