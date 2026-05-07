-- Spark SQL DDL for nebula_pc_silver.silver_coverage.policy_deductible
-- Generated from targets/fabric/manifests/pc/coverage/policy-deductible.fabric.yaml
-- Source: pc.policy-deductible v0.4.1 (references/odcs/pc/coverage/policy-deductible.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_coverage.policy_deductible (
  policy_deductible_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical policy deductible record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  policy_coverage_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the policy coverage associated with the deductible.',
  deductible_type_code STRING NOT NULL COMMENT 'Classification of the deductible type.',
  deductible_basis_code STRING COMMENT 'Classification of the basis to which the deductible applies, such as occurrence, claim, item, location, or policy term.',
  deductible_amount DECIMAL(18, 2) COMMENT 'Monetary amount of the deductible when represented as an amount.',
  deductible_currency_code STRING COMMENT 'Currency code for the deductible amount.',
  deductible_percent DECIMAL(18, 2) COMMENT 'Percentage value of the deductible when represented as a percentage.',
  minimum_deductible_amount DECIMAL(18, 2) COMMENT 'Minimum monetary deductible amount when the deductible uses a threshold.',
  maximum_deductible_amount DECIMAL(18, 2) COMMENT 'Maximum monetary deductible amount when the deductible uses a cap.',
  effective_date DATE COMMENT 'Date when the policy deductible becomes effective within the policy coverage context.',
  expiration_date DATE COMMENT 'Date when the policy deductible stops being effective within the policy coverage context.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for structured deductible detail associated with a Property and Casualty policy coverage. Source: pc.policy-deductible v0.4.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_coverage.policy_deductible ZORDER BY (policy_deductible_uid);
