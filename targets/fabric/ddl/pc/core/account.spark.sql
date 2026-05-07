-- Spark SQL DDL for nebula_pc_silver.silver_core.account
-- Generated from targets/fabric/manifests/pc/core/account.fabric.yaml
-- Source: pc.account v0.1.1 (references/odcs/pc/core/account.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_core.account (
  account_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical account record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  account_number STRING NOT NULL COMMENT 'Business-facing number assigned to the account.',
  account_name STRING NOT NULL COMMENT 'Business-facing name of the account (typically the legal name of the master customer organization).',
  account_type_code STRING NOT NULL COMMENT 'Classification of the account organization (CORPORATE, PARTNERSHIP, LLC, ASSOCIATION, CAPTIVE, MASTER_PROGRAM, INDIVIDUAL_LARGE, etc.). References the AccountTypeCode codeset.',
  account_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the account (ACTIVE, PROSPECT, INACTIVE, CLOSED, MERGED). References the AccountStatusCode codeset.',
  parent_account_uid STRING COMMENT 'Identifier (GUID reference) for the primary parent account when the account belongs to a corporate hierarchy. Self-references the canonical account contract. Multi-parent or non-primary parent relationships live on AccountRelationship.',
  primary_party_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the legal-entity Party that the account represents. Connects the operational account record to canonical party identity.',
  effective_date DATE COMMENT 'Date when the account becomes effective for business use.',
  expiration_date DATE COMMENT 'Date when the account stops being effective for business use. Null indicates an open-ended account.',
  account_description STRING COMMENT 'Source-neutral business description of the account when additional context is needed.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a commercial-lines account — the master customer record that owns one or more policies, agreements, and submissions. Source: pc.account v0.1.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_core.account ZORDER BY (account_uid);
