-- Spark SQL DDL for nebula_pc_silver.silver_coverage.policy_coverage
-- Generated from targets/fabric/manifests/pc/coverage/policy-coverage.fabric.yaml
-- Source: pc.policy-coverage v0.4.2 (references/odcs/pc/coverage/policy-coverage.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_coverage.policy_coverage (
  policy_coverage_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical policy coverage record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  policy_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the policy where the coverage is selected or applied.',
  coverage_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the reusable coverage definition selected or applied on the policy.',
  policy_term_uid STRING COMMENT 'Identifier (GUID reference) for the policy term where the coverage applies when term detail is represented separately.',
  exposure_uid STRING COMMENT 'Identifier (GUID reference) for the exposure to which the coverage applies when coverage is exposure-specific.',
  policy_limit_uid STRING COMMENT 'Identifier (GUID reference) for the policy limit detail associated with the coverage when represented separately.',
  policy_deductible_uid STRING COMMENT 'Identifier (GUID reference) for the policy deductible detail associated with the coverage when represented separately.',
  coverage_sequence_number INT COMMENT 'Ordering value used when multiple coverage records must be presented or processed in sequence within the policy context.',
  coverage_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the coverage within the policy context.',
  coverage_level_code STRING COMMENT 'Classification of the level where the coverage applies, such as policy, term, location, item, exposure, or coverage part.',
  coverage_basis_code STRING COMMENT 'Classification of the basis used to apply the coverage within the policy context.',
  selected_indicator BOOLEAN COMMENT 'Indicates whether the coverage was selected for the policy context.',
  mandatory_indicator BOOLEAN COMMENT 'Indicates whether the coverage is mandatory within the policy context.',
  effective_date DATE COMMENT 'Date when the coverage becomes effective within the policy context.',
  expiration_date DATE COMMENT 'Date when the coverage stops being effective within the policy context.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for coverage selected or applied within a Property and Casualty policy context. Source: pc.policy-coverage v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_coverage.policy_coverage ZORDER BY (policy_coverage_uid);
