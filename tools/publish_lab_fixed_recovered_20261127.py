#!/usr/bin/env python3
"""Publish the completed 2026-11-27 lab campaign, without CFD or native writes."""
import argparse
import fcntl
import json
from pathlib import Path
import shutil
import tempfile
import transfer_campaign_200s as transfer

HOME = Path.home() / "OpenFOAM"
REPORT = transfer.REPORT
PREFIX = "results/campaign-200s-fixed-lab-v2/"
ORDER = ("C14-3DA-200s", "C14-3DB-200s", "B14-2D-200s", "C14-2D-200s")

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def copy(src, dst):
    if src.is_dir():
        shutil.copytree(src, dst, symlinks=False)
    else:
        shutil.copy2(src, dst, follow_symlinks=True)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=HOME / "MasterProject")
    ap.add_argument("--fresh", type=Path, default=HOME / "CAMPAIGN_200S_FIXED_MPI8_FRESH/run-7rgdo1ih")
    ap.add_argument("--recovery", type=Path, default=HOME / "LAB_FIXED_RECOVERY_mxxgn4nb")
    a = ap.parse_args()
    url = transfer.root_url(a.repo)
    transfer.git("ls-remote", "--heads", url, capture=True)
    transfer.BATCH = 1
    root = HOME / "LAB_FIXED_PUBLICATION_V2"
    root.mkdir(exist_ok=True)
    with (root / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with (a.fresh.parent / ".queue.lock").open("a") as queue_lock:
            fcntl.flock(queue_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            run(a, url, root)

def run(a, url, root):
    summary = {}
    for name in ORDER:
        print("CASE", name, flush=True)
        try:
            serial = name == ORDER[0]
            recovered = name in ORDER[2:]
            native = (HOME / "CAMPAIGN_200S_COMPACT_01" if serial else a.fresh) / name
            case = a.recovery / name if recovered else native
            r = transfer.read(case / REPORT)
            need(r.get("solver_completed") is True and r.get("solver_steps") == 200000 and r.get("final_time_s") == 200, "incomplete solver report")
            need(r["runtime_audit"]["native_runtime_coverage_complete"] is True and not r["runtime_audit"]["errors"], "coverage audit not complete")
            if recovered:
                need(r["original_report_sha256"] == transfer.sha(native / REPORT), "native report changed")
                need(r["recovery"]["profiles_verified"] == 2001 and r["recovery"]["unique_points_per_profile"] == 80 and r["recovery"]["duplicates_removed"] == 2001, "unexpected recovery")
                evidence = transfer.read(case / "PROFILE_RECOVERY_EVIDENCE.json")
                need(len(evidence) == 2001, "missing recovery evidence")
                for i, e in enumerate(evidence):
                    t = format(i / 10, "g")
                    need(e["time"] == t and e["duplicates_removed"] == 1, "recovery timeline mismatch")
                    rel = Path("postProcessing/metal/verticalProfiles") / t / "line_x20mm.xy"
                    need(transfer.sha(native / rel) == e["original_sha256"] and transfer.sha(case / rel) == e["recovered_sha256"], "profile SHA mismatch " + t)
            branch = PREFIX + name
            metadata = {"kind": "fixed_lab_scientific_results", "case": name,
                        "solver_steps": 200000, "final_time_s": 200, "deltaT_s": .001,
                        "time_mode": "fixed", "execution_mode": "serial" if serial else "mpi",
                        "mpi_ranks": 1 if serial else 8,
                        "solver_log_sha256": transfer.sha(native / "log.foamMultiRun"),
                        "report_sha256": transfer.sha(case / REPORT),
                        "native_runtime_coverage_complete": True, "status": r["status"],
                        "volume_fields_included": False, "physical_validation": False,
                        "recovered_profiles": recovered}
            existing = transfer.complete_manifest(url, branch)
            if existing is not None:
                need(existing.get("complete") is True and all(existing.get(k) == v for k, v in metadata.items()), "remote completed result differs")
            else:
                with tempfile.TemporaryDirectory(prefix="stage-", dir=root) as tmp:
                    work = Path(tmp)
                    staged = work / name
                    staged.mkdir()
                    for filename in ("postProcessing", "logs", REPORT, "log.foamMultiRun",
                                     "log.foamLog", "log.decomposePar", "log.reconstructPar",
                                     "log.reconstructZero", "MPI_RUN_METADATA.json",
                                     "TIMING_STEPS.csv", "TIMING_MPI_RANKS.csv",
                                     "PROFILE_RECOVERY_EVIDENCE.json"):
                        p = case / filename
                        if p.exists():
                            copy(p, staged / filename)
                    if recovered:
                        copy(native / REPORT, staged / "ORIGINAL_CAMPAIGN_200S_REPORT.json")
                        copy(native / "postProcessing/metal/verticalProfiles", staged / "native_verticalProfiles")
                    archive = work / "result.tar.gz"
                    with transfer.deterministic_tar(archive) as t:
                        transfer.add(t, staged, name)
                    transfer.publish(url, branch, archive, metadata, work / "git", case=staged)
                existing = transfer.complete_manifest(url, branch)
                need(existing is not None and existing.get("complete") is True and all(existing.get(k) == v for k, v in metadata.items()), "remote manifest not confirmed")
            summary[name] = {"status": "PUBLISHED", "branch": branch, "archive_sha256": existing["archive_sha256"]}
        except Exception as exc:
            summary[name] = {"status": "BLOCKED_PRESERVED", "error": str(exc)}
        tmp_index = root / ".PUBLICATION_STATUS.tmp"
        tmp_index.write_text(json.dumps(summary, indent=2) + "\n")
        tmp_index.replace(root / "PUBLICATION_STATUS.json")
        print(json.dumps(summary[name], indent=2), flush=True)
    print("FINAL_PUBLICATION_STATUS", json.dumps(summary, indent=2), flush=True)
    print("NO CFD EXECUTED; NATIVE RESULTS PRESERVED", flush=True)
    if any(v["status"] != "PUBLISHED" for v in summary.values()):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
