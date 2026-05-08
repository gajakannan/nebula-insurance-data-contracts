-- Spark SQL DDL for nebula_pc_silver.silver_reference_data.lifecycle_event_type
-- Generated from targets/fabric/manifests/pc/reference-data/lifecycle-event-type.fabric.yaml
-- Source: pc.lifecycle-event-type v0.4.2 (references/odcs/pc/reference-data/lifecycle-event-type.odcs.yaml)
-- Contract kind: codeset
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_reference_data.lifecycle_event_type (
  lifecycle_event_type_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical lifecycle event type record across snapshots and source systems.',
  code_value STRING NOT NULL COMMENT 'Business-friendly code value referenced by entity contracts.',
  code_label STRING NOT NULL COMMENT 'Human-readable label for the code value.',
  code_description STRING COMMENT 'Extended description of the code value.',
  external_standard_code STRING COMMENT 'Code value as defined by an external standard (ACORD, NAIC, ISO, etc.) when a mapping is recorded.',
  external_standard_name STRING COMMENT 'Name of the external standard whose code is captured in external_standard_code.',
  lifecycle_subject_code STRING NOT NULL COMMENT 'Classification of the business subject to which the lifecycle event type applies.',
  resulting_lifecycle_status_uid STRING COMMENT 'Identifier (GUID reference) for the lifecycle status that commonly results from this event type when applicable.',
  transaction_type_uid STRING COMMENT 'Identifier (GUID reference) for the transaction type associated with this lifecycle event type when applicable.',
  lifecycle_event_type_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the lifecycle event type reference record.',
  effective_date DATE COMMENT 'Date when the lifecycle event type reference record becomes effective for canonical use.',
  expiration_date DATE COMMENT 'Date when the lifecycle event type reference record stops being effective for canonical use.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for lifecycle event type reference data used across Property and Casualty business lifecycles. Source: pc.lifecycle-event-type v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_reference_data.lifecycle_event_type ZORDER BY (lifecycle_event_type_uid);
