-- Spark SQL DDL for nebula_pc_silver.silver_claims.claim_feature
-- Generated from targets/fabric/manifests/pc/claims/claim-feature.fabric.yaml
-- Source: pc.claim-feature v0.3.3 (references/odcs/pc/claims/claim-feature.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_claims.claim_feature (
  claim_feature_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical claim feature record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  claim_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the claim that this feature partitions.',
  feature_number STRING COMMENT 'Business-friendly identifier for the feature within the claim.',
  feature_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the claim feature.',
  cause_of_loss_code STRING COMMENT 'Cause of loss classification associated with the feature when known. References the CauseOfLossCode codeset.',
  policy_coverage_uid STRING COMMENT 'Identifier (GUID reference) for the policy coverage that this feature primarily responds to when known.',
  exposure_uid STRING COMMENT 'Identifier (GUID reference) for the exposure associated with the feature when exposure context is known.',
  opened_date DATE COMMENT 'Date when the claim feature was opened for handling.',
  closed_date DATE COMMENT 'Date when the claim feature was closed.',
  feature_description STRING COMMENT 'Source-neutral business description of the claim feature when additional context is needed.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset.',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a claim feature, partitioning a claim into independent handling streams by coverage, peril, claimant, or other business dimension. Source: pc.claim-feature v0.3.3.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_claims.claim_feature ZORDER BY (claim_feature_uid);
