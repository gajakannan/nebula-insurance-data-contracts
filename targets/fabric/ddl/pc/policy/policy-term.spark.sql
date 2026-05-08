-- Spark SQL DDL for nebula_pc_silver.silver_policy.policy_term
-- Generated from targets/fabric/manifests/pc/policy/policy-term.fabric.yaml
-- Source: pc.policy-term v0.4.2 (references/odcs/pc/policy/policy-term.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_policy.policy_term (
  policy_term_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical policy term record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  policy_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the policy associated with the term.',
  policy_term_number INT COMMENT 'Sequence number or ordinal value for the policy term within the durable policy history.',
  policy_term_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the policy term.',
  term_effective_date DATE NOT NULL COMMENT 'Date when the policy term becomes effective.',
  term_expiration_date DATE NOT NULL COMMENT 'Date when the policy term expires.',
  cancellation_date DATE COMMENT 'Date when the policy term is cancelled when cancellation applies.',
  renewal_indicator BOOLEAN COMMENT 'Indicates whether the policy term represents a renewal term.',
  annualized_premium_amount DECIMAL(18, 2) COMMENT 'Annualized premium amount associated with the policy term when available.',
  annualized_premium_currency_code STRING COMMENT 'Currency code for the annualized premium amount.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a term period associated with a Property and Casualty policy. Source: pc.policy-term v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_policy.policy_term ZORDER BY (policy_term_uid);
