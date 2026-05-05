#!/usr/bin/env python3
"""Generate missing codeset contracts referenced from entity contracts.

Each codeset follows the uniform shape defined in the codeset-strategy ADR:
`*_uid` GUID PK, `code_value`, `code_label`, `code_description`, optional
`external_standard_code`/`external_standard_name`, plus SCD2 system-time
fields and `record_status_code`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TARGET_DIR = ROOT / "references" / "odcs" / "pc" / "reference-data"

# (filename slug, contract name in CamelCase, subject area, description, suggested external standard)
CODESETS: list[tuple[str, str, str, str, str | None]] = [
    (
        "policy-status-code",
        "PolicyStatusCode",
        "policy",
        "Canonical codeset for policy lifecycle status values such as quoted, bound, issued, in-force, cancelled, lapsed, expired, and reinstated.",
        None,
    ),
    (
        "policy-type-code",
        "PolicyTypeCode",
        "policy",
        "Canonical codeset for policy classification values such as new business, renewal, rewrite, and replacement.",
        None,
    ),
    (
        "term-status-code",
        "TermStatusCode",
        "policy",
        "Canonical codeset for policy term lifecycle status values such as pending, active, cancelled, expired, and replaced.",
        None,
    ),
    (
        "coverage-basis-code",
        "CoverageBasisCode",
        "coverage",
        "Canonical codeset for coverage basis classifications used to apply a coverage within a policy context.",
        None,
    ),
    (
        "coverage-level-code",
        "CoverageLevelCode",
        "coverage",
        "Canonical codeset for the level at which a coverage applies, such as policy, term, location, item, exposure, or coverage part.",
        None,
    ),
    (
        "coverage-status-code",
        "CoverageStatusCode",
        "coverage",
        "Canonical codeset for the lifecycle status of a coverage within a policy context.",
        None,
    ),
    (
        "record-status-code",
        "RecordStatusCode",
        "reference-data",
        "Canonical codeset for warehouse-level record state. Allowed values include ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, and MERGED per the record-state ADR.",
        None,
    ),
    (
        "party-type-code",
        "PartyTypeCode",
        "core",
        "Canonical codeset for party classification values such as person, organization, household, and trust.",
        None,
    ),
    (
        "party-role-type-code",
        "PartyRoleTypeCode",
        "core",
        "Canonical codeset for party role types used across submission, policy, claim, coverage, and insurable-object role contracts. Examples include insured, producer, broker, agent, claimant, adjuster, loss-payee, service-provider, and underwriter.",
        None,
    ),
    (
        "claim-status-code",
        "ClaimStatusCode",
        "claims",
        "Canonical codeset for claim lifecycle status values such as open, closed, reopened, denied, and withdrawn.",
        None,
    ),
    (
        "cause-of-loss-code",
        "CauseOfLossCode",
        "claims",
        "Canonical codeset for the cause of loss classification associated with a claim or claim feature.",
        None,
    ),
    (
        "jurisdiction-code",
        "JurisdictionCode",
        "reference-data",
        "Canonical codeset for jurisdictions in which insurance contracts are issued, governed, or regulated.",
        "ISO 3166-2",
    ),
    (
        "currency-code",
        "CurrencyCode",
        "reference-data",
        "Canonical codeset for currencies used in monetary fields across the contract set.",
        "ISO 4217",
    ),
]


def build_contract(slug: str, name: str, subject_area: str, description: str, external_standard: str | None) -> dict:
    snake = slug.replace("-", "_")
    contract = {
        "apiVersion": "v3.0.2",
        "kind": "DataContract",
        "id": f"pc.{slug}",
        "name": name,
        "version": "0.1.0",
        "status": "draft",
        "description": description,
        "domain": "property-and-casualty",
        "schema": [
            {
                "name": snake,
                "physicalType": "table",
                "description": f"Canonical {name} reference record. One row per allowed code value, versioned through SCD2 system time.",
                "properties": [
                    {
                        "name": f"{snake}_uid",
                        "businessName": f"{name} Identifier",
                        "logicalType": "string",
                        "required": True,
                        "primaryKey": True,
                        "description": f"Immutable system-generated GUID that uniquely identifies the canonical {name} record across snapshots.",
                        "customProperties": {"classifications": {"sensitivity": "PUBLIC"}},
                    },
                    {
                        "name": "code_value",
                        "businessName": "Code Value",
                        "logicalType": "string",
                        "required": True,
                        "description": "Business-friendly code value referenced by entity contracts.",
                        "customProperties": {"classifications": {"sensitivity": "PUBLIC"}},
                    },
                    {
                        "name": "code_label",
                        "businessName": "Code Label",
                        "logicalType": "string",
                        "required": True,
                        "description": "Human-readable label for the code value.",
                        "customProperties": {"classifications": {"sensitivity": "PUBLIC"}},
                    },
                    {
                        "name": "code_description",
                        "businessName": "Code Description",
                        "logicalType": "string",
                        "required": False,
                        "description": "Extended description of the code value.",
                        "customProperties": {"classifications": {"sensitivity": "PUBLIC"}},
                    },
                    {
                        "name": "external_standard_code",
                        "businessName": "External Standard Code",
                        "logicalType": "string",
                        "required": False,
                        "description": (
                            f"Code value as defined by {external_standard} when a mapping is recorded."
                            if external_standard
                            else "Code value as defined by an external standard (ACORD, NAIC, ISO, etc.) when a mapping is recorded."
                        ),
                        "customProperties": {"classifications": {"sensitivity": "PUBLIC"}},
                    },
                    {
                        "name": "external_standard_name",
                        "businessName": "External Standard Name",
                        "logicalType": "string",
                        "required": False,
                        "description": "Name of the external standard whose code is captured in external_standard_code.",
                        "customProperties": {"classifications": {"sensitivity": "PUBLIC"}},
                    },
                    {
                        "name": "record_status_code",
                        "businessName": "Record Status Code",
                        "logicalType": "string",
                        "required": True,
                        "description": "Warehouse-level state of the record. References the RecordStatusCode codeset.",
                        "customProperties": {"classifications": {"sensitivity": "INTERNAL"}},
                    },
                    {
                        "name": "valid_from_datetime",
                        "businessName": "Valid From Datetime",
                        "logicalType": "datetime",
                        "required": True,
                        "description": "System-time start of the SCD2 window for this record version.",
                        "customProperties": {"classifications": {"sensitivity": "INTERNAL"}},
                    },
                    {
                        "name": "valid_to_datetime",
                        "businessName": "Valid To Datetime",
                        "logicalType": "datetime",
                        "required": False,
                        "description": "System-time end of the SCD2 window for this record version. Null indicates the current row.",
                        "customProperties": {"classifications": {"sensitivity": "INTERNAL"}},
                    },
                    {
                        "name": "is_current_indicator",
                        "businessName": "Is Current Indicator",
                        "logicalType": "boolean",
                        "required": True,
                        "description": "True for exactly one row per logical key, indicating the current record version.",
                        "customProperties": {"classifications": {"sensitivity": "INTERNAL"}},
                    },
                ],
            }
        ],
        "quality": [
            {
                "rule": f"{snake}_uid_required",
                "description": f"{snake}_uid must be populated for every record.",
                "dimension": "completeness",
                "severity": "error",
            },
            {
                "rule": "code_value_required",
                "description": "code_value must be populated and unique among current rows.",
                "dimension": "completeness",
                "severity": "error",
            },
            {
                "rule": "code_label_required",
                "description": "code_label must be populated for every code value.",
                "dimension": "completeness",
                "severity": "error",
            },
            {
                "rule": "valid_from_datetime_required",
                "description": "valid_from_datetime must be populated for every record version.",
                "dimension": "completeness",
                "severity": "error",
            },
            {
                "rule": "valid_window_consistent",
                "description": "valid_to_datetime must be greater than valid_from_datetime when populated.",
                "dimension": "consistency",
                "severity": "error",
            },
            {
                "rule": "single_current_row_per_key",
                "description": "Exactly one row per logical key has is_current_indicator equal to true.",
                "dimension": "uniqueness",
                "severity": "error",
            },
            {
                "rule": "record_status_code_required",
                "description": "record_status_code must be populated for every record.",
                "dimension": "completeness",
                "severity": "error",
            },
        ],
        "customProperties": {
            "canonicalLayer": "silver",
            "contractFamily": "property-and-casualty",
            "domainPackage": "pc",
            "subjectArea": subject_area,
            "codesetContract": True,
            "classificationProfile": "INTERNAL",
            "changelog": [
                "0.1.0: Initial codeset contract generated per codeset-strategy ADR.",
            ],
        },
    }
    return contract


def represent_str(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def represent_dict(dumper: yaml.SafeDumper, data: dict) -> yaml.MappingNode:
    return dumper.represent_dict(data.items())


def dump_yaml(data: dict) -> str:
    yaml.SafeDumper.add_representer(str, represent_str)
    yaml.SafeDumper.add_representer(dict, represent_dict)
    return yaml.safe_dump(
        data, sort_keys=False, default_flow_style=False, indent=2, width=200, allow_unicode=True
    )


def main() -> int:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    created = 0
    for slug, name, subject, description, external_standard in CODESETS:
        path = TARGET_DIR / f"{slug}.odcs.yaml"
        if path.exists():
            print(f"exists:  {path.relative_to(ROOT)} (skipping)")
            continue
        contract = build_contract(slug, name, subject, description, external_standard)
        path.write_text(dump_yaml(contract), encoding="utf-8")
        print(f"created: {path.relative_to(ROOT)}")
        created += 1
    print(f"\n{created} codeset contract(s) created.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
