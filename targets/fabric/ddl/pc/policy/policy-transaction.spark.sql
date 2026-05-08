-- Spark SQL DDL for nebula_pc_silver.silver_policy.policy_transaction
-- Generated from targets/fabric/manifests/pc/policy/policy-transaction.fabric.yaml
-- Source: pc.policy-transaction v0.4.1 (references/odcs/pc/policy/policy-transaction.odcs.yaml)
-- Contract kind: transaction
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_policy.policy_transaction (
  policy_transaction_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical policy transaction record across snapshots and source systems.',
  policy_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the policy associated with the transaction.',
  policy_term_uid STRING COMMENT 'Identifier (GUID reference) for the policy term associated with the transaction when term context is known.',
  policy_lifecycle_event_uid STRING COMMENT 'Identifier (GUID reference) for the policy lifecycle event associated with the transaction when event context is known.',
  transaction_type_code STRING NOT NULL COMMENT 'Business-facing code for the policy transaction type.',
  transaction_effective_date DATE NOT NULL COMMENT 'Date when the policy transaction takes business effect.',
  transaction_processed_datetime TIMESTAMP COMMENT 'Datetime when the policy transaction was processed or recorded.',
  transaction_sequence_number INT COMMENT 'Sequence number used to order policy transactions within a policy or term context.',
  requested_by_party_uid STRING COMMENT 'Identifier (GUID reference) for the party that requested the policy transaction when known.',
  processed_by_party_uid STRING COMMENT 'Identifier (GUID reference) for the party that processed or is accountable for the policy transaction when known.',
  premium_change_amount DECIMAL(18, 2) COMMENT 'Monetary premium change associated with the policy transaction when available.',
  premium_change_currency_code STRING COMMENT 'Currency code for the premium change amount.',
  transaction_description STRING COMMENT 'Source-neutral business description of the policy transaction when additional context is needed.',
  correction_indicator BOOLEAN NOT NULL COMMENT 'True when this row corrects a previously emitted row. False for original (uncorrected) rows.',
  corrects_policy_transaction_uid STRING COMMENT 'Reference to the prior row that this row corrects. Populated only when correction_indicator is true.'
)
USING DELTA
PARTITIONED BY (transaction_effective_date)
COMMENT 'Canonical contract for transaction-level policy activity in Property and Casualty insurance. Source: pc.policy-transaction v0.4.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);
