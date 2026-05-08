-- Spark SQL DDL for nebula_pc_silver.silver_exposure.insurable_object
-- Generated from targets/fabric/manifests/pc/exposure/insurable-object.fabric.yaml
-- Source: pc.insurable-object v0.4.2 (references/odcs/pc/exposure/insurable-object.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_exposure.insurable_object (
  insurable_object_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical insurable object record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  insurable_object_type_code STRING NOT NULL COMMENT 'Classification of the thing, operation, interest, or location that may be insured.',
  insurable_object_name STRING COMMENT 'Business-facing name or label for the insurable object.',
  insurable_object_classification_uid STRING COMMENT 'Identifier (GUID reference) for the durable classification associated with the insurable object when classification detail is represented separately.',
  geographic_location_uid STRING COMMENT 'Identifier (GUID reference) for the geographic location associated with the insurable object when location context is available.',
  insurable_object_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the insurable object.',
  insurable_object_description STRING COMMENT 'Source-neutral business description of the insurable object when additional context is needed.',
  effective_date DATE COMMENT 'Date when the insurable object becomes effective in the business context.',
  expiration_date DATE COMMENT 'Date when the insurable object stops being effective in the business context.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for an object, property, vehicle, operation, interest, or location that may be insured in Property and Casualty insurance. Source: pc.insurable-object v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_exposure.insurable_object ZORDER BY (insurable_object_uid);
