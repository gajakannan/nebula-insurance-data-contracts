# Policy Coverage Pattern

Use the policy coverage pattern when modeling coverage that is offered, selected, bound, issued, limited, or deducted within a policy context.

## Intent

Separate the reusable product or coverage definition from the coverage instance that applies to a policy or policy term.

## Recommended Contracts

```text
Product
Coverage
PolicyCoverage
PolicyLimit
PolicyDeductible
```

## Modeling Guidance

Use `Product` for the marketed or filed insurance product.

Use `Coverage` for the reusable protection concept.

Use `PolicyCoverage` for coverage selected or applied on a policy or policy term.

Use `PolicyLimit` and `PolicyDeductible` for limits and deductibles that apply within the policy coverage context.

Keep target-specific rating, form, or implementation details out of these canonical contracts unless they represent stable business meaning.
