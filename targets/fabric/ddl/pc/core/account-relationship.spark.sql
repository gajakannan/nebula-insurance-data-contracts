-- Spark SQL DDL for nebula_pc_silver.silver_core.account_relationship
-- Generated from targets/fabric/manifests/pc/core/account-relationship.fabric.yaml
-- Source: pc.account-relationship v0.1.1 (references/odcs/pc/core/account-relationship.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_core.account_relationship (
  account_relationship_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical account relationship record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  from_account_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the originating account in the relationship.',
  to_account_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the receiving account in the relationship (e.g. the parent in a parent-child relationship).',
  relationship_type_code STRING NOT NULL COMMENT 'Classification of the relationship (PARENT, BILLING_PARENT, UNDERWRITING_PARENT, MASTER_PROGRAM, ULTIMATE_PARENT, MERGED_INTO, DEMERGED_FROM, etc.). References the AccountRelationshipTypeCode codeset.',
  relationship_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the relationship. References the RelationshipStatusCode codeset.',
  relationship_description STRING COMMENT 'Source-neutral business description of the relationship when additional context is needed.',
  effective_date DATE COMMENT 'Date when the relationship becomes effective.',
  expiration_date DATE COMMENT 'Date when the relationship stops being effective.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for relationships between accounts — corporate hierarchies, billing parents, master programs, ultimate parents, and merger restructurings. Source: pc.account-relationship v0.1.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_core.account_relationship ZORDER BY (account_relationship_uid);
