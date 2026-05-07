#!/usr/bin/env python3
"""Validate Fabric manifests for drift against canonical ODCS contracts.

Implements the 17 drift checks listed in `targets/fabric/manifest-schema.md` §9
and `planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` §16. A drifted manifest fails;
the fix is to re-run `scripts/generation/generate-fabric-manifests.py`. Manifests
are never edited by hand.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_GLOB = "references/odcs/pc/**/*.odcs.yaml"
MANIFEST_GLOB = "targets/fabric/manifests/pc/**/*.fabric.yaml"
MANIFEST_ROOT = ROOT / "targets" / "fabric" / "manifests" / "pc"
CONTRACT_ROOT = ROOT / "references" / "odcs" / "pc"

ALLOWED_SPARK_TYPES = {"STRING", "INT", "BIGINT", "BOOLEAN", "DATE", "TIMESTAMP"}
DECIMAL_RE = re.compile(r"^DECIMAL\(\d+,\s*\d+\)$")

LOGICAL_TO_SPARK = {
    "string": {"STRING"},
    "integer": {"INT", "BIGINT"},
    "decimal": {"DECIMAL"},  # special-cased via DECIMAL_RE
    "boolean": {"BOOLEAN"},
    "date": {"DATE"},
    "datetime": {"TIMESTAMP"},
    "timestamp": {"TIMESTAMP"},
    "uuid": {"STRING"},
}

EVENT_SLUG_SUFFIX = "-lifecycle-event"
TRANSACTION_SLUG_SUFFIX = "-transaction"
TRANSACTION_EXACT_SLUGS = {
    "financial-transaction",
    "policy-financial-transaction",
    "claim-financial-transaction",
}

VALID_ROLES = {
    "identity",
    "business-key",
    "source-attribution",
    "source-time",
    "scd2-valid-from",
    "scd2-valid-to",
    "scd2-is-current",
    "record-state",
    "foreign-key",
    "code-reference",
    "monetary-amount",
    "monetary-currency",
    "data",
    "event-correction-flag",
    "event-corrects-ref",
    "lifecycle-event-link",
}

ENTITY_REQUIRED_ROLES = {
    "scd2-valid-from",
    "scd2-valid-to",
    "scd2-is-current",
    "record-state",
}

APPEND_ONLY_REQUIRED_ROLES = {
    "event-correction-flag",
    "event-corrects-ref",
}

APPEND_ONLY_FORBIDDEN_NAMES = {
    "valid_from_datetime",
    "valid_to_datetime",
    "is_current_indicator",
    "record_status_code",
    "source_created_datetime",
    "source_updated_datetime",
}


class Finding:
    def __init__(self, location: str, message: str, severity: str = "error") -> None:
        self.location = location
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        return f"[{self.severity}] {self.location}: {self.message}"


# ---------------------------------------------------------------------------
# Loading helpers.
# ---------------------------------------------------------------------------


def _yaml_load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _expected_kind(path: Path) -> str:
    slug = path.name.removesuffix(".odcs.yaml")
    if path.parent.name == "reference-data":
        return "codeset"
    if slug.endswith(EVENT_SLUG_SUFFIX):
        return "event"
    if slug.endswith(TRANSACTION_SLUG_SUFFIX) or slug in TRANSACTION_EXACT_SLUGS:
        return "transaction"
    return "entity"


def _load_contract_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in sorted(ROOT.glob(CONTRACT_GLOB)):
        try:
            data = _yaml_load(path)
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and isinstance(data.get("id"), str):
            index[data["id"]] = path
    return index


def _expected_manifest_path(contract_path: Path) -> Path:
    rel = contract_path.relative_to(ROOT)
    area = rel.parts[3] if len(rel.parts) > 4 else ""
    slug = contract_path.name.removesuffix(".odcs.yaml")
    return MANIFEST_ROOT / area / f"{slug}.fabric.yaml"


def _expected_contract_path(manifest_path: Path) -> Path:
    rel = manifest_path.relative_to(MANIFEST_ROOT)
    area = rel.parts[0] if len(rel.parts) > 1 else ""
    slug = manifest_path.name.removesuffix(".fabric.yaml")
    return CONTRACT_ROOT / area / f"{slug}.odcs.yaml"


# ---------------------------------------------------------------------------
# Per-manifest checks.
# ---------------------------------------------------------------------------


def _columns(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    fabric = manifest.get("fabric")
    if not isinstance(fabric, dict):
        return []
    cols = fabric.get("columns")
    return [c for c in cols if isinstance(c, dict)] if isinstance(cols, list) else []


def _contract_properties(contract: dict[str, Any]) -> list[dict[str, Any]]:
    schema = contract.get("schema")
    if not isinstance(schema, list) or not schema:
        return []
    entry = schema[0]
    if not isinstance(entry, dict):
        return []
    props = entry.get("properties")
    return [p for p in props if isinstance(p, dict)] if isinstance(props, list) else []


def _check_path_and_id(
    rel_loc: str, manifest: dict[str, Any], manifest_path: Path
) -> list[Finding]:
    findings: list[Finding] = []
    contract_block = manifest.get("contract") or {}
    cid = contract_block.get("id") if isinstance(contract_block, dict) else None
    slug = manifest_path.name.removesuffix(".fabric.yaml")
    expected_id = f"pc.{slug}"
    if cid != expected_id:
        findings.append(
            Finding(rel_loc, f"contract.id `{cid}` does not match path slug; expected `{expected_id}` (check 4)")
        )
    return findings


def _check_version(rel_loc: str, manifest: dict[str, Any], contract: dict[str, Any]) -> list[Finding]:
    block = manifest.get("contract") or {}
    mver = block.get("version") if isinstance(block, dict) else None
    cver = contract.get("version")
    if mver != cver:
        return [Finding(rel_loc, f"contract.version `{mver}` does not match source `{cver}` (check 3)")]
    return []


def _check_digest(
    rel_loc: str, manifest: dict[str, Any], contract_path: Path
) -> list[Finding]:
    gen = manifest.get("generation")
    if not isinstance(gen, dict):
        return [Finding(rel_loc, "generation block missing or not a mapping (check 5)")]
    actual = gen.get("sourceContractDigest")
    expected = _digest(contract_path)
    if actual != expected:
        return [Finding(rel_loc, f"sourceContractDigest `{actual}` does not match recomputed `{expected}` (check 5)")]
    return []


def _check_kind(rel_loc: str, manifest: dict[str, Any], contract_path: Path) -> list[Finding]:
    block = manifest.get("contract") or {}
    declared = block.get("contractKind") if isinstance(block, dict) else None
    expected = _expected_kind(contract_path)
    if declared != expected:
        return [Finding(rel_loc, f"contract.contractKind `{declared}` does not match path-derived `{expected}` (check 6)")]
    return []


def _check_mutual_exclusion(rel_loc: str, manifest: dict[str, Any]) -> list[Finding]:
    fabric = manifest.get("fabric") or {}
    scd2_enabled = bool((fabric.get("scd2") or {}).get("enabled"))
    append_enabled = bool((fabric.get("appendOnly") or {}).get("enabled"))
    if scd2_enabled and append_enabled:
        return [Finding(rel_loc, "scd2.enabled and appendOnly.enabled cannot both be true (check 7)")]
    return []


def _check_required_scd2_columns(
    rel_loc: str, manifest: dict[str, Any]
) -> list[Finding]:
    fabric = manifest.get("fabric") or {}
    if not (fabric.get("scd2") or {}).get("enabled"):
        return []
    findings: list[Finding] = []
    by_role: dict[str, list[str]] = {}
    for col in _columns(manifest):
        by_role.setdefault(col.get("role", ""), []).append(col.get("name", ""))
    for required in ("scd2-valid-from", "scd2-valid-to", "scd2-is-current"):
        cols = by_role.get(required, [])
        if len(cols) != 1:
            findings.append(
                Finding(rel_loc, f"scd2 enabled but role `{required}` is satisfied by {cols} (check 8)")
            )
    return findings


def _check_required_append_columns(
    rel_loc: str, manifest: dict[str, Any]
) -> list[Finding]:
    fabric = manifest.get("fabric") or {}
    if not (fabric.get("appendOnly") or {}).get("enabled"):
        return []
    findings: list[Finding] = []
    by_role: dict[str, list[str]] = {}
    for col in _columns(manifest):
        by_role.setdefault(col.get("role", ""), []).append(col.get("name", ""))
    for required in APPEND_ONLY_REQUIRED_ROLES:
        cols = by_role.get(required, [])
        if len(cols) != 1:
            findings.append(
                Finding(rel_loc, f"appendOnly enabled but role `{required}` is satisfied by {cols} (check 9)")
            )
    return findings


def _check_forbidden_append_columns(
    rel_loc: str, manifest: dict[str, Any]
) -> list[Finding]:
    fabric = manifest.get("fabric") or {}
    if not (fabric.get("appendOnly") or {}).get("enabled"):
        return []
    findings: list[Finding] = []
    column_names = {col.get("name", "") for col in _columns(manifest)}
    for forbidden in APPEND_ONLY_FORBIDDEN_NAMES:
        if forbidden in column_names:
            findings.append(
                Finding(rel_loc, f"appendOnly contract must not include column `{forbidden}` (check 10)")
            )
    return findings


def _check_spark_types(rel_loc: str, manifest: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for col in _columns(manifest):
        spark = col.get("sparkType")
        name = col.get("name", "<unknown>")
        if not isinstance(spark, str):
            findings.append(Finding(rel_loc, f"column `{name}` missing sparkType (check 11)"))
            continue
        if spark not in ALLOWED_SPARK_TYPES and not DECIMAL_RE.match(spark):
            findings.append(
                Finding(rel_loc, f"column `{name}` sparkType `{spark}` not in allowed set (check 11)")
            )
    return findings


def _check_type_derivation(
    rel_loc: str, manifest: dict[str, Any], contract: dict[str, Any]
) -> list[Finding]:
    findings: list[Finding] = []
    src_by_name = {p.get("name"): p for p in _contract_properties(contract) if isinstance(p.get("name"), str)}
    for col in _columns(manifest):
        name = col.get("name")
        spark = col.get("sparkType")
        src = src_by_name.get(name)
        if src is None:
            findings.append(Finding(rel_loc, f"column `{name}` not present in source contract (check 12)"))
            continue
        logical = src.get("logicalType")
        if not isinstance(logical, str):
            continue
        allowed = LOGICAL_TO_SPARK.get(logical)
        if allowed is None:
            findings.append(Finding(rel_loc, f"column `{name}` source logicalType `{logical}` is not mapped (check 12)"))
            continue
        if logical == "decimal":
            if not isinstance(spark, str) or not DECIMAL_RE.match(spark):
                findings.append(Finding(rel_loc, f"column `{name}` decimal sparkType `{spark}` invalid (check 12)"))
        else:
            if spark not in allowed:
                findings.append(
                    Finding(rel_loc, f"column `{name}` sparkType `{spark}` does not match logicalType `{logical}` (check 12)")
                )
    return findings


def _check_nullability(
    rel_loc: str, manifest: dict[str, Any], contract: dict[str, Any]
) -> list[Finding]:
    findings: list[Finding] = []
    src_by_name = {p.get("name"): p for p in _contract_properties(contract) if isinstance(p.get("name"), str)}
    fabric = manifest.get("fabric") or {}
    is_append = bool((fabric.get("appendOnly") or {}).get("enabled"))
    for col in _columns(manifest):
        name = col.get("name")
        nullable = col.get("nullable")
        is_pk = col.get("primaryKey") is True
        src = src_by_name.get(name) or {}
        required = src.get("required") is True
        # Hard rules per type-mapping.md §3.
        if is_pk and nullable is not False:
            findings.append(Finding(rel_loc, f"PK column `{name}` must be nullable=false (check 13)"))
            continue
        if name == "valid_from_datetime" and nullable is not False:
            findings.append(Finding(rel_loc, "valid_from_datetime must be non-null (check 13)"))
            continue
        if name == "valid_to_datetime" and nullable is not True:
            findings.append(Finding(rel_loc, "valid_to_datetime must be nullable (check 13)"))
            continue
        if name == "is_current_indicator" and nullable is not False:
            findings.append(Finding(rel_loc, "is_current_indicator must be non-null (check 13)"))
            continue
        if name == "record_status_code" and not is_append and nullable is not False:
            findings.append(Finding(rel_loc, "record_status_code must be non-null (check 13)"))
            continue
        if name == "correction_indicator" and is_append and nullable is not False:
            findings.append(Finding(rel_loc, "correction_indicator must be non-null on append-only contracts (check 13)"))
            continue
        # Default: track ODCS `required`.
        if name in {"valid_from_datetime", "valid_to_datetime", "is_current_indicator", "record_status_code", "correction_indicator"}:
            continue
        expected_nullable = not required
        if nullable != expected_nullable:
            findings.append(
                Finding(rel_loc, f"column `{name}` nullable=`{nullable}` does not match source required=`{required}` (check 13)")
            )
    return findings


def _check_role_coverage(rel_loc: str, manifest: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    fabric = manifest.get("fabric") or {}
    is_append = bool((fabric.get("appendOnly") or {}).get("enabled"))
    is_scd2 = bool((fabric.get("scd2") or {}).get("enabled"))
    by_role: dict[str, list[str]] = {}
    for col in _columns(manifest):
        role = col.get("role")
        if role not in VALID_ROLES:
            findings.append(Finding(rel_loc, f"column `{col.get('name')}` has unknown role `{role}` (check 14)"))
            continue
        by_role.setdefault(role, []).append(col.get("name", ""))
    if is_scd2:
        for required in ENTITY_REQUIRED_ROLES:
            cols = by_role.get(required, [])
            if len(cols) != 1:
                findings.append(
                    Finding(rel_loc, f"entity/codeset contract must have exactly one `{required}` column; got {cols} (check 14)")
                )
        identity_cols = by_role.get("identity", [])
        if len(identity_cols) != 1:
            findings.append(
                Finding(rel_loc, f"entity/codeset contract must have exactly one `identity` column; got {identity_cols} (check 14)")
            )
    if is_append:
        for required in APPEND_ONLY_REQUIRED_ROLES:
            cols = by_role.get(required, [])
            if len(cols) != 1:
                findings.append(
                    Finding(rel_loc, f"event/transaction contract must have exactly one `{required}` column; got {cols} (check 14)")
                )
    return findings


def _check_foreign_key_resolution(
    rel_loc: str, manifest: dict[str, Any], contract_index: dict[str, Path]
) -> list[Finding]:
    findings: list[Finding] = []
    for col in _columns(manifest):
        if col.get("role") != "foreign-key":
            continue
        block = col.get("foreignKey")
        if not isinstance(block, dict):
            findings.append(Finding(rel_loc, f"foreign-key column `{col.get('name')}` missing foreignKey block (check 15)"))
            continue
        target = block.get("targetContract")
        if target not in contract_index:
            findings.append(
                Finding(rel_loc, f"foreign-key column `{col.get('name')}` targetContract `{target}` does not resolve (check 15)")
            )
    return findings


def _check_code_reference_resolution(
    rel_loc: str, manifest: dict[str, Any], contract_index: dict[str, Path]
) -> list[Finding]:
    findings: list[Finding] = []
    for col in _columns(manifest):
        block = col.get("codeReference")
        if not isinstance(block, dict):
            continue
        codeset = block.get("codeset")
        if codeset not in contract_index:
            findings.append(
                Finding(rel_loc, f"codeReference on column `{col.get('name')}` codeset `{codeset}` does not resolve (check 16)")
            )
            continue
        target_path = contract_index[codeset]
        if target_path.parent.name != "reference-data":
            findings.append(
                Finding(rel_loc, f"codeReference codeset `{codeset}` does not point at a reference-data contract (check 16)")
            )
    return findings


def _check_currency_pair(rel_loc: str, manifest: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    columns = _columns(manifest)
    name_to_role = {c.get("name"): c.get("role") for c in columns}
    for col in columns:
        if col.get("role") != "monetary-amount":
            continue
        pair = col.get("currencyPair")
        if not isinstance(pair, dict):
            findings.append(
                Finding(rel_loc, f"monetary-amount column `{col.get('name')}` missing currencyPair block (check 17)")
            )
            continue
        paired = pair.get("pairedColumn")
        if name_to_role.get(paired) != "monetary-currency":
            findings.append(
                Finding(rel_loc, f"currencyPair pairedColumn `{paired}` is not a monetary-currency role on the same table (check 17)")
            )
    return findings


# ---------------------------------------------------------------------------
# Top-level check orchestration.
# ---------------------------------------------------------------------------


def check_manifest(
    manifest_path: Path, contract_index: dict[str, Path]
) -> list[Finding]:
    rel_loc = manifest_path.relative_to(ROOT).as_posix()
    findings: list[Finding] = []

    try:
        manifest = _yaml_load(manifest_path)
    except yaml.YAMLError as exc:
        return [Finding(rel_loc, f"YAML parse error: {exc}")]
    if not isinstance(manifest, dict):
        return [Finding(rel_loc, "manifest must be a YAML mapping")]

    expected_contract = _expected_contract_path(manifest_path)
    if not expected_contract.exists():
        findings.append(Finding(rel_loc, f"no contract at expected path `{expected_contract.relative_to(ROOT).as_posix()}` (check 1/2)"))
        return findings

    try:
        contract = _yaml_load(expected_contract)
    except yaml.YAMLError as exc:
        return [Finding(rel_loc, f"source contract YAML parse error: {exc}")]
    if not isinstance(contract, dict):
        return [Finding(rel_loc, "source contract is not a YAML mapping")]

    findings.extend(_check_path_and_id(rel_loc, manifest, manifest_path))
    findings.extend(_check_version(rel_loc, manifest, contract))
    findings.extend(_check_digest(rel_loc, manifest, expected_contract))
    findings.extend(_check_kind(rel_loc, manifest, expected_contract))
    findings.extend(_check_mutual_exclusion(rel_loc, manifest))
    findings.extend(_check_required_scd2_columns(rel_loc, manifest))
    findings.extend(_check_required_append_columns(rel_loc, manifest))
    findings.extend(_check_forbidden_append_columns(rel_loc, manifest))
    findings.extend(_check_spark_types(rel_loc, manifest))
    findings.extend(_check_type_derivation(rel_loc, manifest, contract))
    findings.extend(_check_nullability(rel_loc, manifest, contract))
    findings.extend(_check_role_coverage(rel_loc, manifest))
    findings.extend(_check_foreign_key_resolution(rel_loc, manifest, contract_index))
    findings.extend(_check_code_reference_resolution(rel_loc, manifest, contract_index))
    findings.extend(_check_currency_pair(rel_loc, manifest))
    return findings


def check_coverage(
    manifests: Iterable[Path],
    contract_index: dict[str, Path],
    require_full_coverage: bool,
) -> list[Finding]:
    findings: list[Finding] = []
    seen_contract_ids: set[str] = set()
    for manifest_path in manifests:
        slug = manifest_path.name.removesuffix(".fabric.yaml")
        rel = manifest_path.relative_to(MANIFEST_ROOT)
        area = rel.parts[0] if len(rel.parts) > 1 else ""
        cid = f"pc.{slug}"
        seen_contract_ids.add(cid)
        if cid not in contract_index:
            findings.append(
                Finding(manifest_path.relative_to(ROOT).as_posix(), f"manifest has no corresponding contract (check 1)")
            )
        else:
            expected_manifest = _expected_manifest_path(contract_index[cid])
            if expected_manifest != manifest_path:
                findings.append(
                    Finding(
                        manifest_path.relative_to(ROOT).as_posix(),
                        f"manifest path does not mirror contract path; expected `{expected_manifest.relative_to(ROOT).as_posix()}` (check 2)",
                    )
                )

    if require_full_coverage:
        for cid, contract_path in contract_index.items():
            if cid not in seen_contract_ids:
                expected_manifest = _expected_manifest_path(contract_path)
                findings.append(
                    Finding(
                        contract_path.relative_to(ROOT).as_posix(),
                        f"contract has no manifest at `{expected_manifest.relative_to(ROOT).as_posix()}` (check 1)",
                    )
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Fabric manifests against canonical ODCS contracts.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional manifest files or directories to validate. Defaults to all manifests under targets/fabric/manifests/pc/.",
    )
    parser.add_argument(
        "--require-full-coverage",
        action="store_true",
        help="Fail when any canonical contract lacks a manifest. Off by default during F2 (only Policy is emitted); on for F3+.",
    )
    args = parser.parse_args()

    if args.paths:
        manifests: list[Path] = []
        for raw in args.paths:
            path = Path(raw)
            if not path.is_absolute():
                path = ROOT / path
            if path.is_dir():
                manifests.extend(sorted(path.glob("**/*.fabric.yaml")))
            elif path.exists():
                manifests.append(path)
            else:
                print(f"warning: path `{raw}` does not exist", file=sys.stderr)
        manifests = sorted({p.resolve() for p in manifests})
    else:
        manifests = sorted(ROOT.glob(MANIFEST_GLOB))

    contract_index = _load_contract_index()

    all_findings: list[Finding] = []
    all_findings.extend(check_coverage(manifests, contract_index, args.require_full_coverage))
    for manifest_path in manifests:
        all_findings.extend(check_manifest(manifest_path, contract_index))

    if not manifests:
        print("No manifests found.")
        if args.require_full_coverage and contract_index:
            print(f"FAILED: --require-full-coverage set but {len(contract_index)} contract(s) lack manifests.")
            return 1
        return 0

    errors = [f for f in all_findings if f.severity == "error"]
    warnings = [f for f in all_findings if f.severity == "warning"]

    if all_findings:
        status = "FAILED" if errors else "PASSED with warnings"
        print(f"Validated {len(manifests)} manifest(s): {status} ({len(errors)} errors, {len(warnings)} warnings)")
        for finding in all_findings:
            print(f"- {finding}")
        return 1 if errors else 0

    print(f"Validated {len(manifests)} manifest(s): OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
