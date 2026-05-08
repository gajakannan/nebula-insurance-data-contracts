-- Spark SQL DDL for nebula_pc_silver.silver_reference_data.currency_code
-- Generated from targets/fabric/manifests/pc/reference-data/currency-code.fabric.yaml
-- Source: pc.currency-code v0.4.1 (references/odcs/pc/reference-data/currency-code.odcs.yaml)
-- Contract kind: codeset
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_reference_data.currency_code (
  currency_code_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical CurrencyCode record across snapshots.',
  code_value STRING NOT NULL COMMENT 'Business-friendly code value referenced by entity contracts.',
  code_label STRING NOT NULL COMMENT 'Human-readable label for the code value.',
  code_description STRING COMMENT 'Extended description of the code value.',
  external_standard_code STRING COMMENT 'Code value as defined by ISO 4217 when a mapping is recorded.',
  external_standard_name STRING COMMENT 'Name of the external standard whose code is captured in external_standard_code.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset.',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical codeset for currencies used in monetary fields across the contract set. Source: pc.currency-code v0.4.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_reference_data.currency_code ZORDER BY (currency_code_uid);
