# Financial Terms

## Financial Transaction

Monetary activity associated with policy, claim, coverage, party, exposure, accounting, or other Property and Casualty business context.

## Financial Transaction Identifier

The system identity column on a financial transaction record (`financial_transaction_uid`). An immutable GUID used as the join key for every reference to the transaction.

## Transaction Number

The business-friendly reference the source system or business operations assigns to a financial transaction. Distinct from the financial transaction identifier; not used as the primary key or relationship join key.

## Transaction Type

A classification of operational or financial activity.

## Transaction Classification

A more specific classification that supports analysis of monetary activity without creating a separate contract for every money subtype.

## Transaction Status

The current lifecycle state of a financial transaction.

## Transaction Effective Date

The date when the transaction takes business effect.

## Transaction Posted Date

The date when the transaction is posted to an accounting or reporting context.

## Accounting Period

The accounting or reporting period associated with a financial transaction.

## Transaction Amount

The monetary amount of a financial transaction.

## Transaction Currency

The currency in which the transaction amount is stated.

## Debit Credit Code

A classification that indicates whether a transaction is treated as a debit or credit in the relevant accounting context.

## Source Transaction Reference

A source-neutral reference that helps trace or reconcile a financial transaction without making the canonical contract source-specific.

## Premium

Money charged or recognized for insurance coverage.

## Fee

Money charged for a service, process, or policy-related item that is not the core premium.

## Tax

Money charged or collected for a tax obligation associated with insurance activity.

## Surcharge

An additional charge applied to insurance activity according to a business, regulatory, or product rule.

## Commission

Money associated with compensation for producer, broker, agency, or other distribution participation.

## Payment

Money transferred to satisfy premium, claim, fee, recovery, or other financial obligation.

## Reserve

Money estimated or held for expected claim responsibility.

## Recovery

Money recovered in connection with claim or policy financial activity.

## Salvage

Money or value recovered from damaged property in connection with a claim.

## Subrogation

Recovery activity against a third party that may be responsible for a loss.

## Deductible Recovery

Money recovered from an insured to satisfy a deductible obligation under a coverage.

## Reinsurance Recovery

Money recovered under a reinsurance arrangement in connection with a primary loss. The structural reinsurance contract family is deferred per `references/design-decisions/pc/risk-transfer-scope.md`; reinsurance-recovery activity that flows through carrier financial systems can be represented today as a financial-transaction classification.

## Loss Payment

A financial transaction that pays loss amounts under a claim, distinct from expense payments.

## Expense Payment

A financial transaction that pays expense amounts associated with claim handling, distinct from loss payments.

## Loss Reserve

Money estimated or held for expected loss responsibility on a claim.

## Expense Reserve

Money estimated or held for expected expense responsibility on a claim, distinct from loss reserves.

## Transaction Immutability

The convention that a financial transaction row is never updated in place. Corrections are emitted as new transaction rows with `correction_indicator` set to true and `corrects_*_uid` referencing the corrected row. See `cross-cutting.md` for the broader event-and-transaction convention.

## Currency Pairing

The convention that every monetary field on a financial transaction (or any other contract) is paired with a sibling currency code that names the currency of that amount. The canonical layer does not designate a house currency.
