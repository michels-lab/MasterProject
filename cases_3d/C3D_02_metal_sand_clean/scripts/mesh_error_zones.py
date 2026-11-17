#!/usr/bin/env python3
"""Mandatory OpenFOAM C3D-02 error localization on every integrated build.

Called automatically by build_c3d02.py. It copies any AVAILABLE polyMesh to
an isolated diagnostic case, calls checkMesh with VTK exports, and records
actual error SET geometries (bounding box X/Y/Z in mm and Y intervals).
It NEVER modifies the source polyMesh, never launches CFD, and never hides a
mesh failure. If no mesh exists, reports the failing stage and log evidence.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from analyze_bad_mesh_vtk import vtk_points

Y_BANDS_MM = (-65.5, -49.125, -32.75, -16.375, 0.0)
METRICS = {
    "metal": {"CAD_cm3": 47.9874896432},
    "mold": {"CAD_cm3": 102.84309608},
}


def parse_checkmesh(log: str) -> dict:
    sets = {}
    for m in re.finditer(r"<<Writing\s+(\d+)\b[^\n]*?\bto set\s+(\w+)", log):
        sets[m.group(2)] = int(m.group(1))
    return {
        "cell_count": _number(log, r"(?m)^\s*cells:\s*(\d+)"),
        "failed_checks": _number(log, r"Failed\s+(\d+)\s+mesh checks", 0),
        "volume_m3": _float(log, r"Total volume\s*=\s*([0-9.eE+-]+)"),
        "mesh_ok": bool(re.search(r"(?m)^\s*Mesh OK", log)) and
                   not bool(re.search(r"Failed\s+[1-9]\d*\s+mesh checks", log)),
        "problem_sets": sets,
        "issues": [line.strip() for line in log.splitlines()
                   if line.lstrip().startswith("***") or
                   re.search(r"Failed [1-9]\d* mesh checks", line)][-40:],
    }


def _number(s, pattern, default=None):
    m = re.search(pattern, s)
    return int(m.group(1)) if m else default


def _float(s, pattern, default=None):
    m = re.search(pattern, s)
    return float(m.group(1)) if m else default


def vtk_bounds(vtk: Path) -> dict:
    """Bounds of exported VTK surface vertices, not volume-cell centroids."""
    low = [float("inf")] * 3
    high = [-float("inf")] * 3
    sums = [0.0] * 3
    bands = [0] * 4
    count = 0
    outside = 0
    for xyz in vtk_points(vtk):
        count += 1
        for axis, value in enumerate(xyz):
            mm = value * 1000
            low[axis] = min(low[axis], mm)
            high[axis] = max(high[axis], mm)
            sums[axis] += mm
        y = xyz[1] * 1000
        if Y_BANDS_MM[0] - 0.001 <= y <= Y_BANDS_MM[-1] + 0.001:
            index = max(0, min(3, int((y - Y_BANDS_MM[0]) / 16.375)))
            bands[index] += 1
        else:
            outside += 1
    if not count:
        return {"vtk_vertices": 0, "warning": "Empty VTK geometry"}
    return {
        "vtk_vertices": count,
        "bounding_box_mm": {
            name: [round(low[i], 5), round(high[i], 5)]
            for i, name in enumerate("XYZ")
        },
        "vertex_mean_mm": {
            name: round(sums[i] / count, 5) for i, name in enumerate("XYZ")
        },
        "axial_Y_bands_vertex_counts": [
            {"interval_mm": [Y_BANDS_MM[i], Y_BANDS_MM[i + 1]],
             "vertices": bands[i]}
            for i in range(4)
        ],
        "vertices_outside_nominal_Y": outside,
        "warning": "Counts are VTK surface VERTICES, not counts or centres of bad mesh cells.",
    }


def _evidence_from_run(case: Path, stage: str) -> dict:
    report = {
        "schema": "C3D02_AUTO_ERROR_ZONES_V1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "source_case": str(case),
        "message": "Automatic error localization ran for every available mesh.",
        "regions": {},
        "pipeline_logs": {},
        "interpretation": (
            "Error coordinates are VTK SURFACE VERTEX extents, not exact "
            "cell centroids. Absence of VTK does not mean absence of errors."
        ),
    }
    for logfile in sorted(case.glob("log.*")):
        if not logfile.is_file():
            continue
        try:
            lines = logfile.read_text(errors="replace").splitlines()
            findings = [line.strip() for line in lines
                        if "FOAM FATAL" in line or "ERROR" in line or "Failed " in line
                        or line.lstrip().startswith("***")]
            if findings:
                report["pipeline_logs"][logfile.name] = findings[-12:]
        except OSError as exc:
            report["pipeline_logs"][logfile.name] = [str(exc)]
    return report


def run_error_localization(case: Path, stage: str) -> dict:
    """Never raise: diagnostics must not suppress the true build failure."""
    case = Path(case).resolve()
    report = _evidence_from_run(case, stage)
    diagnostics = case / "error_diagnostics"
    diagnostics.mkdir(exist_ok=True)
    for region in ("global", "metal", "mold"):
        source = (case / "constant/polyMesh" if region == "global"
                  else case / "constant" / region / "polyMesh")
        if not (source / "owner").is_file():
            report["regions"][region] = {
                "available": False,
                "reason": f"No polyMesh for {region} at stage {stage}",
            }
            continue
        target = diagnostics / region
        result = {"available": True, "copied_case": str(target)}
        report["regions"][region] = result
        try:
            if target.exists():
                # Diagnostics in THIS build directory may be regenerated;
                # source meshes are never under error_diagnostics.
                shutil.rmtree(target)
            (target / "constant").mkdir(parents=True)
            (target / "system").mkdir()
            shutil.copytree(source, target / "constant/polyMesh",
                            symlinks=False)
            original_control = case / "system/controlDict"
            if not original_control.is_file():
                original_control = (
                    Path(__file__).resolve().parents[1] / "system/controlDict"
                )
            shutil.copy2(original_control, target / "system/controlDict")
            cmd = (
                'source /opt/openfoam14/etc/bashrc && '
                'checkMesh -case "$1" -allGeometry -allTopology '
                '-writeSurfaces -writeSets'
            )
            proc = subprocess.run(
                ["bash", "-c", cmd, "c3d02-checkMesh", str(target)],
                cwd=target, capture_output=True, text=True, errors="replace"
            )
            log = (proc.stdout or "") + (proc.stderr or "")
            (target / "log.checkMesh.auto").write_text(log)
            result["checkMesh_rc"] = proc.returncode
            result.update(parse_checkmesh(log))
            result["vtk_problems"] = {}
            for vtk in sorted((target / "postProcessing").rglob("*.vtk")) \
                    if (target / "postProcessing").is_dir() else ():
                try:
                    result["vtk_problems"][vtk.stem] = {
                        "file": str(vtk),
                        **vtk_bounds(vtk),
                    }
                except (OSError, ValueError, OverflowError) as exc:
                    result["vtk_problems"][vtk.stem] = {
                        "file": str(vtk), "parse_error": str(exc),
                    }
            if not result["vtk_problems"] and result["failed_checks"]:
                result["diagnostic_warning"] = (
                    "checkMesh reported failures but no VTK was produced. "
                    "See log.checkMesh.auto and check permissions/options."
                )
        except Exception as exc:
            result["diagnostic_error"] = str(exc)
            result["note"] = "Original mesh remains untouched."
    report["has_mesh_quality_failures"] = any(
        x.get("failed_checks", 0) > 0 or
        (x.get("available") and x.get("mesh_ok") is False)
        for x in report["regions"].values()
    )
    _write(report, case)
    return report


def _write(report: dict, case: Path) -> None:
    (case / "ERROR_ZONES.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    md = [
        "# C3D-02 — Reporte automático de errores por zona",
        "",
        f"**Etapa:** \`{report['stage']}\`",
        "",
        "La localización se ejecuta automáticamente al terminar o bloquearse "
        "el comando principal. Los archivos VTK pertenecen a copias de diagnóstico.",
        "",
    ]
    for region, result in report["regions"].items():
        md.extend([f"## {region}", ""])
        if not result.get("available"):
            md.extend([
                f"No existe malla en esta etapa: {result.get('reason', '')}.",
                ""
            ])
            continue
        md.extend([
            f"- Celdas: {result.get('cell_count', 'no disponible')}",
            f"- Comprobaciones fallidas: {result.get('failed_checks', 'desconocidas')}",
            f"- \`checkMesh\` aprobado: {result.get('mesh_ok', 'sin determinar')}",
            f"- Log: \`{result['copied_case']}/log.checkMesh.auto\`",
        ])
        for issue in result.get("issues", []):
            md.append(f"- Incidencia: {issue}")
        if not result.get("vtk_problems"):
            md.append("- VTK: no disponible; revisar log de checkMesh")
        for name, detail in result.get("vtk_problems", {}).items():
            md.append(f"- **{name}** — \`{detail['file']}\`")
            if "bounding_box_mm" in detail:
                for axis, bounds in detail["bounding_box_mm"].items():
                    md.append(f"  - {axis}: {bounds[0]} .. {bounds[1]} mm")
                md.append(
                    "  - Bandas Y (VÉRTICES, no celdas): "
                    + ", ".join(
                        f"{item['interval_mm'][0]}..{item['interval_mm'][1]} mm:"
                        f"{item['vertices']}"
                        for item in detail.get("axial_Y_bands_vertex_counts", [])
                    )
                )
            elif "parse_error" in detail:
                md.append("  - No se pudieron leer coordenadas: " + detail["parse_error"])
        md.append("")
    if report["pipeline_logs"]:
        md.extend(["## Fallos de ejecución anteriores", ""])
        for log, errors in report["pipeline_logs"].items():
            md.append(f"**{log}**")
            md.extend(f"- {x}" for x in errors)
            md.append("")
    md.extend([
        "## Limitaciones",
        "",
        "- Las coordenadas proceden de vértices de superficies VTK, NO de "
        "centroides exactos de las celdas defectuosas.",
        "- Cuando falla el mallado antes de crear un polyMesh, se registra "
        "la etapa y el fallo; no se inventan coordenadas.",
        "- Sin malla aprobada ni parches térmicos recíprocos no se ejecuta CFD.",
        "",
    ])
    (case / "ERROR_ZONES.md").write_text("\n".join(md), encoding="utf-8")


def self_test() -> None:
    sample = (
        "cells: 100\nTotal volume = 0.0002\n"
        " ***Concave cells found, number of cells: 2\n"
        " <<Writing 2 concave cells to set concaveCells\n"
        "Failed 1 mesh checks.\n"
    )
    out = parse_checkmesh(sample)
    assert out["failed_checks"] == 1
    assert out["problem_sets"]["concaveCells"] == 2
    assert not out["mesh_ok"]
    with __import__("tempfile").TemporaryDirectory() as folder:
        case = Path(folder)
        report = run_error_localization(case, "PREFLIGHT")
        assert all(not x["available"] for x in report["regions"].values())
        assert (case / "ERROR_ZONES.json").is_file()
        assert (case / "ERROR_ZONES.md").is_file()
    print("OK: diagnostics always produce report, parse set counts, and work before mesh exists")


if __name__ == "__main__":
    import argparse
    cli = argparse.ArgumentParser()
    cli.add_argument("--case", type=Path)
    cli.add_argument("--stage", default="PREFLIGHT")
    cli.add_argument("--self-test", action="store_true")
    args = cli.parse_args()
    if args.self_test:
        self_test()
    else:
        if not args.case:
            cli.error("--case is required")
        run_error_localization(args.case, args.stage)
