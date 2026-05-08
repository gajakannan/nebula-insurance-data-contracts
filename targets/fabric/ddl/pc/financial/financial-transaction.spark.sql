-- Spark SQL DDL for nebula_pc_silver.silver_financial.financial_transaction
-- Generated from targets/fabric/manifests/pc/financial/financial-transaction.fabric.yaml
-- Source: pc.financial-transaction v0.4.1 (references/odcs/pc/financial/financial-transaction.odcs.yaml)
-- Contract kind: transaction
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_financial.financial_transaction (
  financial_transaction_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical financial transaction record across snapshots and source systems.',
  transaction_number STRING COMMENT 'Business-facing number or reference assigned to the financial transaction when available.',
  transaction_type_code STRING NOT NULL COMMENT 'Classification of the financial transaction type.',
  transaction_classification_code STRING COMMENT 'Classification of the monetary movement, such as premium, fee, tax, commission, payment, reserve, recovery, salvage, or subrogation.',
  transaction_effective_date DATE COMMENT 'Date when the financial transaction becomes effective for business purposes.',
  transaction_posted_date DATE COMMENT 'Date when the financial transaction was posted or recorded.',
  accounting_period_code STRING COMMENT 'Accounting period associated with the financial transaction.',
  transaction_amount DECIMAL(18, 2) NOT NULL COMMENT 'Monetary amount of the financial transaction.',
  transaction_currency_code STRING NOT NULL COMMENT 'Currency code for the transaction amount.',
  debit_credit_code STRING COMMENT 'Classification indicating whether the transaction is a debit, credit, or other recognized accounting direction.',
  policy_uid STRING COMMENT 'Identifier (GUID reference) for the policy associated with the financial transaction when policy context is available.',
  claim_uid STRING COMMENT 'Identifier (GUID reference) for the claim associated with the financial transaction when claim context is available.',
  policy_coverage_uid STRING COMMENT 'Identifier (GUID reference) for the policy coverage associated with the financial transaction when coverage context is known.',
  party_uid STRING COMMENT 'Identifier (GUID reference) for the party associated with the financial transaction when party context is known.',
  exposure_uid STRING COMMENT 'Identifier (GUID reference) for the exposure associated with the financial transaction when exposure context is known.',
  source_transaction_reference STRING COMMENT 'Source-neutral business reference that helps reconcile the financial transaction across processing contexts.',
  transaction_description STRING COMMENT 'Source-neutral business description of the financial transaction when additional context is needed.',
  lifecycle_event_uid STRING COMMENT 'Optional reference to the lifecycle event that this transaction realizes (per the event-and-transaction ADR).',
  correction_indicator BOOLEAN NOT NULL COMMENT 'True when this row corrects a previously emitted row. False for original (uncorrected) rows.',
  corrects_financial_transaction_uid STRING COMMENT 'Reference to the prior row that this row corrects. Populated only when correction_indicator is true.'
)
USING DELTA
PARTITIONED BY (transaction_effective_date)
COMMENT 'Canonical contract for monetary activity associated with Property and Casualty policy, claim, coverage, party, and exposure context. Source: pc.financial-transaction v0.4.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);
