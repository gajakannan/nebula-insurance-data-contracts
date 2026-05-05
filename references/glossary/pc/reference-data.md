# Reference Data Terms

## Reference Data

Canonical coded or descriptive values used consistently across contracts. Includes both governed codeset contracts (where each row is a code value with a label, optional external-standard mapping, and SCD2 history) and entity-like reference contracts such as `GeographicLocation` and `LocationAddress`.

## Codeset Contract

A small, governed reference-data contract whose rows enumerate the allowed values for a `*_code` field. Every codeset has the same uniform shape: a system identity column, `code_value`, `code_label`, `code_description`, optional external standard mapping, and SCD2 system-time fields. See `cross-cutting.md` for the broader codeset strategy.

## Code Value

The business-friendly value an entity contract's `*_code` field references. The canonical foreign-key target into a codeset.

## Code Label

The human-readable name of a code value, used for presentation and reporting.

## External Standard

The external standards body or specification (such as ACORD, NAIC, ISO 4217, or ISO 3166-2) whose code is captured in the codeset's `external_standard_code` field.

## Sentinel Code

An explicit code value (such as `UNKNOWN` or `NOT_APPLICABLE`) used to distinguish unknown from not applicable when the business needs that distinction. Used in place of overloading null.

## Reference Status

The lifecycle state of a reference data value.

## Active Status Indicator

An indicator that a lifecycle status represents an active or in-force state.

## Terminal Status Indicator

An indicator that a lifecycle status represents an ending state for the relevant lifecycle.

## Lifecycle Status

A reusable lifecycle state for a business subject such as submission, policy, term, coverage, claim, assessment, document, party, or transaction.

## Lifecycle Subject

The business subject to which a lifecycle status or lifecycle event type applies.

## Lifecycle Event Type

A reusable classification of a meaningful lifecycle event.

## Resulting Lifecycle Status

The lifecycle status that normally follows a lifecycle event type.

## Transaction Type Reference

Reference data that classifies operational or financial activity.

## Transaction Category

A broader grouping of transaction types.

## Financial Transaction Indicator

An indicator that a transaction type is used for monetary activity.

## Lifecycle Event Indicator

An indicator that a transaction type is also used to describe or support lifecycle activity.

## Line Of Business Reference

Reference data that defines a recognized Property and Casualty line of business.

## Business Segment

A grouping used to organize lines of business for management, reporting, or product context.

## Parent Line Of Business

A higher-level line of business used to organize more specific lines.

## Geographic Location Reference

Reference data that identifies a place or geographic area used across insurance contexts.

## Location Type

A classification of the kind of location represented.

## Country Subdivision

A state, province, territory, or other subdivision within a country.

## Geocode Precision

A classification of how precise a latitude and longitude are for a location.

## Location Address

Address detail associated with a geographic location.

## Address Type

A classification of the business use or form of an address.

## Record Status Code

The codeset that enumerates warehouse-level record states. Allowed values include `ACTIVE`, `SUPERSEDED`, `SOFT_DELETED`, `RESTATED`, and `MERGED`. Referenced from every entity contract's `record_status_code` field.

## Currency Code

The codeset that enumerates currencies used in monetary fields across the contract set. Mapped to the ISO 4217 standard. Referenced from every `*_currency_code` field.

## Jurisdiction Code

The codeset that enumerates jurisdictions in which insurance contracts are issued, governed, or regulated. Mapped to ISO 3166-2 where applicable.

## Policy Status Code

The codeset that enumerates policy lifecycle status values such as quoted, bound, issued, in-force, cancelled, lapsed, expired, and reinstated.

## Policy Type Code

The codeset that enumerates policy classification values such as new business, renewal, rewrite, and replacement.

## Term Status Code

The codeset that enumerates policy term lifecycle status values such as pending, active, cancelled, expired, and replaced.

## Coverage Basis Code

The codeset that enumerates coverage basis classifications used to apply a coverage within a policy context.

## Coverage Level Code

The codeset that enumerates the level at which a coverage applies, such as policy, term, location, item, exposure, or coverage part.

## Coverage Status Code

The codeset that enumerates the lifecycle status of a coverage within a policy context.

## Party Type Code

The codeset that enumerates party classification values such as person, organization, household, and trust.

## Party Role Type Code

The codeset that enumerates party role types used across submission, policy, claim, coverage, and insurable-object role contracts.

## Claim Status Code

The codeset that enumerates claim lifecycle status values such as open, closed, reopened, denied, and withdrawn.

## Cause Of Loss Code

The codeset that enumerates causes of loss associated with a claim or claim feature.
