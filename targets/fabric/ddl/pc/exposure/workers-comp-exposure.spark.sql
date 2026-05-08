-- Spark SQL DDL for nebula_pc_silver.silver_exposure.workers_comp_exposure
-- Generated from targets/fabric/manifests/pc/exposure/workers-comp-exposure.fabric.yaml
-- Source: pc.workers-comp-exposure v0.4.2 (references/odcs/pc/exposure/workers-comp-exposure.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_exposure.workers_comp_exposure (
  workers_comp_exposure_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical workers comp exposure record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  exposure_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the shared exposure record that this workers compensation detail extends.',
  jurisdiction_code STRING COMMENT 'Jurisdiction associated with the workers compensation exposure.',
  classification_code STRING NOT NULL COMMENT 'Work classification code associated with the workers compensation exposure.',
  governing_class_indicator BOOLEAN COMMENT 'Indicates whether the classification is the governing class for the workers compensation exposure context.',
  job_duty_description STRING COMMENT 'Source-neutral description of the job duties or work activities represented by the exposure.',
  payroll_amount DECIMAL(18, 2) COMMENT 'Payroll amount associated with the workers compensation exposure.',
  payroll_currency_code STRING COMMENT 'Currency code for the payroll amount. References the CurrencyCode codeset.',
  employee_count INT COMMENT 'Number of employees associated with the workers compensation exposure.',
  full_time_equivalent_count DECIMAL(18, 2) COMMENT 'Full-time equivalent employee count associated with the workers compensation exposure.',
  payroll_period_start_date DATE COMMENT 'Start date of the payroll period represented by the exposure detail.',
  payroll_period_end_date DATE COMMENT 'End date of the payroll period represented by the exposure detail.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for workers compensation exposure attributes in Property and Casualty insurance. Source: pc.workers-comp-exposure v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_exposure.workers_comp_exposure ZORDER BY (workers_comp_exposure_uid);
