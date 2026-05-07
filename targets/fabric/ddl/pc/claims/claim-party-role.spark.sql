-- Spark SQL DDL for nebula_pc_silver.silver_claims.claim_party_role
-- Generated from targets/fabric/manifests/pc/claims/claim-party-role.fabric.yaml
-- Source: pc.claim-party-role v0.4.1 (references/odcs/pc/claims/claim-party-role.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_claims.claim_party_role (
  claim_party_role_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical claim party role record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  claim_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the claim where the party participates.',
  claim_feature_uid STRING COMMENT 'Identifier (GUID reference) for the claim feature when the role applies to a specific feature rather than the whole claim.',
  party_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the party participating in the claim.',
  role_type_code STRING NOT NULL COMMENT 'Classification of the role the party plays in the claim. References the PartyRoleTypeCode codeset.',
  role_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the party role within the claim context.',
  effective_date DATE COMMENT 'Date when the party role becomes effective within the claim context.',
  expiration_date DATE COMMENT 'Date when the party role stops being effective within the claim context.',
  primary_indicator BOOLEAN COMMENT 'Indicates whether this is the primary party for the role type within the claim context.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset.',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a party participating in a Property and Casualty claim context. Source: pc.claim-party-role v0.4.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_claims.claim_party_role ZORDER BY (claim_party_role_uid);
