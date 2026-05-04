# Party Role Pattern

Use the party-role pattern when a person, organization, or group participates in a business context.

## Intent

A party should not be duplicated across every business context. Keep the party identity separate from the role the party plays.

## Recommended Contracts

```text
Party
PartyRole
PartyRelationship
SubmissionPartyRole
PolicyPartyRole
ClaimPartyRole
InsurableObjectPartyRole
```

## Common Role Examples

```text
Insured
Producer
Broker
Agent
Claimant
Adjuster
LossPayee
ServiceProvider
Underwriter
```

## Modeling Guidance

Use `Party` for reusable person or organization identity.

Use context-specific role contracts for participation in submissions, policies, claims, coverages, and insurable objects.

Role contracts should carry role type, effective dates, status, relationship keys, and context-specific participation fields.

Use `PartyRelationship` for relationships between parties when the relationship exists outside a single policy, claim, or submission context.
