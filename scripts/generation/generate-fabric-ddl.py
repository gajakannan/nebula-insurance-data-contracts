#!/usr/bin/env python3
"""Generate Spark SQL CREATE TABLE IF NOT EXISTS files from Fabric manifests.

Reads ``targets/fabric/manifests/pc/**/*.fabric.yaml`` and emits one
``<slug>.spark.sql`` file per manifest under ``targets/fabric/ddl/pc/<area>/``.

Each emitted file:

- Carries a header comment naming the manifest path and the source contract
  path.
- Declares the Delta table with explicit columns and Spark SQL types from the
  manifest, with NOT NULL on non-nullable columns.
- Includes a per-column ``COMMENT`` derived from the contract field
  description.
- Sets the Delta table properties from
  ``fabric.table.delta.tableProperties``.
- Declares ``PARTITIONED BY`` from ``fabric.table.delta.partitionedBy``.
- Carries a table-level ``COMMENT`` that names ``Source: pc.<contract-id>
  v<version>`` for traceability.
- Carries a trailing ZORDER advisory comment when ``zorderBy`` is set.

DDL is provided as a convenience for consumers who wire up an external
schema-management workflow; the merge notebooks do not require pre-existing
tables. ``OPTIMIZE ... ZORDER`` is a runtime command and is therefore emitted
as a comment, not as part of ``CREATE TABLE``.

Authoritative spec: ``targets/fabric/conventions.md`` §8 and the Fabric plan
``planning-mds/FABRIC_IMPLEMENTATION_PLAN.md`` §11 / §17 (F5).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_GLOB = "targets/fabric/manifests/pc/**/*.fabric.yaml"
DDL_DIR_REL = Path("targets") / "fabric" / "ddl" / "pc"
DDL_DIR = ROOT / DDL_DIR_REL
LAKEHOUSE = "nebula_pc_silver"
INDENT = "  "

# Spark SQL types that may appear in the manifest. Surfaces generator drift if
# the manifest carries an unfamiliar type string.
ALLOWED_SPARK_TYPES = {
    "STRING",
    "INT",
    "BIGINT",
    "BOOLEAN",
    "DATE",
    "TIMESTAMP",
}
ALLOWED_PARAMETERIZED_PREFIXES = ("DECIMAL(",)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def _check_type(spark_type: str, *, manifest_path: Path, column_name: str) -> None:
    if spark_type in ALLOWED_SPARK_TYPES:
        return
    if any(spark_type.startswith(prefix) for prefix in ALLOWED_PARAMETERIZED_PREFIXES):
        return
    raise ValueError(
        f"{manifest_path}: column {column_name!r} has unrecognized sparkType "
        f"{spark_type!r}; extend ALLOWED_SPARK_TYPES."
    )


def _escape_sql(s: str) -> str:
    """Escape a string for use as a SQL single-quoted literal."""
    return s.replace("'", "''")


def _normalize(s: str) -> str:
    """Collapse whitespace; mainly for descriptions that wrap across YAML lines."""
    return " ".join(s.split())


def _render_property(key: str, value: Any) -> str:
    """Render a Delta TBLPROPERTIES key=value pair with both sides quoted."""
    if isinstance(value, bool):
        rendered = "true" if value else "false"
    else:
        rendered = str(value)
    return f"'{key}' = '{rendered}'"


def render_ddl(manifest: dict[str, Any], manifest_path: Path) -> str:
    contract = manifest.get("contract") or {}
    fabric = manifest.get("fabric") or {}
    generation = manifest.get("generation") or {}

    contract_id = contract.get("id") or ""
    contract_version = contract.get("version") or ""
    contract_description = _normalize(str(contract.get("description") or ""))
    contract_kind = contract.get("contractKind") or "entity"

    schema = fabric.get("schema") or ""
    table_block = fabric.get("table") or {}
    table_name = table_block.get("name") or ""
    delta = table_block.get("delta") or {}
    table_properties = delta.get("tableProperties") or {}
    partitioned_by = delta.get("partitionedBy") or []
    zorder_by = delta.get("zorderBy") or []

    columns = fabric.get("columns") or []
    if not schema or not table_name:
        raise ValueError(
            f"{manifest_path}: manifest is missing fabric.schema or fabric.table.name"
        )
    if not columns:
        raise ValueError(f"{manifest_path}: manifest has no columns")

    fq_table = f"{LAKEHOUSE}.{schema}.{table_name}"
    source_contract_path = generation.get("sourceContractPath") or ""
    manifest_rel = manifest_path.relative_to(ROOT).as_posix()

    out: list[str] = []
    out.append(f"-- Spark SQL DDL for {fq_table}")
    out.append(f"-- Generated from {manifest_rel}")
    if source_contract_path:
        out.append(
            f"-- Source: {contract_id} v{contract_version} ({source_contract_path})"
        )
    else:
        out.append(f"-- Source: {contract_id} v{contract_version}")
    out.append(f"-- Contract kind: {contract_kind}")
    out.append(
        "-- Do not edit by hand. Regenerate via "
        "scripts/generation/generate-fabric-ddl.py."
    )
    out.append("")

    out.append(f"CREATE TABLE IF NOT EXISTS {fq_table} (")

    column_lines: list[str] = []
    for column in columns:
        name = column.get("name")
        spark_type = column.get("sparkType")
        if not isinstance(name, str) or not isinstance(spark_type, str):
            raise ValueError(
                f"{manifest_path}: column missing name or sparkType: {column!r}"
            )
        _check_type(spark_type, manifest_path=manifest_path, column_name=name)
        nullable = bool(column.get("nullable", True))
        not_null = "" if nullable else " NOT NULL"
        description = _normalize(str(column.get("description") or ""))
        comment = (
            f" COMMENT '{_escape_sql(description)}'" if description else ""
        )
        column_lines.append(f"{INDENT}{name} {spark_type}{not_null}{comment}")

    out.append(",\n".join(column_lines))
    out.append(")")
    out.append("USING DELTA")

    if partitioned_by:
        cols = ", ".join(str(c) for c in partitioned_by)
        out.append(f"PARTITIONED BY ({cols})")

    table_comment_parts: list[str] = []
    if contract_description:
        table_comment_parts.append(contract_description)
    table_comment_parts.append(f"Source: {contract_id} v{contract_version}.")
    table_comment = " ".join(table_comment_parts)
    out.append(f"COMMENT '{_escape_sql(table_comment)}'")

    if table_properties:
        out.append("TBLPROPERTIES (")
        prop_lines: list[str] = []
        for key in sorted(table_properties.keys()):
            prop_lines.append(
                f"{INDENT}{_render_property(key, table_properties[key])}"
            )
        out.append(",\n".join(prop_lines))
        out.append(")")

    out[-1] = out[-1] + ";"

    if zorder_by:
        out.append("")
        out.append(
            "-- ZORDER hint (advisory; OPTIMIZE ... ZORDER is a runtime command):"
        )
        zorder_cols = ", ".join(str(c) for c in zorder_by)
        out.append(f"--   OPTIMIZE {fq_table} ZORDER BY ({zorder_cols});")

    return "\n".join(out) + "\n"


def _slug_from_manifest(path: Path) -> str:
    suffix = ".fabric.yaml"
    if not path.name.endswith(suffix):
        return path.stem
    return path.name[: -len(suffix)]


def main() -> int:
    paths = sorted(ROOT.glob(MANIFEST_GLOB))
    if not paths:
        print("error: no Fabric manifests found", file=sys.stderr)
        return 1

    written = 0
    by_kind: dict[str, int] = {}
    by_area: dict[str, int] = {}

    for path in paths:
        manifest = _load_yaml(path)
        if not manifest:
            continue
        ddl_text = render_ddl(manifest, path)

        contract = manifest.get("contract") or {}
        contract_kind = str(contract.get("contractKind") or "entity")
        by_kind[contract_kind] = by_kind.get(contract_kind, 0) + 1

        # Mirror the manifest's folder structure under ddl/pc/.
        area = path.parent.name
        by_area[area] = by_area.get(area, 0) + 1
        slug = _slug_from_manifest(path)

        target_dir = DDL_DIR / area
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{slug}.spark.sql"
        with target_path.open("w", encoding="utf-8") as handle:
            handle.write(ddl_text)
        written += 1

    print(f"Emitted {written} DDL file(s) under {DDL_DIR_REL.as_posix()}/.")
    if by_kind:
        kind_summary = ", ".join(
            f"{count} {kind}" for kind, count in sorted(by_kind.items())
        )
        print(f"By contract kind: {kind_summary}.")
    if by_area:
        area_summary = ", ".join(
            f"{count} {area}" for area, count in sorted(by_area.items())
        )
        print(f"By manifest area: {area_summary}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
