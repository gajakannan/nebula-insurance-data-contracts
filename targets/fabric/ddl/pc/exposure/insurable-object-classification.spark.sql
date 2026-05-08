-- Spark SQL DDL for nebula_pc_silver.silver_exposure.insurable_object_classification
-- Generated from targets/fabric/manifests/pc/exposure/insurable-object-classification.fabric.yaml
-- Source: pc.insurable-object-classification v0.4.2 (references/odcs/pc/exposure/insurable-object-classification.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_exposure.insurable_object_classification (
  insurable_object_classification_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical insurable object classification record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  classification_code STRING NOT NULL COMMENT 'Business-facing code for the insurable object classification.',
  classification_name STRING NOT NULL COMMENT 'Business-facing name of the insurable object classification.',
  classification_scheme_code STRING COMMENT 'Classification scheme or taxonomy used for the insurable object classification.',
  parent_insurable_object_classification_uid STRING COMMENT 'Identifier (GUID reference) for a parent insurable object classification when a hierarchy is used.',
  classification_description STRING COMMENT 'Source-neutral business description of the insurable object classification.',
  insurable_object_classification_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the insurable object classification reference record.',
  effective_date DATE COMMENT 'Date when the insurable object classification becomes effective for canonical use.',
  expiration_date DATE COMMENT 'Date when the insurable object classification stops being effective for canonical use.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for durable classification of insurable objects in Property and Casualty insurance. Source: pc.insurable-object-classification v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_exposure.insurable_object_classification ZORDER BY (insurable_object_classification_uid);
