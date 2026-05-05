# Currency Convention

## Decision

Every monetary field stores the **transactional amount** in the **transactional currency**. Each monetary field is paired with a sibling `*_currency_code` field that names the currency of that amount.

The canonical layer does not designate a house currency. Currency conversion (presentation currency, group reporting currency, FX-as-of-date logic) is a downstream concern.

## Rationale

P&C operates across jurisdictions. Booking premiums, paying claims, holding reserves, and recovering subrogation can all happen in different currencies on the same policy or claim. Forcing a canonical "house currency" requires the canonical layer to embed FX policy (which rate, on which date, applied how) — that is a reporting decision that varies by consumer and over time.

Storing the original amount with its original currency keeps the canonical layer stable. Consumers (financial close, regulatory reporting, analytics) apply their own FX rules.

## Consequences

- For every `*_amount` (or other monetary field), the contract also defines `*_currency_code`.
- `*_currency_code` is a foreign-key reference to a `CurrencyCode` codeset contract (per the codeset strategy ADR), populated from ISO 4217 with mapping recorded.
- Quality rule: when a monetary field is populated, its paired currency field must also be populated. When the monetary field is null, the currency field may be null.
- Decimal precision and scale for monetary fields default to a uniform standard documented in the authoring guide. Specialized fields with different precision (e.g. premium rates, FX rates) call this out explicitly.
- Multi-currency aggregations are not represented in canonical contracts. A consumer that needs them computes them in its own model or semantic layer.

## Guidance

- Do not add a `house_currency_amount` or `reporting_currency_amount` field to canonical contracts. That is a target-layer or semantic-layer concern.
- Do not infer currency from jurisdiction. Many jurisdictions accept multiple currencies; many policies are written in a non-local currency.
- Where an entity has a "primary" currency for analytical convenience (e.g. `policy_term.premium_currency_code`), that field stands on its own and is not used to imply the currency of unrelated monetary fields elsewhere on the contract.

## Related

- `references/design-decisions/pc/codeset-strategy.md`
- `references/design-decisions/pc/null-semantics.md`
