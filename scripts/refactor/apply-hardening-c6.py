#!/usr/bin/env python3
"""Apply CANONICAL_HARDENING_PLAN.md §4 phase C6 transforms across the P&C ODCS surface.

Phase handled:
  - C6.3: add `customProperties.adrs: [...]` on every contract, naming the
          ADRs that govern its shape. The validator's C1.12 rule confirms
          each id resolves to a file under `references/design-decisions/pc/`.

C6 does not bump contract versions or add changelog entries: per
CANONICAL_HARDENING_PLAN.md §3, C6 changes are governance/documentation
metadata that the versioning policy treats as below the bump threshold.

Each transform is idempotent. Running the script twice produces no changes
after the first run.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_GLOB = "references/odcs/pc/**/*.odcs.yaml"
REFERENCE_DATA_DIR = ROOT / "references" / "odcs" / "pc" / "reference-data"

# Append-only event/transaction contracts skip SCD2 and record_status_code per
# the temporal-modeling and event-and-transaction ADRs. Mirrors the validator's
# EVENT_OR_TRANSACTION_SLUGS set in scripts/validation/validate-contracts.py.
EVENT_OR_TRANSACTION_SLUGS = {
    "policy-lifecycle-event",
    "policy-transaction",
    "policy-financial-transaction",
    "submission-lifecycle-event",
    "claim-lifecycle-event",
    "financial-transaction",
    "claim-financial-transaction",
}

# ---------------------------------------------------------------------------
# Universal ADR set — applies to every contract on the canonical surface.
# ---------------------------------------------------------------------------
UNIVERSAL_ADRS = (
    "identifier-strategy",
    "data-classification",
    "versioning-policy",
    "status-promotion",
    "canonical-alignment",
    "authoring-source-primacy",
)

# Per-subject-area ADR mapping. Keyed by the directory under references/odcs/pc/
# and then by file slug (filename without `.odcs.yaml`). The slug-level entry
# names ADRs in addition to UNIVERSAL_ADRS plus shape-driven additions
# (temporal-modeling, codeset-strategy, currency-convention, etc.).
SUBJECT_AREA_ADRS: dict[str, dict[str, tuple[str, ...]]] = {
    "core": {
        "party": ("role-modeling", "separation-and-nesting", "null-semantics"),
        "party-relationship": ("role-modeling", "null-semantics"),
        "account": ("entity-boundaries", "null-semantics"),
        "account-relationship": ("entity-boundaries", "null-semantics"),
        "account-party-role": ("entity-boundaries", "role-modeling", "null-semantics"),
        "agreement": ("entity-boundaries", "null-semantics"),
    },
    "submission": {
        "submission": ("submission-modeling", "entity-boundaries", "null-semantics"),
        "submission-risk": ("submission-modeling", "null-semantics"),
        "submission-lifecycle-event": ("submission-modeling", "policy-lifecycle-modeling"),
        "submission-assessment": ("submission-modeling", "null-semantics"),
        "submission-document": ("submission-modeling", "separation-and-nesting", "null-semantics"),
        "submission-party-role": ("submission-modeling", "role-modeling", "null-semantics"),
    },
    "policy": {
        "policy": ("policy-lifecycle-modeling", "entity-boundaries", "null-semantics"),
        "policy-term": ("policy-lifecycle-modeling", "separation-and-nesting", "null-semantics"),
        "policy-document": ("separation-and-nesting", "null-semantics"),
        "policy-party-role": ("role-modeling", "null-semantics"),
        "policy-lifecycle-event": ("policy-lifecycle-modeling",),
        "policy-transaction": ("policy-lifecycle-modeling", "financial-modeling"),
    },
    "coverage": {
        "product": ("product-coverage-modeling", "null-semantics"),
        "coverage": ("product-coverage-modeling", "null-semantics"),
        "product-coverage": ("product-coverage-modeling", "null-semantics"),
        "policy-coverage": ("product-coverage-modeling", "null-semantics"),
        "policy-limit": ("product-coverage-modeling", "separation-and-nesting", "null-semantics"),
        "policy-deductible": ("product-coverage-modeling", "separation-and-nesting", "null-semantics"),
    },
    "exposure": {
        "exposure": ("exposure-modeling", "separation-and-nesting", "null-semantics"),
        "vehicle-exposure": ("exposure-modeling", "null-semantics"),
        "property-exposure": ("exposure-modeling", "null-semantics"),
        "workers-comp-exposure": ("exposure-modeling", "null-semantics"),
        "insurable-object": ("exposure-modeling", "null-semantics"),
        "insurable-object-classification": ("exposure-modeling", "separation-and-nesting", "null-semantics"),
        "insurable-object-party-role": ("exposure-modeling", "role-modeling", "null-semantics"),
    },
    "claims": {
        "claim": ("claims-modeling", "entity-boundaries", "null-semantics"),
        "claim-coverage": ("claims-modeling", "product-coverage-modeling", "null-semantics"),
        "claim-document": ("claims-modeling", "separation-and-nesting", "null-semantics"),
        "claim-feature": ("claims-modeling", "null-semantics"),
        "claim-financial-transaction": ("claims-modeling", "financial-modeling"),
        "claim-lifecycle-event": ("claims-modeling",),
        "claim-party-role": ("claims-modeling", "role-modeling", "null-semantics"),
        "occurrence": ("claims-modeling", "null-semantics"),
        "catastrophe": ("claims-modeling", "null-semantics"),
    },
    "financial": {
        "financial-transaction": ("financial-modeling",),
        "policy-financial-transaction": ("financial-modeling", "policy-lifecycle-modeling"),
    },
}

# Reference-data subject-area additions on top of UNIVERSAL_ADRS + codeset-strategy.
# Pure codesets get only `codeset-strategy`. Richer reference-data entities
# (line-of-business, transaction-type, lifecycle-*) carry additional ADRs that
# describe their richer shape.
REFERENCE_DATA_EXTRA_ADRS: dict[str, tuple[str, ...]] = {
    "line-of-business": ("entity-boundaries",),
    "transaction-type": ("entity-boundaries", "financial-modeling"),
    "lifecycle-event-type": ("entity-boundaries",),
    "lifecycle-status": ("entity-boundaries",),
    "geographic-location": ("entity-boundaries",),
    "location-address": ("entity-boundaries", "separation-and-nesting"),
    "financial-transaction-classification": ("financial-modeling",),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def slug_from_path(path: Path) -> str:
    return path.name.removesuffix(".odcs.yaml")


def subject_dir(path: Path) -> str:
    relative = path.relative_to(ROOT)
    parts = relative.parts
    # parts: ('references', 'odcs', 'pc', '<subject_dir>', '<file>.odcs.yaml')
    if len(parts) < 5:
        return ""
    return parts[3]


def schema_properties(data: dict[str, Any]) -> list[dict[str, Any]] | None:
    schema = data.get("schema")
    if not isinstance(schema, list) or not schema:
        return None
    entry = schema[0]
    if not isinstance(entry, dict):
        return None
    props = entry.get("properties")
    if not isinstance(props, list):
        return None
    return props


def has_field_with_suffix(properties: list[dict[str, Any]], suffix: str) -> bool:
    for prop in properties:
        if not isinstance(prop, dict):
            continue
        name = prop.get("name")
        if isinstance(name, str) and name.endswith(suffix):
            return True
    return False


def is_pure_codeset(path: Path, data: dict[str, Any]) -> bool:
    if path.parent != REFERENCE_DATA_DIR:
        return False
    custom = data.get("customProperties") or {}
    return bool(custom.get("codesetContract"))


def is_reference_data(path: Path) -> bool:
    return path.parent == REFERENCE_DATA_DIR


# ---------------------------------------------------------------------------
# ADR list construction
# ---------------------------------------------------------------------------


def compute_adrs(path: Path, data: dict[str, Any]) -> list[str]:
    slug = slug_from_path(path)
    properties = schema_properties(data) or []

    adrs: set[str] = set(UNIVERSAL_ADRS)

    # Shape-driven additions.
    if slug in EVENT_OR_TRANSACTION_SLUGS:
        adrs.add("temporal-modeling")
        adrs.add("event-and-transaction")
    else:
        # SCD2 entity (and also pure codesets / reference-data entities, which
        # carry the SCD2 system-time fields per codeset-strategy ADR).
        adrs.add("temporal-modeling")
        adrs.add("record-state")
        adrs.add("scd2-primary-key")

    if has_field_with_suffix(properties, "_amount"):
        adrs.add("currency-convention")

    if has_field_with_suffix(properties, "_code"):
        adrs.add("codeset-strategy")

    # Reference-data: always carry codeset-strategy.
    if is_reference_data(path):
        adrs.add("codeset-strategy")
        for extra in REFERENCE_DATA_EXTRA_ADRS.get(slug, ()):
            adrs.add(extra)

    # Subject-area-specific ADRs.
    sd = subject_dir(path)
    if sd in SUBJECT_AREA_ADRS:
        for extra in SUBJECT_AREA_ADRS[sd].get(slug, ()):
            adrs.add(extra)

    return sorted(adrs)


# ---------------------------------------------------------------------------
# customProperties update — preserve key order; insert `adrs` before `changelog`.
# ---------------------------------------------------------------------------


def upsert_adrs(data: dict[str, Any], adrs: list[str]) -> bool:
    custom = data.get("customProperties")
    if not isinstance(custom, dict):
        custom = {}
        data["customProperties"] = custom

    existing = custom.get("adrs")
    if isinstance(existing, list) and sorted(existing) == sorted(adrs):
        return False  # No change needed.

    # Rebuild customProperties preserving original insertion order, replacing or
    # inserting `adrs` immediately before `changelog`.
    rebuilt: dict[str, Any] = {}
    inserted = False
    for key, value in custom.items():
        if key == "adrs":
            continue  # Drop existing in-place; we re-insert at the canonical spot.
        if key == "changelog" and not inserted:
            rebuilt["adrs"] = adrs
            inserted = True
        rebuilt[key] = value
    if not inserted:
        rebuilt["adrs"] = adrs

    data["customProperties"] = rebuilt
    return True


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

    adrs = compute_adrs(path, data)
    changed = upsert_adrs(data, adrs)
    if not changed:
        return False, []

    new_text = dump_yaml(data)
    if new_text == text:
        return False, []
    path.write_text(new_text, encoding="utf-8")
    return True, [f"set adrs ({len(adrs)} entries)"]


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
