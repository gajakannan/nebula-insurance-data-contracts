-- Spark SQL DDL for nebula_pc_silver.silver_reference_data.location_address
-- Generated from targets/fabric/manifests/pc/reference-data/location-address.fabric.yaml
-- Source: pc.location-address v0.3.1 (references/odcs/pc/reference-data/location-address.odcs.yaml)
-- Contract kind: codeset
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_reference_data.location_address (
  location_address_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical location address record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  geographic_location_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the geographic location described by the address.',
  address_type_code STRING COMMENT 'Classification of the address use or address type.',
  address_line_1 STRING COMMENT 'First address line for the location address.',
  address_line_2 STRING COMMENT 'Second address line for the location address.',
  city_name STRING COMMENT 'City, town, municipality, or comparable locality name for the address.',
  country_subdivision_code STRING COMMENT 'State, province, territory, or other first-level country subdivision code for the address.',
  postal_code STRING COMMENT 'Postal or ZIP code for the address.',
  country_code STRING NOT NULL COMMENT 'Country code for the address.',
  effective_date DATE COMMENT 'Date when the address becomes effective for canonical use.',
  expiration_date DATE COMMENT 'Date when the address stops being effective for canonical use.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for address reference data associated with a geographic location in Property and Casualty insurance. Source: pc.location-address v0.3.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_reference_data.location_address ZORDER BY (location_address_uid);
