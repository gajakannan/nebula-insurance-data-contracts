# Coverage Terms

## Coverage

A reusable insurance protection concept that can be offered, selected, or applied in a policy context.

## Coverage Identifier

The system identity column on a coverage record (`coverage_uid`). An immutable GUID used as the join key for every reference to the reusable coverage definition.

## Coverage Code

A business code that identifies a coverage concept.

## Coverage Name

The business-facing name for a coverage concept.

## Coverage Type

A classification of the kind of protection or obligation represented by a coverage.

## Coverage Category

A broader grouping used to organize related coverage concepts.

## Policy Coverage

Coverage selected, required, or applied within a policy, policy term, or exposure context.

## Coverage Sequence Number

A sequence used to order or distinguish coverages within a policy context.

## Coverage Status

The current lifecycle state of a coverage or policy-applied coverage.

## Coverage Level

The level at which coverage applies, such as policy, term, exposure, location, vehicle, or other recognized context.

## Coverage Basis

The basis used to determine how coverage applies or is measured.

## Selected Coverage

Coverage chosen or accepted for a policy context.

## Mandatory Coverage

Coverage required by product, jurisdiction, business rule, or policy structure.

## Policy Limit

Structured detail that defines the maximum amount, quantity, or unit of protection associated with a policy coverage.

## Limit Type

A classification of the kind of limit, such as occurrence, aggregate, per person, per item, or another recognized limit type.

## Limit Basis

The basis used to apply or evaluate a limit.

## Limit Amount

The monetary maximum associated with a policy limit.

## Limit Quantity

A non-monetary maximum associated with a policy limit.

## Limit Unit

The unit of measure for a non-monetary policy limit.

## Policy Deductible

Structured detail that defines the amount, percentage, or basis retained before coverage responds.

## Deductible Type

A classification of the kind of deductible associated with a policy coverage.

## Deductible Basis

The basis used to apply or evaluate a deductible.

## Deductible Amount

The monetary amount of a deductible.

## Deductible Percent

The percentage used to calculate a deductible.

## Minimum Deductible

The lowest deductible amount that can apply under the deductible terms.

## Maximum Deductible

The highest deductible amount that can apply under the deductible terms.

## Product Coverage

The many-to-many junction relating a marketed product to a reusable coverage definition. Carries product-coverage-specific defaults (selection, limits, deductibles), constraints (mandatory, minimum and maximum limits), and filing references.

## Default Selected Indicator

An indicator on a product-coverage record that the coverage is selected by default when the product is offered.

## Default Limit

The limit amount that applies by default when a product is sold under a particular product-coverage filing. Paired with a currency code.

## Default Deductible

The deductible amount that applies by default when a product is sold under a particular product-coverage filing. Paired with a currency code.

## Filing Reference

A form code, edition, or jurisdiction reference associated with a product-coverage offering when filings vary by jurisdiction or revision.

## Form Code

A filed form code associated with a product-coverage offering.

## Form Edition Code

A filed form edition or revision code associated with a product-coverage offering.
