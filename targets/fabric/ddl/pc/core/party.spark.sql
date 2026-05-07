-- Spark SQL DDL for nebula_pc_silver.silver_core.party
-- Generated from targets/fabric/manifests/pc/core/party.fabric.yaml
-- Source: pc.party v0.4.1 (references/odcs/pc/core/party.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_core.party (
  party_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical party record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  party_type_code STRING NOT NULL COMMENT 'Classification of the party as a person, organization, household, trust, or other recognized party type.',
  party_display_name STRING NOT NULL COMMENT 'Name used to identify the party in business-facing contexts.',
  legal_name STRING COMMENT 'Legal name for the party when it differs from the display name or is required for contractual context.',
  given_name STRING COMMENT 'Given or first name for a party that represents an individual person.',
  middle_name STRING COMMENT 'Middle name or initial for a party that represents an individual person.',
  family_name STRING COMMENT 'Family or last name for a party that represents an individual person.',
  birth_date DATE COMMENT 'Date of birth for a party that represents an individual person.',
  organization_name STRING COMMENT 'Registered or commonly used organization name for a party that represents an organization.',
  organization_type_code STRING COMMENT 'Classification of an organization party, such as carrier, agency, employer, vendor, or public entity.',
  party_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the party identity record.',
  effective_date DATE COMMENT 'Date when the party identity record becomes effective for canonical use.',
  expiration_date DATE COMMENT 'Date when the party identity record stops being effective for canonical use.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a reusable person, organization, or group identity in Property and Casualty insurance. Source: pc.party v0.4.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_core.party ZORDER BY (party_uid);
