-- Spark SQL DDL for nebula_pc_silver.silver_core.agreement
-- Generated from targets/fabric/manifests/pc/core/agreement.fabric.yaml
-- Source: pc.agreement v0.1.1 (references/odcs/pc/core/agreement.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_core.agreement (
  agreement_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical agreement record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  agreement_number STRING NOT NULL COMMENT 'Business-facing number assigned to the agreement.',
  agreement_name STRING NOT NULL COMMENT 'Business-facing name of the agreement (typically the program name or master-program designation).',
  agreement_type_code STRING NOT NULL COMMENT 'Classification of the agreement (MASTER_PROGRAM, BROKER_AUTHORITY, MGA_AUTHORITY, SERVICE_AGREEMENT, BINDER_AGREEMENT, etc.). References the AgreementTypeCode codeset.',
  agreement_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the agreement (DRAFT, ACTIVE, EXPIRED, TERMINATED, RENEWED, etc.). References the AgreementStatusCode codeset.',
  account_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the account the agreement belongs to.',
  counterparty_party_uid STRING COMMENT 'Identifier (GUID reference) for the counterparty Party (broker, MGA, program administrator, or master insured) when distinct from the account''s primary party.',
  effective_date DATE NOT NULL COMMENT 'Date when the agreement becomes legally effective.',
  expiration_date DATE COMMENT 'Date when the agreement expires. Null indicates an open-ended agreement (e.g. an evergreen broker authority).',
  agreement_description STRING COMMENT 'Source-neutral business description of the agreement when additional context is needed.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a master legal or program agreement between the insurer and an account, broker, MGA, or program administrator. Spawns one or more policies under shared terms. Source: pc.agreement v0.1.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_core.agreement ZORDER BY (agreement_uid);
