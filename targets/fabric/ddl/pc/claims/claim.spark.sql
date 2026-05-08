-- Spark SQL DDL for nebula_pc_silver.silver_claims.claim
-- Generated from targets/fabric/manifests/pc/claims/claim.fabric.yaml
-- Source: pc.claim v0.4.3 (references/odcs/pc/claims/claim.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_claims.claim (
  claim_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical claim record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  claim_number STRING NOT NULL COMMENT 'Business-facing number assigned to the claim.',
  claim_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the claim.',
  claim_type_code STRING COMMENT 'Classification of the claim by handling, coverage, or operational type.',
  loss_type_code STRING COMMENT 'Classification of the loss or occurrence giving rise to the claim.',
  policy_uid STRING COMMENT 'Identifier (GUID reference) for the policy associated with the claim when policy context is available.',
  policy_coverage_uid STRING COMMENT 'Identifier (GUID reference) for the policy coverage associated with the claim when coverage context is known.',
  exposure_uid STRING COMMENT 'Identifier (GUID reference) for the exposure associated with the claim when exposure context is known.',
  insurable_object_uid STRING COMMENT 'Identifier (GUID reference) for the insurable object directly associated with the claim. Provides a one-hop path from claim to vehicle / property / workers comp class without forcing a join through exposure. Must align with the path through exposure when both are populated.',
  occurrence_uid STRING COMMENT 'Identifier (GUID reference) for the occurrence (loss event) the claim arises from. Multiple claims can share an occurrence so per-event limits and multi-claim correlation are answerable.',
  account_uid STRING COMMENT 'Identifier (GUID reference) for the commercial account the claim rolls up to. Provides a one-hop path for "loss runs by account" without traversing policy. Reachable via policy when null.',
  loss_location_uid STRING COMMENT 'Identifier (GUID reference) for the geographic location where the loss occurred when location detail is available.',
  loss_date DATE COMMENT 'Date when the loss occurred or began.',
  reported_datetime TIMESTAMP COMMENT 'Datetime when the claim or loss notice was reported.',
  opened_date DATE COMMENT 'Date when the claim was opened for handling.',
  closed_date DATE COMMENT 'Date when the claim was closed.',
  catastrophe_uid STRING COMMENT 'Identifier (GUID reference) for the catastrophe associated with the claim when applicable. References the Catastrophe contract; replaces the prior free-string catastrophe_code so per-event accumulation and reinsurance recovery joins resolve cleanly.',
  catastrophe_indicator BOOLEAN COMMENT 'Indicates whether the claim is associated with a catastrophe or similar large-scale event.',
  litigation_indicator BOOLEAN COMMENT 'Indicates whether the claim is involved in litigation.',
  claim_description STRING COMMENT 'Source-neutral business description of the claim or loss when additional context is needed.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for Property and Casualty claim identity, loss context, and current claim summary. Source: pc.claim v0.4.3.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_claims.claim ZORDER BY (claim_uid);
