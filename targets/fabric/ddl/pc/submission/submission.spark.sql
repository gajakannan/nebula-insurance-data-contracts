-- Spark SQL DDL for nebula_pc_silver.silver_submission.submission
-- Generated from targets/fabric/manifests/pc/submission/submission.fabric.yaml
-- Source: pc.submission v0.4.2 (references/odcs/pc/submission/submission.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_submission.submission (
  submission_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical submission record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  submission_number STRING NOT NULL COMMENT 'Business-facing number assigned to the submission.',
  submission_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the submission.',
  submission_type_code STRING COMMENT 'Classification of the submission type, such as new business, renewal, rewrite, or other recognized intake type.',
  line_of_business_code STRING NOT NULL COMMENT 'Line of business associated with the submission.',
  account_uid STRING COMMENT 'Identifier (GUID reference) for the commercial account the submission belongs to. Required for commercial-lines submissions; null for personal-lines submissions that do not live under an account.',
  agreement_uid STRING COMMENT 'Identifier (GUID reference) for the master legal or program agreement the submission is being placed under, when applicable (typically renewals or extensions under an existing master program).',
  product_uid STRING COMMENT 'Identifier (GUID reference) for the product associated with the submission when a product is known.',
  related_policy_uid STRING COMMENT 'Identifier (GUID reference) for a policy associated with the submission when the submission binds, issues, renews, or rewrites policy context.',
  received_date DATE NOT NULL COMMENT 'Date when the submission was received for consideration.',
  requested_effective_date DATE COMMENT 'Requested effective date for the insurance being submitted.',
  quote_date DATE COMMENT 'Date when a quote was provided for the submission.',
  bind_date DATE COMMENT 'Date when the submission was bound when applicable.',
  decline_date DATE COMMENT 'Date when the submission was declined when applicable.',
  withdrawn_date DATE COMMENT 'Date when the submission was withdrawn when applicable.',
  submission_description STRING COMMENT 'Source-neutral business description of the submission when additional context is needed.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for Property and Casualty submission intake and current submission summary. Source: pc.submission v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_submission.submission ZORDER BY (submission_uid);
