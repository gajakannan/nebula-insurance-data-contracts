-- Spark SQL DDL for nebula_pc_silver.silver_exposure.exposure
-- Generated from targets/fabric/manifests/pc/exposure/exposure.fabric.yaml
-- Source: pc.exposure v0.4.2 (references/odcs/pc/exposure/exposure.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_exposure.exposure (
  exposure_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical exposure record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  exposure_type_code STRING NOT NULL COMMENT 'Classification of the exposure by risk basis or insured-object type.',
  exposure_basis_code STRING COMMENT 'Classification of the measurement basis used for the exposure, such as vehicle, property value, payroll, sales, area, or unit count.',
  exposure_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the exposure.',
  policy_uid STRING COMMENT 'Identifier (GUID reference) for the policy associated with the exposure when policy context is available.',
  policy_term_uid STRING COMMENT 'Identifier (GUID reference) for the policy term associated with the exposure when term detail is represented separately.',
  policy_coverage_uid STRING COMMENT 'Identifier (GUID reference) for the policy coverage associated with the exposure when coverage context is known.',
  insurable_object_uid STRING COMMENT 'Identifier (GUID reference) for the object, property, vehicle, operation, or interest that may be insured when represented separately.',
  geographic_location_uid STRING COMMENT 'Identifier (GUID reference) for the location associated with the exposure when a canonical geographic location is available.',
  exposure_quantity DECIMAL(18, 2) COMMENT 'Measured quantity for the exposure when the exposure basis can be represented as a numeric value.',
  exposure_unit_code STRING COMMENT 'Unit of measure for the exposure quantity.',
  rating_territory_code STRING COMMENT 'Territory classification used for rating or risk analysis when applicable.',
  exposure_description STRING COMMENT 'Source-neutral business description of the exposure when additional context is needed.',
  effective_date DATE COMMENT 'Date when the exposure becomes effective in the business context.',
  expiration_date DATE COMMENT 'Date when the exposure stops being effective in the business context.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for the measurable risk basis associated with Property and Casualty policy, coverage, claim, underwriting, or analytics context. Source: pc.exposure v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_exposure.exposure ZORDER BY (exposure_uid);
