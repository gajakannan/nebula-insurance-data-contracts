-- Spark SQL DDL for nebula_pc_silver.silver_policy.policy_document
-- Generated from targets/fabric/manifests/pc/policy/policy-document.fabric.yaml
-- Source: pc.policy-document v0.4.2 (references/odcs/pc/policy/policy-document.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_policy.policy_document (
  policy_document_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical policy document record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  policy_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the policy associated with the document.',
  policy_term_uid STRING COMMENT 'Identifier (GUID reference) for the policy term associated with the document when term context is known.',
  policy_transaction_uid STRING COMMENT 'Identifier (GUID reference) for the policy transaction associated with the document when transaction context is known.',
  document_type_code STRING NOT NULL COMMENT 'Classification of the policy document type.',
  document_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the policy document.',
  document_title STRING COMMENT 'Business-facing title for the policy document.',
  external_storage_reference STRING COMMENT 'Source-neutral reference used to locate or reconcile the policy document in its system of record (storage URI, document-management identifier, etc.).',
  capture_datetime TIMESTAMP COMMENT 'Datetime when the canonical policy document record was captured into the warehouse. Distinct from issued / received which carry business semantics.',
  issued_datetime TIMESTAMP COMMENT 'Datetime when the policy document was issued or generated.',
  received_datetime TIMESTAMP COMMENT 'Datetime when the policy document was received when applicable.',
  contains_phi_indicator BOOLEAN COMMENT 'Indicates whether the document contains protected health information; informs downstream masking and access controls.',
  effective_date DATE COMMENT 'Date when the policy document becomes effective for business use.',
  expiration_date DATE COMMENT 'Date when the policy document stops being effective for business use.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for documents associated with a Property and Casualty policy. Source: pc.policy-document v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_policy.policy_document ZORDER BY (policy_document_uid);
