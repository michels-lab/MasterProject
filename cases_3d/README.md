# Casos de investigación tridimensional

La carpeta `cases_3d/` reúne variantes geométricas 3D separadas de los casos 2D.

- [C3D-01: primer caso QuickCup metal/molde de arena](C3D_01_metal_mold/README.md) — preparado para una prueba local de `blockMesh` y `checkMesh`. No hay simulaciones CFD ni resultados validados.

Los STL originales de SolidWorks se mantienen en la laptop. La ejecución de OpenFOAM está prohibida en GitHub Actions.

**Convención OpenFOAM14:** [C3D-01](C3D_01_metal_mold/README.md) utiliza `units [mm];` en `blockMeshDict` y mantendrá los STL de SolidWorks en milímetros para `snappyHexMesh`, sin conversión binaria en Python.
