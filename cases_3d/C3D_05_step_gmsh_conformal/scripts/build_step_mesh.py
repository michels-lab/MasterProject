#!/usr/bin/env python3
"""C3D-05: STEP/3D CAD conformal metal-mold mesh via Gmsh OpenCASCADE.

Requires TWO real STEP solids exported from the same SolidWorks coordinate
system. This script does not infer/create CAD from STL and never runs CFD.
It validates volume, shared-surface area, dimensions and physical groups
before any mesh generation; then writes MSH2 ASCII with mesh coords in meters.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path


CAD_METAL_MM3 = 47987.697
CAD_MOLD_MM3 = 102843.333
CAD_CONTACT_MM2 = 6352.633693770655
CAD_TOP_MM2 = 1326.8855035725214
VOLUME_TOLERANCE = 0.02
AREA_TOLERANCE = 0.03
SIZE_TOLERANCE_MM = 0.30


def sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            result.update(chunk)
    return result.hexdigest()


def relative_error(observed: float, expected: float) -> float:
    return 100.0 * (observed / expected - 1.0)


def volume_tags(entities: list[tuple[int, int]], source: str) -> list[tuple[int, int]]:
    volumes = [tuple(x) for x in entities if x[0] == 3]
    if len(volumes) != 1:
        raise ValueError(
            f"{source} must contain exactly ONE CLOSED CAD solid; "
            f"found {len(volumes)} volume entities. Export it as one solid STEP."
        )
    return volumes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--metal", type=Path, required=True)
    ap.add_argument("--mold", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mesh-size-mm", type=float, default=1.8)
    ap.add_argument("--algorithm-3d", type=int, choices=(1, 4, 10), default=1,
                    help="Gmsh 3D algorithm: 1=Delaunay baseline, 4=Frontal, 10=HXT")
    args = ap.parse_args()
    if not (0.5 <= args.mesh_size_mm <= 5.0):
        ap.error("--mesh-size-mm must be between 0.5 and 5 mm for the topology pilot")

    metal_path, mold_path = args.metal.resolve(), args.mold.resolve()
    if not metal_path.is_file() or not mold_path.is_file():
        ap.error("Both STEP files must exist, be real solids and use the same coordinates")
    if metal_path == mold_path or metal_path.suffix.lower() not in (".step", ".stp") or mold_path.suffix.lower() not in (".step", ".stp"):
        ap.error("Supply two DISTINCT .step/.stp CAD solids: metal and mold")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report_path, mesh_path = out / "STEP_CAD_AUDIT.json", out / "cad_multivolume.msh"
    if report_path.exists() or mesh_path.exists():
        ap.error("Output already contains evidence. Choose a fresh output path")

    try:
        import gmsh
    except ImportError as exc:
        raise SystemExit("Gmsh Python module missing. Install/verify python3-gmsh in WSL first.") from exc

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 1)
        # All STEP dimensions are interpreted in millimeters in OCC;
        # the saved MSH2 coordinates are scaled to meters, once and only once.
        gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
        gmsh.model.add("C3D05_QuickCup_step_shared_topology")
        metal_import = volume_tags(gmsh.model.occ.importShapes(str(metal_path)), "metal")
        mold_import = volume_tags(gmsh.model.occ.importShapes(str(mold_path)), "mold")
        output, mapping = gmsh.model.occ.fragment(
            metal_import, mold_import, removeObject=True, removeTool=True
        )
        gmsh.model.occ.synchronize()
        if len(mapping) != 2:
            raise ValueError("Unexpected OpenCASCADE fragment mapping. Refuse ambiguous materials.")
        metallic = {tag for dim, tag in mapping[0] if dim == 3}
        sandy = {tag for dim, tag in mapping[1] if dim == 3}
        allvolumes = {tag for dim, tag in gmsh.model.getEntities(3)}
        if len(metallic) != 1 or len(sandy) != 1 or metallic & sandy or allvolumes != metallic | sandy:
            raise ValueError(
                f"Ambiguous/overlapping fragment volumes: metal={sorted(metallic)}, "
                f"mold={sorted(sandy)}, all={sorted(allvolumes)}; "
                "fix SolidWorks solids before meshing"
            )
        mv, sv = next(iter(metallic)), next(iter(sandy))
        mvol = gmsh.model.occ.getMass(3, mv)
        svol = gmsh.model.occ.getMass(3, sv)
        if abs(relative_error(mvol, CAD_METAL_MM3)) > VOLUME_TOLERANCE * 100 or abs(relative_error(svol, CAD_MOLD_MM3)) > VOLUME_TOLERANCE * 100:
            raise ValueError(
                f"STEP volumes do not match the approved STL volumes: metal={mvol:.3f}, "
                f"mold={svol:.3f} mm3. No mesh generated."
            )

        def boundary_surfaces(tag: int) -> set[int]:
            return {int(t) for dim, t in gmsh.model.getBoundary([(3, tag)], oriented=False) if dim == 2}

        metal_bnd = boundary_surfaces(mv)
        mold_bnd = boundary_surfaces(sv)
        shared = metal_bnd & mold_bnd
        mext = metal_bnd - shared
        sext = mold_bnd - shared
        if not shared or not mext or not sext:
            raise ValueError("No shared CAD interface or exterior surfaces; check STEP alignment and fragmentation")
        contact_area = sum(gmsh.model.occ.getMass(2, t) for t in shared)
        if abs(relative_error(contact_area, CAD_CONTACT_MM2)) > AREA_TOLERANCE * 100:
            raise ValueError(
                f"Contact CAD area {contact_area:.3f} mm2 differs from approved STL "
                f"by {relative_error(contact_area, CAD_CONTACT_MM2):+.2f}%; "
                "check whether metal and mold share all side and bottom surfaces"
            )

        # Top metal surface must lie on the y=0 mm plane in the shared STEP coordinates.
        top = set()
        for t in mext:
            xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.occ.getBoundingBox(2, t)
            if abs(ymin) < SIZE_TOLERANCE_MM and abs(ymax) < SIZE_TOLERANCE_MM:
                top.add(t)
        other_metal = mext - top
        top_area = sum(gmsh.model.occ.getMass(2, t) for t in top)
        if not top or other_metal or abs(relative_error(top_area, CAD_TOP_MM2)) > AREA_TOLERANCE * 100:
            raise ValueError(
                f"Unclassified exterior metal or incorrect top: top area={top_area:.3f}mm2, "
                f"unclassified={sorted(other_metal)}. Check STEP / physical boundaries."
            )

        # Confirm length scale before exporting: native CAD mm, MSH -> m.
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.occ.getBoundingBox(3, sv)
        dx, dy, dz = xmax - xmin, ymax - ymin, zmax - zmin
        if max(abs(dx-51.8), abs(dy-65.5), abs(dz-51.8)) > SIZE_TOLERANCE_MM:
            raise ValueError(
                f"Unexpected mold STEP extents (mm): {dx:.4f}, {dy:.4f}, {dz:.4f}; "
                "verify geometry units and STEP placement"
            )

        gmsh.model.addPhysicalGroup(3, [mv], 101, "metal")
        gmsh.model.addPhysicalGroup(3, [sv], 102, "mold")
        gmsh.model.addPhysicalGroup(2, sorted(shared), 201, "metal_mold_contact")
        gmsh.model.addPhysicalGroup(2, sorted(top), 202, "metalTop")
        gmsh.model.addPhysicalGroup(2, sorted(sext), 203, "moldOuterUnclassified")
        report = {
            "status": "CAD_PREFLIGHT_PASSED_MESH_NOT_YET_CONFIRMED",
            "source": {
                "metal_step": str(metal_path), "metal_sha256": sha256(metal_path),
                "mold_step": str(mold_path), "mold_sha256": sha256(mold_path),
            },
            "units": {"occ": "mm", "msh_output": "m", "Mesh.ScalingFactor": 0.001},
            "material_volume_mm3": {"metal": mvol, "mold": svol},
            "volume_error_percent": {
                "metal": relative_error(mvol, CAD_METAL_MM3),
                "mold": relative_error(svol, CAD_MOLD_MM3)
            },
            "common_surfaces": sorted(shared),
            "contact_area_mm2": contact_area,
            "contact_area_error_percent": relative_error(contact_area, CAD_CONTACT_MM2),
            "top_area_mm2": top_area,
            "metal_exterior_surfaces_other_than_top": sorted(other_metal),
            "mold_exterior_surfaces": sorted(sext),
            "mold_bbox_mm": [xmin, ymin, zmin, xmax, ymax, zmax],
            "physical_groups": {"metal": 101, "mold": 102, "contact": 201, "metalTop": 202, "moldOuterUnclassified": 203},
            "mesh_size_mm": args.mesh_size_mm,
            "algorithm_3d": args.algorithm_3d,
            "algorithm_label": {1: "Delaunay", 4: "Frontal", 10: "HXT"}[args.algorithm_3d],
            "physics_status": "NO_CFD_NO_BCS",
        }
        with report_path.open("x", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")
        gmsh.option.setNumber("Mesh.Algorithm3D", args.algorithm_3d)
        gmsh.option.setNumber("Mesh.MeshSizeMin", args.mesh_size_mm / 2)
        gmsh.option.setNumber("Mesh.MeshSizeMax", args.mesh_size_mm)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 18)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        gmsh.option.setNumber("Mesh.Binary", 0)
        gmsh.option.setNumber("Mesh.ScalingFactor", 0.001)
        gmsh.model.mesh.generate(3)
        gmsh.write(str(mesh_path))
        report["status"] = "GMSH_MSH2_WRITTEN_OPENFOAM_NOT_YET_VERIFIED"
        report["mesh_file"] = str(mesh_path)
        report["mesh_file_sha256"] = sha256(mesh_path)
        # Update the freshly created audit in place, never an old output directory.
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
        print("NO CFD: Gmsh mesh written; OpenFOAM conversion/quality still required.")
    finally:
        gmsh.finalize()


if __name__ == "__main__":
    main()
