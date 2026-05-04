# P&C Contract Backlog

The first contract set should cover the full Property and Casualty operating spine: party, submission, policy, coverage, exposure, claim, financial activity, and reference data.

Submission and policy lifecycle concepts are first-class because many submissions never become policies, and issued policies continue to evolve through endorsements, renewals, cancellations, reinstatements, audits, and expiration.

## Suggested First Contracts

```text
references/odcs/pc/core/party.odcs.yaml
references/odcs/pc/core/party-role.odcs.yaml
references/odcs/pc/core/party-relationship.odcs.yaml
references/odcs/pc/core/account.odcs.yaml
references/odcs/pc/core/agreement.odcs.yaml

references/odcs/pc/submission/submission.odcs.yaml
references/odcs/pc/submission/submission-party-role.odcs.yaml
references/odcs/pc/submission/submission-risk.odcs.yaml
references/odcs/pc/submission/submission-assessment.odcs.yaml
references/odcs/pc/submission/submission-document.odcs.yaml
references/odcs/pc/submission/submission-lifecycle-event.odcs.yaml

references/odcs/pc/policy/policy.odcs.yaml
references/odcs/pc/policy/policy-term.odcs.yaml
references/odcs/pc/policy/policy-party-role.odcs.yaml
references/odcs/pc/policy/policy-lifecycle-event.odcs.yaml
references/odcs/pc/policy/policy-transaction.odcs.yaml
references/odcs/pc/policy/policy-document.odcs.yaml

references/odcs/pc/coverage/product.odcs.yaml
references/odcs/pc/coverage/coverage.odcs.yaml
references/odcs/pc/coverage/policy-coverage.odcs.yaml
references/odcs/pc/coverage/policy-limit.odcs.yaml
references/odcs/pc/coverage/policy-deductible.odcs.yaml

references/odcs/pc/exposure/insurable-object.odcs.yaml
references/odcs/pc/exposure/insurable-object-classification.odcs.yaml
references/odcs/pc/exposure/exposure.odcs.yaml
references/odcs/pc/exposure/vehicle-exposure.odcs.yaml
references/odcs/pc/exposure/property-exposure.odcs.yaml
references/odcs/pc/exposure/workers-comp-exposure.odcs.yaml

references/odcs/pc/claims/claim.odcs.yaml
references/odcs/pc/claims/claim-event.odcs.yaml
references/odcs/pc/claims/claim-coverage.odcs.yaml
references/odcs/pc/claims/claim-party-role.odcs.yaml
references/odcs/pc/claims/claim-document.odcs.yaml

references/odcs/pc/financial/financial-transaction.odcs.yaml
references/odcs/pc/financial/policy-financial-transaction.odcs.yaml
references/odcs/pc/financial/claim-financial-transaction.odcs.yaml
references/odcs/pc/financial/financial-transaction-classification.odcs.yaml

references/odcs/pc/reference-data/geographic-location.odcs.yaml
references/odcs/pc/reference-data/location-address.odcs.yaml
references/odcs/pc/reference-data/line-of-business.odcs.yaml
references/odcs/pc/reference-data/transaction-type.odcs.yaml
references/odcs/pc/reference-data/lifecycle-status.odcs.yaml
references/odcs/pc/reference-data/lifecycle-event-type.odcs.yaml
```

## First Milestone

The first meaningful milestone is a usable P&C Silver-layer contract set for:

```text
Party
Policy
Coverage
Exposure
Claim
FinancialTransaction
```

## Future Domains

The repository starts with P&C, but the structure allows future expansion into:

```text
life/
health/
annuity/
reinsurance/
shared/
```

The `shared/` package should contain reusable concepts only after reuse is proven across domains. Start domain-specific, then promote shared concepts deliberately.
