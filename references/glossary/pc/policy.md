# Policy Terms

## Policy

A durable insurance contract identity and current policy summary for Property and Casualty business.

## Policy Identifier

The system identity column on a policy record (`policy_uid`). An immutable GUID generated upstream and used as the join key for every reference to the policy.

## Policy Number

The business-friendly identifier the business or operations assigns to a policy. Distinct from the policy identifier; not used as the primary key or relationship join key.

## Policy Status

The current lifecycle state of a policy.

## Policy Type

A classification of the kind of policy represented.

## Line Of Business

A grouping of insurance business based on the risk or coverage domain, such as auto, property, liability, workers compensation, or another recognized P&C line.

## Product

An insurance offering or product context used to organize policies, coverages, jurisdictions, and line-of-business applicability.

## Issuing Jurisdiction

The jurisdiction whose rules, forms, or authority apply to issuance of a policy or product.

## Original Effective Date

The first date the policy became effective as a durable insurance contract.

## Issue Date

The date when the policy was issued.

## Current Policy Term

The policy term currently associated with the policy summary.

## Prior Policy

A previous policy related to the current policy, often through renewal, rewrite, replacement, or similar continuity.

## Policy Term

A bounded period of coverage or policy activity associated with a policy.

## Policy Party Role

The participation of a party in a policy context.

## Policy Term Number

A business-facing sequence or number that identifies a term for a policy.

## Term Status

The current lifecycle state of a policy term.

## Term Effective Date

The date when a policy term starts.

## Term Expiration Date

The date when a policy term ends.

## Cancellation Date

The date when a policy term or policy context is cancelled.

## Renewal

Continuation of policy coverage into a new policy term or related policy period.

## Annualized Premium

Premium expressed as an annual amount for comparison, reporting, or policy summary context.

## Premium Currency

The currency in which premium amounts are stated.

## Policy Lifecycle Event

A meaningful event that records progress or change in a policy lifecycle.

## Policy Transaction

Transaction-level policy activity with business meaning, such as endorsement, renewal, cancellation, reinstatement, audit, or another policy change process.

## Transaction Sequence Number

A sequence used to order policy transactions within a policy or term context.

## Transaction Processed Datetime

The date and time when a policy transaction was processed or recorded.

## Premium Change Amount

The monetary change in premium associated with a policy transaction.

## Requested By Party

The party that requested a policy transaction.

## Processed By Party

The party that processed or is accountable for a policy transaction.

## Policy Document

A document associated with a policy, policy term, or policy transaction.

## Bind

A business event or state in which coverage is committed before or as part of policy issuance.

## Policy Issue

A lifecycle event or activity that creates the issued policy record or makes the policy available as an issued contract.

## Endorsement

A policy change that modifies policy terms, coverages, parties, limits, deductibles, exposures, or related details after initial issue.

## Reinstatement

Restoration of policy effectiveness after cancellation, lapse, or another inactive state.

## Non-Renewal

A decision or event indicating that a policy will not continue into another term.

## Rewrite

A policy lifecycle activity that replaces or restates policy context through a new or related policy.

## Audit

A review activity that may adjust policy, exposure, premium, or related details after issue or during the policy lifecycle.
