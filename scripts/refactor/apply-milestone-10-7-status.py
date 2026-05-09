#!/usr/bin/env python3
"""Apply M10.7 status promotion: claims walkthrough cohort `proposed` to `approved`.

Resolves MILESTONE_10_PLAN.md §5 open question 1 — "Should the held-back claims
cohort advance to `approved` in a follow-up milestone (M10.7) once the M10.1
walkthrough has settled?" — by promoting the six walkthrough contracts plus
the five transitively-referenced codesets the cohort binds to.

Cohort encoded in `M10_7_APPROVED_COHORT`. Every contract not in the cohort is
left alone (no demotion, no further bumping); the M10.6 approved cohort stays
approved.

Each promoted contract gets:
- `status:` updated from `proposed` to `approved`.
- `version:` bumped per `versioning-policy.md` PATCH rules (status-only changes
  do not alter schema, so PATCH is correct).
- A new `customProperties.changelog` entry naming the new version, the
  transition, and the M10.7 phase.

The script is idempotent: a contract already at `approved` is skipped.

Run:
    python3 scripts/refactor/apply-milestone-10-7-status.py

Followed by (since contract versions changed):
    python3 scripts/validation/validate-contracts.py
    python3 scripts/generation/generate-fabric.py
    python3 scripts/generation/generate-contract-inventory.py
    python3 scripts/generation/generate-changelog.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_GLOB = "references/odcs/pc/**/*.odcs.yaml"

PHASE_LABEL = "M10.7"
PROMOTION_DATE = date(2026, 5, 9).isoformat()

# Claims walkthrough cohort (per MILESTONE_10_PLAN.md §M10.1 contract table)
# plus the five codesets those contracts transitively reference via *_code
# fields. pc.source-system-code, pc.record-status-code, and pc.currency-code
# are also referenced by the cohort but were already approved by M10.6.
M10_7_APPROVED_COHORT = frozenset(
    {
        # Claims walkthrough cohort.
        "pc.claim",
        "pc.claim-feature",
        "pc.claim-lifecycle-event",
        "pc.claim-financial-transaction",
        "pc.claim-status-code",
        "pc.financial-transaction-classification",
        # Codesets the claims cohort transitively references and that are not
        # already approved (verified against the `*_code` field bindings on
        # the four claims entity/event/transaction contracts).
        "pc.claim-type-code",            # pc.claim.claim_type_code
        "pc.feature-status-code",        # pc.claim-feature.feature_status_code
        "pc.cause-of-loss-code",         # pc.claim-feature.cause_of_loss_code
        "pc.lifecycle-event-type",       # pc.claim-lifecycle-event.lifecycle_event_type_code
        "pc.transaction-type",           # pc.claim-financial-transaction.transaction_type_code
    }
)


def bump_patch(version: str) -> str:
    parts = version.split(".")
    if len(parts) != 3:
        return version
    try:
        major, minor, patch = (int(p) for p in parts)
    except ValueError:
        return version
    return f"{major}.{minor}.{patch + 1}"


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


def already_promoted(custom: dict[str, Any], current_version: str) -> bool:
    """True when the changelog already records an M10.7 promotion at the
    contract's current version. Defensive against partial reruns."""
    changelog = custom.get("changelog") or []
    if not isinstance(changelog, list):
        return False
    needle = f"{current_version}: Promoted from"
    for entry in changelog:
        if isinstance(entry, str) and entry.startswith(needle) and PHASE_LABEL in entry:
            return True
    return False


def promote_contract(path: Path) -> tuple[bool, str | None]:
    """Promote a single contract if it is in the M10.7 cohort and not yet
    approved. Returns (changed, summary)."""
    text = path.read_text(encoding="utf-8")
    data: Any = yaml.safe_load(text)
    if not isinstance(data, dict):
        return False, None

    contract_id = str(data.get("id", "")).strip()
    if contract_id not in M10_7_APPROVED_COHORT:
        return False, None  # not in cohort; leave alone

    current_status = str(data.get("status", "")).strip()
    if current_status == "approved":
        return False, None  # already at target

    if current_status != "proposed":
        # The cohort precondition is that all eleven start at `proposed`
        # (set by M10.6). If this fails, the cohort decision needs review —
        # do not silently promote from an unexpected state.
        return False, f"{contract_id}: SKIPPED (expected `proposed`, found `{current_status}`)"

    current_version = str(data.get("version", "")).strip()
    if not current_version:
        return False, None

    custom = data.setdefault("customProperties", {})
    if not isinstance(custom, dict):
        return False, None

    if already_promoted(custom, current_version):
        return False, None

    new_version = bump_patch(current_version)
    data["version"] = new_version
    data["status"] = "approved"

    changelog = custom.setdefault("changelog", [])
    if not isinstance(changelog, list):
        changelog = []
        custom["changelog"] = changelog
    entry = (
        f"{new_version}: Promoted from {current_status} to approved "
        f"({PHASE_LABEL}, {PROMOTION_DATE})."
    )
    changelog.append(entry)

    new_text = dump_yaml(data)
    if new_text == text:
        return False, None
    path.write_text(new_text, encoding="utf-8")
    summary = (
        f"{contract_id}: {current_status} → approved; "
        f"{current_version} → {new_version}"
    )
    return True, summary


def main() -> int:
    files = sorted(ROOT.glob(CONTRACT_GLOB))
    files = [f for f in files if "/templates/" not in f.as_posix()]
    promoted: list[str] = []
    skipped_with_warning: list[str] = []

    for path in files:
        changed, summary = promote_contract(path)
        if changed and summary is not None:
            promoted.append(summary)
        elif summary is not None and "SKIPPED" in summary:
            skipped_with_warning.append(summary)

    print(f"Promoted {len(promoted)} contract(s) to approved.")
    if promoted:
        print("\napproved cohort:")
        for line in promoted:
            print(f"  {line}")
    if skipped_with_warning:
        print("\nWarnings:")
        for line in skipped_with_warning:
            print(f"  {line}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
