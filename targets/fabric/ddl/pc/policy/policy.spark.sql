-- Spark SQL DDL for nebula_pc_silver.silver_policy.policy
-- Generated from targets/fabric/manifests/pc/policy/policy.fabric.yaml
-- Source: pc.policy v0.4.3 (references/odcs/pc/policy/policy.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_policy.policy (
  policy_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical policy record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  policy_number STRING NOT NULL COMMENT 'Business-facing number assigned to the policy.',
  policy_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the policy.',
  policy_type_code STRING COMMENT 'Classification of the policy, such as new business, renewal, rewrite, or other recognized policy type.',
  line_of_business_code STRING NOT NULL COMMENT 'Classification of the insurance line of business for the policy.',
  account_uid STRING COMMENT 'Identifier (GUID reference) for the commercial account the policy belongs to. Required for commercial-lines rollups; null for personal-lines policies that do not live under an account.',
  agreement_uid STRING COMMENT 'Identifier (GUID reference) for the master legal or program agreement the policy is issued under, when the policy lives under one. Null when the policy stands alone.',
  product_uid STRING COMMENT 'Identifier (GUID reference) for the insurance product associated with the policy when a canonical product is available.',
  issuing_jurisdiction_code STRING COMMENT 'Jurisdiction where the policy is issued or primarily governed.',
  original_effective_date DATE COMMENT 'Date when the policy first became effective across its durable policy history.',
  issue_date DATE COMMENT 'Date when the policy was issued.',
  current_policy_term_uid STRING COMMENT 'Identifier (GUID reference) for the current policy term when term detail is represented in a separate canonical contract.',
  prior_policy_uid STRING COMMENT 'Identifier (GUID reference) for the prior policy in a renewal, rewrite, or replacement chain when applicable.',
  policy_description STRING COMMENT 'Source-neutral business description of the policy when additional context is needed.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for durable Property and Casualty policy identity and current policy summary. Source: pc.policy v0.4.3.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_policy.policy ZORDER BY (policy_uid);
