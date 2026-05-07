-- Spark SQL DDL for nebula_pc_silver.silver_claims.occurrence
-- Generated from targets/fabric/manifests/pc/claims/occurrence.fabric.yaml
-- Source: pc.occurrence v0.1.1 (references/odcs/pc/claims/occurrence.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_claims.occurrence (
  occurrence_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical occurrence record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  occurrence_number STRING COMMENT 'Business-facing number assigned to the occurrence, when the source system tracks one independently from claim numbers.',
  occurrence_type_code STRING NOT NULL COMMENT 'Classification of the occurrence (collision, fire, theft, weather, liability event, etc.). References the OccurrenceTypeCode codeset.',
  occurrence_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the occurrence record.',
  occurrence_date DATE NOT NULL COMMENT 'Date when the occurrence took place.',
  occurrence_datetime TIMESTAMP COMMENT 'Datetime when the occurrence took place when finer-grained timing is known.',
  catastrophe_uid STRING COMMENT 'Identifier (GUID reference) for the catastrophe associated with the occurrence when applicable.',
  location_uid STRING COMMENT 'Identifier (GUID reference) for the geographic location where the occurrence took place when known.',
  occurrence_description STRING COMMENT 'Source-neutral business description of the occurrence when additional context is needed.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for an insured occurrence — the underlying event that gives rise to one or more Property and Casualty claims. Source: pc.occurrence v0.1.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_claims.occurrence ZORDER BY (occurrence_uid);
