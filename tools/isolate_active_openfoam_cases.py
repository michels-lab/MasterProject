#!/usr/bin/env python3
"""Fail-closed isolation for simultaneous OpenFOAM A/B/contraction worktrees.

Default --plan reads only. --apply creates missing A/B worktrees from the
already fetched origin/main snapshot, with NO upstream to prevent accidental
plain git pull. The active FS_C02_WORKTREE is only verified, never rebuilt.
Never pulls, fetches, remeshes, solves, resets, cleans or deletes CFD data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


SOURCE = "refs/remotes/origin/main"
CASES = (
    ("case_a", "C3D04_A_WORKTREE", "work/c3d04-a-isolated", True),
    ("case_b", "C3D05_B_WORKTREE", "work/c3d05-b-isolated", True),
    ("contraction", "FS_C02_WORKTREE",
     "research/fs-c02-metal-air-vof-20261117", False),
)
SAVED_RUNS = (
    "C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01",
    "C3D04_A_C14_FULL_POSTPROCESS_WORKCOPY_01",
    "C3D04_A_C14_3D_VOLUMETRIC_POSTPROCESS_01",
    "C3D05_T0_C14_SHK_01",
    "C3D05_STEP_GMSH_PILOT_01",
    "FS_C01_RUNS", "FS_C05_VOF_CHT_RUNS", "FS_C06_RUNS", "FS_C07_RUNS",
)


class Blocked(RuntimeError):
    pass


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    try:
        p = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False, text=True, capture_output=True,
        )
    except OSError as exc:
        raise Blocked("Git unavailable: " + str(exc)) from exc
    if check and p.returncode:
        raise Blocked(
            "git " + " ".join(args) + " failed: "
            + (p.stderr or p.stdout).strip()[:700]
        )
    return p


def common_dir(repo: Path) -> Path:
    raw = git(repo, "rev-parse", "--git-common-dir").stdout.strip()
    return (repo / raw).resolve()


def worktrees(repo: Path) -> dict[Path, dict[str, str]]:
    """Read porcelain; NEVER prune or modify existing worktree records."""
    entries: dict[Path, dict[str, str]] = {}
    current: dict[str, str] = {}
    lines = git(repo, "worktree", "list", "--porcelain").stdout.splitlines()
    for line in lines + [""]:
        if not line:
            if "worktree" in current:
                entries[Path(current["worktree"]).resolve()] = dict(current)
            current = {}
        elif line.startswith("worktree "):
            current["worktree"] = line[len("worktree "):]
        elif line.startswith("branch "):
            current["branch"] = line[len("branch "):]
        elif line.startswith("HEAD "):
            current["HEAD"] = line[len("HEAD "):]
        elif line in ("detached", "bare", "locked", "prunable"):
            current[line] = "true"
    return entries


def has_ref(repo: Path, ref: str) -> bool:
    return git(repo, "show-ref", "--verify", "--quiet", ref,
               check=False).returncode == 0


def within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def plan(repo: Path) -> dict:
    repo = repo.expanduser().resolve()
    if not repo.is_dir():
        raise Blocked("MasterProject checkout missing: " + str(repo))
    top = Path(git(repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if top != repo:
        raise Blocked("Expected top-level MasterProject checkout; got " + str(top))
    origin = git(repo, "remote", "get-url", "origin").stdout.strip()
    if not re.search(r"[:/]michels-lab/MasterProject(?:\.git)?$", origin):
        raise Blocked("Unexpected remote origin: " + origin)
    if not has_ref(repo, SOURCE):
        raise Blocked("origin/main absent. Fetch references only; do not pull active cases.")
    existing = worktrees(repo)
    same = common_dir(repo)
    openfoam = repo.parent
    protected = [(openfoam / name).resolve() for name in SAVED_RUNS]
    checks = []
    for label, folder, branch, can_create in CASES:
        dest = openfoam / folder
        target = dest.resolve()
        ref = "refs/heads/" + branch
        if dest.is_symlink():
            raise Blocked(label + ": destination is a symlink: " + str(dest))
        if within(target, repo) or any(
            within(target, run) or within(run, target) for run in protected
        ):
            raise Blocked(label + ": destination overlaps source or CFD runs")
        owners = [p for p, d in existing.items() if d.get("branch") == ref]
        if target in existing:
            info = existing[target]
            if not dest.is_dir() or info.get("branch") != ref:
                raise Blocked(label + ": unexpected existing worktree/branch")
            if common_dir(dest) != same:
                raise Blocked(label + ": existing worktree belongs to other Git repository")
            action = "EXISTING_PRESERVED"
        else:
            if dest.exists() or dest.is_symlink():
                raise Blocked(label + ": destination occupied, never overwrite " + str(dest))
            if owners:
                raise Blocked(label + ": branch already checked out at "
                              + ", ".join(map(str, owners)))
            if not can_create:
                raise Blocked(
                    "Existing FS_C02_WORKTREE not registered at expected path. "
                    "Contraction may be running elsewhere; refuse to rebuild or move it."
                )
            if has_ref(repo, ref):
                raise Blocked(label + ": local branch exists; do not repurpose it")
            action = "CREATE_FROM_ORIGIN_MAIN_SNAPSHOT"
        if owners and target not in owners:
            raise Blocked(label + ": conflicting existing branch owner")
        checks.append({
            "case": label, "path": str(target), "branch": branch,
            "action": action, "head": existing.get(target, {}).get("HEAD"),
        })
    return {
        "schema": "MASTERPROJECT_WSL_CONCURRENT_ISOLATION_V1",
        "repository": str(repo),
        "origin_main_snapshot": git(repo, "rev-parse", SOURCE).stdout.strip(),
        "worktrees": checks,
        "protected_runs": [
            {"path": str(p), "exists": p.exists()} for p in protected
        ],
        "safety": (
            "Does not touch solver inputs/outputs. Existing contraction remains "
            "untouched. New A/B branches have no upstream. No automatic pulls."
        ),
    }


def apply(repo: Path, checked: dict) -> dict:
    # Validate ALL 3 worktree paths and branch owners before the first write.
    for item in checked["worktrees"]:
        if item["action"] == "CREATE_FROM_ORIGIN_MAIN_SNAPSHOT":
            git(repo, "worktree", "add", "--no-track", "-b",
                item["branch"], item["path"], SOURCE)
    verified = plan(repo)
    if any(x["action"] != "EXISTING_PRESERVED" for x in verified["worktrees"]):
        raise Blocked("New worktrees failed the post-creation safety audit")
    for item in verified["worktrees"][:2]:
        upstream = git(
            Path(item["path"]), "rev-parse", "--abbrev-ref",
            "--symbolic-full-name", "@{upstream}", check=False,
        )
        if upstream.returncode == 0:
            raise Blocked("Unsafe upstream set for " + item["case"])
    verified["operation"] = "APPLIED_AND_VERIFIED"
    return verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true")
    modes.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--repo", type=Path,
        default=Path.home() / "OpenFOAM" / "MasterProject",
    )
    args = parser.parse_args()
    try:
        checked = plan(args.repo)
        if args.apply:
            checked = apply(args.repo.expanduser().resolve(), checked)
        else:
            checked["operation"] = "READ_ONLY_PLAN"
        print(json.dumps(checked, indent=2, ensure_ascii=False))
        return 0
    except Blocked as exc:
        print("WORKTREE_ISOLATION_BLOCKED:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
