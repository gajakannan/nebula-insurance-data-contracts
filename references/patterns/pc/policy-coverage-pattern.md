# Policy Coverage Pattern

Use the policy coverage pattern when modeling coverage that is offered, selected, bound, issued, limited, or deducted within a policy context.

## Intent

Separate the reusable product or coverage definition from the coverage instance that applies to a policy or policy term. Treat the relationship between `Product` and `Coverage` as many-to-many.

## Recommended Contracts

```text
Product
Coverage
ProductCoverage
PolicyCoverage
PolicyLimit
PolicyDeductible
```

## Modeling Guidance

Use `Product` for the marketed or filed insurance product.

Use `Coverage` for the reusable protection concept.

Use `ProductCoverage` for the M:N relationship between products and coverages, including product-coverage-specific defaults (selection, limits, deductibles), constraints, and filing references. See `references/design-decisions/pc/product-coverage-modeling.md`.

Use `PolicyCoverage` for coverage selected or applied on a policy or policy term. `PolicyCoverage` references `Coverage` directly and may optionally reference the `ProductCoverage` row that the policy was sold under when filing context is analytically meaningful.

Use `PolicyLimit` and `PolicyDeductible` for limits and deductibles that apply within the policy coverage context.

Keep target-specific rating, form, or implementation details out of these canonical contracts unless they represent stable business meaning.
