#!/usr/bin/env python3
"""Minimal in-memory capability test for HXT Gmsh 3D (algorithm 10).

Does not load CAD, write files, touch prior trials or run CFD.
A successful preflight only verifies this Gmsh build can tetrahedralize a
small test box: the full QuickCup still requires all native mesh checks.
"""
from __future__ import annotations


def main() -> int:
    try:
        import gmsh
    except ImportError as exc:
        print(f"BLOCKED_HXT: Python gmsh not installed: {exc}")
        return 2
    initialized = False
    try:
        gmsh.initialize()
        initialized = True
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("C3D05_HXT_CAPABILITY_PREFLIGHT")
        gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.Algorithm3D", 10)
        gmsh.option.setNumber("Mesh.MeshSizeMin", 0.4)
        gmsh.option.setNumber("Mesh.MeshSizeMax", 0.7)
        gmsh.model.mesh.generate(3)
        element_types, element_tags, _ = gmsh.model.mesh.getElements(3)
        n = sum(len(tags) for tags in element_tags)
        if n < 1 or not element_types:
            raise RuntimeError("HXT generated no 3D elements")
        print(
            f"HXT_PREFLIGHT_OK: Mesh.Algorithm3D=10 supported; "
            f"{n} test 3D elements; test only, not C3D-05 acceptance"
        )
        return 0
    except Exception as exc:
        print(
            f"BLOCKED_HXT: Gmsh build cannot mesh a test OCC box "
            f"with algorithm 10: {exc}"
        )
        return 3
    finally:
        if initialized:
            gmsh.finalize()


if __name__ == "__main__":
    raise SystemExit(main())
