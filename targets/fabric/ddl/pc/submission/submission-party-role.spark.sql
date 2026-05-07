-- Spark SQL DDL for nebula_pc_silver.silver_submission.submission_party_role
-- Generated from targets/fabric/manifests/pc/submission/submission-party-role.fabric.yaml
-- Source: pc.submission-party-role v0.4.1 (references/odcs/pc/submission/submission-party-role.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_submission.submission_party_role (
  submission_party_role_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical submission party role record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  submission_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the submission where the party participates.',
  party_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the party participating in the submission role.',
  role_type_code STRING NOT NULL COMMENT 'Classification of the role the party plays in the submission context.',
  role_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the party role within the submission context.',
  primary_role_indicator BOOLEAN COMMENT 'Indicates whether this party role is the primary role of its type within the submission context.',
  effective_date DATE COMMENT 'Date when the party role becomes effective in the submission context.',
  expiration_date DATE COMMENT 'Date when the party role stops being effective in the submission context.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a party participating in a Property and Casualty submission context. Source: pc.submission-party-role v0.4.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_submission.submission_party_role ZORDER BY (submission_party_role_uid);
