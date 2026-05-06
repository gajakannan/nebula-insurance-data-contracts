#!/usr/bin/env python3
"""Validate canonical ODCS contract files in this repository."""

from __future__ import annotations

import argparse
import re
import subprocess
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
PROMOTED_STATUSES = {"approved", "deprecated", "retired"}
ALLOWED_SEVERITIES = {"info", "warning", "error"}
ALLOWED_SENSITIVITIES = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}
SENSITIVITY_RANK = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}
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
NARRATIVE_SUFFIXES = ("_description", "_notes", "_narrative", "_text", "_summary")
OVER_CLASSIFICATION_SUFFIXES = (
    "_status_code",
    "_result_code",
    "_period_code",
    "_territory_code",
    "_region_code",
)
OVER_CLASSIFICATION_PREFIXES = ("accounting_",)
ADR_DIR = ROOT / "references" / "design-decisions" / "pc"
REFERENCE_DATA_PREFIX = ("references", "odcs", "pc", "reference-data")
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
    def __init__(self, path: Path, message: str, severity: str = "error") -> None:
        self.path = path
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        prefix = f"[{self.severity}] " if self.severity != "error" else ""
        return f"{prefix}{self.path.relative_to(ROOT)}: {self.message}"


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


class ContractIndex:
    """Repository-wide facts that cross-cut per-file validation."""

    def __init__(self, files: list[Path]) -> None:
        self.contract_ids: set[str] = set()
        self.reference_data_ids: set[str] = set()
        # Map prefix (filename slug with hyphens replaced by underscores) -> contract id.
        self.codeset_prefix_to_id: dict[str, str] = {}
        self.adr_ids: set[str] = self._load_adr_ids()
        self._build(files)

    @staticmethod
    def _load_adr_ids() -> set[str]:
        if not ADR_DIR.is_dir():
            return set()
        return {p.stem for p in ADR_DIR.glob("*.md")}

    def _build(self, files: list[Path]) -> None:
        for path in files:
            relative = path.relative_to(ROOT)
            slug = path.name.removesuffix(".odcs.yaml")
            cid = expected_contract_id(path)
            if cid:
                self.contract_ids.add(cid)
            if relative.parts[0:4] == REFERENCE_DATA_PREFIX:
                if cid:
                    self.reference_data_ids.add(cid)
                prefix = slug.replace("-", "_")
                if prefix.endswith("_code"):
                    prefix = prefix.removesuffix("_code")
                self.codeset_prefix_to_id[prefix] = cid or ""


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


# ---------------------------------------------------------------------------
# Canonical-hardening rules (C1.1–C1.12). Per CANONICAL_HARDENING_PLAN.md §4
# phase C1, these add validator coverage for cross-cutting ADR conventions
# without editing any contract.
# ---------------------------------------------------------------------------


def _iter_properties(data: dict[str, Any]):
    """Yield (entry_index, prop_index, entry, prop) for every schema property."""
    schema = data.get("schema")
    if not isinstance(schema, list):
        return
    for entry_index, entry in enumerate(schema):
        if not isinstance(entry, dict):
            continue
        properties = entry.get("properties")
        if not isinstance(properties, list):
            continue
        for prop_index, prop in enumerate(properties):
            if isinstance(prop, dict):
                yield entry_index, prop_index, entry, prop


def _prop_name(prop: dict[str, Any]) -> str:
    name = prop.get("name")
    return name if isinstance(name, str) else ""


def _prop_classifications(prop: dict[str, Any]) -> dict[str, Any]:
    custom = prop.get("customProperties")
    if not isinstance(custom, dict):
        return {}
    cls = custom.get("classifications")
    return cls if isinstance(cls, dict) else {}


def _prop_custom(prop: dict[str, Any]) -> dict[str, Any]:
    custom = prop.get("customProperties")
    return custom if isinstance(custom, dict) else {}


def _has_exemption(prop: dict[str, Any], flag: str) -> bool:
    """True when prop carries `customProperties.<flag>: true` plus a `<flag>Reason` non-empty string."""
    custom = _prop_custom(prop)
    if custom.get(flag) is not True:
        return False
    reason_key = f"{flag}Reason"
    return is_non_empty_string(custom.get(reason_key))


def _has_classification_exemption(prop: dict[str, Any], flag: str) -> bool:
    """True when prop's classifications carries `<flag>: true` plus `<flag>Reason` non-empty string."""
    cls = _prop_classifications(prop)
    if cls.get(flag) is not True:
        return False
    reason_key = f"{flag}Reason"
    return is_non_empty_string(cls.get(reason_key))


def _is_codeset_or_reference_data(path: Path, data: dict[str, Any]) -> bool:
    relative = path.relative_to(ROOT)
    if relative.parts[0:4] == REFERENCE_DATA_PREFIX:
        return True
    custom = data.get("customProperties")
    if isinstance(custom, dict) and custom.get("codesetContract") is True:
        return True
    return False


def validate_amount_currency_pairing(path: Path, data: dict[str, Any]) -> list[Finding]:
    """C1.1 — every `*_amount` field must have a same-prefix `*_currency_code` sibling."""
    findings: list[Finding] = []
    for entry_index, prop_index, entry, prop in _iter_properties(data):
        name = _prop_name(prop)
        if not name.endswith("_amount"):
            continue
        sibling_names = {
            _prop_name(p) for p in (entry.get("properties") or []) if isinstance(p, dict)
        }
        prefix = name.removesuffix("_amount")
        expected_sibling = f"{prefix}_currency_code"
        if expected_sibling in sibling_names:
            continue
        if _has_exemption(prop, "amountCurrencyExempt"):
            continue
        findings.append(
            Finding(
                path,
                f"`schema[{entry_index}].properties[{prop_index}]` `{name}` is missing sibling `{expected_sibling}` (currency-convention ADR / C1.1). "
                f"Set `customProperties.amountCurrencyExempt: true` plus `amountCurrencyExemptReason: ...` to opt out.",
            )
        )
    return findings


def validate_code_codeset_resolution(path: Path, data: dict[str, Any], index: ContractIndex) -> list[Finding]:
    """C1.2 — every `*_code` field on non-reference-data contracts must resolve to a codeset via relationships."""
    findings: list[Finding] = []
    if _is_codeset_or_reference_data(path, data):
        return findings
    relationships = data.get("relationships") or []
    if not isinstance(relationships, list):
        relationships = []
    code_field_to_targets: dict[str, set[str]] = {}
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        target = rel.get("targetContractId")
        sources = rel.get("sourceFields")
        if not isinstance(target, str) or not isinstance(sources, list):
            continue
        for src in sources:
            if isinstance(src, str):
                code_field_to_targets.setdefault(src, set()).add(target)

    for entry_index, prop_index, _entry, prop in _iter_properties(data):
        name = _prop_name(prop)
        if not name.endswith("_code"):
            continue
        if _has_exemption(prop, "codesetExempt"):
            continue
        targets = code_field_to_targets.get(name, set())
        resolved = any(t in index.reference_data_ids for t in targets)
        if not resolved:
            findings.append(
                Finding(
                    path,
                    f"`schema[{entry_index}].properties[{prop_index}]` `{name}` is not bound to a reference-data codeset via `relationships` (codeset-strategy ADR / C1.2). "
                    f"Add a relationship targeting a contract under `references/odcs/pc/reference-data/`, or set `customProperties.codesetExempt: true` plus `codesetExemptReason: ...`.",
                )
            )
    return findings


def validate_target_contract_resolution(path: Path, data: dict[str, Any], index: ContractIndex) -> list[Finding]:
    """C1.3 — every relationship `targetContractId` must resolve to a known contract."""
    findings: list[Finding] = []
    relationships = data.get("relationships") or []
    if not isinstance(relationships, list):
        return findings
    for rel_index, rel in enumerate(relationships):
        if not isinstance(rel, dict):
            continue
        target = rel.get("targetContractId")
        if not isinstance(target, str) or not target:
            continue
        if target not in index.contract_ids:
            findings.append(
                Finding(
                    path,
                    f"`relationships[{rel_index}].targetContractId` `{target}` does not resolve to a known contract (C1.3).",
                )
            )
    return findings


def validate_correction_companion(path: Path, data: dict[str, Any]) -> list[Finding]:
    """C1.4 — when `correction_indicator` is present, a `corrects_*_uid` field must also be present."""
    findings: list[Finding] = []
    schema = data.get("schema")
    if not isinstance(schema, list):
        return findings
    for entry_index, entry in enumerate(schema):
        if not isinstance(entry, dict):
            continue
        properties = entry.get("properties") or []
        if not isinstance(properties, list):
            continue
        names = {_prop_name(p) for p in properties if isinstance(p, dict)}
        if "correction_indicator" not in names:
            continue
        if not any(n.startswith("corrects_") and n.endswith("_uid") for n in names):
            findings.append(
                Finding(
                    path,
                    f"`schema[{entry_index}]` declares `correction_indicator` but lacks a `corrects_*_uid` companion (event-and-transaction ADR / C1.4).",
                )
            )
    return findings


def validate_append_only_datetime_ban(path: Path, data: dict[str, Any]) -> list[Finding]:
    """C1.5 — append-only contracts must not carry `created_datetime` or `updated_datetime`."""
    findings: list[Finding] = []
    schema = data.get("schema")
    if not isinstance(schema, list):
        return findings
    for entry_index, entry in enumerate(schema):
        if not isinstance(entry, dict):
            continue
        properties = entry.get("properties") or []
        if not isinstance(properties, list):
            continue
        names = {_prop_name(p) for p in properties if isinstance(p, dict)}
        if "correction_indicator" not in names:
            continue
        for forbidden in ("created_datetime", "updated_datetime"):
            if forbidden in names:
                findings.append(
                    Finding(
                        path,
                        f"`schema[{entry_index}]` is append-only (declares `correction_indicator`) and must not include `{forbidden}` (temporal-modeling ADR / C1.5).",
                    )
                )
    return findings


def validate_uid_code_redundancy(path: Path, data: dict[str, Any], index: ContractIndex) -> list[Finding]:
    """C1.6 — flag co-occurring `<prefix>_uid` and `<prefix>_code` pairs where `<prefix>` matches a known codeset."""
    findings: list[Finding] = []
    schema = data.get("schema")
    if not isinstance(schema, list):
        return findings
    for entry_index, entry in enumerate(schema):
        if not isinstance(entry, dict):
            continue
        properties = entry.get("properties") or []
        if not isinstance(properties, list):
            continue
        names = {_prop_name(p) for p in properties if isinstance(p, dict)}
        for name in sorted(names):
            if not name.endswith("_uid"):
                continue
            prefix = name.removesuffix("_uid")
            paired_code = f"{prefix}_code"
            if paired_code not in names:
                continue
            if prefix not in index.codeset_prefix_to_id:
                continue
            findings.append(
                Finding(
                    path,
                    f"`schema[{entry_index}]` declares both `{name}` and `{paired_code}` for the same codeset; keep only the `_code` form per identifier-strategy ADR (C1.6).",
                    severity="warning",
                )
            )
    return findings


def validate_narrative_classification(path: Path, data: dict[str, Any]) -> list[Finding]:
    """C1.7 — narrative free-text fields must be CONFIDENTIAL+ with a regulatory tag (or carry a written exception)."""
    findings: list[Finding] = []
    if _is_codeset_or_reference_data(path, data):
        return findings
    for entry_index, prop_index, _entry, prop in _iter_properties(data):
        name = _prop_name(prop)
        if not any(name.endswith(suffix) for suffix in NARRATIVE_SUFFIXES):
            continue
        if _has_classification_exemption(prop, "narrativeException"):
            continue
        cls = _prop_classifications(prop)
        sensitivity = cls.get("sensitivity")
        rank = SENSITIVITY_RANK.get(sensitivity if isinstance(sensitivity, str) else "", -1)
        tags = cls.get("regulatoryTags") or []
        if rank < SENSITIVITY_RANK["CONFIDENTIAL"] or not (isinstance(tags, list) and tags):
            findings.append(
                Finding(
                    path,
                    f"`schema[{entry_index}].properties[{prop_index}]` narrative field `{name}` must be `CONFIDENTIAL` or higher with at least one regulatory tag "
                    f"(data-classification ADR / C1.7). Currently sensitivity=`{sensitivity}`, regulatoryTags=`{list(tags) if isinstance(tags, list) else tags}`. "
                    f"Set `customProperties.classifications.narrativeException: true` plus `narrativeExceptionReason: ...` to opt out.",
                )
            )
    return findings


def validate_over_classification_heuristic(path: Path, data: dict[str, Any]) -> list[Finding]:
    """C1.8 — flag status / period / territory / accounting fields tagged RESTRICTED+PII (warning)."""
    findings: list[Finding] = []
    for entry_index, prop_index, _entry, prop in _iter_properties(data):
        name = _prop_name(prop)
        suffix_match = any(name.endswith(suffix) for suffix in OVER_CLASSIFICATION_SUFFIXES)
        prefix_match = any(name.startswith(prefix) for prefix in OVER_CLASSIFICATION_PREFIXES)
        if not (suffix_match or prefix_match):
            continue
        cls = _prop_classifications(prop)
        sensitivity = cls.get("sensitivity")
        tags = cls.get("regulatoryTags") or []
        if sensitivity == "RESTRICTED" and isinstance(tags, list) and "PII" in tags:
            findings.append(
                Finding(
                    path,
                    f"`schema[{entry_index}].properties[{prop_index}]` `{name}` is tagged `RESTRICTED + PII` but matches a status/period/territory/accounting pattern; "
                    f"verify against data-classification ADR (C1.8).",
                    severity="warning",
                )
            )
    return findings


def validate_classification_profile(path: Path, data: dict[str, Any]) -> list[Finding]:
    """C1.9 — top-level `classificationProfile` must be at least the maximum field-level sensitivity."""
    custom = data.get("customProperties")
    if not isinstance(custom, dict):
        return []
    profile = custom.get("classificationProfile")
    if profile not in ALLOWED_SENSITIVITIES:
        return []
    profile_rank = SENSITIVITY_RANK[profile]
    max_rank = -1
    max_name = ""
    max_sensitivity = ""
    for _entry_index, _prop_index, _entry, prop in _iter_properties(data):
        cls = _prop_classifications(prop)
        sensitivity = cls.get("sensitivity")
        if not isinstance(sensitivity, str):
            continue
        rank = SENSITIVITY_RANK.get(sensitivity, -1)
        if rank > max_rank:
            max_rank = rank
            max_name = _prop_name(prop)
            max_sensitivity = sensitivity
    if max_rank > profile_rank:
        return [
            Finding(
                path,
                f"`customProperties.classificationProfile` `{profile}` is below field `{max_name}` sensitivity `{max_sensitivity}` (data-classification ADR / C1.9).",
            )
        ]
    return []


def validate_status_promotion_gates(path: Path, data: dict[str, Any], index: ContractIndex) -> list[Finding]:
    """C1.10 — promoted contracts (status approved/deprecated/retired) must have a non-empty changelog
    and zero unresolved targetContractId references. Other status-promotion gates documented in
    `status-promotion.md` (steward approval, known consumers) are not checkable from YAML alone and
    are out of scope for the validator per the C2 ADR-reconciliation phase."""
    status = data.get("status")
    if status not in PROMOTED_STATUSES:
        return []
    findings: list[Finding] = []
    custom = data.get("customProperties")
    changelog = custom.get("changelog") if isinstance(custom, dict) else None
    if not isinstance(changelog, list) or not changelog:
        findings.append(
            Finding(
                path,
                f"contract status `{status}` requires a non-empty `customProperties.changelog` (status-promotion ADR / C1.10).",
            )
        )
    relationships = data.get("relationships") or []
    if isinstance(relationships, list):
        for rel_index, rel in enumerate(relationships):
            if not isinstance(rel, dict):
                continue
            target = rel.get("targetContractId")
            if isinstance(target, str) and target and target not in index.contract_ids:
                findings.append(
                    Finding(
                        path,
                        f"contract status `{status}` requires every `relationships[{rel_index}].targetContractId` to resolve; `{target}` does not (C1.10).",
                    )
                )
    return findings


def validate_changelog_on_version_bump(path: Path, data: dict[str, Any]) -> list[Finding]:
    """C1.11 — when version differs from prior git revision, require a matching `changelog` entry."""
    current_version = data.get("version")
    if not isinstance(current_version, str) or not VERSION_RE.match(current_version):
        return []
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError:
        return []
    try:
        completed = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return []
    if completed.returncode != 0:
        return []  # File new at HEAD or git unavailable; nothing to compare.
    try:
        prior = yaml.safe_load(completed.stdout) if yaml else None
    except yaml.YAMLError:
        return []
    if not isinstance(prior, dict):
        return []
    prior_version = prior.get("version")
    if prior_version == current_version:
        return []
    custom = data.get("customProperties")
    changelog = custom.get("changelog") if isinstance(custom, dict) else None
    if not isinstance(changelog, list):
        return [
            Finding(
                path,
                f"version bumped from `{prior_version}` to `{current_version}` but `customProperties.changelog` is missing or not a list (C1.11).",
            )
        ]
    for entry in changelog:
        if isinstance(entry, str) and entry.lstrip().startswith(f"{current_version}:"):
            return []
    return [
        Finding(
            path,
            f"version bumped from `{prior_version}` to `{current_version}` but no changelog entry begins with `{current_version}:` (C1.11).",
        )
    ]


def validate_adr_id_resolution(path: Path, data: dict[str, Any], index: ContractIndex) -> list[Finding]:
    """C1.12 — when `customProperties.adrs` is present, every id must resolve to a file under
    references/design-decisions/pc/."""
    custom = data.get("customProperties")
    if not isinstance(custom, dict):
        return []
    adrs = custom.get("adrs")
    if adrs is None:
        return []
    if not isinstance(adrs, list):
        return [Finding(path, "`customProperties.adrs` must be a list when present (C1.12).")]
    findings: list[Finding] = []
    for adr in adrs:
        if not isinstance(adr, str) or not adr.strip():
            findings.append(Finding(path, "`customProperties.adrs` entries must be non-empty strings (C1.12)."))
            continue
        if adr not in index.adr_ids:
            findings.append(
                Finding(
                    path,
                    f"`customProperties.adrs` entry `{adr}` does not resolve to a file under `references/design-decisions/pc/` (C1.12).",
                )
            )
    return findings


def validate_hardening_rules(path: Path, data: dict[str, Any], index: ContractIndex) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(validate_amount_currency_pairing(path, data))
    findings.extend(validate_code_codeset_resolution(path, data, index))
    findings.extend(validate_target_contract_resolution(path, data, index))
    findings.extend(validate_correction_companion(path, data))
    findings.extend(validate_append_only_datetime_ban(path, data))
    findings.extend(validate_uid_code_redundancy(path, data, index))
    findings.extend(validate_narrative_classification(path, data))
    findings.extend(validate_over_classification_heuristic(path, data))
    findings.extend(validate_classification_profile(path, data))
    findings.extend(validate_status_promotion_gates(path, data, index))
    findings.extend(validate_changelog_on_version_bump(path, data))
    findings.extend(validate_adr_id_resolution(path, data, index))
    return findings


def validate_file(path: Path, index: ContractIndex | None = None) -> list[Finding]:
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
    if index is not None:
        findings.extend(validate_hardening_rules(path, data, index))
    return findings


_RULE_ID_RE = re.compile(r"\bC1\.\d+\b")


def render_punch_list(findings: list[Finding]) -> str:
    lines = [
        "# Canonical Hardening Punch List",
        "",
        "Auto-generated by `scripts/validation/validate-contracts.py --punch-list`. Transient artifact;",
        "deleted at the end of phase C3 once findings are resolved by the bulk refactor.",
        "",
        f"Total findings: {len(findings)}",
        "",
    ]
    if not findings:
        lines.append("_No findings._")
        return "\n".join(lines) + "\n"

    by_rule: dict[str, int] = {}
    for finding in findings:
        match = _RULE_ID_RE.search(finding.message)
        rule = match.group(0) if match else "other"
        by_rule[rule] = by_rule.get(rule, 0) + 1
    lines.append("## By rule")
    lines.append("")
    lines.append("| Rule | Count |")
    lines.append("| --- | --- |")
    for rule in sorted(by_rule):
        lines.append(f"| {rule} | {by_rule[rule]} |")
    lines.append("")

    by_path: dict[str, list[Finding]] = {}
    for finding in findings:
        rel = finding.path.relative_to(ROOT).as_posix()
        by_path.setdefault(rel, []).append(finding)
    for rel in sorted(by_path):
        lines.append(f"## {rel}")
        lines.append("")
        for finding in sorted(by_path[rel], key=lambda f: (f.severity, f.message)):
            lines.append(f"- [{finding.severity}] {finding.message}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ODCS data contract YAML files.")
    parser.add_argument("paths", nargs="*", help="Optional files or directories to validate.")
    parser.add_argument(
        "--punch-list",
        metavar="PATH",
        help="Write a deterministic markdown punch list of findings to PATH (still exits non-zero on findings).",
    )
    args = parser.parse_args()

    files = contract_files(args.paths)
    if not files:
        print("No contract files found.")
        return 1

    index = ContractIndex(files)

    all_findings: list[Finding] = []
    for path in files:
        all_findings.extend(validate_file(path, index))

    if args.punch_list:
        out_path = Path(args.punch_list)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render_punch_list(all_findings), encoding="utf-8")
        print(f"Punch list written to {out_path.relative_to(ROOT)}")

    error_findings = [f for f in all_findings if f.severity == "error"]
    warning_findings = [f for f in all_findings if f.severity == "warning"]

    if all_findings:
        status = "FAILED" if error_findings else "PASSED with warnings"
        print(f"Validated {len(files)} contract file(s): {status} ({len(error_findings)} errors, {len(warning_findings)} warnings)")
        for finding in all_findings:
            print(f"- {finding}")
        return 1 if error_findings else 0

    print(f"Validated {len(files)} contract file(s): OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
