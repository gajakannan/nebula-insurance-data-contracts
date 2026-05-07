-- Spark SQL DDL for nebula_pc_silver.silver_coverage.product_coverage
-- Generated from targets/fabric/manifests/pc/coverage/product-coverage.fabric.yaml
-- Source: pc.product-coverage v0.4.0 (references/odcs/pc/coverage/product-coverage.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_coverage.product_coverage (
  product_coverage_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical product-coverage record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  product_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the product offering this coverage.',
  coverage_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the reusable coverage definition offered by this product.',
  jurisdiction_code STRING COMMENT 'Jurisdiction in which this product-coverage filing applies. References the JurisdictionCode codeset.',
  form_code STRING COMMENT 'Filed form code associated with the product-coverage offering when applicable.',
  form_edition_code STRING COMMENT 'Form edition or revision code associated with the filed form when applicable.',
  mandatory_indicator BOOLEAN COMMENT 'Indicates whether the coverage is mandatory when the product is sold within the applicable scope.',
  default_selected_indicator BOOLEAN COMMENT 'Indicates whether the coverage is selected by default when the product is offered.',
  default_limit_amount DECIMAL(18, 2) COMMENT 'Default limit amount associated with the coverage in this product context when one is filed.',
  default_limit_currency_code STRING COMMENT 'Currency code for the default limit amount. References the CurrencyCode codeset.',
  default_deductible_amount DECIMAL(18, 2) COMMENT 'Default deductible amount associated with the coverage in this product context when one is filed.',
  default_deductible_currency_code STRING COMMENT 'Currency code for the default deductible amount. References the CurrencyCode codeset.',
  minimum_limit_amount DECIMAL(18, 2) COMMENT 'Minimum allowable limit amount for the coverage when offered under this product.',
  maximum_limit_amount DECIMAL(18, 2) COMMENT 'Maximum allowable limit amount for the coverage when offered under this product.',
  limit_constraint_currency_code STRING COMMENT 'Currency code for the minimum and maximum limit constraint amounts. References the CurrencyCode codeset.',
  effective_date DATE COMMENT 'Date when the product-coverage offering becomes effective for new business.',
  expiration_date DATE COMMENT 'Date when the product-coverage offering stops being effective for new business.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset.',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical many-to-many junction contract relating a Product to a Coverage with product-coverage-specific defaults, constraints, and filing context. Source: pc.product-coverage v0.4.0.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_coverage.product_coverage ZORDER BY (product_coverage_uid);
