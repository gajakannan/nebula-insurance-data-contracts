-- Spark SQL DDL for nebula_pc_silver.silver_exposure.property_exposure
-- Generated from targets/fabric/manifests/pc/exposure/property-exposure.fabric.yaml
-- Source: pc.property-exposure v0.4.2 (references/odcs/pc/exposure/property-exposure.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_exposure.property_exposure (
  property_exposure_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical property exposure record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  exposure_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the shared exposure record that this property detail extends.',
  property_location_uid STRING COMMENT 'Identifier (GUID reference) for the geographic location of the property.',
  property_use_code STRING COMMENT 'Classification of how the property is used in the insured context.',
  occupancy_type_code STRING COMMENT 'Classification of the occupancy associated with the property exposure.',
  construction_type_code STRING COMMENT 'Classification of the construction type associated with the property exposure.',
  protection_class_code STRING COMMENT 'Fire protection or public protection classification associated with the property exposure when applicable.',
  year_built_number INT COMMENT 'Year the property structure was built.',
  square_footage_count INT COMMENT 'Area of the property structure measured in square feet when applicable.',
  building_value_amount DECIMAL(18, 2) COMMENT 'Valuation amount for the building or structure when used for underwriting, rating, or analytics.',
  building_value_currency_code STRING COMMENT 'Currency code for the building value amount. References the CurrencyCode codeset.',
  contents_value_amount DECIMAL(18, 2) COMMENT 'Valuation amount for contents associated with the property exposure when applicable.',
  contents_value_currency_code STRING COMMENT 'Currency code for the contents value amount. References the CurrencyCode codeset.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for property-specific exposure attributes in Property and Casualty insurance. Source: pc.property-exposure v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_exposure.property_exposure ZORDER BY (property_exposure_uid);
