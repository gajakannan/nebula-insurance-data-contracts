#!/usr/bin/env python3
"""Apply CANONICAL_HARDENING_PLAN.md §4 phase C7 transforms across the P&C ODCS surface.

Phases handled:

  - C7.1 vehicle-exposure: rename `vehicle_identifier` → `vin_number`
        (business keys end in `_number` per identifier-strategy ADR).
  - C7.2 submission-lifecycle-event: drop `triggering_transaction_uid` dead
        reference (no `submission-transaction` contract exists; submission
        lifecycle is event-only).
  - C7.3 submission: add mutually-exclusive-outcome quality rule on
        bind_date / decline_date / withdrawn_date.
  - C7.4 every contract carrying legacy `created_datetime` / `updated_datetime`:
        rename to `source_created_datetime` / `source_updated_datetime` and
        rewrite descriptions to name source-system-time semantics (distinct
        from SCD2 system time in `valid_from_datetime` / `valid_to_datetime`).

Each transform is idempotent. Running the script twice produces no further
changes after the first run. Touched contracts get a single patch-version bump
plus one combined changelog entry per CANONICAL_HARDENING_PLAN.md §3.2.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_GLOB = "references/odcs/pc/**/*.odcs.yaml"

LEGACY_DATETIME_RENAMES = {
    "created_datetime": "source_created_datetime",
    "updated_datetime": "source_updated_datetime",
}

SOURCE_DATETIME_DESCRIPTIONS = {
    "source_created_datetime": (
        "Source-system timestamp asserting when this record was created. "
        "Captured for late-arriving-data analysis; distinct from the SCD2 "
        "system-time start in valid_from_datetime."
    ),
    "source_updated_datetime": (
        "Source-system timestamp asserting when this record was last updated. "
        "Captured for late-arriving-data analysis; distinct from the SCD2 "
        "system-time markers valid_from_datetime / valid_to_datetime."
    ),
}

SOURCE_DATETIME_BUSINESS_NAMES = {
    "source_created_datetime": "Source Created Datetime",
    "source_updated_datetime": "Source Updated Datetime",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def slug_from_path(path: Path) -> str:
    return path.name.removesuffix(".odcs.yaml")


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


def bump_patch(version: str) -> str:
    parts = version.split(".")
    if len(parts) != 3:
        return version
    try:
        major, minor, patch = (int(p) for p in parts)
    except ValueError:
        return version
    return f"{major}.{minor}.{patch + 1}"


# ---------------------------------------------------------------------------
# C7.1 — vehicle-exposure: rename vehicle_identifier → vin_number
# ---------------------------------------------------------------------------


def apply_vin_rename(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    if slug != "vehicle-exposure":
        return
    properties = schema_properties(data)
    if properties is None:
        return
    if find_property(properties, "vin_number") is not None:
        return  # already renamed
    prop = find_property(properties, "vehicle_identifier")
    if prop is None:
        return
    prop["name"] = "vin_number"
    prop["businessName"] = "VIN Number"
    prop["description"] = (
        "Vehicle Identification Number assigned to the vehicle when available. "
        "Business key per identifier-strategy ADR (`*_number` form)."
    )
    change_log.append("rename vehicle_identifier → vin_number (C7.1)")


# ---------------------------------------------------------------------------
# C7.2 — submission-lifecycle-event: drop triggering_transaction_uid
# ---------------------------------------------------------------------------


def apply_submission_dead_reference_drop(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    if slug != "submission-lifecycle-event":
        return
    properties = schema_properties(data)
    if properties is None:
        return
    if not remove_property(properties, "triggering_transaction_uid"):
        return
    change_log.append(
        "drop triggering_transaction_uid dead reference — no submission-transaction contract exists; "
        "submission lifecycle is event-only (C7.2)"
    )


# ---------------------------------------------------------------------------
# C7.3 — submission: mutually-exclusive-outcome quality rule
# ---------------------------------------------------------------------------


SUBMISSION_OUTCOME_RULE = {
    "rule": "submission_outcome_dates_mutually_exclusive",
    "description": (
        "At most one of bind_date, decline_date, or withdrawn_date is populated per snapshot. "
        "Submission outcomes are mutually exclusive — a submission cannot be both bound and "
        "declined, both bound and withdrawn, or both declined and withdrawn."
    ),
    "dimension": "consistency",
    "severity": "error",
}


def apply_submission_outcome_rule(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    if slug != "submission":
        return
    quality = data.setdefault("quality", []) or []
    if not isinstance(quality, list):
        return
    for rule in quality:
        if isinstance(rule, dict) and rule.get("rule") == SUBMISSION_OUTCOME_RULE["rule"]:
            return  # already added
    quality.append(dict(SUBMISSION_OUTCOME_RULE))
    change_log.append(
        "add mutually-exclusive-outcome quality rule on bind_date / decline_date / withdrawn_date (C7.3)"
    )


# ---------------------------------------------------------------------------
# C7.4 — rename created_datetime / updated_datetime → source_*
# ---------------------------------------------------------------------------


def apply_source_datetime_rename(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    properties = schema_properties(data)
    if properties is None:
        return
    renamed: list[str] = []
    for old_name, new_name in LEGACY_DATETIME_RENAMES.items():
        # Idempotent: skip if the new name already exists.
        if find_property(properties, new_name) is not None:
            continue
        prop = find_property(properties, old_name)
        if prop is None:
            continue
        prop["name"] = new_name
        prop["businessName"] = SOURCE_DATETIME_BUSINESS_NAMES[new_name]
        prop["description"] = SOURCE_DATETIME_DESCRIPTIONS[new_name]
        renamed.append(f"{old_name} → {new_name}")
    if renamed:
        change_log.append(
            f"rename {'; '.join(renamed)} — capture source-system time, distinct from SCD2 "
            f"system time (C7.4)"
        )


# ---------------------------------------------------------------------------
# Version bump + changelog entry
# ---------------------------------------------------------------------------


def apply_version_bump(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    if not change_log:
        return
    current_version = data.get("version")
    if not isinstance(current_version, str):
        return
    custom = data.setdefault("customProperties", {})
    changelog = custom.setdefault("changelog", [])
    if not isinstance(changelog, list):
        changelog = []
        custom["changelog"] = changelog

    # Idempotency: if the current version already has a C7 entry, do not bump again.
    for entry in changelog:
        if isinstance(entry, str) and entry.startswith(f"{current_version}: Canonical hardening C7"):
            return

    new_version = bump_patch(current_version)
    data["version"] = new_version
    entry = f"{new_version}: Canonical hardening C7 — " + "; ".join(change_log) + "."
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

    apply_vin_rename(slug, data, change_log)
    apply_submission_dead_reference_drop(slug, data, change_log)
    apply_submission_outcome_rule(slug, data, change_log)
    apply_source_datetime_rename(slug, data, change_log)
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
    print(f"\n{changed} of {len(files)} contract files refactored.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
