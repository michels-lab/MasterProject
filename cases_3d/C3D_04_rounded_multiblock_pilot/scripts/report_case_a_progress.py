#!/usr/bin/env python3
"""Enforce and print canonical C3D-04-A progress on every integrated milestone.

No hand-estimated percentages, no connection to C3D-05, no CFD.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
STATUS_FILE = REPO / "docs/C3D04_CASE_A_STATUS.json"


def report(path: Path) -> dict:
    status = json.loads(path.read_text(encoding="utf-8"))
    milestone = status.get("milestones")
    assert status.get("scope") == "CASE_A_C3D_04_V4_T02_ONLY", "Wrong case/status!"
    assert isinstance(milestone, list) and len(milestone) == 10, "Expected 10 milestone gates"
    ids = [entry["id"] for entry in milestone]
    assert len(set(ids)) == 10, "Duplicate milestone IDs"
    phases = [entry["status"] for entry in milestone]
    assert all(x in ("DONE", "IN_PROGRESS", "PENDING") for x in phases), "Unknown phase state"
    assert phases.count("IN_PROGRESS") == 1, "Exactly one active phase required"
    n = phases.count("DONE")
    active = next(x for x in milestone if x["status"] == "IN_PROGRESS")
    assert status["progress_count_done"] == n, "Stale progress count"
    assert status["progress_count_total"] == len(milestone), "Stale denominator"
    assert status["progress_percent"] == 100*n/len(milestone), "Stale percentage"
    assert status["current_stage"] == active["id"], "Active phase contradicts status"
    for entry in milestone:
        if entry["status"] == "DONE":
            assert entry.get("evidence"), f"DONE without evidence: {entry['id']}"
    assert status["CFD_run"] is False or active["id"] not in ("05_THERMAL_T0_DESIGN",), (
        "Do not mark unexecuted T0 CFD as run"
    )
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", type=Path, default=STATUS_FILE)
    args = parser.parse_args()
    d = report(args.status)
    stage = next(i+1 for i, m in enumerate(d["milestones"])
                 if m["status"] == "IN_PROGRESS")
    print(f"CASO A C3D-04 | ETAPA {stage}/{d['progress_count_total']}: "
          f"{d['milestones'][stage-1]['label']}")
    print(f"AVANCE OPERATIVO (HITOS CON EVIDENCIA): "
          f"{d['progress_count_done']}/{d['progress_count_total']} = "
          f"{d['progress_percent']:g}%")
    print("Esto NO es porcentaje de validacion fisica ni plazo.")
    print(f"CFD ejecutado: {d['CFD_run']} | "
          f"independencia de malla: {d['grid_independence']} | "
          f"validacion experimental: {d['physical_validation']}")
    print("Siguiente entrega: paquete integral, no comandos por microprueba.")
    print("STATUS_CONTRACT_OK")


if __name__ == "__main__":
    main()
