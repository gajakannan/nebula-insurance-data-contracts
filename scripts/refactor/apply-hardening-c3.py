#!/usr/bin/env python3
"""Apply CANONICAL_HARDENING_PLAN.md §4 phase C3 transforms across the P&C ODCS surface.

The script consumes the C1 punch-list categories (C1.1 currency pairing,
C1.5 append-only datetime ban, C1.6 *_uid+*_code redundancy, C1.7 narrative
classification, C1.8 over-classification heuristic) plus the named per-contract
fixes from CANONICAL_HARDENING_PLAN.md §4 phase C3.

Each transform is idempotent. Running the script twice produces no further
changes after the first run.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_GLOB = "references/odcs/pc/**/*.odcs.yaml"
TARGET_VERSION = "0.3.0"

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
    "_uid",
)
OVER_CLASSIFICATION_PREFIXES = ("accounting_",)

# Plan §4 C3.6 names two non-narrative-suffix fields explicitly. Add them so the
# discipline matches the plan even when the C1.7 heuristic does not catch them.
EXTRA_NARRATIVE_FIELDS = {
    "claim-document": ["document_title"],
    "policy-document": ["document_title"],
    "submission-document": ["document_title"],
}

# Currency-pairing renames per CANONICAL_HARDENING_PLAN.md §4 C3.4 plus the two
# extras the C1.1 strict-prefix matcher caught and the user folded into C3.4.
# Keys are file slugs; values are { existing_amount: existing_currency_to_rename_to }.
CURRENCY_RENAMES: dict[str, dict[str, str]] = {
    "policy-term": {"annualized_premium_amount": "premium_currency_code -> annualized_premium_currency_code"},
    "policy-transaction": {"premium_change_amount": "premium_currency_code -> premium_change_currency_code"},
}

# Currency-pairing additions: amount fields that need a brand-new same-prefix
# *_currency_code sibling with a relationship to pc.currency-code.
CURRENCY_ADDITIONS: dict[str, list[tuple[str, str]]] = {
    "property-exposure": [
        ("building_value_amount", "building_value_currency_code"),
        ("contents_value_amount", "contents_value_currency_code"),
    ],
    "vehicle-exposure": [
        ("stated_value_amount", "stated_value_currency_code"),
    ],
    "workers-comp-exposure": [
        ("payroll_amount", "payroll_currency_code"),
    ],
}

# Currency-pairing exemptions: amount fields whose currency is shared with another
# field in the same contract (typical for min/max bounds that share the primary
# amount's currency). Each entry maps a slug to a list of (amount_name, shared_currency_field).
CURRENCY_EXEMPTIONS: dict[str, list[tuple[str, str]]] = {
    "policy-deductible": [
        ("minimum_deductible_amount", "deductible_currency_code"),
        ("maximum_deductible_amount", "deductible_currency_code"),
    ],
    "product-coverage": [
        ("minimum_limit_amount", "limit_constraint_currency_code"),
        ("maximum_limit_amount", "limit_constraint_currency_code"),
    ],
}

# Plan §4 C3.7 — drop redundant *_uid + *_code pairs and keep the *_code form.
# Keys are file slugs; values are list of (uid_field_to_drop, code_field_to_keep, codeset_target_id).
REDUNDANT_UID_CODE_PAIRS: dict[str, list[tuple[str, str, str]]] = {
    "policy-lifecycle-event": [
        ("lifecycle_event_type_uid", "lifecycle_event_type_code", "pc.lifecycle-event-type"),
    ],
    "submission-lifecycle-event": [
        ("lifecycle_event_type_uid", "lifecycle_event_type_code", "pc.lifecycle-event-type"),
    ],
    "policy-transaction": [
        ("transaction_type_uid", "transaction_type_code", "pc.transaction-type"),
    ],
}

# Plan §4 C3.3 — drop mutable transaction_status_code from these append-only
# contracts. Status changes belong on lifecycle events.
TRANSACTION_STATUS_DROP_SLUGS = {"policy-transaction", "financial-transaction"}


def slug_from_path(path: Path) -> str:
    return path.name.removesuffix(".odcs.yaml")


def is_event_or_txn(slug: str) -> bool:
    return slug in EVENT_OR_TRANSACTION_SLUGS


def schema_properties(data: dict[str, Any]) -> list[dict[str, Any]] | None:
    schema = data.get("schema") or []
    if not schema or not isinstance(schema[0], dict):
        return None
    return schema[0].setdefault("properties", [])


def find_property(properties: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for prop in properties:
        if isinstance(prop, dict) and prop.get("name") == name:
            return prop
    return None


def remove_property(properties: list[dict[str, Any]], name: str) -> bool:
    for i, prop in enumerate(properties):
        if isinstance(prop, dict) and prop.get("name") == name:
            del properties[i]
            return True
    return False


def insert_after(properties: list[dict[str, Any]], anchor_name: str, field: dict[str, Any]) -> bool:
    for i, prop in enumerate(properties):
        if isinstance(prop, dict) and prop.get("name") == anchor_name:
            properties.insert(i + 1, field)
            return True
    return False


def rename_property(properties: list[dict[str, Any]], old_name: str, new_name: str) -> bool:
    prop = find_property(properties, old_name)
    if prop is None:
        return False
    if find_property(properties, new_name) is not None:
        return False  # rename already done; idempotent
    prop["name"] = new_name
    prop["businessName"] = " ".join(part.capitalize() for part in new_name.split("_"))
    return True


def update_relationship_fields(
    relationships: list[dict[str, Any]],
    rename_map: dict[str, str] | None = None,
    target_field_overrides: dict[str, str] | None = None,
) -> None:
    """Rename source/target field references; allow overriding per-source target field name."""
    rename_map = rename_map or {}
    target_field_overrides = target_field_overrides or {}
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        for key in ("sourceFields", "targetFields"):
            fields = rel.get(key)
            if not isinstance(fields, list):
                continue
            rel[key] = [rename_map.get(f, f) for f in fields]
        # Re-derive targetFields if a per-source override applies (e.g. when
        # the source field changes from `*_uid` to `*_code`, the target field
        # must move from `*_uid` to `code_value`).
        sources = rel.get("sourceFields") or []
        for src in sources:
            if isinstance(src, str) and src in target_field_overrides:
                rel["targetFields"] = [target_field_overrides[src]]
                break


def update_quality_descriptions(
    quality: list[dict[str, Any]],
    rename_map: dict[str, str],
) -> None:
    for rule in quality:
        if not isinstance(rule, dict):
            continue
        for old, new in rename_map.items():
            if isinstance(rule.get("rule"), str) and old in rule["rule"]:
                rule["rule"] = rule["rule"].replace(old, new)
            if isinstance(rule.get("description"), str) and old in rule["description"]:
                rule["description"] = rule["description"].replace(old, new)


# ---------------------------------------------------------------------------
# C3.1 — composite SCD2 PK
# ---------------------------------------------------------------------------


def apply_scd2_pk(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    if is_event_or_txn(slug):
        return
    properties = schema_properties(data)
    if properties is None:
        return
    valid_from = find_property(properties, "valid_from_datetime")
    if valid_from is None:
        return
    if valid_from.get("primaryKey") is True:
        return
    valid_from["primaryKey"] = True
    if valid_from.get("required") is not True:
        valid_from["required"] = True
    change_log.append("composite SCD2 PK on (uid, valid_from_datetime) per scd2-primary-key ADR")


# ---------------------------------------------------------------------------
# C3.2 — drop created/updated_datetime on append-only contracts
# ---------------------------------------------------------------------------


def apply_append_only_datetime_drop(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    if not is_event_or_txn(slug):
        return
    properties = schema_properties(data)
    if properties is None:
        return
    dropped = []
    for name in ("created_datetime", "updated_datetime"):
        if remove_property(properties, name):
            dropped.append(name)
    if dropped:
        change_log.append(f"drop {', '.join(dropped)} (append-only per temporal-modeling ADR)")


# ---------------------------------------------------------------------------
# C3.3 — drop transaction_status_code
# ---------------------------------------------------------------------------


def apply_transaction_status_drop(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    if slug not in TRANSACTION_STATUS_DROP_SLUGS:
        return
    properties = schema_properties(data)
    if properties is None:
        return
    if not remove_property(properties, "transaction_status_code"):
        return
    change_log.append("drop mutable transaction_status_code (status belongs on lifecycle events)")
    quality = data.get("quality") or []
    quality[:] = [
        q for q in quality
        if not (
            isinstance(q, dict)
            and isinstance(q.get("rule"), str)
            and "transaction_status_code" in q["rule"]
        )
    ]


# ---------------------------------------------------------------------------
# C3.4 — currency pairing
# ---------------------------------------------------------------------------


CURRENCY_FIELD_TEMPLATE = {
    "businessName": "Currency Code",
    "logicalType": "string",
    "required": False,
    "description": "Currency code for the paired amount. References the CurrencyCode codeset.",
    "customProperties": {
        "classifications": {"sensitivity": "INTERNAL"},
    },
}


def _make_currency_field(name: str, paired_amount_label: str) -> dict[str, Any]:
    field = {
        "name": name,
        "businessName": " ".join(part.capitalize() for part in name.split("_")),
        "logicalType": "string",
        "required": False,
        "description": f"Currency code for {paired_amount_label}. References the CurrencyCode codeset.",
        "customProperties": {
            "classifications": {"sensitivity": "INTERNAL"},
        },
    }
    return field


def apply_currency_pairing(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    properties = schema_properties(data)
    if properties is None:
        return
    relationships = data.setdefault("relationships", []) or []
    if relationships is None:
        relationships = []
        data["relationships"] = relationships
    quality = data.setdefault("quality", []) or []

    # Renames: an existing currency field is renamed to the same-prefix form.
    if slug in CURRENCY_RENAMES:
        rename_map: dict[str, str] = {}
        for amount_field, rename_directive in CURRENCY_RENAMES[slug].items():
            old_name, new_name = [s.strip() for s in rename_directive.split("->")]
            if rename_property(properties, old_name, new_name):
                rename_map[old_name] = new_name
                change_log.append(f"rename {old_name} → {new_name} for currency pairing on {amount_field}")
        if rename_map:
            update_relationship_fields(relationships, rename_map=rename_map)
            update_quality_descriptions(quality, rename_map)

    # Additions: brand-new same-prefix *_currency_code sibling.
    if slug in CURRENCY_ADDITIONS:
        for amount_name, currency_name in CURRENCY_ADDITIONS[slug]:
            if find_property(properties, currency_name) is not None:
                continue
            if find_property(properties, amount_name) is None:
                continue
            label = amount_name.replace("_amount", "").replace("_", " ")
            new_field = _make_currency_field(currency_name, f"the {label} amount")
            insert_after(properties, amount_name, new_field)
            # Add a relationship to pc.currency-code if not already present.
            existing_targets = {
                tuple(rel.get("sourceFields") or []): rel.get("targetContractId")
                for rel in relationships
                if isinstance(rel, dict)
            }
            if (currency_name,) not in existing_targets:
                relationships.append({
                    "name": f"{slug.replace('-', '_')}_to_currency_for_{amount_name}",
                    "description": f"Relates {amount_name} to its currency code.",
                    "relationshipType": "many-to-one",
                    "targetContractId": "pc.currency-code",
                    "sourceFields": [currency_name],
                    "targetFields": ["code_value"],
                })
            change_log.append(f"add {currency_name} sibling for {amount_name}")

    # Exemptions: bound-style amount fields that share another field's currency.
    if slug in CURRENCY_EXEMPTIONS:
        for amount_name, shared_currency in CURRENCY_EXEMPTIONS[slug]:
            prop = find_property(properties, amount_name)
            if prop is None:
                continue
            custom = prop.setdefault("customProperties", {})
            if custom.get("amountCurrencyExempt") is True and is_non_empty_string(custom.get("amountCurrencyExemptReason")):
                continue
            custom["amountCurrencyExempt"] = True
            custom["amountCurrencyExemptReason"] = (
                f"Bound shares the contract's primary `{shared_currency}` field; min/max amounts and the primary "
                f"amount are denominated in the same currency by definition."
            )
            change_log.append(f"exempt {amount_name} (shares {shared_currency})")


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


# ---------------------------------------------------------------------------
# C3.5 — over-classification fix (re-tag RESTRICTED+PII patterns to INTERNAL)
# ---------------------------------------------------------------------------


def apply_over_classification_fix(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    properties = schema_properties(data)
    if properties is None:
        return
    fixed = []
    for prop in properties:
        if not isinstance(prop, dict):
            continue
        name = prop.get("name") or ""
        suffix_match = any(name.endswith(s) for s in OVER_CLASSIFICATION_SUFFIXES)
        prefix_match = any(name.startswith(p) for p in OVER_CLASSIFICATION_PREFIXES)
        if not (suffix_match or prefix_match):
            continue
        custom = prop.get("customProperties") or {}
        cls = custom.get("classifications") or {}
        if cls.get("sensitivity") != "RESTRICTED":
            continue
        tags = cls.get("regulatoryTags") or []
        if "PII" not in tags:
            continue
        cls["sensitivity"] = "INTERNAL"
        new_tags = [t for t in tags if t != "PII"]
        if new_tags:
            cls["regulatoryTags"] = new_tags
        else:
            cls.pop("regulatoryTags", None)
        custom["classifications"] = cls
        prop["customProperties"] = custom
        fixed.append(name)
    if fixed:
        change_log.append(f"re-tag over-classified field(s) to INTERNAL: {', '.join(sorted(fixed))}")


# ---------------------------------------------------------------------------
# C3.6 — narrative classification fix (lift INTERNAL → CONFIDENTIAL + PII tag)
# ---------------------------------------------------------------------------


def _is_narrative_field(name: str, slug: str) -> bool:
    if any(name.endswith(suffix) for suffix in NARRATIVE_SUFFIXES):
        return True
    extras = EXTRA_NARRATIVE_FIELDS.get(slug, [])
    return name in extras


def apply_narrative_classification_fix(slug: str, data: dict[str, Any], change_log: list[str], path: Path) -> None:
    # Skip codeset / reference-data contracts; their narrative-shaped fields
    # are PUBLIC by design (data-classification ADR carve-out).
    custom_root = data.get("customProperties") or {}
    if custom_root.get("codesetContract") is True:
        return
    relative = path.relative_to(ROOT)
    if relative.parts[0:4] == ("references", "odcs", "pc", "reference-data"):
        return
    properties = schema_properties(data)
    if properties is None:
        return
    fixed = []
    for prop in properties:
        if not isinstance(prop, dict):
            continue
        name = prop.get("name") or ""
        if not _is_narrative_field(name, slug):
            continue
        custom = prop.get("customProperties") or {}
        cls = custom.get("classifications") or {}
        sensitivity = cls.get("sensitivity")
        tags = cls.get("regulatoryTags") or []
        # If already at CONFIDENTIAL+ and has a regulatory tag, leave alone.
        rank = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}
        if rank.get(sensitivity, -1) >= rank["CONFIDENTIAL"] and tags:
            continue
        cls["sensitivity"] = "CONFIDENTIAL"
        if not tags:
            cls["regulatoryTags"] = ["PII"]
        elif "PII" not in tags:
            cls["regulatoryTags"] = list(tags) + ["PII"]
        custom["classifications"] = cls
        prop["customProperties"] = custom
        fixed.append(name)
    if fixed:
        change_log.append(f"re-tag narrative free-text field(s) to CONFIDENTIAL + PII: {', '.join(sorted(fixed))}")


# ---------------------------------------------------------------------------
# C3.7 — drop redundant *_uid + *_code pairs
# ---------------------------------------------------------------------------


def apply_uid_code_redundancy_fix(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    if slug not in REDUNDANT_UID_CODE_PAIRS:
        return
    properties = schema_properties(data)
    if properties is None:
        return
    relationships = data.setdefault("relationships", []) or []
    quality = data.setdefault("quality", []) or []
    rename_map: dict[str, str] = {}
    target_field_overrides: dict[str, str] = {}
    for uid_field, code_field, codeset_target in REDUNDANT_UID_CODE_PAIRS[slug]:
        if find_property(properties, code_field) is None:
            continue
        if not remove_property(properties, uid_field):
            continue
        rename_map[uid_field] = code_field
        target_field_overrides[code_field] = "code_value"
        change_log.append(f"drop redundant {uid_field} (keep {code_field})")
    if rename_map:
        # Rewrite relationships: any relationship that references the dropped
        # `_uid` field as a sourceField must now reference the `_code` field
        # and target `code_value` on the codeset contract.
        update_relationship_fields(relationships, rename_map=rename_map, target_field_overrides=target_field_overrides)
        update_quality_descriptions(quality, rename_map)


# ---------------------------------------------------------------------------
# Profile reconcile — keep classificationProfile ≥ max field sensitivity (C1.9).
# ---------------------------------------------------------------------------


SENSITIVITY_RANK = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}


def reconcile_classification_profile(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    properties = schema_properties(data)
    if properties is None:
        return
    custom = data.setdefault("customProperties", {})
    profile = custom.get("classificationProfile")
    if profile not in SENSITIVITY_RANK:
        return
    profile_rank = SENSITIVITY_RANK[profile]
    max_rank = -1
    max_sensitivity = profile
    for prop in properties:
        if not isinstance(prop, dict):
            continue
        cls = (prop.get("customProperties") or {}).get("classifications") or {}
        sens = cls.get("sensitivity")
        rank = SENSITIVITY_RANK.get(sens, -1)
        if rank > max_rank:
            max_rank = rank
            max_sensitivity = sens
    if max_rank > profile_rank:
        custom["classificationProfile"] = max_sensitivity
        change_log.append(f"raise classificationProfile {profile} → {max_sensitivity} (matches max field sensitivity)")


# ---------------------------------------------------------------------------
# C3.9 — version bump + changelog entry
# ---------------------------------------------------------------------------


def apply_version_bump(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    if not change_log:
        return
    current_version = data.get("version")
    if current_version == TARGET_VERSION:
        # already bumped on a prior run
        return
    data["version"] = TARGET_VERSION
    custom = data.setdefault("customProperties", {})
    changelog = custom.setdefault("changelog", [])
    if not isinstance(changelog, list):
        changelog = []
        custom["changelog"] = changelog
    entry = f"{TARGET_VERSION}: Canonical hardening C3 — " + "; ".join(change_log) + "."
    if not any(isinstance(e, str) and e.startswith(f"{TARGET_VERSION}:") for e in changelog):
        changelog.append(entry)


# ---------------------------------------------------------------------------
# YAML I/O — preserve key ordering, expand anchors, block style.
# ---------------------------------------------------------------------------


def represent_str(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def represent_dict(dumper: yaml.SafeDumper, data: dict[str, Any]) -> yaml.MappingNode:
    return dumper.represent_dict(data.items())


class NoAliasDumper(yaml.SafeDumper):
    """SafeDumper that never emits YAML anchors / aliases.

    PyYAML re-emits anchors whenever the same Python object is referenced
    multiple times in the data tree. The C3.8 plan rules out anchors because
    not all downstream parsers preserve them; this dumper forces explicit
    lists / dicts everywhere.
    """

    def ignore_aliases(self, data: Any) -> bool:  # noqa: ARG002
        return True


def dump_yaml(data: dict[str, Any]) -> str:
    NoAliasDumper.add_representer(str, represent_str)
    NoAliasDumper.add_representer(dict, represent_dict)
    return yaml.dump(
        data,
        Dumper=NoAliasDumper,
        sort_keys=False,
        default_flow_style=False,
        indent=2,
        width=200,
        allow_unicode=True,
    )


def transform_file(path: Path) -> tuple[bool, list[str]]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        return False, []

    slug = slug_from_path(path)
    change_log: list[str] = []

    # Order matters: re-tag fixes can run before structural drops/renames.
    apply_scd2_pk(slug, data, change_log)
    apply_append_only_datetime_drop(slug, data, change_log)
    apply_transaction_status_drop(slug, data, change_log)
    apply_currency_pairing(slug, data, change_log)
    apply_over_classification_fix(slug, data, change_log)
    apply_narrative_classification_fix(slug, data, change_log, path)
    apply_uid_code_redundancy_fix(slug, data, change_log)
    reconcile_classification_profile(slug, data, change_log)
    apply_version_bump(slug, data, change_log)

    new_text = dump_yaml(data)
    if new_text == text:
        return False, []
    path.write_text(new_text, encoding="utf-8")
    return True, change_log


def main() -> int:
    files = sorted(ROOT.glob(CONTRACT_GLOB))
    files = [f for f in files if "/templates/" not in f.as_posix()]
    changed = 0
    for path in files:
        did_change, log = transform_file(path)
        if did_change:
            changed += 1
            print(f"refactored: {path.relative_to(ROOT)}")
            for entry in log:
                print(f"    - {entry}")
        else:
            print(f"unchanged:  {path.relative_to(ROOT)}")
    print(f"\n{changed} of {len(files)} contract files refactored.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
