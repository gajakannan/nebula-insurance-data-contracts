-- Spark SQL DDL for nebula_pc_silver.silver_exposure.insurable_object_party_role
-- Generated from targets/fabric/manifests/pc/exposure/insurable-object-party-role.fabric.yaml
-- Source: pc.insurable-object-party-role v0.1.2 (references/odcs/pc/exposure/insurable-object-party-role.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_exposure.insurable_object_party_role (
  insurable_object_party_role_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical insurable-object party role record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  insurable_object_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the insurable object the party role applies to.',
  party_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the party participating in the insurable object context.',
  role_type_code STRING NOT NULL COMMENT 'Classification of the role the party plays for the insurable object (NAMED_DRIVER, ADDITIONAL_INSURED, LOSS_PAYEE, LESSEE, etc.). References the PartyRoleTypeCode codeset.',
  role_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the party role within the insurable-object context.',
  primary_role_indicator BOOLEAN COMMENT 'Indicates whether this is the primary party for the role type within the insurable-object context (e.g. primary named driver).',
  effective_date DATE COMMENT 'Date when the party role becomes effective within the insurable-object context.',
  expiration_date DATE COMMENT 'Date when the party role stops being effective within the insurable-object context.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a party participating in an insurable object context — named drivers on a vehicle, additional insureds on a property, loss-payees, lessees, and other object-scoped party participations. Source: pc.insurable-object-party-role v0.1.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_exposure.insurable_object_party_role ZORDER BY (insurable_object_party_role_uid);
