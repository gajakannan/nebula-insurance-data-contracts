# Role Modeling

## Decision

Separate party identity from contextual participation.

## Rationale

The same person or organization may be an insured on one policy, a producer on another, a claimant on a claim, a loss payee on coverage, or a service provider on a claim. Duplicating party attributes in each context creates inconsistent identity and relationship handling.

## Consequences

Use `Party` for reusable identity.

Use role contracts for contextual participation:

```text
PartyRole
SubmissionPartyRole
PolicyPartyRole
ClaimPartyRole
InsurableObjectPartyRole
```

Use `PartyRelationship` for relationships between parties that are not limited to one business context.

See `references/patterns/pc/party-role-pattern.md`.
