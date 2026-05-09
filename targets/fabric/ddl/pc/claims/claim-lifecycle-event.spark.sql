-- Spark SQL DDL for nebula_pc_silver.silver_claims.claim_lifecycle_event
-- Generated from targets/fabric/manifests/pc/claims/claim-lifecycle-event.fabric.yaml
-- Source: pc.claim-lifecycle-event v0.1.3 (references/odcs/pc/claims/claim-lifecycle-event.odcs.yaml)
-- Contract kind: event
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_claims.claim_lifecycle_event (
  claim_lifecycle_event_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical claim lifecycle event record across snapshots and source systems.',
  claim_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the claim associated with the event.',
  claim_feature_uid STRING COMMENT 'Identifier (GUID reference) for the claim feature associated with the event when feature context is known.',
  lifecycle_event_type_code STRING NOT NULL COMMENT 'Classification of the lifecycle event. References the LifecycleEventType codeset.',
  event_datetime TIMESTAMP NOT NULL COMMENT 'Datetime when the event occurred or was recognized.',
  effective_date DATE COMMENT 'Business-effective date for the event when it differs from the event datetime.',
  actor_party_uid STRING COMMENT 'Identifier (GUID reference) for the party that performed or owned the event when known.',
  reason_code STRING COMMENT 'Classification of the reason for the event when applicable.',
  event_narrative STRING COMMENT 'Source-neutral narrative describing the event when additional context is needed.',
  triggering_transaction_uid STRING COMMENT 'Optional reference to the transaction that produced this lifecycle event, when the event is the consequence of a processed transaction.',
  correction_indicator BOOLEAN NOT NULL COMMENT 'True when this row corrects a previously emitted row. False for original (uncorrected) rows.',
  corrects_claim_lifecycle_event_uid STRING COMMENT 'Reference to the prior row that this row corrects. Populated only when correction_indicator is true.'
)
USING DELTA
PARTITIONED BY (event_datetime)
COMMENT 'Canonical contract for lifecycle events in the Property and Casualty claim history. Source: pc.claim-lifecycle-event v0.1.3.'
TBLPROPERTIES (
  'delta.appendOnly' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);
