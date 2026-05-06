#!/usr/bin/env python3
"""Unit tests for the C1 canonical-hardening validator rules.

Run via:

    python3 -m unittest scripts/validation/tests/test_hardening_rules.py

Each rule has at least one passing case and one failing case. Tests build
minimal in-memory contract dicts plus a stub `ContractIndex` so they exercise
the rule functions in isolation.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = ROOT / "scripts" / "validation" / "validate-contracts.py"

_spec = importlib.util.spec_from_file_location("validate_contracts", VALIDATOR_PATH)
assert _spec and _spec.loader
validator = importlib.util.module_from_spec(_spec)
sys.modules["validate_contracts"] = validator
_spec.loader.exec_module(validator)


class StubIndex:
    def __init__(
        self,
        contract_ids=None,
        reference_data_ids=None,
        codeset_prefix_to_id=None,
        adr_ids=None,
    ) -> None:
        self.contract_ids = set(contract_ids or [])
        self.reference_data_ids = set(reference_data_ids or [])
        self.codeset_prefix_to_id = dict(codeset_prefix_to_id or {})
        self.adr_ids = set(adr_ids or [])


def _classifications(sensitivity="INTERNAL", regulatory_tags=None, **extra):
    cls = {"sensitivity": sensitivity}
    if regulatory_tags is not None:
        cls["regulatoryTags"] = list(regulatory_tags)
    cls.update(extra)
    return cls


def _prop(name, **overrides):
    base = {
        "name": name,
        "businessName": name.replace("_", " ").title(),
        "logicalType": "string",
        "required": False,
        "description": f"description for {name}",
        "customProperties": {"classifications": _classifications()},
    }
    if "classifications" in overrides:
        base["customProperties"]["classifications"] = overrides.pop("classifications")
    if "customProperties" in overrides:
        base["customProperties"].update(overrides.pop("customProperties"))
    base.update(overrides)
    return base


def _contract(properties, *, custom=None, status="draft", relationships=None, version="0.2.0", subject_area="claims"):
    cp = {
        "canonicalLayer": "silver",
        "contractFamily": "property-and-casualty",
        "domainPackage": "pc",
        "subjectArea": subject_area,
    }
    if custom:
        cp.update(custom)
    return {
        "apiVersion": "v3.0.2",
        "kind": "DataContract",
        "id": "pc.test",
        "name": "Test",
        "version": version,
        "status": status,
        "description": "Test contract",
        "domain": "property-and-casualty",
        "schema": [
            {
                "name": "test",
                "physicalType": "table",
                "description": "test entity",
                "properties": properties,
            }
        ],
        "relationships": relationships or [],
        "customProperties": cp,
    }


PATH = ROOT / "references" / "odcs" / "pc" / "claims" / "test.odcs.yaml"
CODESET_PATH = ROOT / "references" / "odcs" / "pc" / "reference-data" / "test-code.odcs.yaml"


class TestC1_1AmountCurrencyPairing(unittest.TestCase):
    def test_pass_with_sibling(self):
        data = _contract([
            _prop("transaction_amount", logicalType="decimal"),
            _prop("transaction_currency_code"),
        ])
        self.assertEqual(validator.validate_amount_currency_pairing(PATH, data), [])

    def test_fail_missing_sibling(self):
        data = _contract([_prop("payroll_amount", logicalType="decimal")])
        findings = validator.validate_amount_currency_pairing(PATH, data)
        self.assertEqual(len(findings), 1)
        self.assertIn("payroll_currency_code", findings[0].message)

    def test_pass_with_exemption(self):
        data = _contract([
            _prop(
                "premium_change_amount",
                logicalType="decimal",
                customProperties={
                    "amountCurrencyExempt": True,
                    "amountCurrencyExemptReason": "Premium movements share contract-level currency.",
                },
            )
        ])
        self.assertEqual(validator.validate_amount_currency_pairing(PATH, data), [])


class TestC1_2CodeCodesetResolution(unittest.TestCase):
    def setUp(self):
        self.index = StubIndex(
            contract_ids={"pc.test", "pc.policy-status-code"},
            reference_data_ids={"pc.policy-status-code"},
        )

    def test_pass_with_relationship(self):
        data = _contract(
            [_prop("policy_status_code")],
            relationships=[
                {
                    "name": "test_to_policy_status",
                    "description": "x",
                    "relationshipType": "many-to-one",
                    "targetContractId": "pc.policy-status-code",
                    "sourceFields": ["policy_status_code"],
                    "targetFields": ["code_value"],
                }
            ],
        )
        self.assertEqual(validator.validate_code_codeset_resolution(PATH, data, self.index), [])

    def test_fail_missing_relationship(self):
        data = _contract([_prop("policy_status_code")])
        findings = validator.validate_code_codeset_resolution(PATH, data, self.index)
        self.assertEqual(len(findings), 1)

    def test_pass_with_exemption(self):
        data = _contract([
            _prop(
                "source_system_code",
                customProperties={
                    "codesetExempt": True,
                    "codesetExemptReason": "Source-attribution field; not a codeset reference per identifier-strategy ADR.",
                },
            )
        ])
        self.assertEqual(validator.validate_code_codeset_resolution(PATH, data, self.index), [])

    def test_codeset_contract_exempt(self):
        data = _contract(
            [_prop("external_standard_code")],
            custom={"codesetContract": True, "subjectArea": "codesets"},
        )
        self.assertEqual(validator.validate_code_codeset_resolution(CODESET_PATH, data, self.index), [])


class TestC1_3TargetContractResolution(unittest.TestCase):
    def setUp(self):
        self.index = StubIndex(contract_ids={"pc.test", "pc.policy"})

    def test_pass(self):
        data = _contract(
            [_prop("policy_uid")],
            relationships=[
                {
                    "name": "test_to_policy",
                    "description": "x",
                    "relationshipType": "many-to-one",
                    "targetContractId": "pc.policy",
                    "sourceFields": ["policy_uid"],
                    "targetFields": ["policy_uid"],
                }
            ],
        )
        self.assertEqual(validator.validate_target_contract_resolution(PATH, data, self.index), [])

    def test_fail_unknown_target(self):
        data = _contract(
            [_prop("ghost_uid")],
            relationships=[
                {
                    "name": "test_to_ghost",
                    "description": "x",
                    "relationshipType": "many-to-one",
                    "targetContractId": "pc.does-not-exist",
                    "sourceFields": ["ghost_uid"],
                    "targetFields": ["ghost_uid"],
                }
            ],
        )
        findings = validator.validate_target_contract_resolution(PATH, data, self.index)
        self.assertEqual(len(findings), 1)
        self.assertIn("pc.does-not-exist", findings[0].message)


class TestC1_4CorrectionCompanion(unittest.TestCase):
    def test_pass(self):
        data = _contract([
            _prop("test_uid", primaryKey=True, required=True),
            _prop("correction_indicator", logicalType="boolean", required=True),
            _prop("corrects_test_uid"),
        ])
        self.assertEqual(validator.validate_correction_companion(PATH, data), [])

    def test_fail_missing_companion(self):
        data = _contract([
            _prop("test_uid", primaryKey=True, required=True),
            _prop("correction_indicator", logicalType="boolean", required=True),
        ])
        findings = validator.validate_correction_companion(PATH, data)
        self.assertEqual(len(findings), 1)


class TestC1_5AppendOnlyDatetimeBan(unittest.TestCase):
    def test_pass_no_correction(self):
        data = _contract([
            _prop("test_uid", primaryKey=True, required=True),
            _prop("created_datetime", logicalType="datetime"),
        ])
        self.assertEqual(validator.validate_append_only_datetime_ban(PATH, data), [])

    def test_fail_with_correction(self):
        data = _contract([
            _prop("test_uid", primaryKey=True, required=True),
            _prop("correction_indicator", logicalType="boolean", required=True),
            _prop("corrects_test_uid"),
            _prop("created_datetime", logicalType="datetime"),
            _prop("updated_datetime", logicalType="datetime"),
        ])
        findings = validator.validate_append_only_datetime_ban(PATH, data)
        self.assertEqual(len(findings), 2)


class TestC1_6UidCodeRedundancy(unittest.TestCase):
    def setUp(self):
        self.index = StubIndex(codeset_prefix_to_id={"transaction_type": "pc.transaction-type"})

    def test_pass_no_pair(self):
        data = _contract([_prop("transaction_type_code")])
        self.assertEqual(validator.validate_uid_code_redundancy(PATH, data, self.index), [])

    def test_fail_pair(self):
        data = _contract([
            _prop("transaction_type_uid"),
            _prop("transaction_type_code"),
        ])
        findings = validator.validate_uid_code_redundancy(PATH, data, self.index)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "warning")

    def test_pass_pair_unknown_codeset(self):
        data = _contract([
            _prop("policy_uid"),
            _prop("policy_code"),
        ])
        self.assertEqual(validator.validate_uid_code_redundancy(PATH, data, self.index), [])


class TestC1_7NarrativeClassification(unittest.TestCase):
    def test_pass_confidential_with_tag(self):
        data = _contract([
            _prop(
                "claim_description",
                classifications=_classifications(sensitivity="CONFIDENTIAL", regulatory_tags=["PII"]),
            )
        ])
        self.assertEqual(validator.validate_narrative_classification(PATH, data), [])

    def test_fail_internal_no_tag(self):
        data = _contract([_prop("claim_description")])
        findings = validator.validate_narrative_classification(PATH, data)
        self.assertEqual(len(findings), 1)

    def test_pass_with_exception(self):
        data = _contract([
            _prop(
                "code_description",
                classifications=_classifications(
                    sensitivity="PUBLIC",
                    narrativeException=True,
                    narrativeExceptionReason="Codeset code description is reference data.",
                ),
            )
        ])
        self.assertEqual(validator.validate_narrative_classification(PATH, data), [])

    def test_codeset_contract_exempt_by_path(self):
        data = _contract(
            [_prop("code_description", classifications=_classifications(sensitivity="PUBLIC"))],
            custom={"codesetContract": True, "subjectArea": "codesets"},
        )
        self.assertEqual(validator.validate_narrative_classification(CODESET_PATH, data), [])


class TestC1_8OverClassificationHeuristic(unittest.TestCase):
    def test_pass_internal_status(self):
        data = _contract([_prop("claim_status_code")])
        self.assertEqual(validator.validate_over_classification_heuristic(PATH, data), [])

    def test_fail_restricted_pii_status(self):
        data = _contract([
            _prop(
                "claim_status_code",
                classifications=_classifications(sensitivity="RESTRICTED", regulatory_tags=["PII"]),
            )
        ])
        findings = validator.validate_over_classification_heuristic(PATH, data)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "warning")

    def test_fail_accounting_prefix(self):
        data = _contract([
            _prop(
                "accounting_period_code",
                classifications=_classifications(sensitivity="RESTRICTED", regulatory_tags=["PII"]),
            )
        ])
        findings = validator.validate_over_classification_heuristic(PATH, data)
        self.assertEqual(len(findings), 1)

    def test_fail_uid_at_restricted_pii(self):
        """`_uid` fields are opaque GUIDs per identifier-strategy ADR; RESTRICTED+PII is almost certainly a mis-tag."""
        data = _contract([
            _prop(
                "claim_uid",
                primaryKey=True,
                required=True,
                classifications=_classifications(sensitivity="RESTRICTED", regulatory_tags=["PII"]),
            )
        ])
        findings = validator.validate_over_classification_heuristic(PATH, data)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "warning")

    def test_pass_uid_at_internal(self):
        data = _contract([
            _prop("claim_uid", primaryKey=True, required=True),  # default INTERNAL
        ])
        self.assertEqual(validator.validate_over_classification_heuristic(PATH, data), [])


class TestC1_9ClassificationProfile(unittest.TestCase):
    def test_pass_profile_at_max(self):
        data = _contract(
            [_prop("amt", classifications=_classifications(sensitivity="CONFIDENTIAL", regulatory_tags=["FINANCIAL"]))],
            custom={"classificationProfile": "CONFIDENTIAL"},
        )
        self.assertEqual(validator.validate_classification_profile(PATH, data), [])

    def test_fail_profile_below_max(self):
        data = _contract(
            [_prop("amt", classifications=_classifications(sensitivity="CONFIDENTIAL", regulatory_tags=["FINANCIAL"]))],
            custom={"classificationProfile": "INTERNAL"},
        )
        findings = validator.validate_classification_profile(PATH, data)
        self.assertEqual(len(findings), 1)
        self.assertIn("INTERNAL", findings[0].message)


class TestC1_10StatusPromotionGates(unittest.TestCase):
    def setUp(self):
        self.index = StubIndex(contract_ids={"pc.test", "pc.policy"})

    def test_pass_draft_no_gates(self):
        data = _contract([_prop("test_uid", primaryKey=True, required=True)], status="draft")
        self.assertEqual(validator.validate_status_promotion_gates(PATH, data, self.index), [])

    def test_fail_approved_no_changelog(self):
        data = _contract([_prop("test_uid", primaryKey=True, required=True)], status="approved")
        findings = validator.validate_status_promotion_gates(PATH, data, self.index)
        self.assertTrue(any("changelog" in f.message for f in findings))

    def test_pass_approved_with_changelog(self):
        data = _contract(
            [_prop("test_uid", primaryKey=True, required=True)],
            status="approved",
            custom={"changelog": ["0.2.0: initial"]},
        )
        self.assertEqual(validator.validate_status_promotion_gates(PATH, data, self.index), [])

    def test_fail_approved_unresolved_target(self):
        data = _contract(
            [_prop("test_uid", primaryKey=True, required=True)],
            status="approved",
            custom={"changelog": ["0.2.0: initial"]},
            relationships=[
                {
                    "name": "test_to_ghost",
                    "description": "x",
                    "relationshipType": "many-to-one",
                    "targetContractId": "pc.does-not-exist",
                    "sourceFields": ["ghost_uid"],
                    "targetFields": ["ghost_uid"],
                }
            ],
        )
        findings = validator.validate_status_promotion_gates(PATH, data, self.index)
        self.assertTrue(any("does-not-exist" in f.message for f in findings))


class TestC1_11ChangelogOnVersionBump(unittest.TestCase):
    """Behavior depends on git state; smoke-test the pure-Python branches we control."""

    def test_skip_when_version_invalid(self):
        data = _contract([_prop("test_uid", primaryKey=True, required=True)], version="not-a-version")
        self.assertEqual(validator.validate_changelog_on_version_bump(PATH, data), [])

    def test_skip_when_path_outside_repo(self):
        data = _contract([_prop("test_uid", primaryKey=True, required=True)])
        outside_path = Path("/tmp/not-in-repo.odcs.yaml")
        self.assertEqual(validator.validate_changelog_on_version_bump(outside_path, data), [])


class TestC1_12AdrIdResolution(unittest.TestCase):
    def setUp(self):
        self.index = StubIndex(adr_ids={"identifier-strategy", "temporal-modeling"})

    def test_pass_no_adrs_field(self):
        data = _contract([_prop("test_uid", primaryKey=True, required=True)])
        self.assertEqual(validator.validate_adr_id_resolution(PATH, data, self.index), [])

    def test_pass_resolved_adrs(self):
        data = _contract(
            [_prop("test_uid", primaryKey=True, required=True)],
            custom={"adrs": ["identifier-strategy", "temporal-modeling"]},
        )
        self.assertEqual(validator.validate_adr_id_resolution(PATH, data, self.index), [])

    def test_fail_unresolved_adr(self):
        data = _contract(
            [_prop("test_uid", primaryKey=True, required=True)],
            custom={"adrs": ["identifier-strategy", "ghost-adr"]},
        )
        findings = validator.validate_adr_id_resolution(PATH, data, self.index)
        self.assertEqual(len(findings), 1)
        self.assertIn("ghost-adr", findings[0].message)

    def test_fail_non_list_adrs(self):
        data = _contract(
            [_prop("test_uid", primaryKey=True, required=True)],
            custom={"adrs": "identifier-strategy"},
        )
        findings = validator.validate_adr_id_resolution(PATH, data, self.index)
        self.assertEqual(len(findings), 1)


class TestAllowedStatusesAlignsWithAdr(unittest.TestCase):
    """C2.2 — validator allowed-status set must match `status-promotion.md`."""

    def test_allowed_statuses_set(self):
        self.assertEqual(
            validator.ALLOWED_STATUSES,
            {"draft", "proposed", "approved", "deprecated", "retired"},
        )

    def test_review_rejected_by_top_level(self):
        data = _contract([_prop("test_uid", primaryKey=True, required=True)], status="review")
        findings = validator.validate_top_level(PATH, data)
        self.assertTrue(any("must be one of" in f.message for f in findings))


if __name__ == "__main__":
    unittest.main()
