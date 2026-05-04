# Financial Transaction Pattern

Use the financial transaction pattern for policy and claim monetary activity.

## Intent

Financial concepts should not explode into one canonical contract per money subtype. A transaction-oriented model gives consumers a cleaner and more queryable structure.

## Recommended Contracts

```text
FinancialTransaction
PolicyFinancialTransaction
ClaimFinancialTransaction
FinancialTransactionClassification
```

## Transaction Classifications

Common classifications may include:

```text
Premium
Fee
Tax
Surcharge
Commission
LossPayment
ExpensePayment
ClaimReserve
LossReserve
ExpenseReserve
Salvage
Subrogation
Recovery
DeductibleRecovery
ReinsuranceRecovery
```

## Modeling Guidance

Use a separate top-level contract only when the concept has durable canonical behavior that cannot be represented as a transaction type, amount classification, relationship, or financial dimension.

Preserve context through references to policy, claim, coverage, party, exposure, accounting period, currency, and transaction classification where appropriate.
