-- Spark SQL DDL for nebula_pc_silver.silver_claims.catastrophe
-- Generated from targets/fabric/manifests/pc/claims/catastrophe.fabric.yaml
-- Source: pc.catastrophe v0.1.1 (references/odcs/pc/claims/catastrophe.odcs.yaml)
-- Contract kind: entity
-- Do not edit by hand. Regenerate via scripts/generation/generate-fabric-ddl.py.

CREATE TABLE IF NOT EXISTS nebula_pc_silver.silver_claims.catastrophe (
  catastrophe_uid STRING NOT NULL COMMENT 'Immutable system-generated GUID that uniquely identifies the canonical catastrophe record across snapshots and source systems.',
  source_system_code STRING COMMENT 'Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.',
  source_natural_key STRING COMMENT 'Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.',
  industry_catastrophe_code STRING COMMENT 'Industry-standard catastrophe identifier (e.g. PCS catastrophe number) used for cross-carrier and reinsurance aggregation when one is assigned.',
  company_catastrophe_code STRING COMMENT 'Company-internal catastrophe identifier used for accumulation and reporting when distinct from the industry code.',
  catastrophe_name STRING NOT NULL COMMENT 'Human-readable name of the catastrophe (e.g. named storm, fire complex name, civil event designation).',
  catastrophe_type_code STRING NOT NULL COMMENT 'Classification of the catastrophe (HURRICANE, WILDFIRE, EARTHQUAKE, FLOOD, CIVIL_EVENT, etc.). References the CatastropheTypeCode codeset.',
  catastrophe_status_code STRING NOT NULL COMMENT 'Current lifecycle status of the catastrophe record (e.g. OPEN, CLOSED, REOPENED).',
  effective_datetime TIMESTAMP NOT NULL COMMENT 'Datetime when the catastrophe is deemed to begin for accumulation purposes.',
  expiration_datetime TIMESTAMP COMMENT 'Datetime when the catastrophe is deemed to end for accumulation purposes. Null while the event is ongoing.',
  catastrophe_description STRING COMMENT 'Source-neutral business description of the catastrophe when additional context is needed.',
  record_status_code STRING NOT NULL COMMENT 'Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).',
  valid_from_datetime TIMESTAMP NOT NULL COMMENT 'System-time start of the SCD2 window for this record version.',
  valid_to_datetime TIMESTAMP COMMENT 'System-time end of the SCD2 window for this record version. Null indicates the current row.',
  is_current_indicator BOOLEAN NOT NULL COMMENT 'True for exactly one row per logical key, indicating the current record version.'
)
USING DELTA
PARTITIONED BY (is_current_indicator)
COMMENT 'Canonical contract for a catastrophe — a named industry or company event (named storm, wildfire, earthquake, civil event) used to aggregate exposures, occurrences, and claims for reinsurance recovery, regulatory reporting, and industry benchmarking. Source: pc.catastrophe v0.1.1.'
TBLPROPERTIES (
  'delta.appendOnly' = 'false',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.enableChangeDataFeed' = 'true'
);

-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):
--   OPTIMIZE nebula_pc_silver.silver_claims.catastrophe ZORDER BY (catastrophe_uid);
