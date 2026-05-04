# Exposure Modeling

## Decision

Model exposure as a first-class concept in the P&C contract spine.

## Rationale

Exposure is the measurable risk basis that connects underwriting, rating, coverage, claims, loss analysis, and operational reporting. Treating exposure as a first-class concept keeps risk analytics usable without forcing every insured-object subtype into its own top-level canonical contract.

## Consequences

The model separates:

- The contractual container: `Policy`
- The protection concept: `Coverage`
- The thing or interest that may be insured: `InsurableObject`
- The measurable risk basis: `Exposure`

Specialized exposure contracts should be added when they carry durable, distinct business fields.

See `references/patterns/pc/exposure-pattern.md`.
