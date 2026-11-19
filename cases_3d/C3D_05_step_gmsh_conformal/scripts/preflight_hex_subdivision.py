#!/usr/bin/env python3
"""Native Gmsh capability preflight: conformal TWO-volume tet-to-hex topology.

In-memory two-box OCC model, shared interface and physical groups. No files
written, no STEP loaded, no OpenFOAM run or CFD. Exits nonzero if this Gmsh
build cannot generate only HEX8 volume elements and QUAD4 surfaces after
Mesh.SubdivisionAlgorithm=2 followed by mesh.refine().
"""
from __future__ import annotations

def main() -> int:
    try:
        import gmsh
    except ImportError as exc:
        print(f"HEX_PREFLIGHT_BLOCKED: gmsh Python bindings unavailable: {exc}")
        return 2
    initialized = False
    try:
        gmsh.initialize()
        initialized = True
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("C3D05_HEX_SUBDIVISION_TWO_MATERIAL_PREFLIGHT")
        metal = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
        mold = gmsh.model.occ.addBox(1, 0, 0, 1, 1, 1)
        _, mapping = gmsh.model.occ.fragment([(3, metal)], [(3, mold)])
        gmsh.model.occ.synchronize()
        if len(mapping) != 2:
            raise RuntimeError("OCC fragmentation did not return two material maps")
        a, b = ({tag for dim, tag in item if dim == 3} for item in mapping)
        if len(a) != 1 or len(b) != 1 or a == b:
            raise RuntimeError("OCC fragment material volumes are not two distinct solids")
        av, bv = next(iter(a)), next(iter(b))
        ab = {tag for dim, tag in gmsh.model.getBoundary([(3, av)], oriented=False) if dim == 2}
        bb = {tag for dim, tag in gmsh.model.getBoundary([(3, bv)], oriented=False) if dim == 2}
        shared = sorted(ab & bb)
        if not shared:
            raise RuntimeError("Two boxes lost their common OCC interface")
        gmsh.model.addPhysicalGroup(3, [av], 101, "metal")
        gmsh.model.addPhysicalGroup(3, [bv], 102, "mold")
        gmsh.model.addPhysicalGroup(2, shared, 201, "metal_mold_contact")
        gmsh.model.addPhysicalGroup(2, sorted((ab | bb) - set(shared)), 203, "outer")
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)
        gmsh.option.setNumber("Mesh.MeshSizeMin", 0.30)
        gmsh.option.setNumber("Mesh.MeshSizeMax", 0.55)
        gmsh.model.mesh.generate(3)
        initial = set(map(int, gmsh.model.mesh.getElementTypes(3)))
        if initial != {4}:
            raise RuntimeError(f"Expected TET4 before subdivision, got {initial}")
        gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 2)
        gmsh.model.mesh.refine()
        final_volume = set(map(int, gmsh.model.mesh.getElementTypes(3)))
        final_surface = set(map(int, gmsh.model.mesh.getElementTypes(2)))
        if final_volume != {5} or final_surface != {3}:
            raise RuntimeError(
                f"Hex/quad conversion incomplete: 3D={sorted(final_volume)}, "
                f"2D={sorted(final_surface)}"
            )
        for physical_id in (101, 102):
            vols = gmsh.model.getEntitiesForPhysicalGroup(3, physical_id)
            if len(vols) != 1:
                raise RuntimeError(f"Lost material physical group {physical_id}")
            types = set(map(int, gmsh.model.mesh.getElementTypes(3, int(vols[0]))))
            if types != {5}:
                raise RuntimeError(f"Physical material {physical_id} lacks HEX8 elements")
        for face_tag in shared:
            types = set(map(int, gmsh.model.mesh.getElementTypes(2, face_tag)))
            if types != {3}:
                raise RuntimeError(f"Shared face {face_tag} not QUAD4: {types}")
        num = sum(len(group) for group in gmsh.model.mesh.getElements(3)[1])
        if not num:
            raise RuntimeError("No 3D cells after subdivision")
        print(
            f"HEX_SUBDIVISION_PREFLIGHT_OK: two OCC materials, common shared QUAD4 "
            f"contact, {num} HEX8 cells, physical regions 101/102 preserved; "
            "memory-only test, NOT QuickCup quality approval"
        )
        return 0
    except Exception as exc:
        print(f"HEX_SUBDIVISION_PREFLIGHT_BLOCKED: {type(exc).__name__}: {exc}")
        return 3
    finally:
        if initialized:
            gmsh.finalize()


if __name__ == "__main__":
    raise SystemExit(main())
