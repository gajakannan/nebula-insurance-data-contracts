-- Spark SQL DDL for nebula_pc_silver.silver_policy.policy_party_role
-- Generated from targets/fabric/manifests/pc/policy/policy-party-role.fabric.yaml
-- Source: pc.policy-party-role v0.4.2 (references/odcs/pc/policy/policy-party-role.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_policy.policy_party_role (
  policy_party_role_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical policy party role record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  policy_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the policy where the party participates.',
  policy_term_uid STRING COMMENT 'Identifier (GUID reference) for the policy term where the party role applies when the role is term-specific.',
  party_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the party participating in the policy role.',
  role_type_code STRING NOT NULL COMMENT 'Classification of the role the party plays in the policy context.',
  role_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the party role within the policy context.',
  primary_role_indicator BOOLEAN COMMENT 'Indicates whether this party role is the primary role of its type within the policy context.',
  effective_date DATE COMMENT 'Date when the party role becomes effective in the policy context.',
  expiration_date DATE COMMENT 'Date when the party role stops being effective in the policy context.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a party participating in a Property and Casualty policy context. Source: pc.policy-party-role v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_policy.policy_party_role ZORDER BY (policy_party_role_uid);
