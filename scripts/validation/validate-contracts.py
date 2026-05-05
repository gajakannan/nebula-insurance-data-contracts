#!/usr/bin/env python3
"""Validate canonical ODCS contract files in this repository."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - depends on local environment
    yaml = None


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT_GLOB = "references/odcs/**/*.odcs.yaml"

REQUIRED_TOP_LEVEL = [
    "apiVersion",
    "kind",
    "id",
    "name",
    "version",
    "status",
    "description",
    "domain",
]
ALLOWED_STATUSES = {"draft", "proposed", "review", "approved", "deprecated", "retired"}
ALLOWED_SEVERITIES = {"info", "warning", "error"}
ALLOWED_SENSITIVITIES = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}
ALLOWED_REGULATORY_TAGS = {
    "PII",
    "PHI",
    "PCI",
    "SPI",
    "FINANCIAL",
    "JURISDICTION_RESTRICTED",
}
FIELD_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
CONTRACT_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9][a-z0-9-]*)+$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Append-only event/transaction contracts skip SCD2 and record_status_code per
# the temporal-modeling and event-and-transaction ADRs. They get correction
# fields instead.
EVENT_OR_TRANSACTION_SLUGS = {
    "policy-lifecycle-event",
    "policy-transaction",
    "submission-lifecycle-event",
    "claim-lifecycle-event",
    "financial-transaction",
    "claim-financial-transaction",
}
BANNED_CONTENT_PATTERNS = [
    (re.compile(r"https?://", re.IGNORECASE), "URLs must not appear in tracked contract files"),
    (re.compile(r"\bwww\.", re.IGNORECASE), "URLs must not appear in tracked contract files"),
    (re.compile(r"_private-research|_external-sources|_source-review|_scratch", re.IGNORECASE), "private research paths must not appear in contracts"),
    (re.compile(r"\braw\s+(schema|ddl|ontology)\b", re.IGNORECASE), "raw source artifact references are not allowed"),
    (re.compile(r"\bsource\s+review\b", re.IGNORECASE), "source review notes are not allowed"),
    (re.compile(r"\bontology\s+export\b", re.IGNORECASE), "raw ontology export references are not allowed"),
    (re.compile(r"\bvendor\s+schema\b", re.IGNORECASE), "vendor schema references are not allowed"),
    (re.compile(r"\bcopied\s+definition\b", re.IGNORECASE), "copied definition references are not allowed"),
]


class Finding:
    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"{self.path.relative_to(ROOT)}: {self.message}"


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def contract_files(paths: list[str]) -> list[Path]:
    if paths:
        candidates = [Path(path) for path in paths]
    else:
        candidates = list(ROOT.glob(DEFAULT_CONTRACT_GLOB))

    files: list[Path] = []
    for candidate in candidates:
        path = candidate if candidate.is_absolute() else ROOT / candidate
        if not path.exists():
            files.append(path)
            continue
        if path.is_dir():
            files.extend(path.glob("**/*.odcs.yaml"))
        else:
            files.append(path)

    return sorted({path.resolve() for path in files if "/references/odcs/templates/" not in path.resolve().as_posix()})


def expected_contract_id(path: Path) -> str | None:
    relative = path.relative_to(ROOT)
    parts = relative.parts
    if len(parts) < 4 or parts[0:3] != ("references", "odcs", "pc"):
        return None
    slug = path.name.removesuffix(".odcs.yaml")
    return f"pc.{slug}"


def expected_contract_name(path: Path) -> str | None:
    if expected_contract_id(path) is None:
        return None
    slug = path.name.removesuffix(".odcs.yaml")
    return "".join(part.capitalize() for part in slug.split("-"))


def validate_content_guardrails(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for pattern, message in BANNED_CONTENT_PATTERNS:
        if pattern.search(text):
            findings.append(Finding(path, message))
    return findings


def validate_top_level(path: Path, data: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(data, dict):
        return [Finding(path, "contract must be a YAML mapping, not an empty placeholder or scalar")]

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            findings.append(Finding(path, f"missing required top-level field `{key}`"))
        elif not is_non_empty_string(data[key]):
            findings.append(Finding(path, f"`{key}` must be a non-empty string"))

    if data.get("apiVersion") != "v3.0.2":
        findings.append(Finding(path, "`apiVersion` must be `v3.0.2`"))
    if data.get("kind") != "DataContract":
        findings.append(Finding(path, "`kind` must be `DataContract`"))
    if isinstance(data.get("id"), str) and not CONTRACT_ID_RE.match(data["id"]):
        findings.append(Finding(path, "`id` must use a dotted lowercase namespace, for example `pc.party`"))
    if isinstance(data.get("version"), str) and not VERSION_RE.match(data["version"]):
        findings.append(Finding(path, "`version` must use MAJOR.MINOR.PATCH format"))
    if isinstance(data.get("status"), str) and data["status"] not in ALLOWED_STATUSES:
        findings.append(Finding(path, f"`status` must be one of {sorted(ALLOWED_STATUSES)}"))

    expected_id = expected_contract_id(path)
    if expected_id and data.get("id") != expected_id:
        findings.append(Finding(path, f"`id` must align to path as `{expected_id}`"))

    expected_name = expected_contract_name(path)
    if expected_name and data.get("name") != expected_name:
        findings.append(Finding(path, f"`name` must align to filename as `{expected_name}`"))

    if path.relative_to(ROOT).parts[0:3] == ("references", "odcs", "pc") and data.get("domain") != "property-and-casualty":
        findings.append(Finding(path, "`domain` must be `property-and-casualty` for P&C contracts"))

    return findings


def validate_classifications(prop_location: str, prop: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    custom = prop.get("customProperties")
    if not isinstance(custom, dict):
        findings.append(Finding(Path(prop_location), f"{prop_location} missing `customProperties.classifications`"))
        return findings
    classifications = custom.get("classifications")
    if not isinstance(classifications, dict):
        findings.append(Finding(Path(prop_location), f"{prop_location}.customProperties.classifications must be a mapping (data-classification ADR)"))
        return findings
    sensitivity = classifications.get("sensitivity")
    if sensitivity not in ALLOWED_SENSITIVITIES:
        findings.append(Finding(Path(prop_location), f"{prop_location}.customProperties.classifications.sensitivity must be one of {sorted(ALLOWED_SENSITIVITIES)}"))
    tags = classifications.get("regulatoryTags")
    if tags is not None:
        if not isinstance(tags, list):
            findings.append(Finding(Path(prop_location), f"{prop_location}.customProperties.classifications.regulatoryTags must be a list when present"))
        else:
            for tag in tags:
                if tag not in ALLOWED_REGULATORY_TAGS:
                    findings.append(Finding(Path(prop_location), f"{prop_location}.customProperties.classifications.regulatoryTags contains unknown tag `{tag}`"))
    return findings


def validate_schema(path: Path, data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    schema = data.get("schema")
    if not isinstance(schema, list) or not schema:
        return [Finding(path, "`schema` must be a non-empty list")]

    slug = path.name.removesuffix(".odcs.yaml")
    is_event_or_txn = slug in EVENT_OR_TRANSACTION_SLUGS

    for index, entry in enumerate(schema):
        location = f"`schema[{index}]`"
        if not isinstance(entry, dict):
            findings.append(Finding(path, f"{location} must be a mapping"))
            continue

        for key in ("name", "physicalType", "description", "properties"):
            if key not in entry:
                findings.append(Finding(path, f"{location} missing `{key}`"))

        if not is_non_empty_string(entry.get("name")):
            findings.append(Finding(path, f"{location}.name must be a non-empty string"))
        elif not FIELD_NAME_RE.match(entry["name"]):
            findings.append(Finding(path, f"{location}.name must be lowercase snake_case"))

        if not is_non_empty_string(entry.get("description")):
            findings.append(Finding(path, f"{location}.description must be populated"))

        properties = entry.get("properties")
        if not isinstance(properties, list) or not properties:
            findings.append(Finding(path, f"{location}.properties must be a non-empty list"))
            continue

        primary_keys = []
        property_names: set[str] = set()
        for prop_index, prop in enumerate(properties):
            prop_location = f"{location}.properties[{prop_index}]"
            if not isinstance(prop, dict):
                findings.append(Finding(path, f"{prop_location} must be a mapping"))
                continue

            for key in ("name", "businessName", "logicalType", "required", "description"):
                if key not in prop:
                    findings.append(Finding(path, f"{prop_location} missing `{key}`"))

            name = prop.get("name")
            if not is_non_empty_string(name):
                findings.append(Finding(path, f"{prop_location}.name must be a non-empty string"))
            elif not FIELD_NAME_RE.match(name):
                findings.append(Finding(path, f"{prop_location}.name `{name}` must be lowercase snake_case"))
            else:
                property_names.add(name)
                if name.endswith("_id") and prop.get("primaryKey") is not True:
                    findings.append(Finding(path, f"{prop_location}.name `{name}` must use `_uid` suffix per identifier-strategy ADR"))

            for key in ("businessName", "logicalType", "description"):
                if not is_non_empty_string(prop.get(key)):
                    findings.append(Finding(path, f"{prop_location}.{key} must be populated"))

            if not isinstance(prop.get("required"), bool):
                findings.append(Finding(path, f"{prop_location}.required must be true or false"))

            if prop.get("primaryKey") is True:
                primary_keys.append(prop)
                if prop.get("required") is not True:
                    findings.append(Finding(path, f"{prop_location} primary key fields must be required"))
                if isinstance(name, str) and not name.endswith("_uid"):
                    findings.append(Finding(path, f"{prop_location} primary key `{name}` must use `_uid` suffix per identifier-strategy ADR"))

            for f in validate_classifications(prop_location, prop):
                findings.append(Finding(path, f.message))

        if not primary_keys:
            findings.append(Finding(path, f"{location} must define at least one primary key property"))

        # ADR enforcement: SCD2 + record_status on entity contracts;
        # correction fields on event/transaction contracts.
        if is_event_or_txn:
            if "correction_indicator" not in property_names:
                findings.append(Finding(path, f"{location} event/transaction contract must include `correction_indicator` per event-and-transaction ADR"))
            for forbidden in ("valid_from_datetime", "valid_to_datetime", "is_current_indicator", "record_status_code"):
                if forbidden in property_names:
                    findings.append(Finding(path, f"{location} event/transaction contract must not include `{forbidden}` (append-only per temporal-modeling ADR)"))
        else:
            for required_field in ("valid_from_datetime", "valid_to_datetime", "is_current_indicator", "record_status_code"):
                if required_field not in property_names:
                    findings.append(Finding(path, f"{location} entity contract must include `{required_field}` per temporal-modeling/record-state ADR"))

    return findings


def validate_relationships(path: Path, data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    relationships = data.get("relationships", [])
    if relationships in (None, []):
        return findings
    if not isinstance(relationships, list):
        return [Finding(path, "`relationships` must be a list when present")]

    for index, relationship in enumerate(relationships):
        location = f"`relationships[{index}]`"
        if not isinstance(relationship, dict):
            findings.append(Finding(path, f"{location} must be a mapping"))
            continue
        for key in ("name", "description", "relationshipType", "targetContractId", "sourceFields", "targetFields"):
            if key not in relationship:
                findings.append(Finding(path, f"{location} missing `{key}`"))
        for key in ("name", "description", "relationshipType", "targetContractId"):
            if key in relationship and not is_non_empty_string(relationship.get(key)):
                findings.append(Finding(path, f"{location}.{key} must be populated"))
        for key in ("sourceFields", "targetFields"):
            fields = relationship.get(key)
            if not isinstance(fields, list) or not fields:
                findings.append(Finding(path, f"{location}.{key} must be a non-empty list"))
            else:
                for field in fields:
                    if not isinstance(field, str) or not FIELD_NAME_RE.match(field):
                        findings.append(Finding(path, f"{location}.{key} values must be lowercase snake_case"))
    return findings


def validate_quality(path: Path, data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    quality = data.get("quality")
    if not isinstance(quality, list) or not quality:
        return [Finding(path, "`quality` must contain at least one data quality rule")]

    for index, rule in enumerate(quality):
        location = f"`quality[{index}]`"
        if not isinstance(rule, dict):
            findings.append(Finding(path, f"{location} must be a mapping"))
            continue
        for key in ("rule", "description", "dimension", "severity"):
            if key not in rule:
                findings.append(Finding(path, f"{location} missing `{key}`"))
            elif not is_non_empty_string(rule[key]):
                findings.append(Finding(path, f"{location}.{key} must be populated"))
        if isinstance(rule.get("rule"), str) and not FIELD_NAME_RE.match(rule["rule"]):
            findings.append(Finding(path, f"{location}.rule must be lowercase snake_case"))
        if isinstance(rule.get("severity"), str) and rule["severity"] not in ALLOWED_SEVERITIES:
            findings.append(Finding(path, f"{location}.severity must be one of {sorted(ALLOWED_SEVERITIES)}"))
    return findings


def validate_custom_properties(path: Path, data: dict[str, Any]) -> list[Finding]:
    custom = data.get("customProperties")
    if not isinstance(custom, dict):
        return [Finding(path, "`customProperties` must be a mapping")]

    findings: list[Finding] = []
    expected = {
        "canonicalLayer": "silver",
        "contractFamily": "property-and-casualty",
    }
    for key, expected_value in expected.items():
        if custom.get(key) != expected_value:
            findings.append(Finding(path, f"`customProperties.{key}` must be `{expected_value}`"))
    if not is_non_empty_string(custom.get("domainPackage")):
        findings.append(Finding(path, "`customProperties.domainPackage` must be populated"))

    profile = custom.get("classificationProfile")
    if profile is not None and profile not in ALLOWED_SENSITIVITIES:
        findings.append(Finding(path, f"`customProperties.classificationProfile` must be one of {sorted(ALLOWED_SENSITIVITIES)} when present"))

    changelog = custom.get("changelog")
    if changelog is not None and not isinstance(changelog, list):
        findings.append(Finding(path, "`customProperties.changelog` must be a list when present"))

    return findings


def validate_file(path: Path) -> list[Finding]:
    if not path.exists():
        return [Finding(path, "file does not exist")]

    text = path.read_text(encoding="utf-8")
    findings = validate_content_guardrails(path, text)

    if yaml is None:
        return findings + [Finding(path, "PyYAML is required to parse contract files")]

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return findings + [Finding(path, f"YAML parse error: {exc}")]

    top_level_findings = validate_top_level(path, data)
    findings.extend(top_level_findings)
    if not isinstance(data, dict):
        return findings

    findings.extend(validate_schema(path, data))
    findings.extend(validate_relationships(path, data))
    findings.extend(validate_quality(path, data))
    findings.extend(validate_custom_properties(path, data))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ODCS data contract YAML files.")
    parser.add_argument("paths", nargs="*", help="Optional files or directories to validate.")
    args = parser.parse_args()

    files = contract_files(args.paths)
    if not files:
        print("No contract files found.")
        return 1

    all_findings: list[Finding] = []
    for path in files:
        all_findings.extend(validate_file(path))

    if all_findings:
        print(f"Validated {len(files)} contract file(s): FAILED")
        for finding in all_findings:
            print(f"- {finding}")
        return 1

    print(f"Validated {len(files)} contract file(s): OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
