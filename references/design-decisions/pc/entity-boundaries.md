# Entity Boundaries

## Decision

Canonical contracts should represent stable insurance business concepts, not source tables, vendor schemas, physical DDL, reporting marts, or external model boundaries.

## Rationale

Insurance systems often use different names, shapes, lifecycle assumptions, and normalization choices for the same business idea. A canonical contract layer should provide a stable business agreement across those systems rather than reproduce any one source.

## Guidance

Use source structures as design input only.

Do not copy source table boundaries or subtype hierarchies directly into canonical contracts.

Use subtype concepts to inform:

- Classifications
- Specialized exposure contracts
- Reference data
- Optional extensions
- Data quality rules
- Semantic relationships

Create a separate canonical contract only when the concept has durable business meaning, clear ownership, independent lifecycle, or relationships that would otherwise make an existing contract ambiguous.
