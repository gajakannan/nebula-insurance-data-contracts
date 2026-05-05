# Product and Coverage Modeling

## Decision

The relationship between `Product` and `Coverage` is many-to-many and is represented by an explicit junction contract `ProductCoverage`.

`Product` is the marketed or filed insurance product. `Coverage` is the reusable protection concept. A single product offers many coverages; a single coverage may be offered by many products with different defaults, optionality, and constraints.

`PolicyCoverage` continues to represent coverage as it applies to a specific policy or policy term and references the underlying `Coverage` (and, where the product context matters analytically, the `Product`).

## Rationale

In practice, the same coverage definition (for example "Bodily Injury Liability") is offered by multiple commercial auto products, multiple personal auto products, and multiple package products, each with different defaults, limits ranges, optionality rules, and form references. Modeling the relationship as one-to-many in either direction forces duplication of either products or coverages.

Treating `ProductCoverage` as a first-class junction contract preserves the integrity of `Product` and `Coverage` as reusable definitions and gives a clean home for product-coverage-specific defaults (default selection, default limit, default deductible, mandatory flag).

## Consequences

- New contract: `ProductCoverage` under `references/odcs/pc/coverage/`.
- `ProductCoverage` carries product-coverage scope fields:
  - Defaults (`default_selected_indicator`, `default_limit_amount`, `default_deductible_amount` with currency pairs)
  - Constraints (`mandatory_indicator`, `min_limit_amount`, `max_limit_amount` with currency pairs)
  - Filing references (form code, edition, jurisdiction scoping) where governed
- `PolicyCoverage` retains its `coverage_uid` reference and gains an optional `product_coverage_uid` reference for cases where the policy was sold under a specific product context that should be preserved analytically.
- `ProductCoverage` follows SCD2 because the relationship and its defaults change over time (filings, rate revisions).
- The `policy-coverage-pattern.md` is updated to call out the M:N relationship and the role of `ProductCoverage`.

## Guidance

- Do not collapse `ProductCoverage` defaults into `Product` or `Coverage`. Defaults belong to the relationship, not to either endpoint.
- Do not require `product_coverage_uid` on `PolicyCoverage`. Many policy systems issue coverage without a stable product-coverage filing reference; the field is optional and populated when known.
- Where filings vary by jurisdiction, prefer one `ProductCoverage` row per product/coverage/jurisdiction combination over inflating fields with arrays. The junction is the right granularity.

## Related

- `references/patterns/pc/policy-coverage-pattern.md`
- `references/design-decisions/pc/separation-and-nesting.md`
