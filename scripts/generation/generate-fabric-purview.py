#!/usr/bin/env python3
"""Generate Fabric Purview manifests from canonical contracts and Fabric manifests.

Two outputs under `targets/fabric/purview/`:

- `sensitivity-labels.json` — column-level sensitivity manifest (Microsoft Purview
  sensitivity-label import format), one entry per Delta column across the entire
  Lakehouse, plus a table-level entry per contract carrying the contract's
  `classificationProfile` and a `complianceProfile: HIPAA` flag when the source
  contract sets `customProperties.subjectToHipaa: true`.
- `business-glossary.json` — canonical terms harvested from
  `references/glossary/pc/`, each linked to the column FQNs that match its
  `businessName`.

Authoritative spec: `targets/fabric/conventions.md` §11, plan
`planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` §15.3 / §17 (F4).
"""

from __future__ import annotations

import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_GLOB = "references/odcs/pc/**/*.odcs.yaml"
MANIFEST_GLOB = "targets/fabric/manifests/pc/**/*.fabric.yaml"
GLOSSARY_DIR = ROOT / "references" / "glossary" / "pc"
PURVIEW_DIR = ROOT / "targets" / "fabric" / "purview"

LAKEHOUSE = "nebula_pc_silver"
SCHEMA_VERSION = "1.0"

CANONICAL_TO_PURVIEW = {
    "PUBLIC": "Public",
    "INTERNAL": "Internal",
    "CONFIDENTIAL": "Confidential",
    "RESTRICTED": "Restricted",
}


# ---------------------------------------------------------------------------
# Inputs.
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def load_manifests() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in sorted(ROOT.glob(MANIFEST_GLOB)):
        data = _load_yaml(path)
        if data:
            out.append(data)
    return out


def load_contract_business_names() -> dict[tuple[str, str], str]:
    """Index (contract_id, column_name) -> businessName for glossary linking."""
    index: dict[tuple[str, str], str] = {}
    for path in sorted(ROOT.glob(CONTRACT_GLOB)):
        data = _load_yaml(path)
        contract_id = data.get("id")
        if not isinstance(contract_id, str):
            continue
        schema = data.get("schema") or []
        if not isinstance(schema, list) or not schema:
            continue
        first = schema[0]
        if not isinstance(first, dict):
            continue
        for prop in first.get("properties") or []:
            if not isinstance(prop, dict):
                continue
            name = prop.get("name")
            business = prop.get("businessName")
            if isinstance(name, str) and isinstance(business, str):
                index[(contract_id, name)] = business
    return index


# ---------------------------------------------------------------------------
# Glossary parsing.
# ---------------------------------------------------------------------------


GITHUB_SLUG_STRIP = re.compile(r"[^a-z0-9 -]")


def _github_slug(text: str) -> str:
    lowered = text.strip().lower()
    cleaned = GITHUB_SLUG_STRIP.sub("", lowered)
    return cleaned.replace(" ", "-")


def _harvest_terms(path: Path) -> list[dict[str, str]]:
    """Harvest glossary terms from a markdown file.

    Cross-cutting style: terms are h3 (`### Term`) under h2 sections (`## Section`).
    Area-file style: terms are h2 (`## Term`) directly under the file's h1.

    A file mixing both is supported: an h2 block that contains any h3 children is
    treated as a section (h3s become terms, the h2 itself is not a term); an h2
    block with no h3 children is itself a term.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    h2_blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            current = None
            continue
        if line.startswith("## ") and not line.startswith("### "):
            if current is not None:
                h2_blocks.append(current)
            current = {
                "title": line[3:].strip(),
                "buffer": [],
                "h3s": [],
            }
            continue
        if line.startswith("### ") and current is not None:
            current["h3s"].append({"title": line[4:].strip(), "buffer": []})
            continue
        if current is None:
            continue
        if current["h3s"]:
            current["h3s"][-1]["buffer"].append(line)
        else:
            current["buffer"].append(line)
    if current is not None:
        h2_blocks.append(current)

    terms: list[dict[str, str]] = []
    for block in h2_blocks:
        if block["h3s"]:
            for h3 in block["h3s"]:
                definition = _first_paragraph(h3["buffer"])
                if not definition:
                    continue
                terms.append({"name": h3["title"], "definition": definition})
        else:
            definition = _first_paragraph(block["buffer"])
            if not definition:
                continue
            terms.append({"name": block["title"], "definition": definition})
    return terms


def _first_paragraph(buffer: list[str]) -> str:
    paragraph: list[str] = []
    for line in buffer:
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith("```") or stripped.startswith("|"):
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    return " ".join(paragraph)


def load_glossary() -> list[dict[str, Any]]:
    """Return [{name, definition, category, sourcePath, anchor}, ...]."""
    if not GLOSSARY_DIR.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(GLOSSARY_DIR.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        category = path.stem
        rel = path.relative_to(ROOT).as_posix()
        for term in _harvest_terms(path):
            anchor = _github_slug(term["name"])
            out.append(
                {
                    "name": term["name"],
                    "definition": term["definition"],
                    "category": category,
                    "sourcePath": f"{rel}#{anchor}",
                }
            )
    return out


# ---------------------------------------------------------------------------
# Sensitivity manifest.
# ---------------------------------------------------------------------------


def _table_fqn(schema: str, table: str) -> str:
    return f"Lakehouse://{LAKEHOUSE}/Tables/{schema}/{table}"


def _column_fqn(schema: str, table: str, column: str) -> str:
    return f"Lakehouse://{LAKEHOUSE}/Tables/{schema}/{table}/{column}"


def _purview_label(sensitivity: str | None) -> str:
    if not isinstance(sensitivity, str):
        return "Internal"
    return CANONICAL_TO_PURVIEW.get(sensitivity, "Internal")


def build_sensitivity_manifest(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    tables: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []

    for manifest in manifests:
        contract = manifest.get("contract") or {}
        fabric = manifest.get("fabric") or {}
        schema = fabric.get("schema") or ""
        table_block = fabric.get("table") or {}
        table_name = table_block.get("name") or ""
        if not schema or not table_name:
            continue

        contract_id = contract.get("id") or ""
        contract_version = contract.get("version") or ""
        contract_profile = contract.get("classificationProfile") or "INTERNAL"
        subject_to_hipaa = bool(contract.get("subjectToHipaa", False))

        table_entry: dict[str, Any] = {
            "fullyQualifiedName": _table_fqn(schema, table_name),
            "sourceContract": contract_id,
            "sourceContractVersion": contract_version,
            "classificationProfile": contract_profile,
            "purviewLabel": _purview_label(contract_profile),
        }
        if subject_to_hipaa:
            table_entry["complianceProfile"] = "HIPAA"
        tables.append(table_entry)

        for column in fabric.get("columns") or []:
            if not isinstance(column, dict):
                continue
            name = column.get("name")
            if not isinstance(name, str):
                continue
            classifications = column.get("classifications") or {}
            sensitivity = classifications.get("sensitivity")
            tags = classifications.get("regulatoryTags") or []
            tags_out: list[str] = [t for t in tags if isinstance(t, str)]
            entry: dict[str, Any] = {
                "fullyQualifiedName": _column_fqn(schema, table_name, name),
                "sensitivityLabel": _purview_label(sensitivity),
                "regulatoryTags": tags_out,
                "sourceContract": contract_id,
                "sourceContractVersion": contract_version,
            }
            if subject_to_hipaa:
                entry["complianceProfile"] = "HIPAA"
            labels.append(entry)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "lakehouse": LAKEHOUSE,
        "tables": tables,
        "labels": labels,
    }


# ---------------------------------------------------------------------------
# Business glossary.
# ---------------------------------------------------------------------------


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _column_index(
    manifests: list[dict[str, Any]],
    business_names: dict[tuple[str, str], str],
) -> dict[str, list[str]]:
    """Map normalized businessName -> list of column FQNs."""
    index: dict[str, list[str]] = {}
    for manifest in manifests:
        contract = manifest.get("contract") or {}
        fabric = manifest.get("fabric") or {}
        contract_id = contract.get("id") or ""
        schema = fabric.get("schema") or ""
        table_block = fabric.get("table") or {}
        table_name = table_block.get("name") or ""
        if not contract_id or not schema or not table_name:
            continue
        for column in fabric.get("columns") or []:
            if not isinstance(column, dict):
                continue
            name = column.get("name")
            if not isinstance(name, str):
                continue
            business = business_names.get((contract_id, name))
            if not business:
                continue
            index.setdefault(_norm(business), []).append(
                _column_fqn(schema, table_name, name)
            )
    return index


def _contract_term_index(manifests: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Map normalized contract `name` -> list of table FQNs.

    Lets glossary terms whose name matches a contract name (e.g. `## Policy`)
    bind to the entire table FQN even though no column carries the bare term as
    its `businessName`.
    """
    index: dict[str, list[str]] = {}
    for manifest in manifests:
        contract = manifest.get("contract") or {}
        fabric = manifest.get("fabric") or {}
        name = contract.get("name") or ""
        schema = fabric.get("schema") or ""
        table_block = fabric.get("table") or {}
        table_name = table_block.get("name") or ""
        if not name or not schema or not table_name:
            continue
        index.setdefault(_norm(name), []).append(_table_fqn(schema, table_name))
    return index


def build_glossary_manifest(
    glossary: list[dict[str, Any]],
    manifests: list[dict[str, Any]],
    business_names: dict[tuple[str, str], str],
) -> dict[str, Any]:
    column_index = _column_index(manifests, business_names)
    contract_index = _contract_term_index(manifests)

    # Deduplicate same term name across files: cross-cutting wins; otherwise
    # first-seen wins.  Order preserves cross-cutting first, then alpha-by-file.
    seen: OrderedDict[str, dict[str, Any]] = OrderedDict()
    cross_cutting: list[dict[str, Any]] = []
    others: list[dict[str, Any]] = []
    for term in glossary:
        if term["category"] == "cross-cutting":
            cross_cutting.append(term)
        else:
            others.append(term)

    terms_out: list[dict[str, Any]] = []
    for term in cross_cutting + others:
        norm = _norm(term["name"])
        if norm in seen:
            continue
        column_fqns = list(column_index.get(norm, []))
        table_fqns = list(contract_index.get(norm, []))
        entry = {
            "name": term["name"],
            "definition": term["definition"],
            "category": term["category"],
            "sourcePath": term["sourcePath"],
            "columnFQNs": sorted(column_fqns),
            "tableFQNs": sorted(table_fqns),
        }
        seen[norm] = entry
        terms_out.append(entry)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "lakehouse": LAKEHOUSE,
        "terms": terms_out,
    }


# ---------------------------------------------------------------------------
# Output.
# ---------------------------------------------------------------------------


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main() -> int:
    manifests = load_manifests()
    if not manifests:
        print("error: no Fabric manifests found", file=sys.stderr)
        return 1

    business_names = load_contract_business_names()
    glossary = load_glossary()

    sensitivity = build_sensitivity_manifest(manifests)
    business_glossary = build_glossary_manifest(glossary, manifests, business_names)

    sensitivity_path = PURVIEW_DIR / "sensitivity-labels.json"
    glossary_path = PURVIEW_DIR / "business-glossary.json"
    _write_json(sensitivity_path, sensitivity)
    _write_json(glossary_path, business_glossary)

    rel_sens = sensitivity_path.relative_to(ROOT).as_posix()
    rel_gloss = glossary_path.relative_to(ROOT).as_posix()
    table_count = len(sensitivity["tables"])
    label_count = len(sensitivity["labels"])
    term_count = len(business_glossary["terms"])
    bound_terms = sum(
        1
        for t in business_glossary["terms"]
        if t["columnFQNs"] or t["tableFQNs"]
    )
    print(
        f"Emitted {rel_sens}: {table_count} tables, {label_count} column labels."
    )
    print(
        f"Emitted {rel_gloss}: {term_count} terms ({bound_terms} bound to FQNs)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
