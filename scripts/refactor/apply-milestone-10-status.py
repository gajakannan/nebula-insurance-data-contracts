#!/usr/bin/env python3
"""Apply MILESTONE_10_PLAN.md §4 phase M10.6 status promotions.

Promotes every canonical contract under `references/odcs/pc/` from `draft` to
`proposed` (the bulk cohort), and a curated subset to `approved` (the policy
worked-example cohort plus the codesets that cohort transitively depends on).

The cohort decision is encoded in `APPROVED_COHORT` below. Every contract not
in `APPROVED_COHORT` advances to `proposed` only.

Each promoted contract gets:
- `status:` updated to the new value.
- `version:` bumped per `versioning-policy.md` PATCH rules (status-only changes
  do not alter schema, so PATCH is correct).
- A new `customProperties.changelog` entry naming the new version, the
  transition, and the M10.6 phase.

The script is idempotent: if a contract's `status:` already matches its target
and the current version's changelog already records the M10.6 promotion, no
edit is made.

Run:
    python3 scripts/refactor/apply-milestone-10-status.py

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

PHASE_LABEL = "M10.6"
PROMOTION_DATE = date(2026, 5, 8).isoformat()  # M10.6 commit date

# Contracts that advance from `proposed` to `approved`. Every other contract
# stops at `proposed`. See MILESTONE_10_PLAN.md §3.3 cohort rationale and §4
# phase M10.6 cohort table; cohort verified against the actual `relationships:`
# blocks in the four worked-example contracts before authoring.
APPROVED_COHORT = frozenset(
    {
        # Policy worked-example cohort (the four contracts that compose the
        # walkthrough at targets/fabric/examples/end-to-end-policy.md).
        "pc.policy",
        "pc.policy-term",
        "pc.policy-coverage",
        "pc.policy-status-code",
        # Codesets the policy walkthrough cohort transitively references. Every
        # one of these appears in a `relationships:` block on pc.policy /
        # pc.policy-term / pc.policy-coverage. Promoting them together
        # strengthens the proposed→approved gate "all *_code fields reference
        # codesets that are themselves at least proposed."
        "pc.line-of-business",
        "pc.policy-type-code",
        "pc.jurisdiction-code",
        "pc.term-status-code",
        "pc.currency-code",
        "pc.coverage-status-code",
        "pc.coverage-basis-code",
        "pc.coverage-level-code",
        "pc.source-system-code",
        "pc.record-status-code",
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


def target_status(contract_id: str) -> str:
    return "approved" if contract_id in APPROVED_COHORT else "proposed"


def already_promoted(custom: dict[str, Any], current_version: str) -> bool:
    """True when the changelog already records an M10.6 promotion at the
    contract's current version. Used for idempotency on rerun."""
    changelog = custom.get("changelog") or []
    if not isinstance(changelog, list):
        return False
    needle = f"{current_version}: Promoted from"
    for entry in changelog:
        if isinstance(entry, str) and entry.startswith(needle) and PHASE_LABEL in entry:
            return True
    return False


def promote_contract(path: Path) -> tuple[bool, str | None]:
    """Promote a single contract. Returns (changed, summary)."""
    text = path.read_text(encoding="utf-8")
    data: Any = yaml.safe_load(text)
    if not isinstance(data, dict):
        return False, None

    contract_id = str(data.get("id", "")).strip()
    if not contract_id:
        return False, None

    current_status = str(data.get("status", "")).strip()
    desired_status = target_status(contract_id)
    if current_status == desired_status:
        return False, None  # nothing to do; already at target

    current_version = str(data.get("version", "")).strip()
    if not current_version:
        return False, None

    custom = data.setdefault("customProperties", {})
    if not isinstance(custom, dict):
        return False, None

    if already_promoted(custom, current_version):
        # Defensive — should not happen given the status-mismatch check above,
        # but guards against partial reruns.
        return False, None

    new_version = bump_patch(current_version)
    data["version"] = new_version
    data["status"] = desired_status

    changelog = custom.setdefault("changelog", [])
    if not isinstance(changelog, list):
        changelog = []
        custom["changelog"] = changelog
    entry = (
        f"{new_version}: Promoted from {current_status} to {desired_status} "
        f"({PHASE_LABEL}, {PROMOTION_DATE})."
    )
    changelog.append(entry)

    new_text = dump_yaml(data)
    if new_text == text:
        return False, None
    path.write_text(new_text, encoding="utf-8")
    summary = (
        f"{contract_id}: {current_status} → {desired_status}; "
        f"{current_version} → {new_version}"
    )
    return True, summary


def main() -> int:
    files = sorted(ROOT.glob(CONTRACT_GLOB))
    files = [f for f in files if "/templates/" not in f.as_posix()]
    promoted_to_proposed: list[str] = []
    promoted_to_approved: list[str] = []
    skipped = 0

    for path in files:
        changed, summary = promote_contract(path)
        if not changed or summary is None:
            skipped += 1
            continue
        if "→ approved" in summary:
            promoted_to_approved.append(summary)
        else:
            promoted_to_proposed.append(summary)

    total_changed = len(promoted_to_proposed) + len(promoted_to_approved)
    print(f"Promoted {total_changed} contract file(s).")
    print(f"  to proposed: {len(promoted_to_proposed)}")
    print(f"  to approved: {len(promoted_to_approved)}")
    print(f"  unchanged (already at target): {skipped}")
    if promoted_to_approved:
        print("\napproved cohort:")
        for line in promoted_to_approved:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
