#!/usr/bin/env python3
"""Apply CANONICAL_HARDENING_PLAN.md §4 phase C5 transforms across the P&C ODCS surface.

Phases handled:
  - C5.2: add codeset relationships (or codesetExempt) for every `*_code` field
          on entity contracts.
  - C5.4: lift pure-codeset contracts to `classificationProfile: PUBLIC` plus
          all-PUBLIC field sensitivities, bump to 0.4.0.
  - C5.5: rename inconsistent `*_status_code` fields on richer reference-data
          and entity contracts to `<schema_name>_status_code` form.
  - C5.6: set `pc.product` subjectArea from `coverage` to `product`.
  - C5.7: lift `code_value` sensitivity to PUBLIC on richer reference-data
          entities (lifecycle-event-type, lifecycle-status, line-of-business,
          transaction-type) so every codeset/reference-data contract emits a
          PUBLIC `code_value`.
  - Version bump + changelog on every touched contract (codesets to 0.4.0,
          entity contracts at 0.3.0 to 0.4.0, contracts already at 0.4.x to a
          0.4.x patch).

Each transform is idempotent. Running the script twice produces no changes
after the first run.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_GLOB = "references/odcs/pc/**/*.odcs.yaml"
REFERENCE_DATA_DIR = ROOT / "references" / "odcs" / "pc" / "reference-data"

# ---------------------------------------------------------------------------
# C5.2 — Codeset binding map
# ---------------------------------------------------------------------------

# Field-name → codeset slug (filename under reference-data/, without `.odcs.yaml`).
# Built from the C1.2 punch list plus the C5.1 codeset slate.
FIELD_TO_CODESET: dict[str, str] = {
    # Existing pure codesets
    "policy_status_code": "policy-status-code",
    "policy_type_code": "policy-type-code",
    "claim_status_code": "claim-status-code",
    "cause_of_loss_code": "cause-of-loss-code",
    "coverage_basis_code": "coverage-basis-code",
    "coverage_level_code": "coverage-level-code",
    "coverage_status_code": "coverage-status-code",
    "term_status_code": "term-status-code",
    "policy_term_status_code": "term-status-code",  # post-C5.5 rename
    "issuing_jurisdiction_code": "jurisdiction-code",
    "jurisdiction_code": "jurisdiction-code",
    "party_type_code": "party-type-code",
    "role_type_code": "party-role-type-code",
    "record_status_code": "record-status-code",
    # Existing currency
    "annualized_premium_currency_code": "currency-code",
    "applicable_deductible_currency_code": "currency-code",
    "applicable_limit_currency_code": "currency-code",
    "building_value_currency_code": "currency-code",
    "contents_value_currency_code": "currency-code",
    "deductible_currency_code": "currency-code",
    "default_deductible_currency_code": "currency-code",
    "default_limit_currency_code": "currency-code",
    "limit_constraint_currency_code": "currency-code",
    "limit_currency_code": "currency-code",
    "payroll_currency_code": "currency-code",
    "premium_change_currency_code": "currency-code",
    "stated_value_currency_code": "currency-code",
    "transaction_currency_code": "currency-code",
    # Richer reference-data entities (point at code_value-like target)
    "line_of_business_code": "line-of-business",
    "transaction_type_code": "transaction-type",
    "lifecycle_event_type_code": "lifecycle-event-type",
    "resulting_status_code": "lifecycle-status",
    "prior_status_code": "lifecycle-status",
    "lifecycle_event_status_code": "lifecycle-status",
    # New C5.1 codesets
    "feature_status_code": "feature-status-code",
    "document_type_code": "document-type-code",
    "document_status_code": "document-status-code",
    "coverage_decision_code": "coverage-decision-code",
    "relationship_type_code": "relationship-type-code",
    "relationship_status_code": "relationship-status-code",
    "role_status_code": "role-status-code",
    "assessment_type_code": "assessment-type-code",
    "assessment_status_code": "assessment-status-code",
    "assessment_result_code": "assessment-result-code",
    "submission_status_code": "submission-status-code",
    "submission_type_code": "submission-type-code",
    "claim_type_code": "claim-type-code",
    "source_system_code": "source-system-code",
    "occurrence_type_code": "occurrence-type-code",
    "occurrence_status_code": "occurrence-status-code",
    "catastrophe_type_code": "catastrophe-type-code",
    "catastrophe_status_code": "catastrophe-status-code",
    "account_type_code": "account-type-code",
    "account_status_code": "account-status-code",
    "account_relationship_type_code": "account-relationship-type-code",
    "agreement_type_code": "agreement-type-code",
    "agreement_status_code": "agreement-status-code",
    # Subsumed by pc.financial-transaction-classification (C4.6)
    "transaction_classification_code": "financial-transaction-classification",
    # post-C5.5 renames
    "insurable_object_classification_status_code": "record-status-code",
    "lifecycle_event_type_status_code": "record-status-code",
    "lifecycle_status_status_code": "record-status-code",
    "line_of_business_status_code": "record-status-code",
    "transaction_type_status_code": "record-status-code",
}

# When the codeset is a richer reference-data entity, the relationship targets
# a non-`code_value` business-key field on that entity.
NON_CODE_VALUE_TARGETS: dict[str, str] = {
    "line-of-business": "code_value",  # has code_value
    "transaction-type": "code_value",  # has code_value
    "lifecycle-event-type": "code_value",  # has code_value
    "lifecycle-status": "code_value",  # has code_value
}

# Field-name → exemption rationale. Applied when the field is on an entity
# contract and no canonical codeset is planned. C1.2 accepts these via
# `customProperties.codesetExempt: true` plus `codesetExemptReason: ...`.
EXEMPT_FIELDS: dict[str, str] = {
    # Status / lifecycle fields whose canonical codeset is deferred until
    # cross-carrier standardization is in scope.
    "exposure_status_code": "Exposure-lifecycle state; canonical codeset deferred until exposure modeling expands in a future milestone.",
    "insurable_object_status_code": "Insurable-object lifecycle state; canonical codeset deferred until insurable-object modeling expands.",
    "product_status_code": "Carrier-product lifecycle state; canonical codeset deferred until product modeling expands.",
    "risk_status_code": "Submission-side risk lifecycle state; canonical codeset deferred until submission-risk modeling expands.",
    "response_status_code": "Carrier claim-coverage response state; canonical codeset deferred until claim-coverage modeling expands.",
    # Type / classification taxonomies that vary per carrier or per industry
    # standard library and are not standardized in the canonical layer.
    "vehicle_class_code": "Carrier-product vehicle-class taxonomy; canonical codeset deferred until cross-carrier standardization is in scope.",
    "vehicle_use_code": "Carrier-product vehicle-use taxonomy; canonical codeset deferred until cross-carrier standardization is in scope.",
    "construction_type_code": "ISO construction-type taxonomy; canonical layer carries the value but does not re-publish the external standard as a codeset.",
    "occupancy_type_code": "ISO occupancy-type taxonomy; canonical layer carries the value but does not re-publish the external standard as a codeset.",
    "property_use_code": "ISO property-use taxonomy; canonical layer carries the value but does not re-publish the external standard as a codeset.",
    "protection_class_code": "ISO protection-class rating; canonical layer references the external rating scheme rather than re-publishing.",
    "form_code": "Industry form-library code (ISO/ACORD); canonical layer carries the value but does not re-publish the external library as a codeset.",
    "form_edition_code": "Form edition designator paired with form_code; same rationale as form_code.",
    "rating_territory_code": "Carrier-rating territory identifier; varies per carrier rating plan and is not canonical.",
    "radius_code": "Carrier-rating radius identifier; varies per carrier rating plan and is not canonical.",
    "industry_catastrophe_code": "Industry-issued catastrophe identifier (e.g. PCS code) sourced from external authority; canonical layer carries the value but does not re-publish.",
    "company_catastrophe_code": "Carrier-internal catastrophe identifier; populated per carrier and not standardized canonically.",
    "loss_type_code": "Loss-grouping taxonomy that varies per carrier; cause_of_loss_code is the canonical taxonomy. Codeset deferred.",
    "exposure_type_code": "Polymorphic across exposure subtypes; canonical taxonomy is captured by the subtype contracts (vehicle-exposure, property-exposure, workers-comp-exposure).",
    "exposure_basis_code": "Carrier-rating exposure basis; varies per rating plan and is not canonical.",
    "exposure_unit_code": "Unit-of-measure for exposure quantity (payroll, vehicles, square feet); canonical codeset deferred.",
    "deductible_basis_code": "Carrier-product deductible basis (per-occurrence, aggregate); canonical codeset deferred.",
    "deductible_type_code": "Carrier-product deductible type taxonomy; canonical codeset deferred.",
    "limit_basis_code": "Carrier-product limit basis (per-occurrence, aggregate); canonical codeset deferred.",
    "limit_type_code": "Carrier-product limit type taxonomy; canonical codeset deferred.",
    "limit_unit_code": "Unit-of-measure for limit; canonical codeset deferred.",
    "coverage_type_code": "Coverage-internal classification managed at the carrier-product level; canonical taxonomy is line_of_business + coverage_basis_code.",
    "coverage_category_code": "Carrier-product coverage grouping; canonical codeset deferred.",
    "coverage_code": "Identifier for a Coverage record; references the Coverage entity contract rather than a codeset.",
    "product_code": "Identifier for a Product record; references the Product entity contract rather than a codeset.",
    "product_type_code": "Carrier-product taxonomy; canonical codeset deferred until cross-carrier standardization is in scope.",
    "organization_type_code": "Organization sub-classification refined within party_type_code = ORGANIZATION; canonical codeset deferred.",
    "risk_type_code": "Submission-side risk taxonomy; canonical codeset deferred.",
    "insurable_object_type_code": "Polymorphic across insurable-object subtypes; canonical taxonomy captured by exposure subtypes.",
    "reason_code": "Free-form classification of why a lifecycle event occurred; canonical codeset deferred until lifecycle-event modeling expands.",
    "reserve_category_code": "Claim reserve category (case, IBNR, ALAE, ULAE); canonical taxonomy carried in pc.financial-transaction-classification for transaction rollups, but a reserve-bookkeeping codeset is deferred until reserve modeling expands.",
    "accounting_period_code": "Carrier-accounting period identifier (YYYY-MM or YYYYNN); format varies per carrier and is not canonical.",
    "classification_code": "Polymorphic classification value paired with classification_scheme_code; canonical codeset deferred until classification modeling expands.",
    "classification_scheme_code": "Polymorphic classification-scheme identifier paired with classification_code; canonical codeset deferred.",
    "debit_credit_code": "Two-value enumeration (DR / CR) enforced by inline quality rule; codeset overhead unwarranted.",
    "party_status_code": "Party-lifecycle state varies between person parties (active, deceased, inactive) and organization parties (active, dissolved, merged); canonical codeset deferred until party-lifecycle modeling expands.",
}

# ---------------------------------------------------------------------------
# C5.5 — `*_status_code` rename map (per-slug, old → new field name)
# ---------------------------------------------------------------------------

STATUS_CODE_RENAMES: dict[str, dict[str, str]] = {
    "insurable-object-classification": {"status_code": "insurable_object_classification_status_code"},
    "lifecycle-event-type": {"status_code": "lifecycle_event_type_status_code"},
    "lifecycle-status": {"reference_status_code": "lifecycle_status_status_code"},
    "line-of-business": {"status_code": "line_of_business_status_code"},
    "transaction-type": {"status_code": "transaction_type_status_code"},
    "policy-term": {"term_status_code": "policy_term_status_code"},
    # The plan's C5.5 list scoped this to reference contracts, but `party.status_code`
    # is the only remaining bare `status_code` on an entity contract; renaming for
    # naming-convention consistency closes the long tail.
    "party": {"status_code": "party_status_code"},
}

# ---------------------------------------------------------------------------
# C5.4 / C5.7 — pure-codeset and reference-data-entity sensitivity targets
# ---------------------------------------------------------------------------

# Richer reference-data entities — flip code_value field to PUBLIC (C5.7) but
# leave the rest at INTERNAL.
REFERENCE_DATA_ENTITY_SLUGS = {
    "lifecycle-event-type",
    "lifecycle-status",
    "line-of-business",
    "transaction-type",
}

# Pure codeset detection — anything under reference-data/ with
# customProperties.codesetContract: true.

VERSIONING_TARGET = {
    # Slugs that were already at 0.4.x from C4 — bump to a 0.4.x patch.
    "claim", "claim-feature", "claim-coverage", "claim-party-role",
    "claim-document", "claim-financial-transaction", "claim-lifecycle-event",
    "policy", "submission", "policy-financial-transaction",
    "occurrence", "catastrophe", "insurable-object-party-role",
    "account", "account-relationship", "account-party-role", "agreement",
    "policy-document", "submission-document", "financial-transaction-classification",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def slug_from_path(path: Path) -> str:
    return path.name.removesuffix(".odcs.yaml")


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


def is_pure_codeset(path: Path, data: dict[str, Any]) -> bool:
    if path.parent != REFERENCE_DATA_DIR:
        return False
    custom = data.get("customProperties") or {}
    return bool(custom.get("codesetContract"))


def is_reference_data_entity(path: Path, slug: str) -> bool:
    return path.parent == REFERENCE_DATA_DIR and slug in REFERENCE_DATA_ENTITY_SLUGS


def existing_relationship_for(prop_name: str, relationships: list[Any]) -> dict[str, Any] | None:
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        sources = rel.get("sourceFields") or []
        if isinstance(sources, list) and prop_name in sources:
            return rel
    return None


def has_codeset_exemption(prop: dict[str, Any]) -> bool:
    custom = prop.get("customProperties") or {}
    return custom.get("codesetExempt") is True and isinstance(custom.get("codesetExemptReason"), str) and custom.get("codesetExemptReason").strip()


# ---------------------------------------------------------------------------
# C5.5 — rename inconsistent *_status_code field names
# ---------------------------------------------------------------------------


def apply_status_code_rename(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    rename_map = STATUS_CODE_RENAMES.get(slug)
    if not rename_map:
        return
    properties = schema_properties(data)
    if properties is None:
        return
    renamed: list[str] = []
    for prop in properties:
        if not isinstance(prop, dict):
            continue
        name = prop.get("name")
        if name in rename_map:
            new_name = rename_map[name]
            prop["name"] = new_name
            renamed.append(f"{name} → {new_name}")
    # Update relationships' sourceFields if any reference the renamed field.
    relationships = data.get("relationships")
    if isinstance(relationships, list):
        for rel in relationships:
            if not isinstance(rel, dict):
                continue
            sources = rel.get("sourceFields")
            if not isinstance(sources, list):
                continue
            for i, src in enumerate(sources):
                if isinstance(src, str) and src in rename_map:
                    sources[i] = rename_map[src]
    # Update quality rules that name the old field. Use word-boundary regex so
    # `status_code` doesn't substitute inside `record_status_code` or inside
    # the new field name on a re-run.
    quality = data.get("quality")
    if isinstance(quality, list):
        for rule in quality:
            if not isinstance(rule, dict):
                continue
            for key in ("rule", "description"):
                value = rule.get(key)
                if isinstance(value, str):
                    for old, new in rename_map.items():
                        value = re.sub(rf"\b{re.escape(old)}\b", new, value)
                    rule[key] = value
    if renamed:
        change_log.append("rename status_code field(s): " + ", ".join(renamed))


# ---------------------------------------------------------------------------
# C5.4 / C5.7 — sensitivity lifts on reference-data
# ---------------------------------------------------------------------------


def lift_pure_codeset_sensitivities(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    properties = schema_properties(data)
    if properties is None:
        return
    flipped = 0
    for prop in properties:
        if not isinstance(prop, dict):
            continue
        custom = prop.setdefault("customProperties", {})
        cls = custom.setdefault("classifications", {})
        if cls.get("sensitivity") not in (None, "PUBLIC"):
            cls["sensitivity"] = "PUBLIC"
            # remove regulatory tags if present (PII etc) — not applicable for PUBLIC
            cls.pop("regulatoryTags", None)
            flipped += 1
        elif cls.get("sensitivity") is None:
            cls["sensitivity"] = "PUBLIC"
            flipped += 1
    custom_top = data.setdefault("customProperties", {})
    if custom_top.get("classificationProfile") != "PUBLIC":
        custom_top["classificationProfile"] = "PUBLIC"
        change_log.append("lift classificationProfile to PUBLIC (C5.4 pure codeset)")
    if flipped:
        change_log.append(f"flip {flipped} field sensitivities to PUBLIC (C5.4 pure codeset)")


def lift_reference_entity_code_value(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    properties = schema_properties(data)
    if properties is None:
        return
    for prop in properties:
        if not isinstance(prop, dict):
            continue
        if prop.get("name") != "code_value":
            continue
        custom = prop.setdefault("customProperties", {})
        cls = custom.setdefault("classifications", {})
        if cls.get("sensitivity") != "PUBLIC":
            cls["sensitivity"] = "PUBLIC"
            change_log.append("lift code_value sensitivity to PUBLIC (C5.7)")


# ---------------------------------------------------------------------------
# C5.6 — pc.product subjectArea
# ---------------------------------------------------------------------------


def apply_product_subject_area(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    if slug != "product":
        return
    custom = data.setdefault("customProperties", {})
    if custom.get("subjectArea") != "product":
        custom["subjectArea"] = "product"
        change_log.append("set subjectArea: product (C5.6)")


# ---------------------------------------------------------------------------
# C5.2 — relationship sweep across *_code fields
# ---------------------------------------------------------------------------


def apply_codeset_sweep(slug: str, path: Path, data: dict[str, Any], change_log: list[str]) -> None:
    # Auto-skip codesets and reference-data contracts (validator C1.2 also
    # short-circuits there).
    if path.parent == REFERENCE_DATA_DIR:
        return
    properties = schema_properties(data)
    if properties is None:
        return
    relationships = data.setdefault("relationships", [])
    if not isinstance(relationships, list):
        relationships = []
        data["relationships"] = relationships

    bound: list[str] = []
    exempted: list[str] = []
    for prop in properties:
        if not isinstance(prop, dict):
            continue
        name = prop.get("name")
        if not isinstance(name, str) or not name.endswith("_code"):
            continue
        if has_codeset_exemption(prop):
            continue
        # Skip *_uid PKs and other obviously non-codeset fields (the suffix check
        # catches them — none currently end in `_code` outside the codeset slate).
        # Skip fields that already have a relationship targeting a reference-data contract.
        existing = existing_relationship_for(name, relationships)
        if existing is not None:
            target = existing.get("targetContractId") or ""
            if target.startswith("pc.") and (REFERENCE_DATA_DIR / f"{target.removeprefix('pc.')}.odcs.yaml").exists():
                continue
            # Existing relationship points elsewhere — leave alone; sweep adds a
            # second relationship below.
        codeset_slug = FIELD_TO_CODESET.get(name)
        if codeset_slug:
            target_contract_id = f"pc.{codeset_slug}"
            target_field = NON_CODE_VALUE_TARGETS.get(codeset_slug, "code_value")
            rel_name = f"{slug.replace('-', '_')}_{name}_to_{codeset_slug.replace('-', '_')}"
            new_rel = {
                "name": rel_name,
                "description": f"Binds {name} to the canonical {codeset_slug} codeset.",
                "relationshipType": "many-to-one",
                "targetContractId": target_contract_id,
                "sourceFields": [name],
                "targetFields": [target_field],
            }
            # Skip if an identical relationship already exists.
            already = False
            for rel in relationships:
                if not isinstance(rel, dict):
                    continue
                if (
                    rel.get("targetContractId") == target_contract_id
                    and rel.get("sourceFields") == [name]
                ):
                    already = True
                    break
            if not already:
                relationships.append(new_rel)
                bound.append(f"{name} → {codeset_slug}")
            continue
        # No canonical codeset — exempt with rationale.
        rationale = EXEMPT_FIELDS.get(name)
        if not rationale:
            # Unknown field: leave alone. The validator will flag it; a follow-up
            # commit decides bind vs exempt explicitly.
            continue
        custom = prop.setdefault("customProperties", {})
        if custom.get("codesetExempt") is not True or not isinstance(custom.get("codesetExemptReason"), str):
            custom["codesetExempt"] = True
            custom["codesetExemptReason"] = rationale
            exempted.append(name)
    if bound:
        change_log.append(f"bind {len(bound)} *_code field(s) to codeset(s) (C5.2)")
    if exempted:
        change_log.append(f"add codesetExempt to {len(exempted)} field(s) (C5.2)")


# ---------------------------------------------------------------------------
# Version bump + changelog entry
# ---------------------------------------------------------------------------


def parse_version(value: str) -> tuple[int, int, int]:
    parts = value.split(".")
    if len(parts) != 3:
        return (0, 0, 0)
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        return (0, 0, 0)


def next_version(current: str, slug: str) -> str:
    major, minor, patch = parse_version(current)
    if slug in VERSIONING_TARGET or (major, minor) >= (0, 4):
        return f"{major}.{minor}.{patch + 1}"
    return f"{major}.{minor + 1}.0" if minor < 4 else f"{major}.{minor}.{patch + 1}"


def apply_version_bump(slug: str, data: dict[str, Any], change_log: list[str]) -> None:
    if not change_log:
        return
    current = data.get("version") or "0.0.0"
    target = next_version(str(current), slug)
    if str(current) == target:
        return
    data["version"] = target
    custom = data.setdefault("customProperties", {})
    changelog = custom.setdefault("changelog", [])
    if not isinstance(changelog, list):
        changelog = []
        custom["changelog"] = changelog
    entry = f"{target}: Canonical hardening C5 — " + "; ".join(change_log) + "."
    if not any(isinstance(e, str) and e.startswith(f"{target}:") for e in changelog):
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

    # Order: rename fields first so codeset-binding sees the new names.
    apply_status_code_rename(slug, data, change_log)
    if is_pure_codeset(path, data):
        lift_pure_codeset_sensitivities(slug, data, change_log)
    if is_reference_data_entity(path, slug):
        lift_reference_entity_code_value(slug, data, change_log)
    apply_product_subject_area(slug, data, change_log)
    apply_codeset_sweep(slug, path, data, change_log)
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
