#!/usr/bin/env python3
"""Generate Fabric manifests from canonical ODCS contracts.

One manifest per contract, mirroring the source path under
`targets/fabric/manifests/pc/<area>/<slug>.fabric.yaml`. The manifest is the
single intermediate artifact that drives every downstream Fabric file (Delta
DDL, SCD2 / append / codeset notebooks at runtime, Purview labels, glossary).

Authoritative spec: `targets/fabric/manifest-schema.md`,
`targets/fabric/conventions.md`, `targets/fabric/type-mapping.md`. Plan:
`planning-mds/FABRIC_IMPLEMENTATION_PLAN.md` §15.1.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_GLOB = "references/odcs/pc/**/*.odcs.yaml"
MANIFEST_ROOT = ROOT / "targets" / "fabric" / "manifests" / "pc"

GENERATOR_VERSION = "1.0.0"
MANIFEST_VERSION = "1.0.0"
LAKEHOUSE_NAME = "nebula_pc_silver"
REFERENCE_DATA_SCHEMA = "silver_reference_data"

# Slugs that map to append-only event/transaction kinds. Mirrors
# `EVENT_OR_TRANSACTION_SLUGS` in the contract validator.
EVENT_SLUG_SUFFIX = "-lifecycle-event"
TRANSACTION_SLUG_SUFFIX = "-transaction"
TRANSACTION_EXACT_SLUGS = {
    "financial-transaction",
    "policy-financial-transaction",
    "claim-financial-transaction",
}

SENSITIVITY_TO_PURVIEW = {
    "PUBLIC": "Public",
    "INTERNAL": "Internal",
    "CONFIDENTIAL": "Confidential",
    "RESTRICTED": "Restricted",
}

LOGICAL_TYPE_TO_SPARK = {
    "string": "STRING",
    "integer": "INT",
    "decimal": "DECIMAL(18, 2)",
    "boolean": "BOOLEAN",
    "date": "DATE",
    "datetime": "TIMESTAMP",
    "timestamp": "TIMESTAMP",
    "uuid": "STRING",
}

SOURCE_ATTRIBUTION_NAMES = {"source_system_code", "source_natural_key"}
SOURCE_TIME_NAMES = {"source_created_datetime", "source_updated_datetime"}
SCD2_FIELDS = ("valid_from_datetime", "valid_to_datetime", "is_current_indicator")
RECORD_STATE_FIELD = "record_status_code"
CORRECTION_FIELD = "correction_indicator"
LIFECYCLE_EVENT_LINK_FIELD = "lifecycle_event_uid"

EVENT_BUSINESS_TIME = "event_datetime"
TRANSACTION_BUSINESS_TIME_CANDIDATES = (
    "transaction_effective_date",
    "transaction_posted_date",
    "transaction_datetime",
)


# ---------------------------------------------------------------------------
# Custom YAML dumper: stable order, block style, no aliases, useful folding.
# ---------------------------------------------------------------------------

class _StableDumper(yaml.SafeDumper):
    pass


def _represent_dict(dumper: yaml.SafeDumper, data: dict[str, Any]) -> Any:
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


def _represent_str(dumper: yaml.SafeDumper, data: str) -> Any:
    # Use plain style for ordinary strings; let yaml.dump fold long lines.
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_StableDumper.add_representer(dict, _represent_dict)
_StableDumper.add_representer(str, _represent_str)
_StableDumper.ignore_aliases = lambda self, data: True  # type: ignore[assignment]


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.dump(
        data,
        Dumper=_StableDumper,
        default_flow_style=False,
        allow_unicode=True,
        width=100,
        sort_keys=False,
    )


# ---------------------------------------------------------------------------
# Contract loading and indexing.
# ---------------------------------------------------------------------------


class Contract:
    __slots__ = ("path", "data", "slug", "id", "subject_area", "kind", "table_schema", "table_name")

    def __init__(self, path: Path, data: dict[str, Any]) -> None:
        self.path = path
        self.data = data
        self.slug = path.name.removesuffix(".odcs.yaml")
        self.id = data.get("id", "")
        self.subject_area = self._extract_subject_area(data)
        self.kind = self._derive_kind(path, self.slug)
        self.table_schema = self._derive_schema(path, self.subject_area)
        self.table_name = self.slug.replace("-", "_")

    @staticmethod
    def _extract_subject_area(data: dict[str, Any]) -> str:
        custom = data.get("customProperties")
        if isinstance(custom, dict):
            value = custom.get("subjectArea")
            if isinstance(value, str) and value.strip():
                return value
        return ""

    @staticmethod
    def _derive_kind(path: Path, slug: str) -> str:
        if path.parent.name == "reference-data":
            return "codeset"
        if slug.endswith(EVENT_SLUG_SUFFIX):
            return "event"
        if slug.endswith(TRANSACTION_SLUG_SUFFIX) or slug in TRANSACTION_EXACT_SLUGS:
            return "transaction"
        return "entity"

    @staticmethod
    def _derive_schema(path: Path, subject_area: str) -> str:
        # Codesets always land in silver_reference_data regardless of the
        # contract's subjectArea (which describes domain ownership, not storage).
        if path.parent.name == "reference-data":
            return REFERENCE_DATA_SCHEMA
        if subject_area:
            return f"silver_{subject_area.replace('-', '_')}"
        return "silver_unknown"


class ContractIndex:
    def __init__(self) -> None:
        self.by_id: dict[str, Contract] = {}
        self.reference_data_ids: set[str] = set()

    def add(self, contract: Contract) -> None:
        if contract.id:
            self.by_id[contract.id] = contract
        if contract.kind == "codeset":
            self.reference_data_ids.add(contract.id)

    def fq_table(self, contract_id: str) -> str | None:
        target = self.by_id.get(contract_id)
        if not target:
            return None
        return f"{target.table_schema}.{target.table_name}"


def load_contracts() -> ContractIndex:
    index = ContractIndex()
    for path in sorted(ROOT.glob(CONTRACT_GLOB)):
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            continue
        index.add(Contract(path, data))
    return index


# ---------------------------------------------------------------------------
# Column derivation.
# ---------------------------------------------------------------------------


def _classifications(prop: dict[str, Any]) -> dict[str, Any]:
    custom = prop.get("customProperties")
    if not isinstance(custom, dict):
        return {}
    cls = custom.get("classifications")
    return cls if isinstance(cls, dict) else {}


def _custom(prop: dict[str, Any]) -> dict[str, Any]:
    custom = prop.get("customProperties")
    return custom if isinstance(custom, dict) else {}


def _spark_type(prop: dict[str, Any]) -> str:
    logical = prop.get("logicalType")
    if not isinstance(logical, str):
        return "STRING"
    return LOGICAL_TYPE_TO_SPARK.get(logical, "STRING")


def _is_nullable(prop: dict[str, Any], name: str, kind: str) -> bool:
    if prop.get("primaryKey") is True:
        return False
    if name in (RECORD_STATE_FIELD, "valid_from_datetime", "is_current_indicator"):
        return False
    if name == "valid_to_datetime":
        return True
    if name == CORRECTION_FIELD:
        return False
    return prop.get("required") is not True


def _purview_label(sensitivity: str | None) -> str:
    if not isinstance(sensitivity, str):
        return "Internal"
    return SENSITIVITY_TO_PURVIEW.get(sensitivity, "Internal")


def _resolve_relationship_targets(
    relationships: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Map source-field name -> list of relationships that bind it."""
    mapping: dict[str, list[dict[str, Any]]] = {}
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        sources = rel.get("sourceFields")
        if not isinstance(sources, list):
            continue
        for src in sources:
            if isinstance(src, str):
                mapping.setdefault(src, []).append(rel)
    return mapping


def _codeset_binding(
    name: str,
    rels_for_field: list[dict[str, Any]],
    index: ContractIndex,
) -> dict[str, str] | None:
    for rel in rels_for_field:
        target_id = rel.get("targetContractId")
        if not isinstance(target_id, str):
            continue
        if target_id not in index.reference_data_ids:
            continue
        target = index.by_id.get(target_id)
        if not target:
            continue
        target_fields = rel.get("targetFields") or []
        target_field = "code_value"
        if isinstance(target_fields, list) and target_fields:
            if isinstance(target_fields[0], str):
                target_field = target_fields[0]
        return {
            "codeset": target_id,
            "codesetTable": f"{target.table_schema}.{target.table_name}",
            "codesetField": target_field,
        }
    return None


def _foreign_key_binding(
    rels_for_field: list[dict[str, Any]],
    index: ContractIndex,
) -> dict[str, str] | None:
    for rel in rels_for_field:
        target_id = rel.get("targetContractId")
        if not isinstance(target_id, str):
            continue
        if target_id in index.reference_data_ids:
            continue
        target = index.by_id.get(target_id)
        if not target:
            continue
        target_fields = rel.get("targetFields") or []
        target_field = ""
        if isinstance(target_fields, list) and target_fields:
            if isinstance(target_fields[0], str):
                target_field = target_fields[0]
        return {
            "targetContract": target_id,
            "targetTable": f"{target.table_schema}.{target.table_name}",
            "targetField": target_field,
        }
    return None


def _currency_pair_for_amount(name: str, sibling_names: set[str]) -> dict[str, str] | None:
    prefix = name.removesuffix("_amount")
    paired = f"{prefix}_currency_code"
    if paired in sibling_names:
        return {"pairedColumn": paired}
    return None


def _shared_currency_column(sibling_names: set[str]) -> str | None:
    candidates = sorted(n for n in sibling_names if n.endswith("_currency_code"))
    return candidates[0] if candidates else None


def _column_role(
    name: str,
    prop: dict[str, Any],
    contract_kind: str,
    is_pk: bool,
    sibling_names: set[str],
    rels_for_field: list[dict[str, Any]],
    index: ContractIndex,
    has_codeset_binding: bool,
    has_foreign_key_binding: bool,
) -> str:
    if name == "valid_from_datetime":
        return "scd2-valid-from"
    if name == "valid_to_datetime":
        return "scd2-valid-to"
    if name == "is_current_indicator":
        return "scd2-is-current"
    if name == RECORD_STATE_FIELD:
        return "record-state"
    if name in SOURCE_TIME_NAMES:
        return "source-time"
    if name in SOURCE_ATTRIBUTION_NAMES:
        return "source-attribution"
    if contract_kind in ("event", "transaction"):
        if name == CORRECTION_FIELD:
            return "event-correction-flag"
        if name.startswith("corrects_") and name.endswith("_uid"):
            return "event-corrects-ref"
        if contract_kind == "transaction" and name == LIFECYCLE_EVENT_LINK_FIELD:
            return "lifecycle-event-link"
    if is_pk and name.endswith("_uid"):
        return "identity"
    if name.endswith("_number") and not is_pk:
        return "business-key"
    logical = prop.get("logicalType")
    if logical == "decimal" and name.endswith("_amount"):
        return "monetary-amount"
    if name.endswith("_currency_code"):
        prefix = name.removesuffix("_currency_code")
        # A monetary-currency role requires a sibling amount field, OR an
        # amountCurrencyExempt sibling that pairs against this column.
        if f"{prefix}_amount" in sibling_names:
            return "monetary-currency"
    if name.endswith("_uid") and not is_pk and has_foreign_key_binding:
        return "foreign-key"
    if name.endswith("_code") and has_codeset_binding and _custom(prop).get("codesetExempt") is not True:
        return "code-reference"
    return "data"


def _column_entry(
    prop: dict[str, Any],
    contract: Contract,
    sibling_names: set[str],
    rel_index: dict[str, list[dict[str, Any]]],
    index: ContractIndex,
) -> dict[str, Any]:
    name = prop["name"]
    is_pk = prop.get("primaryKey") is True
    rels_for_field = rel_index.get(name, [])
    code_block = _codeset_binding(name, rels_for_field, index)
    fk_block = _foreign_key_binding(rels_for_field, index) if (
        name.endswith("_uid") and not is_pk
    ) else None
    role = _column_role(
        name=name,
        prop=prop,
        contract_kind=contract.kind,
        is_pk=is_pk,
        sibling_names=sibling_names,
        rels_for_field=rels_for_field,
        index=index,
        has_codeset_binding=code_block is not None,
        has_foreign_key_binding=fk_block is not None,
    )

    cls = _classifications(prop)
    sensitivity = cls.get("sensitivity") if isinstance(cls.get("sensitivity"), str) else "INTERNAL"
    tags = cls.get("regulatoryTags") if isinstance(cls.get("regulatoryTags"), list) else []
    custom = _custom(prop)

    entry: dict[str, Any] = {
        "name": name,
        "sparkType": _spark_type(prop),
        "nullable": _is_nullable(prop, name, contract.kind),
    }
    if is_pk:
        entry["primaryKey"] = True
    entry["role"] = role
    entry["description"] = prop.get("description", "")

    classifications: dict[str, Any] = {"sensitivity": sensitivity}
    if tags:
        classifications["regulatoryTags"] = list(tags)
    entry["classifications"] = classifications
    entry["purview"] = {"sensitivityLabel": _purview_label(sensitivity)}

    if role == "foreign-key" and fk_block is not None:
        entry["foreignKey"] = fk_block

    # codeReference is emitted whenever a codeset binding exists, regardless of
    # whether the role is `code-reference` (it can also accompany source-attribution
    # and record-state when those columns bind to a codeset).
    if code_block is not None and not custom.get("codesetExempt"):
        entry["codeReference"] = code_block

    if role == "monetary-amount":
        pair = _currency_pair_for_amount(name, sibling_names)
        if pair is None and custom.get("amountCurrencyExempt") is True:
            shared = _shared_currency_column(sibling_names)
            if shared is not None:
                pair = {"pairedColumn": shared}
        if pair is not None:
            entry["currencyPair"] = pair

    return entry


# ---------------------------------------------------------------------------
# Quality rule projection.
# ---------------------------------------------------------------------------


# Hand-mapped expression rules. Falls back to a placeholder when the rule name
# does not match any known pattern; F3 will refine these as new patterns appear.
KNOWN_EXPRESSION_RULES: dict[str, str] = {
    "valid_window_consistent": (
        "valid_to_datetime IS NULL OR valid_to_datetime > valid_from_datetime"
    ),
}


PRIOR_DIFF_PATTERN = re.compile(r"^(?P<entity>[a-z][a-z0-9_]*)_prior_(?P=entity)_must_differ$")
EFFECTIVE_NOT_AFTER_EXPIRATION = re.compile(r"^[a-z][a-z0-9_]*_effective_date_not_after_expiration_date$")


def _project_quality_rule(
    rule: dict[str, Any],
    column_names: list[str],
    natural_key: list[str],
) -> dict[str, Any] | None:
    rule_name = rule.get("rule")
    severity = rule.get("severity", "error")
    description = rule.get("description", "")
    if not isinstance(rule_name, str) or not rule_name:
        return None

    # 1. not_null pattern: <column>_required.
    if rule_name.endswith("_required"):
        candidate = _match_required_column(rule_name, column_names)
        if candidate:
            return {
                "id": rule_name,
                "type": "not_null",
                "column": candidate,
                "severity": severity,
                "sourceRule": rule_name,
            }

    # 2. unique pattern: single_*_per_key.
    if rule_name.startswith("single_") and rule_name.endswith("_per_key"):
        return {
            "id": rule_name,
            "type": "unique",
            "keyColumns": list(natural_key) if natural_key else [],
            "filter": "is_current_indicator = true",
            "severity": severity,
            "sourceRule": rule_name,
        }

    # 3. Hand-mapped expression rules (well-known cross-cutting names).
    if rule_name in KNOWN_EXPRESSION_RULES:
        return {
            "id": rule_name,
            "type": "expression",
            "expression": KNOWN_EXPRESSION_RULES[rule_name],
            "severity": severity,
            "sourceRule": rule_name,
        }

    # 4. <entity>_prior_<entity>_must_differ pattern.
    prior_match = PRIOR_DIFF_PATTERN.match(rule_name)
    if prior_match:
        entity = prior_match.group("entity")
        return {
            "id": rule_name,
            "type": "expression",
            "expression": (
                f"prior_{entity}_uid IS NULL OR prior_{entity}_uid <> {entity}_uid"
            ),
            "severity": severity,
            "sourceRule": rule_name,
        }

    # 5. <entity>_effective_date_not_after_expiration_date pattern.
    if EFFECTIVE_NOT_AFTER_EXPIRATION.match(rule_name):
        return {
            "id": rule_name,
            "type": "expression",
            "expression": (
                "effective_date IS NULL OR expiration_date IS NULL "
                "OR effective_date <= expiration_date"
            ),
            "severity": severity,
            "sourceRule": rule_name,
        }

    # 6. Fallback: emit as expression with description placeholder. F3 will
    # surface these for refinement; the notebook treats unimplemented expressions
    # as warnings until patterned.
    return {
        "id": rule_name,
        "type": "expression",
        "expression": f"TRUE  -- TODO: derive from contract description: {description}",
        "severity": severity,
        "sourceRule": rule_name,
    }


def _match_required_column(rule_name: str, column_names: list[str]) -> str | None:
    suffix = "_required"
    base = rule_name.removesuffix(suffix)
    # Prefer exact column match.
    if base in column_names:
        return base
    # Fallback: longest column name that matches the rule-name suffix.
    candidates = [c for c in column_names if rule_name == f"{c}_required" or rule_name.endswith(f"_{c}_required")]
    if not candidates:
        return None
    return max(candidates, key=len)


# ---------------------------------------------------------------------------
# Manifest assembly.
# ---------------------------------------------------------------------------


def _entity_partition(columns: list[dict[str, Any]]) -> list[str]:
    return ["is_current_indicator"]


def _entity_zorder(columns: list[dict[str, Any]]) -> list[str]:
    for col in columns:
        if col.get("role") == "identity":
            return [col["name"]]
    return []


def _append_only_business_time(
    contract_kind: str, slug: str, columns: list[dict[str, Any]]
) -> str:
    column_names = [c["name"] for c in columns]
    if contract_kind == "event" and EVENT_BUSINESS_TIME in column_names:
        return EVENT_BUSINESS_TIME
    if contract_kind == "transaction":
        for candidate in TRANSACTION_BUSINESS_TIME_CANDIDATES:
            if candidate in column_names:
                return candidate
    if EVENT_BUSINESS_TIME in column_names:
        return EVENT_BUSINESS_TIME
    return column_names[0] if column_names else ""


def _append_only_corrects_field(columns: list[dict[str, Any]]) -> str:
    for col in columns:
        if col.get("role") == "event-corrects-ref":
            return col["name"]
    return ""


def _table_block(contract: Contract, columns: list[dict[str, Any]]) -> dict[str, Any]:
    is_append = contract.kind in ("event", "transaction")
    if is_append:
        business_time = _append_only_business_time(contract.kind, contract.slug, columns)
        partitioned_by = [business_time] if business_time else []
        zorder_by: list[str] = []
    else:
        partitioned_by = _entity_partition(columns)
        zorder_by = _entity_zorder(columns)

    properties: dict[str, Any] = {
        "delta.appendOnly": is_append,
        "delta.autoOptimize.optimizeWrite": True,
        "delta.autoOptimize.autoCompact": True,
        "delta.enableChangeDataFeed": True,
    }

    return {
        "name": contract.table_name,
        "delta": {
            "tableProperties": properties,
            "partitionedBy": partitioned_by,
            "zorderBy": zorder_by,
            "vorder": True,
        },
    }


def _scd2_block(columns: list[dict[str, Any]], contract: Contract) -> dict[str, Any]:
    if contract.kind in ("event", "transaction"):
        return {
            "enabled": False,
            "validFrom": None,
            "validTo": None,
            "isCurrent": None,
            "naturalKey": [],
            "deletionAware": False,
            "changeDetection": {"excludeFromHashing": []},
        }
    natural_key: list[str] = []
    for col in columns:
        if col.get("role") == "identity":
            natural_key.append(col["name"])
            break
    return {
        "enabled": True,
        "validFrom": "valid_from_datetime",
        "validTo": "valid_to_datetime",
        "isCurrent": "is_current_indicator",
        "naturalKey": natural_key,
        "deletionAware": contract.kind == "codeset",
        "changeDetection": {
            "excludeFromHashing": [
                "valid_from_datetime",
                "valid_to_datetime",
                "is_current_indicator",
                "record_status_code",
            ],
        },
    }


def _record_state_block(contract: Contract) -> dict[str, Any]:
    if contract.kind in ("event", "transaction"):
        return {
            "enabled": False,
            "field": None,
            "activeValue": None,
            "supersededValue": None,
            "softDeletedValue": None,
        }
    return {
        "enabled": True,
        "field": RECORD_STATE_FIELD,
        "activeValue": "ACTIVE",
        "supersededValue": "SUPERSEDED",
        "softDeletedValue": "SOFT_DELETED",
    }


def _append_only_block(contract: Contract, columns: list[dict[str, Any]]) -> dict[str, Any]:
    if contract.kind not in ("event", "transaction"):
        return {
            "enabled": False,
            "correctionIndicator": None,
            "correctsRefField": None,
            "businessTimeField": None,
            "partitionExpression": None,
        }
    business_time = _append_only_business_time(contract.kind, contract.slug, columns)
    corrects_field = _append_only_corrects_field(columns)
    partition_expr = ""
    if business_time:
        # Date columns get partitioned by month at expression level too.
        partition_expr = f"MONTH({business_time})"
    return {
        "enabled": True,
        "correctionIndicator": CORRECTION_FIELD,
        "correctsRefField": corrects_field,
        "businessTimeField": business_time,
        "partitionExpression": partition_expr,
    }


def _quality_rules(
    data: dict[str, Any], columns: list[dict[str, Any]], natural_key: list[str]
) -> list[dict[str, Any]]:
    column_names = [c["name"] for c in columns]
    projected: list[dict[str, Any]] = []
    rules = data.get("quality") or []
    if isinstance(rules, list):
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            entry = _project_quality_rule(rule, column_names, natural_key)
            if entry is not None:
                projected.append(entry)

    # Derived: currency_pair assertion for every monetary-amount column with a
    # currencyPair block.
    for col in columns:
        if col.get("role") != "monetary-amount":
            continue
        pair = col.get("currencyPair")
        if not isinstance(pair, dict):
            continue
        paired = pair.get("pairedColumn")
        if not isinstance(paired, str):
            continue
        projected.append(
            {
                "id": f"{col['name']}_currency_pair",
                "type": "currency_pair",
                "amountColumn": col["name"],
                "currencyColumn": paired,
                "severity": "error",
                "sourceRule": "derived",
            }
        )

    # Derived: accepted_values assertion for every column with a codeReference
    # binding (regardless of role).
    for col in columns:
        cref = col.get("codeReference")
        if not isinstance(cref, dict):
            continue
        projected.append(
            {
                "id": f"{col['name']}_in_codeset",
                "type": "accepted_values",
                "column": col["name"],
                "codeset": cref["codeset"],
                "codesetTable": cref["codesetTable"],
                "codesetField": cref["codesetField"],
                "severity": "error",
                "sourceRule": "derived",
            }
        )

    return projected


def _bronze_block(contract: Contract, columns: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "table": f"bronze.{contract.table_name}_raw",
        "incrementalColumn": "_ingested_at",
        "expectedColumns": [c["name"] for c in columns],
    }


def _relationships_block(
    data: dict[str, Any], index: ContractIndex
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    rels = data.get("relationships") or []
    if not isinstance(rels, list):
        return out
    for rel in rels:
        if not isinstance(rel, dict):
            continue
        target_id = rel.get("targetContractId")
        target_table = index.fq_table(target_id) if isinstance(target_id, str) else None
        out.append(
            {
                "name": rel.get("name", ""),
                "description": rel.get("description", ""),
                "cardinality": rel.get("relationshipType", ""),
                "targetContract": target_id or "",
                "targetTable": target_table or "",
                "sourceFields": list(rel.get("sourceFields") or []),
                "targetFields": list(rel.get("targetFields") or []),
            }
        )
    return out


def _generation_block(
    contract: Contract,
    digest: str,
    generated_at: str,
    existing: dict[str, Any] | None,
) -> dict[str, Any]:
    # Preserve `generatedAt` across reruns when the contract digest is unchanged.
    if isinstance(existing, dict):
        prior_digest = existing.get("sourceContractDigest")
        prior_generated = existing.get("generatedAt")
        if prior_digest == digest and isinstance(prior_generated, str):
            generated_at = prior_generated
    rel_path = contract.path.relative_to(ROOT).as_posix()
    return {
        "generatorVersion": GENERATOR_VERSION,
        "generatedAt": generated_at,
        "sourceContractPath": rel_path,
        "sourceContractDigest": digest,
    }


def _contract_block(contract: Contract) -> dict[str, Any]:
    data = contract.data
    custom = data.get("customProperties") or {}
    block: dict[str, Any] = {
        "id": data.get("id", ""),
        "name": data.get("name", ""),
        "version": data.get("version", ""),
        "domain": data.get("domain", ""),
        "description": data.get("description", ""),
        "classificationProfile": custom.get("classificationProfile", "INTERNAL"),
        "subjectToHipaa": bool(custom.get("subjectToHipaa", False)),
        "contractKind": contract.kind,
        "subjectArea": contract.subject_area,
    }
    adrs = custom.get("adrs")
    if isinstance(adrs, list):
        block["adrs"] = list(adrs)
    return block


def build_manifest(
    contract: Contract,
    index: ContractIndex,
    digest: str,
    generated_at: str,
    existing_generation: dict[str, Any] | None,
) -> dict[str, Any]:
    data = contract.data
    schema_entry = (data.get("schema") or [{}])[0]
    if not isinstance(schema_entry, dict):
        schema_entry = {}
    properties = schema_entry.get("properties") or []
    sibling_names = {
        p.get("name")
        for p in properties
        if isinstance(p, dict) and isinstance(p.get("name"), str)
    }
    rel_index = _resolve_relationship_targets(data.get("relationships") or [])

    columns: list[dict[str, Any]] = []
    for prop in properties:
        if not isinstance(prop, dict) or not isinstance(prop.get("name"), str):
            continue
        columns.append(
            _column_entry(
                prop=prop,
                contract=contract,
                sibling_names=sibling_names,
                rel_index=rel_index,
                index=index,
            )
        )

    natural_key = [c["name"] for c in columns if c.get("role") == "identity"]

    fabric_block: dict[str, Any] = {
        "lakehouse": LAKEHOUSE_NAME,
        "schema": contract.table_schema,
        "table": _table_block(contract, columns),
        "columns": columns,
        "scd2": _scd2_block(columns, contract),
        "recordState": _record_state_block(contract),
        "appendOnly": _append_only_block(contract, columns),
        "qualityRules": _quality_rules(data, columns, natural_key),
        "bronze": _bronze_block(contract, columns),
    }

    return {
        "manifestVersion": MANIFEST_VERSION,
        "contract": _contract_block(contract),
        "fabric": fabric_block,
        "relationships": _relationships_block(data, index),
        "generation": _generation_block(contract, digest, generated_at, existing_generation),
    }


# ---------------------------------------------------------------------------
# Filesystem orchestration.
# ---------------------------------------------------------------------------


def _manifest_path(contract: Contract) -> Path:
    rel = contract.path.relative_to(ROOT)
    # references/odcs/pc/<area>/<slug>.odcs.yaml ->
    # targets/fabric/manifests/pc/<area>/<slug>.fabric.yaml
    area = rel.parts[3] if len(rel.parts) > 4 else ""
    return MANIFEST_ROOT / area / f"{contract.slug}.fabric.yaml"


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _existing_generation(manifest_path: Path) -> dict[str, Any] | None:
    if not manifest_path.exists():
        return None
    try:
        with manifest_path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    gen = data.get("generation")
    return gen if isinstance(gen, dict) else None


def emit_manifest(contract: Contract, index: ContractIndex, generated_at: str) -> Path:
    manifest_path = _manifest_path(contract)
    digest = _digest(contract.path)
    existing = _existing_generation(manifest_path)
    manifest = build_manifest(contract, index, digest, generated_at, existing)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(dump_yaml(manifest), encoding="utf-8")
    return manifest_path


def _select_contracts(index: ContractIndex, ids: list[str] | None) -> list[Contract]:
    if not ids:
        return sorted(index.by_id.values(), key=lambda c: c.path)
    out: list[Contract] = []
    for cid in ids:
        contract = index.by_id.get(cid)
        if contract is None:
            print(f"warning: contract id `{cid}` not found in index", file=sys.stderr)
            continue
        out.append(contract)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Fabric manifests from canonical ODCS contracts.")
    parser.add_argument(
        "--contract",
        action="append",
        default=None,
        help="Restrict generation to these contract ids (e.g. `pc.policy`). Repeatable.",
    )
    parser.add_argument(
        "--generated-at",
        default=None,
        help="Override the `generation.generatedAt` timestamp (ISO 8601 UTC). "
        "Default: today at midnight UTC. Existing manifests reuse their stamp "
        "when the source contract digest is unchanged.",
    )
    args = parser.parse_args()

    if args.generated_at:
        generated_at = args.generated_at
    else:
        today = dt.datetime.now(dt.timezone.utc).date()
        generated_at = f"{today.isoformat()}T00:00:00Z"

    index = load_contracts()
    contracts = _select_contracts(index, args.contract)
    if not contracts:
        print("No contracts to generate.", file=sys.stderr)
        return 1

    written: list[Path] = []
    for contract in contracts:
        manifest_path = emit_manifest(contract, index, generated_at)
        written.append(manifest_path)
        print(f"Emitted {manifest_path.relative_to(ROOT)}")

    print(f"Generated {len(written)} manifest(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
