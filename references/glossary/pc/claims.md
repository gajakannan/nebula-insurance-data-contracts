# Claim Terms

## Claim

A record of loss, damage, injury, liability, or other covered or potentially covered event being handled under a Property and Casualty insurance context.

## Claim Identifier

The system identity column on a claim record (`claim_uid`). An immutable GUID used as the join key for every reference to the claim.

## Claim Number

The business-friendly identifier the business or operations assigns to a claim. Distinct from the claim identifier; not used as the primary key or relationship join key.

## Claim Status

The current lifecycle state of a claim.

## Claim Type

A classification of the kind of claim being handled.

## Loss Type

A classification of the kind of loss associated with a claim.

## Policy Context

The policy connected to a claim when the claim can be tied to policy coverage.

## Claim Coverage Context

The policy coverage connected to claim handling when coverage association is known.

## Claim Exposure Context

The exposure connected to claim handling when the risk basis is known.

## Loss Location

The location associated with the loss or event giving rise to the claim.

## Loss Date

The date when the loss occurred or is treated as having occurred.

## Reported Datetime

The date and time when the claim or loss was reported.

## Opened Date

The date when claim handling was opened.

## Closed Date

The date when claim handling was closed.

## Catastrophe Code

A code used to associate a claim with a catastrophe or large event grouping.

## Catastrophe Indicator

An indicator that the claim is associated with a catastrophe or large event grouping.

## Litigation Indicator

An indicator that the claim involves litigation or litigation handling.

## Claim Description

A source-neutral business description of the claim or loss context.

## Loss Notice

The initial notification that a loss or potential claim has occurred.

## Reserve Change

A change in expected claim financial responsibility or reserve amount.

## Recovery

Money or value recovered in connection with a claim.

## Salvage

Value recovered from damaged property associated with a claim.

## Subrogation

Recovery activity against another party that may be responsible for a loss.

## Reopen

An event or state where a previously closed claim becomes active again.

## Claim Feature

A partition of a claim into independent handling streams when distinct coverages, perils, or claimants are handled separately on a single claim. Optional; used by carriers that model feature-level handling.

## Feature Number

A business-friendly identifier for a feature within a claim. Distinct from the system identity column on the feature record.

## Feature Status

The current lifecycle state of a claim feature.

## Cause Of Loss

The classification of what caused the loss associated with a claim or claim feature. Captured through the `CauseOfLossCode` codeset.

## Claim Coverage

The connection between claim handling and the policy coverage that responds to the claim. Many-to-one from claim feature to policy coverage when features are used; many-to-many between claim and policy coverage when no feature partition is in place.

## Coverage Decision

The disposition recorded for the policy coverage's response to the claim, such as accepted, partially accepted, denied, or pending.

## Applicable Limit

The limit amount applied or available under a particular coverage response on a claim. Paired with a currency code.

## Applicable Deductible

The deductible amount applied under a particular coverage response on a claim. Paired with a currency code.

## Claim Lifecycle Event

A meaningful state change in the claim history. Examples include FNOL received, acknowledged, assigned, reserved, partial payment, full payment, closed, reopened, subrogation initiated, salvage initiated, denied, and withdrawn. Append-only; corrections are emitted as new immutable rows.

## FNOL

First Notice of Loss. The lifecycle event that records the initial notification of a loss or potential claim.

## Claim Party Role

The participation of a party in a claim context, such as claimant, insured contact, adjuster, supervisor, attorney, expert, witness, service provider, or recovery party.

## Adjuster

A party role on a claim that handles investigation, evaluation, and resolution.

## Claimant

A party role on a claim that asserts a claim against an insured or insurer.

## Service Provider

A party role on a claim that performs repair, medical, legal, or other services in connection with the claim.

## Recovery Party

A party role on a claim that is the source or target of a recovery, such as a subrogated party or a salvage purchaser.

## Claim Document

A document associated with a claim or claim feature. Stores metadata only; document content is held in an external store referenced through an opaque storage reference.

## External Storage Reference

An opaque pointer to document content held outside the canonical contract layer. The document body is never stored in the canonical contract.

## Contains PHI Indicator

An indicator that a claim document is known to contain Protected Health Information. Used by downstream targets to apply HIPAA-compliant handling.

## Claim Financial Transaction

Append-only canonical record of a financial movement attached to a claim, such as reserves, payments, recoveries, salvage, subrogation, deductible recovery, or expense activity. Specializes the financial-transaction pattern with claim, feature, coverage, payee party role, and reserve-category context.

## Reserve Category

The classification of a reserve a financial transaction affects, such as indemnity reserve or expense reserve.

## Payee Party Role

The claim party role that is the payee of a financial transaction when the transaction transfers value to a party.

## Indemnity

The portion of claim cost that compensates for the loss itself, distinct from expense costs incurred to handle the claim.

## ALAE

Allocated Loss Adjustment Expense. Expense activity directly attributable to a specific claim, distinct from indemnity.

## ULAE

Unallocated Loss Adjustment Expense. Expense activity associated with claim handling that cannot be allocated to a specific claim.

## Catastrophe

A large event grouping that aggregates many claims arising from a single occurrence such as a hurricane, wildfire, or flood. Captured through the catastrophe code on a claim and reinforced by the catastrophe indicator.
