-- Spark SQL DDL for nebula_pc_silver.silver_claims.claim_coverage
-- Generated from targets/fabric/manifests/pc/claims/claim-coverage.fabric.yaml
-- Source: pc.claim-coverage v0.3.2 (references/odcs/pc/claims/claim-coverage.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_claims.claim_coverage (
  claim_coverage_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical claim coverage record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  claim_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the claim associated with the coverage response.',
  claim_feature_uid STRING COMMENT 'Identifier (GUID reference) for the claim feature when the response is feature-specific.',
  policy_coverage_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the policy coverage that responds to the claim.',
  response_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the coverage response on the claim.',
  applicable_limit_amount DECIMAL(18, 2) COMMENT 'Limit amount applied or available under this coverage response when known.',
  applicable_limit_currency_code STRING COMMENT 'Currency code for the applicable limit amount. References the CurrencyCode codeset.',
  applicable_deductible_amount DECIMAL(18, 2) COMMENT 'Deductible amount applied under this coverage response when known.',
  applicable_deductible_currency_code STRING COMMENT 'Currency code for the applicable deductible amount. References the CurrencyCode codeset.',
  coverage_decision_date DATE COMMENT 'Date when the coverage decision (acceptance, partial acceptance, denial) was recorded.',
  coverage_decision_code STRING COMMENT 'Classification of the coverage decision such as accepted, partially accepted, denied, or pending.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset.',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract that connects a claim or claim feature to the policy coverage that responds to it. Source: pc.claim-coverage v0.3.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_claims.claim_coverage ZORDER BY (claim_coverage_uid);
