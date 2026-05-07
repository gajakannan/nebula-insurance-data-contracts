# Party Role Pattern

Use the party-role pattern when a person, organization, or group participates in a business context.

## Intent

A party should not be duplicated across every business context. Keep the party identity separate from the role the party plays.

## Recommended Contracts

```text
Party
PartyRelationship
SubmissionPartyRole
PolicyPartyRole
ClaimPartyRole
InsurableObjectPartyRole
AccountPartyRole
```

A generic `PartyRole` contract is **not** part of the canonical surface. The polymorphic `context_type_code + context_uid` shape it would require cannot be validated by ODCS, and every shipped use case maps to one of the five context-specific role contracts. Authors needing a new role context add a new context-specific contract following the same shape.

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

Role contracts should carry role type, effective dates, status, relationship keys, and context-specific participation fields. The role-type code references the `PartyRoleTypeCode` codeset.

Use `PartyRelationship` for relationships between parties when the relationship exists outside a single policy, claim, or submission context.

Party identity carries PII; role contracts carry context. See `references/design-decisions/pc/data-classification.md` for field-level sensitivity tagging that applies across the party-role contract family.
