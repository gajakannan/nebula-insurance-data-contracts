#!/usr/bin/env python3
"""Orchestrate Fabric artifact generation from canonical ODCS contracts.

Runs the four sub-generators in dependency order, then runs the manifest
drift validator with full-coverage required. The orchestrator is a thin
shim: each sub-generator owns its own arguments, output, and exit codes,
and the orchestrator stops as soon as any step fails so a downstream
artifact never reflects an upstream half-finished state.

Run order:

    1. generate-fabric-manifests.py   (ODCS YAML  -> *.fabric.yaml)
    2. generate-fabric-purview.py     (manifests + glossary -> Purview JSON)
    3. generate-fabric-ddl.py         (manifests -> Spark SQL CREATE TABLE)
    4. generate-fabric-notebooks.py   (template notebooks + lakehouse binding)
    5. validate-fabric-manifests.py   (manifest drift; --require-full-coverage)

Steps 2 and 3 both consume the manifest set produced by step 1. Step 4
emits parameterized notebook templates that read manifests at runtime,
so it does not consume the manifest files at generation time and is run
last for output ordering. Validation comes after every generator so a
green orchestrator run is the same green check the persona flow in
``planning-mds/FABRIC_IMPLEMENTATION_PLAN.md`` §3.3.3 step 2 describes.

Authoritative spec: ``planning-mds/FABRIC_IMPLEMENTATION_PLAN.md``
§15.5 / §17 (F8) and ``targets/fabric/README.md`` §"Generation flow at
a glance".
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATION_DIR = ROOT / "scripts" / "validation"


@dataclass
class Step:
    label: str
    script: Path
    args: tuple[str, ...] = ()


def _build_steps(skip_validate: bool) -> list[Step]:
    steps = [
        Step(
            label="Generate manifests",
            script=SCRIPT_DIR / "generate-fabric-manifests.py",
        ),
        Step(
            label="Generate Purview manifests",
            script=SCRIPT_DIR / "generate-fabric-purview.py",
        ),
        Step(
            label="Generate Spark SQL DDL",
            script=SCRIPT_DIR / "generate-fabric-ddl.py",
        ),
        Step(
            label="Generate notebook templates",
            script=SCRIPT_DIR / "generate-fabric-notebooks.py",
        ),
    ]
    if not skip_validate:
        steps.append(
            Step(
                label="Validate manifest drift",
                script=VALIDATION_DIR / "validate-fabric-manifests.py",
                args=("--require-full-coverage",),
            )
        )
    return steps


def _run(step: Step) -> tuple[int, float]:
    if not step.script.exists():
        print(f"error: missing script {step.script.relative_to(ROOT)}", file=sys.stderr)
        return 1, 0.0
    cmd = [sys.executable, str(step.script), *step.args]
    rel_script = Path(cmd[1]).relative_to(ROOT).as_posix()
    print(f"\n==> {step.label}: {rel_script} {' '.join(step.args)}".rstrip(), flush=True)
    start = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, check=False)
    elapsed = time.perf_counter() - start
    return proc.returncode, elapsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help=(
            "Skip the trailing validate-fabric-manifests.py drift check. Useful"
            " when iterating on a generator and intentionally producing partial"
            " output; CI runs should leave validation on."
        ),
    )
    args = parser.parse_args(argv)

    steps = _build_steps(skip_validate=args.skip_validate)
    results: list[tuple[Step, int, float]] = []
    failed_at: int | None = None

    for index, step in enumerate(steps):
        code, elapsed = _run(step)
        results.append((step, code, elapsed))
        if code != 0:
            failed_at = index
            break

    print("\n==> Summary")
    label_width = max(len(s.label) for s in steps)
    for step, code, elapsed in results:
        status = "OK" if code == 0 else f"FAIL (exit {code})"
        print(f"  {step.label.ljust(label_width)}  {elapsed:6.2f}s  {status}")
    skipped = steps[len(results):]
    for step in skipped:
        print(f"  {step.label.ljust(label_width)}  ------  SKIPPED")

    if failed_at is not None:
        failed_step = results[failed_at][0]
        print(f"\nFAILED at step {failed_at + 1}: {failed_step.label}.")
        return 1

    if args.skip_validate:
        print(
            "\nDone (validation skipped). Run "
            "scripts/validation/validate-fabric-manifests.py --require-full-coverage "
            "before relying on the artifact set."
        )
    else:
        print("\nDone. Manifests, Purview, DDL, notebooks regenerated and validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
