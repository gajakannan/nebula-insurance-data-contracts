-- Spark SQL DDL for nebula_pc_silver.silver_exposure.vehicle_exposure
-- Generated from targets/fabric/manifests/pc/exposure/vehicle-exposure.fabric.yaml
-- Source: pc.vehicle-exposure v0.4.1 (references/odcs/pc/exposure/vehicle-exposure.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_exposure.vehicle_exposure (
  vehicle_exposure_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical vehicle exposure record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  exposure_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the shared exposure record that this vehicle detail extends.',
  vin_number STRING COMMENT 'Vehicle Identification Number assigned to the vehicle when available. Business key per identifier-strategy ADR (`*_number` form).',
  vehicle_year_number INT COMMENT 'Model year of the vehicle.',
  vehicle_make_name STRING COMMENT 'Manufacturer or make name of the vehicle.',
  vehicle_model_name STRING COMMENT 'Model name of the vehicle.',
  vehicle_use_code STRING COMMENT 'Classification of how the vehicle is used in the insured context.',
  vehicle_class_code STRING COMMENT 'Rating, underwriting, or analytical classification of the vehicle.',
  garaging_location_uid STRING COMMENT 'Identifier (GUID reference) for the geographic location where the vehicle is principally garaged.',
  radius_code STRING COMMENT 'Classification of the operating radius or distance band for the vehicle when applicable.',
  stated_value_amount DECIMAL(18, 2) COMMENT 'Stated value of the vehicle when used for underwriting, rating, or analytics.',
  stated_value_currency_code STRING COMMENT 'Currency code for the stated value amount. References the CurrencyCode codeset.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for vehicle-specific exposure attributes in Property and Casualty insurance. Source: pc.vehicle-exposure v0.4.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_exposure.vehicle_exposure ZORDER BY (vehicle_exposure_uid);
