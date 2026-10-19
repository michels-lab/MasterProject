# Superficies STL nativas para OpenFOAM Foundation v14

**Flujo recomendado sin Python:** copiar directamente los STL originales de SolidWorks, en milímetros, desde `~/OpenFOAM/Piezas_STL/`:

```bash
# Desde la carpeta C3D_01_metal_mold:
cp -n "$HOME/OpenFOAM/Piezas_STL/QuickCup.STL" constant/geometry/mold.stl
cp -n "$HOME/OpenFOAM/Piezas_STL/metal.STL" constant/geometry/metal.stl
```

Las copias siguen en mm; no se cambia ni un vértice. Los nombres internos se mantienen `mold.stl` y `metal.stl` para referenciarlos desde `snappyHexMeshDict`.

**Conversión SI al leer las superficies:** en OpenFOAM Foundation v14 el futuro diccionario `snappyHexMeshDict` declarará `units [mm];` en cada superficie `triSurfaceMesh`. No preescalar los STL, no declarar además `scale 0.001;`. El comando `blockMesh` únicamente construye la caja inicial y no necesita leer estos STL.

`scripts/prepare_geometry.py` y `analysis_tools/preflight_c3d_stl.py` siguen presentes **solo como opciones de auditoría**, no son pasos del mallado ni son llamados por el script de `blockMesh`. Se conservan los STL fuera del repositorio público; aquí están excluidos por `.gitignore`.
