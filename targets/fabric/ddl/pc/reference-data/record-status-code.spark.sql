-- Spark SQL DDL for nebula_pc_silver.silver_reference_data.record_status_code
-- Generated from targets/fabric/manifests/pc/reference-data/record-status-code.fabric.yaml
-- Source: pc.record-status-code v0.4.0 (references/odcs/pc/reference-data/record-status-code.odcs.yaml)
-- Contract kind: codeset
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_reference_data.record_status_code (
  record_status_code_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical RecordStatusCode record across snapshots.',
  code_value STRING NOT NULL COMMENT 'Business-friendly code value referenced by entity contracts.',
  code_label STRING NOT NULL COMMENT 'Human-readable label for the code value.',
  code_description STRING COMMENT 'Extended description of the code value.',
  external_standard_code STRING COMMENT 'Code value as defined by an external standard (ACORD, NAIC, ISO, etc.) when a mapping is recorded.',
  external_standard_name STRING COMMENT 'Name of the external standard whose code is captured in external_standard_code.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset.',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical codeset for warehouse-level record state. Allowed values include ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, and MERGED per the record-state ADR. Source: pc.record-status-code v0.4.0.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_reference_data.record_status_code ZORDER BY (record_status_code_uid);
