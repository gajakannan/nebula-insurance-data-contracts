# Exposure Pattern

Use the exposure pattern when modeling the measurable risk basis for a policy, coverage, claim, underwriting decision, or analytical product.

## Intent

In insurance, exposure is where much of the analytical and underwriting value lives.

- `Policy` is the contractual container.
- `Coverage` defines what protection applies.
- `InsurableObject` identifies what may be insured.
- `Exposure` describes the measurable risk basis.

This pattern avoids creating a separate top-level canonical contract for every possible insured-object subtype.

## Recommended Contracts

```text
InsurableObject
InsurableObjectClassification
Exposure
VehicleExposure
PropertyExposure
WorkersCompExposure
```

## Use This Pattern To Answer

- What is being insured?
- What type of risk basis is being measured?
- Which coverage applies?
- Which policy term does the exposure belong to?
- Which claim arose from which exposure?
- Which rating, underwriting, or loss analytics should use this exposure?

## Modeling Guidance

Use `InsurableObject` for the thing, location, property, vehicle, operation, or interest that may be insured.

Use `InsurableObjectClassification` for durable categorization of the object.

Use `Exposure` for shared exposure fields and relationships.

Use specialized exposure contracts only when a line of business or risk basis has durable, distinct fields that would make the base exposure ambiguous or overloaded.
