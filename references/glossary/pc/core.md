# Core Terms

## Party

A reusable identity for a person, organization, household, trust, public entity, or other recognized participant in Property and Casualty insurance activity.

## Party Identifier

The system identity column on a party record (`party_uid`). An immutable GUID generated upstream and used as the join key for every reference to the party. Distinct from any business-friendly identifier the source systems may assign.

## Party Type

A classification that describes the kind of party represented, such as person, organization, household, trust, or other recognized party type.

## Party Display Name

The business-facing name used to identify a party in operational and analytical contexts.

## Legal Name

The formal name for a party when contractual, regulatory, or legal context requires it.

## Person Party

A party that represents an individual human being.

## Organization Party

A party that represents a company, agency, carrier, employer, vendor, public entity, or other organized body.

## Party Role

The participation of a party in a specific business context, separated from the reusable party identity.

## Role Type

A classification of what a party does in a business context, such as insured, claimant, agent, producer, adjuster, beneficiary, employer, or vendor.

## Business Context

The business subject in which a party role applies, such as submission, policy, claim, account, agreement, coverage, or exposure.

## Context Identifier

The canonical identifier of the business context where a party role applies.

## Primary Role

The party role treated as the main role of its type within a business context.

## Party Relationship

A durable relationship between two parties that is not limited to one submission, policy, claim, or other single business context.

## Relationship Direction

The orientation of a party relationship from one party to another party.

## Relationship Type

A classification of the business meaning of a party-to-party relationship.

## Effective Date

The date when a record, role, relationship, value, or classification becomes valid for canonical business use.

## Expiration Date

The date when a record, role, relationship, value, or classification stops being valid for canonical business use.

## Canonical Identifier

A stable identifier used by the canonical contract layer to connect records without depending on any one source system. See `cross-cutting.md` for the full identifier strategy.

## Party Role Type

The classification of a role a party plays in a business context, such as insured, claimant, producer, broker, agent, adjuster, loss payee, service provider, or underwriter. Captured through the `PartyRoleTypeCode` codeset.

## Effective Window

The pair of effective and expiration dates that bounds when a party identity, party role, or party relationship is valid for canonical business use. Distinct from the SCD2 system-time window.
