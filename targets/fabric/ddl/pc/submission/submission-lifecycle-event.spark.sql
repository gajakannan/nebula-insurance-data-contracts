-- Spark SQL DDL for nebula_pc_silver.silver_submission.submission_lifecycle_event
-- Generated from targets/fabric/manifests/pc/submission/submission-lifecycle-event.fabric.yaml
-- Source: pc.submission-lifecycle-event v0.4.1 (references/odcs/pc/submission/submission-lifecycle-event.odcs.yaml)
-- Contract kind: event
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_submission.submission_lifecycle_event (
  submission_lifecycle_event_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical submission lifecycle event record across snapshots and source systems.',
  submission_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the submission associated with the lifecycle event.',
  lifecycle_event_type_code STRING NOT NULL COMMENT 'Business-facing code for the lifecycle event type.',
  lifecycle_event_status_code STRING COMMENT 'Current lifecycle status of the lifecycle event record.',
  prior_status_code STRING COMMENT 'Submission status before the lifecycle event when known.',
  resulting_status_code STRING COMMENT 'Submission status after the lifecycle event when known.',
  event_datetime TIMESTAMP NOT NULL COMMENT 'Datetime when the lifecycle event occurred.',
  initiated_by_party_uid STRING COMMENT 'Identifier (GUID reference) for the party that initiated the lifecycle event when known.',
  event_description STRING COMMENT 'Source-neutral business description of the lifecycle event when additional context is needed.',
  correction_indicator BOOLEAN NOT NULL COMMENT 'True when this row corrects a previously emitted row. False for original (uncorrected) rows.',
  corrects_submission_lifecycle_event_uid STRING COMMENT 'Reference to the prior row that this row corrects. Populated only when correction_indicator is true.'
)
USING DELTA
PARTITIONED BY (event_datetime)
COMMENT 'Canonical contract for meaningful lifecycle events in a Property and Casualty submission. Source: pc.submission-lifecycle-event v0.4.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);
