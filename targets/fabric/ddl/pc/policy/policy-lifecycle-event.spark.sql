-- Spark SQL DDL for nebula_pc_silver.silver_policy.policy_lifecycle_event
-- Generated from targets/fabric/manifests/pc/policy/policy-lifecycle-event.fabric.yaml
-- Source: pc.policy-lifecycle-event v0.4.1 (references/odcs/pc/policy/policy-lifecycle-event.odcs.yaml)
-- Contract kind: event
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_policy.policy_lifecycle_event (
  policy_lifecycle_event_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical policy lifecycle event record across snapshots and source systems.',
  policy_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the policy associated with the lifecycle event.',
  policy_term_uid STRING COMMENT 'Identifier (GUID reference) for the policy term associated with the lifecycle event when term context is known.',
  lifecycle_event_type_code STRING NOT NULL COMMENT 'Business-facing code for the lifecycle event type.',
  lifecycle_event_status_code STRING COMMENT 'Current lifecycle status of the lifecycle event record.',
  prior_status_code STRING COMMENT 'Policy or term status before the lifecycle event when known.',
  resulting_status_code STRING COMMENT 'Policy or term status after the lifecycle event when known.',
  event_datetime TIMESTAMP NOT NULL COMMENT 'Datetime when the policy lifecycle event occurred.',
  initiated_by_party_uid STRING COMMENT 'Identifier (GUID reference) for the party that initiated the policy lifecycle event when known.',
  event_description STRING COMMENT 'Source-neutral business description of the policy lifecycle event when additional context is needed.',
  triggering_transaction_uid STRING COMMENT 'Optional reference to the transaction that produced this lifecycle event, when the event is the consequence of a processed transaction.',
  correction_indicator BOOLEAN NOT NULL COMMENT 'True when this row corrects a previously emitted row. False for original (uncorrected) rows.',
  corrects_policy_lifecycle_event_uid STRING COMMENT 'Reference to the prior row that this row corrects. Populated only when correction_indicator is true.'
)
USING DELTA
PARTITIONED BY (event_datetime)
COMMENT 'Canonical contract for meaningful lifecycle events in a Property and Casualty policy. Source: pc.policy-lifecycle-event v0.4.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);
