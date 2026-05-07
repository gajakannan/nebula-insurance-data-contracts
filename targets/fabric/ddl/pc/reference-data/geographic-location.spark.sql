-- Spark SQL DDL for nebula_pc_silver.silver_reference_data.geographic_location
-- Generated from targets/fabric/manifests/pc/reference-data/geographic-location.fabric.yaml
-- Source: pc.geographic-location v0.3.1 (references/odcs/pc/reference-data/geographic-location.odcs.yaml)
-- Contract kind: codeset
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_reference_data.geographic_location (
  geographic_location_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical geographic location record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  location_type_code STRING NOT NULL COMMENT 'Classification of the geographic location, such as country, jurisdiction, county, city, postal area, territory, coordinates, or addressable place.',
  location_name STRING COMMENT 'Business-facing name for the geographic location.',
  country_code STRING NOT NULL COMMENT 'Country code associated with the geographic location.',
  country_subdivision_code STRING COMMENT 'State, province, territory, or other first-level country subdivision code associated with the geographic location.',
  county_name STRING COMMENT 'County, parish, borough, or comparable local jurisdiction name associated with the geographic location.',
  city_name STRING COMMENT 'City, town, municipality, or comparable locality name associated with the geographic location.',
  postal_code STRING COMMENT 'Postal or ZIP code associated with the geographic location.',
  latitude_number DECIMAL(18, 2) COMMENT 'Latitude coordinate associated with the geographic location.',
  longitude_number DECIMAL(18, 2) COMMENT 'Longitude coordinate associated with the geographic location.',
  geocode_precision_code STRING COMMENT 'Classification of the precision level for the geographic coordinates when coordinates are populated.',
  effective_date DATE COMMENT 'Date when the geographic location reference record becomes effective for canonical use.',
  expiration_date DATE COMMENT 'Date when the geographic location reference record stops being effective for canonical use.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for geographic location reference data used across Property and Casualty insurance contexts. Source: pc.geographic-location v0.3.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_reference_data.geographic_location ZORDER BY (geographic_location_uid);
