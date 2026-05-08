-- Spark SQL DDL for nebula_pc_silver.silver_core.party_relationship
-- Generated from targets/fabric/manifests/pc/core/party-relationship.fabric.yaml
-- Source: pc.party-relationship v0.4.2 (references/odcs/pc/core/party-relationship.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_core.party_relationship (
  party_relationship_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical party relationship record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  from_party_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the party where the relationship direction starts.',
  to_party_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the party where the relationship direction ends.',
  relationship_type_code STRING NOT NULL COMMENT 'Classification of the relationship between the two parties.',
  relationship_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the party relationship.',
  relationship_description STRING COMMENT 'Source-neutral business description of the party relationship when additional context is needed.',
  effective_date DATE COMMENT 'Date when the party relationship becomes effective.',
  expiration_date DATE COMMENT 'Date when the party relationship stops being effective.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a durable relationship between two parties in Property and Casualty insurance. Source: pc.party-relationship v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_core.party_relationship ZORDER BY (party_relationship_uid);
