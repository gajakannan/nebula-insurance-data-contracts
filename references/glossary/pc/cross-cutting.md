# Cross-Cutting Terms

Terms that apply across the whole Property and Casualty contract set rather than to a single subject area. These define the conventions that every entity, event, transaction, and codeset contract follows. The full rules live as ADRs under `references/design-decisions/pc/`.

## Identity

### Canonical Identifier

A stable identifier owned by the canonical contract layer. Independent of any one source system; not changed when source systems re-key, merge, or migrate.

### System Identity Column

The immutable, system-generated GUID that is the primary key on every entity and codeset contract. Field name follows the pattern `*_uid`. Used as the join key for every relationship.

### Business Key

A human-readable identifier the business or operations assigns to an entity, such as a policy number, claim number, or submission number. Required where the business assigns one. Stored alongside the system identity column but not used as the canonical primary key.

### Source System Code

A code identifying the upstream system that produced or last asserted a canonical record. Captured for multi-source mastering and lineage; does not replace the system identity column.

### Source Natural Key

The natural key assigned by the source system. Captured for provenance and reconciliation; not used as the canonical primary key.

## Time

### Business Time

The time dimension that describes when a business concept is or was effective in the real world. Examples: a policy term's `term_effective_date` and `term_expiration_date`, a coverage's `effective_date`.

### System Time

The time dimension that describes when the canonical record was valid in the warehouse. Captured through SCD2 fields independent of business-time fields.

### Valid From Datetime

The system-time start of an SCD2 record version. Populated for every record version on every entity and codeset contract.

### Valid To Datetime

The system-time end of an SCD2 record version. Null indicates the current row.

### Is Current Indicator

A boolean that is true for exactly one row per logical key, indicating the current canonical record version.

### SCD2 Window

The pair of `valid_from_datetime` and `valid_to_datetime` that defines the time interval during which a record version was current in the warehouse.

### Bi-Temporal Model

A model that preserves both business time and system time. Required because insurance routinely backdates and corrects records, so the answers to "what was effective" and "what we knew, when" are different and both must be answerable.

## Record State

### Record Status

The warehouse-level state of a canonical record, distinct from any business lifecycle status the entity may also carry. Captured in `record_status_code` on every entity contract.

### Active Record

A record whose `record_status_code` is `ACTIVE`. The default state for every newly written record.

### Superseded Record

A record version whose `record_status_code` is `SUPERSEDED` because a later version of the same logical key has taken its place.

### Soft-Deleted Record

A record whose `record_status_code` is `SOFT_DELETED` because the upstream truth is that the record should not have existed (data-entry error, duplicate, or system-of-record retraction). Soft delete is the only delete; rows are not physically removed from canonical contracts.

### Restated Record

A record whose `record_status_code` is `RESTATED` because the canonical interpretation has been revised even though the record itself is still considered to have existed.

### Merged Record

A record whose `record_status_code` is `MERGED` because the entity it represented has been consolidated into another canonical record. Carries `merged_into_uid` to point at the surviving record.

## Lifecycle Events and Transactions

### Lifecycle Event

An append-only canonical record of a business-meaningful state change in an entity's history. Captures *what happened*. Does not by itself imply financial impact or processing.

### Transaction

An append-only canonical record of a unit of business activity that has financial impact, document generation, or independent processing identity. Captures *what was processed*.

### Correction Indicator

A boolean on every event and transaction record. True when the row corrects a previously emitted row, false otherwise. Original rows are immutable; corrections are emitted as new rows.

### Corrects Reference

The reference field (named `corrects_*_uid`) that points from a correcting event or transaction to the prior row it corrects. Populated only when the correction indicator is true.

### Triggering Transaction Reference

The optional reference on a lifecycle event that points to the transaction that produced the event, when the event is the consequence of a processed transaction rather than its cause.

## Codesets

### Codeset

A small, governed reference-data contract that enumerates the allowed values for a coded field, their human-readable labels, optional external-standard mappings, and their effective windows.

### Code Value

The business-friendly code value that an entity contract's `*_code` field references. Treated as the canonical foreign key into a codeset.

### Code Label

The human-readable name of a code value, used for presentation and reporting.

### External Standard Code

The code value as defined by an external standard (such as ACORD, NAIC, ISO 4217, or ISO 3166-2) when the canonical codeset records a mapping to that standard.

### Allowed Value

A code value that currently exists in the codeset and is valid for use. Adding an allowed value is a non-breaking change; removing or renaming one is breaking.

### Sentinel Code

An explicit codeset value used to distinguish "unknown" or "not applicable" from missing data. Used in place of overloading null when the business needs the distinction.

## Classification and Sensitivity

### Data Classification

Field-level metadata that captures the sensitivity tier and any applicable regulatory tags for a property. Used by downstream targets to enforce masking, row-level security, retention, and lineage tagging.

### Sensitivity Tier

The classification of how sensitive a field is. One of `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, or `RESTRICTED`. Every property declares one explicitly.

### Regulatory Tag

A tag indicating regulatory category. Includes `PII`, `PHI`, `PCI`, `SPI`, `FINANCIAL`, and `JURISDICTION_RESTRICTED`. Applied additively where multiple categories apply.

### Classification Profile

A contract-level summary of the most-sensitive class present on any property in the contract. Used by target generators to set the default sensitivity label on the materialized table.

### Subject To HIPAA

A contract-level flag that is true when any property is tagged with `PHI`. Used by downstream targets to branch into HIPAA-aware generation logic.

## Currency

### Transactional Currency

The currency in which a monetary amount was originally booked. Stored on every monetary field through a sibling `*_currency_code` reference to the `CurrencyCode` codeset.

### House Currency

A reporting or presentation currency selected by a consumer for aggregation. Not represented in canonical contracts; computed downstream.

### Currency Pairing

The convention that every monetary field is paired with a `*_currency_code` field naming the currency of that amount. Required by the canonical layer; enforced by quality rules.

## Versioning and Status

### Contract Version

The SemVer identifier on every contract: `MAJOR.MINOR.PATCH`. Major bumps signal breaking changes for consumers, minor bumps signal additive changes, patch bumps signal documentation-only changes.

### Pre-Stable Version

A contract whose version is below `1.0.0`. Breaking changes are permitted between `0.x` minor versions but must still be recorded in the contract changelog.

### Changelog

The list of version entries on every contract, captured under `customProperties.changelog`. Each entry records date, change type, and brief description.

### Contract Status

The lifecycle position of a contract: `draft`, `proposed`, `approved`, `deprecated`, or `retired`. Promotion is gated by criteria documented in `status-promotion.md`.

### Deprecated Contract

A contract that is still emitted but discouraged because a successor exists. Carries deprecation metadata pointing at the replacement.

### Retired Contract

A contract that is no longer emitted. The contract file remains in the repository for historical reference but produces no target artifacts.

### Domain Steward

The named owner of a contract who signs off on promotion to `approved` and on subsequent changes that affect consumers.

## Conformance

### Canonical Layer

The Silver-layer position in the medallion architecture. The contracts in this repository define the canonical layer; Bronze landing and Gold mart shapes are downstream concerns.

### Source-Neutral

The property of a canonical contract that it does not embed source-system structure, vendor schema, raw DDL, ontology export, or copied definition. Source signal is allowed as design input only.

### Platform-Neutral

The property of a canonical contract that it does not embed target-platform mechanics. Target-specific projection (dbt, Microsoft Fabric, Databricks, Snowflake) lives under `targets/`.
