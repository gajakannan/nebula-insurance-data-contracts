# Null Semantics

## Decision

`null` in a canonical contract means **value not present, reason unspecified**. It is the default and covers the common cases of "not collected," "not applicable in this row," and "unknown" without further distinction.

When the business genuinely needs to distinguish "unknown" from "not applicable" — typically because regulatory or actuarial reporting requires it — the distinction is carried in an explicit codeset value on a paired `*_code` field, **never** by overloading null.

## Rationale

`null` is unavoidable. It will occur when source systems do not collect a value, when an optional field is omitted, when a backfill has not yet run, and when a field is genuinely inapplicable for the row. Trying to encode multiple meanings into the single `null` value loses information that downstream consumers cannot recover.

Three-valued logic ("unknown" vs "not applicable" vs "value") is occasionally required (e.g. for claim cause-of-loss, jurisdiction-required disclosures). Where it is required, the right place to express it is the codeset itself, by including explicit values such as `UNKNOWN` or `NOT_APPLICABLE`.

## Consequences

- `required: true` fields must be populated. The validator enforces presence.
- `required: false` fields may be null. Null carries no further interpretation.
- Codeset contracts that need to distinguish unknown vs not-applicable include explicit `UNKNOWN` and `NOT_APPLICABLE` rows and document when each applies. Consumers see a populated code value, not a null.
- Field descriptions in YAML state when null is meaningful and when it should not occur in healthy data. Quality rules express completeness expectations rather than relying on the description alone.
- Empty string is not a permitted alternative to null. The validator rejects empty-string sentinel values in canonical contracts.

## Business booleans vs null-presence indicators

The prohibition on companion null-presence indicators does **not** apply to business-meaning booleans. A `*_indicator` field that carries genuine business semantics (`litigation_indicator`, `catastrophe_indicator`, `mandatory_indicator`, `selected_indicator`, `active_status_indicator`, `terminal_status_indicator`, `correction_indicator`, `is_current_indicator`) is a legitimate canonical field — it asserts a fact the business cares about, independent of whether some other field is null.

The rule is on intent: if the indicator answers a business question ("is this claim in litigation?", "is this lifecycle status terminal?"), it stays. If the indicator's only job is to encode "the value of *that other field* is null/unknown/not-applicable," it does not — use null or a codeset value.

## Guidance

- Do not introduce a sibling `*_unknown_indicator` or `*_not_applicable_indicator` boolean. Use the codeset.
- Do not use a magic sentinel value (`"N/A"`, `"-"`, `"0001-01-01"`) to mean unknown. Use null or use a codeset value.
- When a field is "required for some rows, not for others" the right model is usually two contracts or a discriminator code, not nullable on a single contract.
- Business booleans should be named so the truth value is unambiguous from the field name alone: `litigation_indicator: true` reads as "the claim is in litigation," not "the litigation field is populated."

## Related

- `references/design-decisions/pc/codeset-strategy.md`
