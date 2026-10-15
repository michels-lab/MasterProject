#!/usr/bin/env python3
"""Strict, read-only preflight for the paired QuickCup V15/V16 input variants.

Checks provenance and controlled input changes. Does NOT execute OpenFOAM and
does NOT establish numerical convergence, physical accuracy or experiment fit.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = "cases_controlled_buoyancy"
INPUT_DIRS = ("0", "constant", "system")
RUN_SCRIPTS = ("Allrun", "Allclean")

VARIANTS = (
    ("B14_topFixedFlux_explicitRef", "B15_adaptiveDt_fromB14", "system/controlDict",
     {"adjustTimeStep": ("no", "yes"),
      "writeControl": ("timeStep", "adjustableRunTime"),
      "writeInterval": ("100", "0.1")}),
    ("C14_topFixedFlux_explicitRef", "C15_adaptiveDt_fromC14", "system/controlDict",
     {"adjustTimeStep": ("no", "yes"),
      "writeControl": ("timeStep", "adjustableRunTime"),
      "writeInterval": ("100", "0.1")}),
    ("B14_topFixedFlux_explicitRef", "B16_phaseRelax025_fromB14",
     "constant/metal/fvModels", {"relax": ("0.1", "0.25")}),
    ("C14_topFixedFlux_explicitRef", "C16_phaseRelax025_fromC14",
     "constant/metal/fvModels", {"relax": ("0.1", "0.25")}),
)


def input_files(case: Path, input_dirs: tuple[str, ...] = INPUT_DIRS) -> dict[str, Path]:
    result = {}
    for dirname in input_dirs:
        directory = case / dirname
        if not directory.is_dir():
            raise ValueError(f"Required input directory missing: {directory}")
        for file in directory.rglob("*"):
            if file.is_file():
                result[file.relative_to(case).as_posix()] = file
    for name in RUN_SCRIPTS:
        path = case / name
        if not path.is_file():
            raise ValueError(f"Required run script missing: {path}")
        result[name] = path
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def active_text(text: str) -> str:
    """Remove C-style and // comments without treating appendix text as input."""
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.DOTALL)


def parameter_value_and_mask(text: str, key: str) -> tuple[str, str]:
    pattern = re.compile(r"(?m)^(\s*" + re.escape(key) + r"\s+)([^;]*)(;)")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"Expected one active assignment of {key}; found {len(matches)}")
    original = matches[0].group(2).strip()
    masked = pattern.sub(lambda m: m.group(1) + "<CONTROLLED>" + m.group(3), text)
    return original, masked


def copied_evidence(case: Path) -> list[str]:
    """Prepared variants must contain no solver state or inherited evidence."""
    bad = []
    for child in case.iterdir():
        name = child.name
        if (name in {"logs", "postProcessing", "processor0"} or
                re.fullmatch(r"processor\d+", name) or
                re.fullmatch(r"(?:\d+\.?\d*|\.\d+)", name) and name != "0" or
                name.startswith("log.")):
            bad.append(name)
    return sorted(bad)


def audit_pair(cases_root: Path, spec: tuple, mode: str = "prepared") -> list[str]:
    parent_name, child_name, target, allowed = spec
    parent = cases_root / parent_name
    child = cases_root / child_name
    issues = []
    if not parent.is_dir() or not child.is_dir():
        return [f"Missing parent or variant: {parent_name} / {child_name}"]

    evidence = copied_evidence(child)
    if mode == "prepared" and evidence:
        issues.append("Prepared case includes simulation output: " + ", ".join(evidence))
    if mode == "post-run" and not evidence:
        issues.append("Post-run mode requested but no runtime evidence was found")
    # Runtime function objects can legitimately rewrite diagnostic fields in 0/.
    # In post-run mode assert constant/system and Allrun/Allclean parity only.
    # Initial 0/ fields and numerical validity require a separate audit.
    check_dirs = ("system", "constant") if mode == "post-run" else INPUT_DIRS
    try:
        old = input_files(parent, check_dirs)
        new = input_files(child, check_dirs)
    except ValueError as exc:
        return issues + [str(exc)]

    missing = sorted(old.keys() - new.keys())
    added = sorted(new.keys() - old.keys())
    if missing:
        issues.append("Missing inputs: " + ", ".join(missing))
    if added:
        issues.append("Extra inputs: " + ", ".join(added))
    diffs = sorted(p for p in old.keys() & new.keys()
                   if sha256(old[p]) != sha256(new[p]))
    if diffs != [target]:
        issues.append(f"Expected sole changed input {target}, observed {diffs}")

    if target in old and target in new:
        source = active_text(old[target].read_text(encoding="utf-8"))
        variant = active_text(new[target].read_text(encoding="utf-8"))
        for key, (expected_parent, expected_child) in allowed.items():
            try:
                pval, source = parameter_value_and_mask(source, key)
                cval, variant = parameter_value_and_mask(variant, key)
            except ValueError as exc:
                issues.append(str(exc))
                continue
            if (pval, cval) != (expected_parent, expected_child):
                issues.append(
                    f"{key}: expected {expected_parent!r} -> {expected_child!r}; "
                    f"observed {pval!r} -> {cval!r}")
        if " ".join(source.split()) != " ".join(variant.split()):
            issues.append("Unexpected additional active statement change in controlled file")
    return issues


def audit_all(cases_root: Path = ROOT / CASES, mode: str = "prepared") -> dict[str, list[str]]:
    result = {}
    for spec in VARIANTS:
        selected = mode
        if mode == "auto":
            selected = "post-run" if copied_evidence(cases_root / spec[1]) else "prepared"
        result[spec[1]] = audit_pair(cases_root, spec, selected)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / CASES,
                        help="Directory containing controlled case folders")
    parser.add_argument("--mode", choices=("prepared", "post-run", "auto"),
                        default="prepared", help="Use auto after laptop runs are pushed")
    parser.add_argument("--strict", action="store_true",
                        help="Fail with exit code 1 if any case violates provenance")
    args = parser.parse_args()
    report = audit_all(args.root, args.mode)
    for case, issues in report.items():
        print(f"{'PASS' if not issues else 'FAIL'} {case}")
        for issue in issues:
            print("  - " + issue)
    failed = sum(bool(value) for value in report.values())
    print(f"Preflight: {len(report) - failed}/{len(report)} cases meet input-only controls")
    print("No simulation was run. Post-run mode excludes 0/ from input parity;")
    print("verify initial fields and scientific evidence separately. Not physical validation.")
    return 1 if failed and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
