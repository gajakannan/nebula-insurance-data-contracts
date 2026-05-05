#!/usr/bin/env python3
"""One-time refactor: bring all P&C ODCS contracts in line with the ADRs.

Applies, per contract category:

- Entity contracts: rename `*_id` PK to `*_uid`, add SCD2 fields, add
  `record_status_code`, add `source_system_code` and `source_natural_key`,
  add `customProperties.classifications` per property, add changelog,
  add quality rules for SCD2 and record state, and update relationships
  to target `*_uid` columns.
- Event/transaction contracts: rename `*_id` PK to `*_uid`, add
  `lifecycle_event_uid` (transactions) or `triggering_transaction_uid`
  (events), add correction fields, skip SCD2 and record-state.
- Codeset contracts: rename PK to `*_code_uid`, ensure
  `code_value`/`code_label`/`code_description`/external mapping fields
  are present, add SCD2 and record state.

The script is idempotent. Running it twice produces no further changes.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_GLOB = "references/odcs/pc/**/*.odcs.yaml"

# Contracts that are append-only events or transactions. They do not get SCD2
# or record_status_code; they get correction fields instead.
EVENT_OR_TRANSACTION_SLUGS = {
    "policy-lifecycle-event",
    "policy-transaction",
    "submission-lifecycle-event",
    "financial-transaction",
    "claim-lifecycle-event",
    "claim-financial-transaction",
}

# Contracts that are codesets. They get SCD2 and record_status_code, and a
# uniform code_value/code_label/external mapping shape.
CODESET_SLUGS = {
    "lifecycle-event-type",
    "lifecycle-status",
    "line-of-business",
    "transaction-type",
}

# PII-sensitive field name patterns. Matched against the property `name` in
# lowercase. Returns (sensitivity_tier, regulatory_tags).
PII_PATTERNS: list[tuple[str, str, list[str]]] = [
    ("ssn", "RESTRICTED", ["PII", "SPI"]),
    ("social_security", "RESTRICTED", ["PII", "SPI"]),
    ("tax_id", "RESTRICTED", ["PII"]),
    ("tin", "RESTRICTED", ["PII"]),
    ("ein", "RESTRICTED", ["PII"]),
    ("driver_license", "RESTRICTED", ["PII"]),
    ("license_number", "RESTRICTED", ["PII"]),
    ("passport", "RESTRICTED", ["PII"]),
    ("national_id", "RESTRICTED", ["PII"]),
    ("date_of_birth", "RESTRICTED", ["PII"]),
    ("birth_date", "RESTRICTED", ["PII"]),
    ("medical", "RESTRICTED", ["PHI"]),
    ("diagnosis", "RESTRICTED", ["PHI"]),
    ("health", "RESTRICTED", ["PHI"]),
    ("injury", "RESTRICTED", ["PHI"]),
    ("treatment", "RESTRICTED", ["PHI"]),
    ("credit_card", "RESTRICTED", ["PCI"]),
    ("cardholder", "RESTRICTED", ["PCI"]),
    ("bank_account", "RESTRICTED", ["FINANCIAL", "PII"]),
    ("routing_number", "RESTRICTED", ["FINANCIAL"]),
    ("first_name", "CONFIDENTIAL", ["PII"]),
    ("last_name", "CONFIDENTIAL", ["PII"]),
    ("middle_name", "CONFIDENTIAL", ["PII"]),
    ("full_name", "CONFIDENTIAL", ["PII"]),
    ("given_name", "CONFIDENTIAL", ["PII"]),
    ("family_name", "CONFIDENTIAL", ["PII"]),
    ("surname", "CONFIDENTIAL", ["PII"]),
    ("maiden_name", "CONFIDENTIAL", ["PII"]),
    ("party_name", "CONFIDENTIAL", ["PII"]),
    ("legal_name", "CONFIDENTIAL", ["PII"]),
    ("display_name", "CONFIDENTIAL", ["PII"]),
    ("contact_name", "CONFIDENTIAL", ["PII"]),
    ("phone", "CONFIDENTIAL", ["PII"]),
    ("email", "CONFIDENTIAL", ["PII"]),
    ("address", "CONFIDENTIAL", ["PII"]),
    ("street", "CONFIDENTIAL", ["PII"]),
    ("postal", "CONFIDENTIAL", ["PII"]),
    ("zip", "CONFIDENTIAL", ["PII"]),
    ("gender", "CONFIDENTIAL", ["PII"]),
    ("marital", "CONFIDENTIAL", ["PII"]),
    ("nationality", "CONFIDENTIAL", ["PII"]),
    ("ethnicity", "RESTRICTED", ["PII", "SPI"]),
    ("narrative", "CONFIDENTIAL", ["PII"]),
    ("notes", "CONFIDENTIAL", ["PII"]),
    ("comment", "CONFIDENTIAL", ["PII"]),
    # Money is commercially sensitive but not PII unless paired with party.
    ("premium_amount", "CONFIDENTIAL", ["FINANCIAL"]),
    ("reserve_amount", "CONFIDENTIAL", ["FINANCIAL"]),
    ("payment_amount", "CONFIDENTIAL", ["FINANCIAL"]),
    ("loss_amount", "CONFIDENTIAL", ["FINANCIAL"]),
    ("paid_amount", "CONFIDENTIAL", ["FINANCIAL"]),
    ("amount", "CONFIDENTIAL", ["FINANCIAL"]),
    ("rate", "CONFIDENTIAL", ["FINANCIAL"]),
]

DEFAULT_SENSITIVITY = "INTERNAL"


def slug_from_path(path: Path) -> str:
    return path.name.removesuffix(".odcs.yaml")


def is_event(slug: str) -> bool:
    return slug in EVENT_OR_TRANSACTION_SLUGS


def is_codeset(slug: str) -> bool:
    return slug in CODESET_SLUGS


def classify_field(name: str) -> dict[str, Any]:
    """Return a `classifications` mapping for a property, given its name."""
    lower = name.lower()
    for pattern, sensitivity, tags in PII_PATTERNS:
        if pattern in lower:
            entry: dict[str, Any] = {"sensitivity": sensitivity}
            if tags:
                entry["regulatoryTags"] = tags
            return entry
    return {"sensitivity": DEFAULT_SENSITIVITY}


def classification_profile(properties: list[dict[str, Any]]) -> str:
    order = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]
    profile = "PUBLIC"
    for prop in properties:
        cls = (prop.get("customProperties") or {}).get("classifications") or {}
        sens = cls.get("sensitivity")
        if sens in order and order.index(sens) > order.index(profile):
            profile = sens
    return profile


def has_phi(properties: list[dict[str, Any]]) -> bool:
    for prop in properties:
        cls = (prop.get("customProperties") or {}).get("classifications") or {}
        if "PHI" in (cls.get("regulatoryTags") or []):
            return True
    return False


def ensure_property_classification(properties: list[dict[str, Any]]) -> None:
    """Add or refresh `customProperties.classifications` on each property."""
    for prop in properties:
        if not isinstance(prop, dict):
            continue
        existing = prop.get("customProperties") or {}
        existing["classifications"] = classify_field(prop.get("name", ""))
        prop["customProperties"] = existing


def rename_pk_to_uid(
    properties: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    quality: list[dict[str, Any]],
    slug: str,
) -> str | None:
    """Rename the PK property `*_id` to `*_uid`. Returns the new uid name or None."""
    pk_index = None
    for i, prop in enumerate(properties):
        if isinstance(prop, dict) and prop.get("primaryKey") is True:
            pk_index = i
            break
    if pk_index is None:
        return None

    pk = properties[pk_index]
    old_name = pk.get("name", "")
    if old_name.endswith("_uid"):
        return old_name
    if old_name.endswith("_id"):
        new_name = old_name[: -len("_id")] + "_uid"
    else:
        new_name = old_name + "_uid"
    pk["name"] = new_name
    pk["logicalType"] = "string"
    pk["description"] = (
        "Immutable system-generated GUID that uniquely identifies the canonical "
        f"{slug.replace('-', ' ')} record across snapshots and source systems."
    )

    for prop in properties:
        if isinstance(prop, dict) and prop.get("name") == old_name and prop is not pk:
            prop["name"] = new_name

    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        for key in ("sourceFields", "targetFields"):
            fields = rel.get(key)
            if isinstance(fields, list):
                rel[key] = [new_name if f == old_name else f for f in fields]

    for rule in quality:
        if not isinstance(rule, dict):
            continue
        if rule.get("rule") == f"{old_name}_required":
            rule["rule"] = f"{new_name}_required"
            rule["description"] = (
                f"{new_name} must be populated for every record."
            )

    return new_name


def rename_id_referencing_others(
    properties: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    quality: list[dict[str, Any]],
) -> None:
    """Rename every non-PK property whose name ends in `_id` to `*_uid`.

    A `*_id` field on an entity contract is overwhelmingly a foreign-key
    reference. After this refactor, every PK is `*_uid`, so every FK should
    also be `*_uid`. Source-system natural keys live on `source_natural_key`;
    they are not what these `_id` fields capture.

    Excludes fields that look like external string identifiers we explicitly
    keep (none in current contracts; carve-outs may be added here later).
    """
    rename_map: dict[str, str] = {}

    keep_as_id = set()  # Reserved for future carve-outs.

    for prop in properties:
        if not isinstance(prop, dict):
            continue
        if prop.get("primaryKey") is True:
            continue
        name = prop.get("name", "")
        if not isinstance(name, str) or not name.endswith("_id"):
            continue
        if name in keep_as_id:
            continue
        new_name = name[: -len("_id")] + "_uid"
        rename_map[name] = new_name

    for prop in properties:
        if not isinstance(prop, dict):
            continue
        name = prop.get("name", "")
        if name in rename_map:
            prop["name"] = rename_map[name]
            desc = prop.get("description", "")
            if "Identifier" in desc and "GUID" not in desc:
                prop["description"] = desc.replace(
                    "Identifier", "Identifier (GUID reference)"
                )

    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        for key in ("sourceFields", "targetFields"):
            fields = rel.get(key) or []
            new_fields = []
            for f in fields:
                if isinstance(f, str) and f.endswith("_id"):
                    new_f = rename_map.get(f, f[: -len("_id")] + "_uid")
                    new_fields.append(new_f)
                else:
                    new_fields.append(f)
            rel[key] = new_fields

    for rule in quality:
        if not isinstance(rule, dict):
            continue
        for old, new in rename_map.items():
            if rule.get("rule") and old in rule["rule"]:
                rule["rule"] = rule["rule"].replace(old, new)
            if rule.get("description") and old in rule["description"]:
                rule["description"] = rule["description"].replace(old, new)


SCD2_FIELDS: list[dict[str, Any]] = [
    {
        "name": "valid_from_datetime",
        "businessName": "Valid From Datetime",
        "logicalType": "datetime",
        "required": True,
        "description": "System-time start of the SCD2 window for this record version.",
    },
    {
        "name": "valid_to_datetime",
        "businessName": "Valid To Datetime",
        "logicalType": "datetime",
        "required": False,
        "description": "System-time end of the SCD2 window for this record version. Null indicates the current row.",
    },
    {
        "name": "is_current_indicator",
        "businessName": "Is Current Indicator",
        "logicalType": "boolean",
        "required": True,
        "description": "True for exactly one row per logical key, indicating the current record version.",
    },
]

RECORD_STATE_FIELD: dict[str, Any] = {
    "name": "record_status_code",
    "businessName": "Record Status Code",
    "logicalType": "string",
    "required": True,
    "description": "Warehouse-level state of the record. References the RecordStatusCode codeset (ACTIVE, SUPERSEDED, SOFT_DELETED, RESTATED, MERGED).",
}

SOURCE_ATTRIBUTION_FIELDS: list[dict[str, Any]] = [
    {
        "name": "source_system_code",
        "businessName": "Source System Code",
        "logicalType": "string",
        "required": False,
        "description": "Identifier of the upstream system that produced or last asserted this record. Used for multi-source mastering and lineage.",
    },
    {
        "name": "source_natural_key",
        "businessName": "Source Natural Key",
        "logicalType": "string",
        "required": False,
        "description": "Natural key assigned by the source system. Captured for provenance; not used as the canonical primary key.",
    },
]

CORRECTION_FIELDS: list[dict[str, Any]] = [
    {
        "name": "correction_indicator",
        "businessName": "Correction Indicator",
        "logicalType": "boolean",
        "required": True,
        "description": "True when this row corrects a previously emitted row. False for original (uncorrected) rows.",
    },
]


def add_field_after(
    properties: list[dict[str, Any]],
    field: dict[str, Any],
    after_name: str | None,
) -> None:
    """Insert `field` after the property named `after_name`. If absent, insert
    at the end. Skip insertion if a property with the same name already exists.
    """
    if any(isinstance(p, dict) and p.get("name") == field["name"] for p in properties):
        return
    if after_name is None:
        properties.append(field)
        return
    for i, prop in enumerate(properties):
        if isinstance(prop, dict) and prop.get("name") == after_name:
            properties.insert(i + 1, field)
            return
    properties.append(field)


def quality_rule_present(quality: list[dict[str, Any]], rule_name: str) -> bool:
    return any(isinstance(r, dict) and r.get("rule") == rule_name for r in quality)


def add_scd2_quality(quality: list[dict[str, Any]]) -> None:
    additions = [
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
    ]
    for rule in additions:
        if not quality_rule_present(quality, rule["rule"]):
            quality.append(rule)


def add_correction_quality(quality: list[dict[str, Any]]) -> None:
    rule = {
        "rule": "correction_indicator_required",
        "description": "correction_indicator must be populated for every event or transaction row.",
        "dimension": "completeness",
        "severity": "error",
    }
    if not quality_rule_present(quality, rule["rule"]):
        quality.append(rule)


def transform_entity(data: dict[str, Any], slug: str) -> None:
    schema = data.get("schema") or []
    if not schema:
        return
    entry = schema[0]
    properties = entry.setdefault("properties", [])
    relationships = data.setdefault("relationships", []) or []
    if relationships is None:
        relationships = []
        data["relationships"] = relationships
    quality = data.setdefault("quality", []) or []

    uid_name = rename_pk_to_uid(properties, relationships, quality, slug)
    rename_id_referencing_others(properties, relationships, quality)

    after = uid_name
    for field in SOURCE_ATTRIBUTION_FIELDS:
        add_field_after(properties, dict(field), after)
        after = field["name"]

    end_anchor = None
    for field in [RECORD_STATE_FIELD] + SCD2_FIELDS:
        add_field_after(properties, dict(field), end_anchor)

    add_scd2_quality(quality)
    ensure_property_classification(properties)


def remove_duplicate_link_fields(properties: list[dict[str, Any]]) -> None:
    """Remove a generic `lifecycle_event_uid` if a more specific `*_lifecycle_event_uid`
    is also present, and same for `triggering_transaction_uid`."""
    names = [p.get("name") for p in properties if isinstance(p, dict)]
    has_specific_lifecycle = any(
        isinstance(n, str) and n.endswith("_lifecycle_event_uid") for n in names
    )
    has_specific_transaction = any(
        isinstance(n, str) and n.endswith("_transaction_uid") and n != "triggering_transaction_uid"
        for n in names
    )
    if has_specific_lifecycle and "lifecycle_event_uid" in names:
        for i, p in enumerate(properties):
            if isinstance(p, dict) and p.get("name") == "lifecycle_event_uid":
                del properties[i]
                break
    if has_specific_transaction and "triggering_transaction_uid" in names:
        for i, p in enumerate(properties):
            if isinstance(p, dict) and p.get("name") == "triggering_transaction_uid":
                del properties[i]
                break


def transform_event(data: dict[str, Any], slug: str) -> None:
    schema = data.get("schema") or []
    if not schema:
        return
    entry = schema[0]
    properties = entry.setdefault("properties", [])
    relationships = data.setdefault("relationships", []) or []
    if relationships is None:
        relationships = []
        data["relationships"] = relationships
    quality = data.setdefault("quality", []) or []

    rename_pk_to_uid(properties, relationships, quality, slug)
    rename_id_referencing_others(properties, relationships, quality)

    existing_names = {p.get("name") for p in properties if isinstance(p, dict)}
    has_lifecycle_event_link = any(
        isinstance(n, str) and n.endswith("lifecycle_event_uid") for n in existing_names
    )
    has_transaction_link = any(
        isinstance(n, str) and n.endswith("transaction_uid") and n != properties[0].get("name")
        for n in existing_names
    )

    if "transaction" in slug and not has_lifecycle_event_link:
        link_field = {
            "name": "lifecycle_event_uid",
            "businessName": "Lifecycle Event Identifier",
            "logicalType": "string",
            "required": False,
            "description": "Optional reference to the lifecycle event that this transaction realizes (per the event-and-transaction ADR).",
        }
        add_field_after(properties, link_field, None)
    elif "lifecycle-event" in slug and not has_transaction_link:
        link_field = {
            "name": "triggering_transaction_uid",
            "businessName": "Triggering Transaction Identifier",
            "logicalType": "string",
            "required": False,
            "description": "Optional reference to the transaction that produced this lifecycle event, when the event is the consequence of a processed transaction.",
        }
        add_field_after(properties, link_field, None)

    pk_name = next(
        (p["name"] for p in properties if isinstance(p, dict) and p.get("primaryKey")),
        None,
    )
    corrects_field_name = (
        f"corrects_{pk_name[:-len('_uid')]}_uid" if pk_name and pk_name.endswith("_uid") else "corrects_uid"
    )
    corrects_field = {
        "name": corrects_field_name,
        "businessName": "Corrects Record Identifier",
        "logicalType": "string",
        "required": False,
        "description": "Reference to the prior row that this row corrects. Populated only when correction_indicator is true.",
    }
    add_field_after(properties, dict(CORRECTION_FIELDS[0]), None)
    add_field_after(properties, corrects_field, None)

    add_correction_quality(quality)
    remove_duplicate_link_fields(properties)
    ensure_property_classification(properties)


def transform_codeset(data: dict[str, Any], slug: str) -> None:
    schema = data.get("schema") or []
    if not schema:
        return
    entry = schema[0]
    properties = entry.setdefault("properties", [])
    relationships = data.setdefault("relationships", []) or []
    if relationships is None:
        relationships = []
        data["relationships"] = relationships
    quality = data.setdefault("quality", []) or []

    rename_pk_to_uid(properties, relationships, quality, slug)
    rename_id_referencing_others(properties, relationships, quality)

    # Remove fields that duplicate the canonical codeset trio (code_value,
    # code_label, code_description). Old per-codeset-named twins like
    # `lifecycle_status_code`, `lifecycle_status_name`,
    # `lifecycle_status_description` are dropped in favor of the canonical
    # uniform shape.
    slug_field_prefix = slug.replace("-", "_")
    redundant_names = {
        f"{slug_field_prefix}_code",
        f"{slug_field_prefix}_name",
        f"{slug_field_prefix}_description",
    }
    properties[:] = [
        p for p in properties
        if not (isinstance(p, dict) and p.get("name") in redundant_names)
    ]
    quality[:] = [
        q for q in quality
        if not (
            isinstance(q, dict)
            and isinstance(q.get("rule"), str)
            and any(r in q["rule"] for r in (
                f"{slug_field_prefix}_code_required",
                f"{slug_field_prefix}_name_required",
            ))
        )
    ]

    code_value_present = any(p.get("name") == "code_value" for p in properties if isinstance(p, dict))
    if not code_value_present:
        pk_name = next(
            (p["name"] for p in properties if isinstance(p, dict) and p.get("primaryKey")),
            None,
        )
        codeset_fields = [
            {
                "name": "code_value",
                "businessName": "Code Value",
                "logicalType": "string",
                "required": True,
                "description": "Business-friendly code value referenced by entity contracts.",
            },
            {
                "name": "code_label",
                "businessName": "Code Label",
                "logicalType": "string",
                "required": True,
                "description": "Human-readable label for the code value.",
            },
            {
                "name": "code_description",
                "businessName": "Code Description",
                "logicalType": "string",
                "required": False,
                "description": "Extended description of the code value.",
            },
            {
                "name": "external_standard_code",
                "businessName": "External Standard Code",
                "logicalType": "string",
                "required": False,
                "description": "Code value as defined by an external standard (ACORD, NAIC, ISO, etc.) when a mapping is recorded.",
            },
            {
                "name": "external_standard_name",
                "businessName": "External Standard Name",
                "logicalType": "string",
                "required": False,
                "description": "Name of the external standard whose code is captured in external_standard_code.",
            },
        ]
        after = pk_name
        for field in codeset_fields:
            add_field_after(properties, dict(field), after)
            after = field["name"]

    add_field_after(properties, dict(RECORD_STATE_FIELD), None)
    for field in SCD2_FIELDS:
        add_field_after(properties, dict(field), None)

    add_scd2_quality(quality)
    if not quality_rule_present(quality, "code_value_required"):
        quality.append({
            "rule": "code_value_required",
            "description": "code_value must be populated and unique among current rows.",
            "dimension": "completeness",
            "severity": "error",
        })
    ensure_property_classification(properties)


def update_top_level(data: dict[str, Any]) -> None:
    data["version"] = "0.2.0"
    custom = data.setdefault("customProperties", {})
    schema = data.get("schema") or []
    properties: list[dict[str, Any]] = []
    if schema and isinstance(schema[0], dict):
        properties = schema[0].get("properties") or []

    custom["classificationProfile"] = classification_profile(properties)
    if has_phi(properties):
        custom["subjectToHipaa"] = True
    elif "subjectToHipaa" in custom:
        del custom["subjectToHipaa"]

    changelog = custom.get("changelog")
    if not isinstance(changelog, list):
        changelog = []
    entry_text = "0.2.0: Apply cross-cutting ADRs (identifier strategy, SCD2 temporal, record state, classifications, codeset references, source attribution)."
    if not any(isinstance(e, str) and e.startswith("0.2.0:") for e in changelog):
        changelog.append(entry_text)
    custom["changelog"] = changelog


def represent_str(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def represent_dict(dumper: yaml.SafeDumper, data: dict[str, Any]) -> yaml.MappingNode:
    return dumper.represent_dict(data.items())


def dump_yaml(data: dict[str, Any]) -> str:
    yaml.SafeDumper.add_representer(str, represent_str)
    yaml.SafeDumper.add_representer(dict, represent_dict)
    return yaml.safe_dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        indent=2,
        width=200,
        allow_unicode=True,
    )


def strip_empty_relationships(data: dict[str, Any]) -> None:
    rels = data.get("relationships")
    if isinstance(rels, list) and not rels:
        del data["relationships"]


def transform_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        return False

    slug = slug_from_path(path)
    if is_event(slug):
        transform_event(data, slug)
    elif is_codeset(slug):
        transform_codeset(data, slug)
    else:
        transform_entity(data, slug)

    update_top_level(data)
    strip_empty_relationships(data)
    new_text = dump_yaml(data)

    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main() -> int:
    files = sorted(ROOT.glob(CONTRACT_GLOB))
    files = [f for f in files if "/templates/" not in f.as_posix()]
    changed = 0
    for path in files:
        if transform_file(path):
            changed += 1
            print(f"refactored: {path.relative_to(ROOT)}")
        else:
            print(f"unchanged:  {path.relative_to(ROOT)}")
    print(f"\n{changed} of {len(files)} contract files refactored.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
