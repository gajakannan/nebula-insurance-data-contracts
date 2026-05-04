# Financial Modeling

## Decision

Model financial activity using transaction-oriented contracts.

## Rationale

Premiums, fees, taxes, surcharges, payments, reserves, salvage, subrogation, and recoveries are related monetary movements. Modeling each as a separate top-level canonical contract would make the contract set harder to query and govern.

## Consequences

Use:

```text
FinancialTransaction
PolicyFinancialTransaction
ClaimFinancialTransaction
FinancialTransactionClassification
```

Separate contracts may still be introduced when a financial concept has independent lifecycle, ownership, or durable business behavior that cannot be represented through transaction classification and relationships.

See `references/patterns/pc/financial-transaction-pattern.md`.
