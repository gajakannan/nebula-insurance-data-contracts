-- Spark SQL DDL for nebula_pc_silver.silver_claims.claim_document
-- Generated from targets/fabric/manifests/pc/claims/claim-document.fabric.yaml
-- Source: pc.claim-document v0.3.1 (references/odcs/pc/claims/claim-document.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_claims.claim_document (
  claim_document_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical claim document record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  claim_uid STRING NOT NULL COMMENT 'Identifier (GUID reference) for the claim associated with the document.',
  claim_feature_uid STRING COMMENT 'Identifier (GUID reference) for the claim feature associated with the document when feature context is known.',
  document_type_code STRING NOT NULL COMMENT 'Classification of the document such as FNOL form, police report, medical record, photograph, repair estimate, demand letter, settlement agreement, or correspondence.',
  document_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the document such as received, indexed, reviewed, redacted, or archived.',
  document_title STRING COMMENT 'Title or short label assigned to the document when known.',
  external_storage_reference STRING COMMENT 'Opaque reference to the document content held in an external storage system. Treated as a pointer; the document body is not stored in this contract.',
  capture_datetime TIMESTAMP COMMENT 'Datetime when the document was captured, received, or registered.',
  capture_party_uid STRING COMMENT 'Identifier (GUID reference) for the party that captured or registered the document when known.',
  contains_phi_indicator BOOLEAN COMMENT 'Indicates whether the document is known to contain Protected Health Information. Used by downstream targets to apply HIPAA-compliant handling.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset.',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for documents associated with a Property and Casualty claim. Stores document metadata only; document content is held in an external store. Source: pc.claim-document v0.3.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_claims.claim_document ZORDER BY (claim_document_uid);
