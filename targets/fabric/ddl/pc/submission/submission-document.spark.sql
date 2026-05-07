-- Spark SQL DDL for nebula_pc_silver.silver_submission.submission_document
-- Generated from targets/fabric/manifests/pc/submission/submission-document.fabric.yaml
-- Source: pc.submission-document v0.4.2 (references/odcs/pc/submission/submission-document.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_submission.submission_document (
  submission_document_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical submission document record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  submission_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the submission associated with the document.',
  document_type_code STRING NOT NULL COMMENT 'Classification of the document type.',
  document_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the submission document.',
  document_title STRING COMMENT 'Business-facing title for the submission document.',
  external_storage_reference STRING COMMENT 'Source-neutral reference used to locate or reconcile the submission document in its system of record (storage URI, document-management identifier, etc.).',
  required_indicator BOOLEAN COMMENT 'Indicates whether the document is required for the submission context.',
  capture_datetime TIMESTAMP COMMENT 'Datetime when the canonical submission document record was captured into the warehouse. Distinct from issued / received which carry business semantics.',
  received_datetime TIMESTAMP COMMENT 'Datetime when the document was received.',
  issued_datetime TIMESTAMP COMMENT 'Datetime when the document was issued or generated when applicable.',
  contains_phi_indicator BOOLEAN COMMENT 'Indicates whether the document contains protected health information; informs downstream masking and access controls.',
  source_created_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was created. Captured for late-arriving-data analysis; distinct from the SCD2 system-time start in valid_from_datetime.',
  source_updated_datetime TIMESTAMP COMMENT 'Source-system timestamp asserting when this record was last updated. Captured for late-arriving-data analysis; distinct from the SCD2 system-time markers valid_from_datetime / valid_to_datetime.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for documents associated with a Property and Casualty submission. Source: pc.submission-document v0.4.2.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_submission.submission_document ZORDER BY (submission_document_uid);
