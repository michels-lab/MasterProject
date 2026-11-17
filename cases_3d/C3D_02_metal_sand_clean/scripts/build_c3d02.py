#!/usr/bin/env python3
"""One-command C3D-02: common mesh -> coupled regions -> quality -> C14 -> solver.

Never overwrite prior experiments. Only run foamMultiRun after both regions
and their reciprocal mappedWall interface pass strict geometry checks.
Requires actual Foundation 14 on the user's Ubuntu WSL; static CI cannot
certify numerical results.
"""
import argparse
import json
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from mesh_error_zones import run_error_localization

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
C14 = REPO / "cases_controlled_buoyancy/C14_topFixedFlux_explicitRef"
CAD = {"metal": 0.0000479874896432, "mold": 0.00010284309608}
METAL_POINT = "(0.0259 -0.0200 0.0259)"
STL = {"metal": "metal.stl", "mold": "mold_repaired.stl"}


def snappy_dictionary():
    source = (ROOT / "system/materialSingle/snappyHexMeshDict.template").read_text()
    if source.count("snapControls\n") != 1:
        raise ValueError("Cannot reuse approved snapControls template")
    tail = "snapControls\n" + source.split("snapControls\n", 1)[1]
    return """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object snappyHexMeshDict;
}
castellatedMesh true;
snap true;
addLayers false;
geometry
{
    metal { type triSurfaceMesh; file "metal.stl"; units [mm]; }
    mold { type triSurfaceMesh; file "mold_repaired.stl"; units [mm]; }
}
castellatedMeshControls
{
    maxLocalCells 400000;
    maxGlobalCells 3000000;
    minRefinementCells 0;
    nCellsBetweenLevels 2;
    features ();
    refinementSurfaces
    {
        metal
        {
            level (2 2);
            faceZone metalInterface;
            cellZone metal;
            mode inside;
            faceType internal;
            patchInfo { type wall; }
        }
        mold
        {
            level (2 2);
            faceZone moldInterface;
            cellZone mold;
            mode inside;
            faceType internal;
            patchInfo { type wall; }
        }
    }
    resolveFeatureAngle 30;
    refinementRegions {}
    insidePoints
    (
        (0.0259 -0.0200 0.0259)
        (0.0043 -0.0207 0.0259)
        (-0.002 -0.068 -0.002)
    );
    allowFreeStandingZoneFaces false;
}
""" + tail


def foam_block(source, name):
    m = re.search(r"(?m)^\s*" + re.escape(name) + r"\s*\{", source)
    if not m:
        return None
    left = source.index("{", m.start())
    depth = 1
    pos = left + 1
    while depth and pos < len(source):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
        pos += 1
    if depth:
        raise ValueError("Unbalanced dictionary braces: " + name)
    return m.start(), pos, source[left+1:pos-1]


def boundary_entries(path):
    text = path.read_text(errors="replace")
    result = {}
    for m in re.finditer(r"(?m)^\s*([A-Za-z]\w*)\s*\{([^{}]*)\}", text, re.S):
        body = m.group(2)
        def val(key):
            match = re.search(r"(?m)^\s*" + key + r"\s+(\w+);", body)
            return match.group(1) if match else None
        if val("type"):
            result[m.group(1)] = {
                "type": val("type"), "nFaces": int(val("nFaces") or 0),
                "neighbourRegion": val("neighbourRegion"),
                "neighbourPatch": val("neighbourPatch"),
            }
    return result


def discard_exterior_coupling(path):
    # The third cellZone, exterior, is NOT a solver region. Its interfaces
    # become physical walls; the metal-mold interface remains mappedWall.
    raw = path.read_text()
    pattern = re.compile(r"(?m)^(\s*)([A-Za-z]\w*)\s*\{([^{}]*)\}", re.S)
    def edit(m):
        name, body = m.group(2), m.group(3)
        if re.search(r"\bneighbourRegion\s+exterior;", body):
            if not re.search(r"\btype\s+mappedWall;", body):
                raise ValueError("Unexpected non-mapped exterior patch: " + name)
            body = re.sub(r"\btype\s+mappedWall;", "type wall;", body)
            body = re.sub(r"(?m)^\s*neighbour(?:Region|Patch)\s+\w+;[ \t]*\n", "\n", body)
            body = re.sub(r"(?m)^\s*sample(?:Region|Patch|Mode)\s+\w+;[ \t]*\n", "\n", body)
        return m.group(1) + name + "\n{" + body + "}"
    path.write_text(pattern.sub(edit, raw))


def field_with_3d_patches(source, region, patches, field):
    block = foam_block(source, "boundaryField")
    if block is None:
        raise ValueError("C14 field lacks boundaryField: " + region + "/" + field)
    start, end, inside = block
    choices = {}
    # CoupledTemperature contains nested h{...}; DO NOT parse via [^{}]*.
    for name in ("metalTop", "moldTop", "metal_to_mold", "mold_to_metal"):
        found = foam_block(inside, name)
        if found is not None:
            choices[name] = found[2].strip()
    contact = "metal_to_mold" if region == "metal" else "mold_to_metal"
    exterior = "metalTop" if region == "metal" else "moldTop"
    parts = []
    for name, data in patches.items():
        # Even an empty mesh patch requires a matching boundaryField entry in
        # OpenFOAM; do not silently drop zero-face patches.
        if data["type"] == "mappedWall":
            if name != contact or data["neighbourRegion"] not in ("metal", "mold"):
                raise ValueError("Unexpected non-contact mappedWall: " + name)
            bc = choices.get(contact)
            if bc is None and field == "T":
                raise ValueError("Missing C14 coupledTemperature for " + contact)
        else:
            bc = choices.get(exterior)
        if bc is None:
            raise ValueError(
                "Missing C14 boundary condition for " + region + "/" + field
                + " at patch " + name + "; implicit zeroGradient is forbidden"
            )
        if field == "T" and data["type"] == "mappedWall" and not re.search(
            r"\btype\s+coupledTemperature\s*;", bc
        ):
            raise ValueError("C14 temperature contact is not coupledTemperature: " + name)
        if re.search(r"\btype\s+empty\s*;", bc):
            raise ValueError("Cannot copy a 2D empty patch to 3D")
        parts.append("    " + name + "\n    {\n        " + bc + "\n    }")
    return source[:start] + "\nboundaryField\n{\n" + "\n".join(parts) + "\n}\n" + source[end:]


def status(case, stage, ok, message, **extra):
    record = {"stage": stage, "ok": ok, "message": message, "output": str(case),
              "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **extra}
    case.mkdir(parents=True, exist_ok=True)
    # MANDATORY: error-location report on success AND on every failure,
    # even if preflight/snappy aborted before any physical region exists.
    try:
        details = run_error_localization(case, stage)
        record["error_zones"] = str(case / "ERROR_ZONES.json")
        record["error_zones_summary"] = str(case / "ERROR_ZONES.md")
        record["regions_examined"] = sorted(
            k for k, v in details["regions"].items() if v.get("available")
        )
        if details["has_mesh_quality_failures"]:
            record["mesh_error_zones_detected"] = True
    except Exception as diagnostic_exc:
        # An error in diagnostics must never mask the primary CFD/build failure.
        record["error_zones_failure"] = str(diagnostic_exc)
        (case / "ERROR_ZONES.md").write_text(
            "# C3D-02 — Error del diagnóstico automático\n\n"
            + str(diagnostic_exc) + "\n"
        )
        (case / "ERROR_ZONES.json").write_text(
            json.dumps({"stage": stage, "diagnostic_error": str(diagnostic_exc)},
                       ensure_ascii=False, indent=2) + "\n"
        )
    (case / "BUILD_STATUS.json").write_text(json.dumps(record, indent=2, ensure_ascii=False)+"\n")
    print("\n=== ESTADO FINAL C3D-02 ===\n"+json.dumps(record, indent=2, ensure_ascii=False), flush=True)


def run(case, cmd, logfile):
    command = "source /opt/openfoam14/etc/bashrc && " + shlex.join(cmd)
    print("→ " + shlex.join(cmd), flush=True)
    target = case / logfile
    with target.open("w") as out:
        rc = subprocess.call(["bash", "-lc", command], cwd=case,
                             stdout=out, stderr=subprocess.STDOUT)
    log = target.read_text(errors="replace")
    if rc:
        raise RuntimeError(logfile + " failed rc=" + str(rc) + "\n" + "\n".join(log.splitlines()[-24:]))
    return log


def quality(case, region):
    log = run(case, ["checkMesh", "-case", str(case), "-region", region,
                     "-allGeometry", "-allTopology"], "log.checkMesh." + region)
    def match(expr, default=None):
        m = re.search(expr, log, re.I | re.M)
        return m.group(1) if m else default
    cells = match(r"^\s*cells:\s*(\d+)")
    vol = match(r"Total volume\s*=\s*([0-9eE+.-]+)")
    nr = match(r"Number of regions:\s*(\d+)")
    if not cells or not vol or not nr:
        raise RuntimeError("Incomplete checkMesh output: " + region)
    return {
        "cells": int(cells), "volume_m3": float(vol),
        "deviation_cad_pct": 100 * (float(vol) / CAD[region] - 1),
        "regions": int(nr),
        "concave": int(match(r"Concave cells .*?number of cells:\s*(\d+)", "0")),
        "failed_checks": int(match(r"Failed\s+(\d+)\s+mesh checks", "0")),
        "mesh_ok": "Mesh OK" in log and not re.search(r"Failed\s+[1-9]\d*\s+mesh checks", log),
    }


def gates(q, patches):
    errors = []
    for region in ("metal", "mold"):
        value = q[region]
        if value["cells"] <= 0 or value["regions"] != 1 or abs(value["deviation_cad_pct"]) > 2:
            errors.append(region + ": volume, connectivity or cell count invalid")
        if not value["mesh_ok"]:
            errors.append(region + ": checkMesh failed (" + str(value["failed_checks"]) + " tests)")
    for region, other in (("metal", "mold"), ("mold", "metal")):
        name = region + "_to_" + other
        p = patches[region].get(name)
        reciprocal = patches[other].get(other + "_to_" + region)
        if not p or not reciprocal or not p["nFaces"] or p["nFaces"] != reciprocal["nFaces"]:
            errors.append(name + ": missing or non-reciprocal contact faces")
        elif (p["type"] != "mappedWall" or p["neighbourRegion"] != other
              or p["neighbourPatch"] != other + "_to_" + region):
            errors.append(name + ": mappedWall coupling incomplete")
    return sorted(set(errors))


def prepare_c14(case, patches):
    # This stage executes ONLY if the two coupled region meshes pass G1.
    for region in ("metal", "mold"):
        original = C14 / "system" / region
        initial = C14 / "0" / region
        if not original.is_dir() or not initial.is_dir():
            raise RuntimeError("C14 source missing system/0 for "+region)
        shutil.copytree(original, case / "system" / region, dirs_exist_ok=True)
        for source in (ROOT / "constant" / region).rglob("*"):
            if source.is_file():
                target = case / "constant" / region / source.relative_to(ROOT / "constant" / region)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        out0 = case / "0" / region
        out0.mkdir(parents=True, exist_ok=True)
        for source in initial.iterdir():
            if not source.is_file():
                continue
            content = source.read_text(errors="replace")
            if "boundaryField" in content:
                content = field_with_3d_patches(content, region, patches[region], source.name)
            (out0 / source.name).write_text(content)
    # The 3D metal region contains ONLY iron. Preserve the controlled C14
    # source terms; if splitMeshRegions drops the named cellZone, selection
    # of the entire regional mesh is physically equivalent to that cellZone.
    zoned = case / "constant/metal/polyMesh/cellZones"
    if not zoned.is_file() or not re.search(r"\bmetal\b", zoned.read_text()):
        model = case / "constant/metal/fvModels"
        model_text = model.read_text()
        model_text, count = re.subn(
            r"(?m)^\s*selectionMode\s+cellZone;\s*\n\s*cellZone\s+metal;",
            "    selectionMode   all;", model_text, count=1)
        if count != 1:
            raise RuntimeError("Cannot map C14 phase-change cellZone to the 3D metal-only mesh")
        model.write_text(model_text)
        (case / "G1_FVMODELS_REGION_ADAPTATION.txt").write_text(
            "Metal contains iron only. phaseChangeSource selectionMode all "
            "replaces cellZone metal if the split removed that zone; "
            "phase-change constants are unchanged.\n")
    for name in ("fvSolution", "controlDict"):
        shutil.copy2(C14 / "system" / name, case / "system" / name)
    # The C14 2D pressure reference uses y=+0.04 m, outside the 3D metal.
    field = case / "system/metal/fvSolution"
    data = field.read_text()
    data, count = re.subn(r"(?m)^\s*pRefPoint\s+\([^;]+\);",
                          "    pRefPoint          " + METAL_POINT + ";", data, count=1)
    if count != 1:
        raise RuntimeError("C14 pRefPoint missing; 3D pressure reference unresolved")
    field.write_text(data)


def self_test():
    s = snappy_dictionary()
    for token in ("cellZone metal;", "cellZone mold;", "insidePoints", "snap true;",
                  "mode inside;", "faceType internal;"):
        assert token in s, token
    sample = """FoamFile{version 2.0;}
2
(
metal_to_exterior
{
type mappedWall;
nFaces 10;
neighbourRegion exterior;
neighbourPatch exterior_to_metal;
}
metal_to_mold
{
type mappedWall;
nFaces 20;
neighbourRegion mold;
neighbourPatch mold_to_metal;
}
)
"""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "boundary"
        p.write_text(sample)
        discard_exterior_coupling(p)
        b = boundary_entries(p)
        assert b["metal_to_exterior"]["type"] == "wall"
        assert b["metal_to_mold"]["neighbourRegion"] == "mold"
        source = """internalField uniform 1500;
boundaryField
{
frontAndBack { type empty; }
metalTop { type slip; }
metal_to_mold
{
type coupledTemperature;
h
{
type wallLayersHeatTransferCoefficient;
thicknessLayers (2e-4);
kappaLayers (1e-1);
}
value uniform 1500;
}
}
"""
        field = field_with_3d_patches(source, "metal", b, "T")
        assert "wallLayersHeatTransferCoefficient" in field
        assert "frontAndBack" not in field
        assert "empty;" not in field
    print("OK: two-region zones, nested C14 coupledTemperature, reciprocal walls, no 2D empty")


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--dest", type=Path, default=Path.home() / "OpenFOAM/C3D02_DELIVERY_01")
    cli.add_argument("--mesh-only", action="store_true", help="Compile two regions, skip solver")
    cli.add_argument("--self-test", action="store_true")
    args = cli.parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    case = args.dest.expanduser().resolve()
    if case.exists():
        print("La carpeta existe y NO se sobrescribe:", case)
        if (case/"BUILD_STATUS.json").exists():
            print((case/"BUILD_STATUS.json").read_text())
        return 2
    case.mkdir(parents=True)
    step = "PREFLIGHT"
    # Always create the two error-zone reports at launch; final status()
    # refreshes them with VTK coordinates if a mesh has been generated.
    run_error_localization(case, "PREFLIGHT")
    try:
        for stl in STL.values():
            if not (ROOT/"constant/geometry"/stl).is_file():
                raise RuntimeError("Missing approved STL: "+stl)
        run(case, ["bash", str(ROOT/"tests/test_sources.sh")], "log.source_integrity")
        for cmd in ("blockMesh", "snappyHexMesh", "splitMeshRegions", "checkMesh", "foamMultiRun"):
            run(case, ["bash", "-c", "command -v "+cmd], "log.preflight."+cmd)
        step = "MESH_BOTH_MATERIALS"
        (case/"system").mkdir(exist_ok=True)
        (case/"constant/geometry").mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/"system/blockMeshDict", case/"system/blockMeshDict")
        shutil.copy2(ROOT/"system/controlDict", case/"system/controlDict")
        for stl in STL.values():
            shutil.copy2(ROOT/"constant/geometry"/stl, case/"constant/geometry"/stl)
        (case/"system/snappyHexMeshDict").write_text(snappy_dictionary())
        run(case, ["blockMesh", "-case", str(case)], "log.blockMesh")
        run(case, ["snappyHexMesh", "-case", str(case), "-overwrite"], "log.snappyHexMesh")
        step = "SPLIT_REGIONS_AND_CREATE_CONTACT"
        zones = (case/"constant/polyMesh/cellZones").read_text()
        for region in ("metal", "mold"):
            if not re.search(r"\b"+region+r"\b", zones):
                raise RuntimeError("No "+region+" cellZone from the two-solid mesh")
        # Foundation 14 constructs reciprocal mappedWall patches here, on a
        # *single shared parent mesh*. The exterior region is excluded from
        # the C14 regionSolvers dictionary and its contacts become walls.
        run(case, ["splitMeshRegions", "-case", str(case), "-cellZones", "(metal mold)",
                   "-defaultRegion", "exterior", "-noFields"], "log.splitMeshRegions")
        patches = {}
        for region in ("metal", "mold"):
            boundary = case/"constant"/region/"polyMesh/boundary"
            if not boundary.is_file():
                raise RuntimeError("splitMeshRegions did not produce region "+region)
            discard_exterior_coupling(boundary)
            patches[region] = boundary_entries(boundary)
        step = "STRICT_MESH_AND_INTERFACE_GATE"
        measures = {region: quality(case, region) for region in ("metal", "mold")}
        problems = gates(measures, patches)
        if problems:
            status(case, "BLOCKED_G1", False,
                   "Geometry/mesh/contact quality rejected: foamMultiRun NOT executed.",
                   quality=measures, problems=problems, patches=patches)
            return 5
        step = "ADAPT_C14_3D"
        prepare_c14(case, patches)
        if args.mesh_only:
            status(case, "READY_MESH_ONLY", True,
                   "Conformal metal/mold regions and C14 fields staged; CFD skipped by flag.",
                   quality=measures, patches=patches)
            return 0
        step = "RUN_C14_FOAM_MULTI_RUN"
        log = run(case, ["foamMultiRun", "-case", str(case)], "log.foamMultiRun")
        if not re.search(r"(?m)^End\s*$", log):
            raise RuntimeError("foamMultiRun log missing End marker")
        status(case, "SOLVER_COMPLETED", True,
               "Numerical foamMultiRun ended; experimental validity is not yet demonstrated.",
               quality=measures, patches=patches)
        return 0
    except Exception as exc:
        status(case, step, False, str(exc))
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
