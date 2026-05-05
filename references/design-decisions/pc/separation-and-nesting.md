# Separation and Nesting

## Decision

A concept is modeled as its own canonical contract when **at least one** of these is true:

1. It has an independent lifecycle (its own create, update, close, or retire path that does not always coincide with its parent).
2. It has its own canonical identity that is referenced from elsewhere (multiple parents, cross-domain references, or stable joins from analytical products).
3. It carries its own SCD2 history that should be preserved independently of its parent's history.
4. It has its own ownership, stewardship, or quality regime.
5. It can exist without the parent, even temporarily (a coverage limit defined at the product level before any policy applies it).

A concept is modeled as **nested attributes** on a parent contract when none of the above hold and the concept is purely descriptive of the parent at a single point in time.

## Rationale

Treating every business concept as a separate contract bloats the model and forces consumers into joins that add no analytical value. Treating every concept as nested attributes hides relationships, defeats SCD2 history per concept, and produces wide, brittle entity contracts.

The five criteria above force a deliberate decision per concept rather than a default in either direction.

## Consequences

- `PolicyLimit` and `PolicyDeductible` remain separate contracts because they carry independent identity, are referenced from `PolicyCoverage`, can change within a coverage instance over time, and warrant SCD2 history of their own.
- `LocationAddress` remains a separate contract because addresses are reused across parties, insurable objects, and locations.
- Purely descriptive attributes (e.g. coverage textual descriptions, narrative fields, single-valued classifications) stay nested on the parent.
- When a concept is split out as its own contract, the parent retains a `*_uid` foreign-key reference and the relationship is declared in `relationships:`.
- When a concept is nested, fields are inlined on the parent with a clear naming prefix (e.g. `mailing_address_*`) only when nesting more than two or three fields; otherwise use plain field names.

## Guidance

- Re-evaluate borderline cases when adding a new line of business or a new analytical use case. A concept that started as nested may earn its own contract once a second consumer needs it.
- Do not split a concept into its own contract solely to mirror a source-system table. Source structure is design input, not a separation criterion (see `entity-boundaries.md`).
- Avoid nesting structured collections (lists of structs) inside an entity contract when those collection items have any independent lifecycle. ODCS YAML supports nested arrays, but use them only for genuinely value-typed lists.

## Related

- `references/design-decisions/pc/entity-boundaries.md`
- `references/design-decisions/pc/identifier-strategy.md`
