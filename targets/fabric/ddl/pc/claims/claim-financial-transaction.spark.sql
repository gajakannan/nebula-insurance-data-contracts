-- Spark SQL DDL for nebula_pc_silver.silver_claims.claim_financial_transaction
-- Generated from targets/fabric/manifests/pc/claims/claim-financial-transaction.fabric.yaml
-- Source: pc.claim-financial-transaction v0.1.3 (references/odcs/pc/claims/claim-financial-transaction.odcs.yaml)
-- Contract kind: transaction
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_claims.claim_financial_transaction (
  claim_financial_transaction_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical claim financial transaction record across snapshots and source systems.',
  claim_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the claim associated with the transaction.',
  claim_feature_uid STRING COMMENT 'Identifier (GUID reference) for the claim feature when the transaction is feature-specific.',
  claim_coverage_uid STRING COMMENT 'Identifier (GUID reference) for the claim coverage that the transaction is booked against when known.',
  payee_party_role_uid STRING COMMENT 'Identifier (GUID reference) for the claim party role that is the payee of the transaction when applicable.',
  transaction_type_code STRING NOT NULL COMMENT 'Classification of the transaction such as PAYMENT, RESERVE_CHANGE, RECOVERY, SALVAGE, SUBROGATION, DEDUCTIBLE_RECOVERY, or EXPENSE. References the TransactionType codeset.',
  transaction_classification_code STRING COMMENT 'Optional secondary classification (e.g. INDEMNITY, EXPENSE_ALAE, EXPENSE_ULAE, RESERVE_INDEMNITY, RESERVE_EXPENSE) used by analytics and reporting.',
  reserve_category_code STRING COMMENT 'Reserve category for transactions that affect a reserve, such as INDEMNITY_RESERVE or EXPENSE_RESERVE. Null for transactions that do not affect a reserve.',
  transaction_amount DECIMAL(18, 2) NOT NULL COMMENT 'Signed monetary amount of the transaction in the transactional currency. Sign convention is positive for outbound payments and reserve increases, negative for recoveries and reserve decreases.',
  transaction_currency_code STRING NOT NULL COMMENT 'Currency code for the transaction amount. References the CurrencyCode codeset.',
  transaction_effective_date DATE NOT NULL COMMENT 'Business-effective date of the transaction.',
  transaction_processed_datetime TIMESTAMP COMMENT 'Datetime when the transaction was processed or posted.',
  accounting_period_code STRING COMMENT 'Accounting period to which the transaction is booked (e.g. YYYY-MM, YYYY-QN) when known.',
  lifecycle_event_uid STRING COMMENT 'Optional reference to the claim lifecycle event that this transaction realizes (per the event-and-transaction ADR).',
  transaction_narrative STRING COMMENT 'Source-neutral narrative describing the transaction when additional context is needed.',
  correction_indicator BOOLEAN NOT NULL COMMENT 'True when this row corrects a previously emitted row. False for original (uncorrected) rows.',
  corrects_claim_financial_transaction_uid STRING COMMENT 'Reference to the prior row that this row corrects. Populated only when correction_indicator is true.'
)
USING DELTA
PARTITIONED BY (transaction_effective_date)
COMMENT 'Canonical contract for claim-related financial activity such as reserves, payments, recoveries, salvage, subrogation, and expense activity. Source: pc.claim-financial-transaction v0.1.3.'
TBLPROPERTIES (
  'delta.appendOnly' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);
