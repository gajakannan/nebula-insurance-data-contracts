-- Spark SQL DDL for nebula_pc_silver.silver_coverage.coverage
-- Generated from targets/fabric/manifests/pc/coverage/coverage.fabric.yaml
-- Source: pc.coverage v0.4.2 (references/odcs/pc/coverage/coverage.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_coverage.coverage (
  coverage_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical coverage record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  coverage_code STRING NOT NULL COMMENT 'Business-facing code that classifies the coverage definition.',
  coverage_name STRING NOT NULL COMMENT 'Business-facing name of the coverage definition.',
  coverage_description STRING COMMENT 'Source-neutral business description of the protection provided by the coverage.',
  coverage_type_code STRING COMMENT 'Classification of the coverage by protection type or coverage family.',
  coverage_category_code STRING COMMENT 'Higher-level grouping used to organize related coverage definitions.',
  line_of_business_code STRING NOT NULL COMMENT 'Classification of the insurance line of business where the coverage is generally offered.',
  product_uid STRING COMMENT 'Identifier (GUID reference) for the product that offers the coverage when the coverage is product-specific.',
  coverage_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the coverage definition.',
  effective_date DATE COMMENT 'Date when the coverage definition becomes effective for canonical use.',
  expiration_date DATE COMMENT 'Date when the coverage definition stops being effective for canonical use.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a reusable Property and Casualty coverage concept. Source: pc.coverage v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_coverage.coverage ZORDER BY (coverage_uid);
