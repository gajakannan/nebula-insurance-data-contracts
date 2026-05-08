-- Spark SQL DDL for nebula_pc_silver.silver_financial.policy_financial_transaction
-- Generated from targets/fabric/manifests/pc/financial/policy-financial-transaction.fabric.yaml
-- Source: pc.policy-financial-transaction v0.2.2 (references/odcs/pc/financial/policy-financial-transaction.odcs.yaml)
-- Contract kind: transaction
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_financial.policy_financial_transaction (
  policy_financial_transaction_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical policy financial transaction record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  policy_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the policy associated with the transaction.',
  account_uid STRING COMMENT 'Identifier (GUID reference) for the commercial account the transaction rolls up to. Enables account-level financial rollups (master-program billing, account-level commission accruals) without traversing policy.',
  agreement_uid STRING COMMENT 'Identifier (GUID reference) for the master legal or program agreement under which the transaction was booked, when applicable.',
  policy_term_uid STRING COMMENT 'Identifier (GUID reference) for the policy term associated with the transaction when term context is known.',
  policy_coverage_uid STRING COMMENT 'Identifier (GUID reference) for the policy coverage that the transaction is booked against when coverage-level allocation is known.',
  payee_party_role_uid STRING COMMENT 'Identifier (GUID reference) for the policy party role that is the payee of the transaction when applicable (e.g. agent commission, broker fee).',
  transaction_type_code STRING NOT NULL COMMENT 'Classification of the transaction such as PREMIUM, RETURN_PREMIUM, FEE, COMMISSION, SURCHARGE, TAX. References the TransactionType codeset.',
  transaction_classification_code STRING COMMENT 'Optional secondary classification (e.g. WRITTEN_PREMIUM, EARNED_PREMIUM, FEE_POLICY, FEE_INSPECTION, COMMISSION_BASE, COMMISSION_OVERRIDE) used by analytics and reporting. References the FinancialTransactionClassification codeset.',
  transaction_amount DECIMAL(18, 2) NOT NULL COMMENT 'Signed monetary amount of the transaction in the transactional currency. Sign convention is positive for charges to the insured, negative for credits and returns.',
  transaction_currency_code STRING NOT NULL COMMENT 'Currency code for the transaction amount. References the CurrencyCode codeset.',
  transaction_effective_date DATE NOT NULL COMMENT 'Business-effective date of the transaction.',
  transaction_processed_datetime TIMESTAMP COMMENT 'Datetime when the transaction was processed or posted.',
  accounting_period_code STRING COMMENT 'Accounting period to which the transaction is booked (e.g. YYYY-MM, YYYY-QN) when known.',
  policy_lifecycle_event_uid STRING COMMENT 'Optional reference to the policy lifecycle event that this transaction realizes (per the event-and-transaction ADR).',
  transaction_narrative STRING COMMENT 'Source-neutral narrative describing the transaction when additional context is needed.',
  correction_indicator BOOLEAN NOT NULL COMMENT 'True when this row corrects a previously emitted row. False for original (uncorrected) rows.',
  corrects_policy_financial_transaction_uid STRING COMMENT 'Reference to the prior row that this row corrects. Populated only when correction_indicator is true.'
)
USING DELTA
PARTITIONED BY (transaction_effective_date)
COMMENT 'Canonical contract for policy-related financial activity such as premium movements, fee posts, commission accruals, surcharges, and other policy-side transactions. Source: pc.policy-financial-transaction v0.2.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);
