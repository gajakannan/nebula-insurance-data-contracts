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

Preserve context through references to policy, claim, coverage, party, exposure, accounting period, currency, and transaction classification where appropriate. `ReinsuranceRecovery` is shown above as a likely classification value; the structural reinsurance contract family is deferred per `references/design-decisions/pc/risk-transfer-scope.md`.

Financial transaction contracts are append-only. Corrections are emitted as new immutable rows referencing the corrected row via `corrects_*_uid` per `references/design-decisions/pc/event-and-transaction.md`. Every monetary amount is paired with a sibling `*_currency_code` per `currency-convention.md`.
