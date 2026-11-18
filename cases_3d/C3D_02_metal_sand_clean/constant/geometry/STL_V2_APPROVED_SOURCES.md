> **ACTUALIZACIÓN CANÓNICA C3D-02 / 18-11-2026 — actualización posterior a la aprobación de procedencia:** el `surfaceCheck` y SHA de `metal_v2.stl`/`mold_v2.stl` verifican fuentes, **NO la clasificación volumétrica**. El ensayo ambos v2 dejó 4+4 celdas; la sustitución aislada de metal v2 dejó **1 celda metálica** y la sustitución aislada de arena v2 dejó **0 celdas de arena**. Todos estos intentos de malla están rechazados; los experimentos de este manifiesto escritos como «siguientes» **ya se ejecutaron**, no repetirlos sobre carpetas existentes. [Datos reales](../../../../docs/C3D_02_ABLACION_STL_V2_20261118_ES.md), [interpretación del caso del doctor](../../../../docs/C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md). Mantener intactos originales y v2, no atribuir sin evidencia el colapso a un STL defectuoso.

# C3D-02 — Nuevas superficies STL de SolidWorks (v2)

**Origen:** los dos archivos finales aportados por el investigador el 17-11-2026. Nombres de origen: `metalmm(2).STL` (metal) y `QuickCupmm.STL` (arena). Los archivos `metal(2).STL`, `metal(3).STL`, `metalmm.STL`, `metalmm(1).STL`, `QuickCup(2).STL` y `QuickCup(3).STL` no son la pareja definitiva.

**ESTADO VERIFICADO — BINARIOS YA INCORPORADOS A `main`:** `metal_v2.stl` y `mold_v2.stl` se subieron sin convertir a ASCII ni cambiar la triangulación en el commit [`e8be4afeae847411cd35b815f90748d71d1c5d90`](https://github.com/michels-lab/MasterProject/commit/e8be4afeae847411cd35b815f90748d71d1c5d90). Sus SHA de objeto Git **coinciden con los calculados sobre los archivos originales**: metal `10b41a9edbf32ec6642587d21fa3cc6ad76a880d`, molde `6ea3ccbab486ccc45842723f68af289b61d9d029`. Los archivos originales `metal.stl`, `mold.stl` y `mold_repaired.stl` permanecen intactos. Estos son los **STL correctos de origen** para el siguiente candidato 3D, no una malla CFD validada.

| Archivo a versionar | Nombre recibido | Bytes | SHA-256 esperado | Triángulos | Volumen de superficie (cm³) |
|---|---|---:|---|---:|---:|
| `metal_v2.stl` | `metalmm(2).STL` | 231,484 | `f8c0fb90f9b5650261d39f1faa2430b3fc7fce462c0d44e460afb5a37b4ddccf` | 4,628 | 47.987697 |
| `mold_v2.stl` | `QuickCupmm.STL` | 185,884 | `ac52991eb254c1bcc65eaf546a25f663343e006e89aeff3ac26aa8e9a1d95a32` | 3,716 | 102.843333 |

**Resultados de auditoría preliminar del archivo adjunto (coordenadas en mm):**
- Metal: bbox x 7.65–44.15, y -40–0, z 7.65–44.15; superficie cerrada y orientación consistente tras unificar vértices coincidentes; 1 componente.
- Arena: bbox x 0–51.8, y -65.5–0, z 0–51.8; superficie cerrada y orientación consistente tras unificar vértices coincidentes; 1 componente.
- Los volúmenes son coherentes con las superficies anteriores: metal 47.98749 cm³, molde 102.843096 cm³. **No está validada todavía la superficie de contacto CAD ni la futura calidad volumétrica OpenFOAM.**
- El STL no almacena unidades; en OpenFOAM Foundation 14 se interpretan mediante `units [mm];` en `snappyHexMeshDict`.

## Auditoría y subida

Los dos STL binarios ya están presentes en este directorio; tras `git pull --ff-only`, ejecutar:

```bash
cd ~/OpenFOAM/MasterProject
bash cases_3d/C3D_02_metal_sand_clean/scripts/check_stl_v2.sh
```

La comprobación utiliza SHA-256 y `surfaceCheck -checkSelfIntersection` de Foundation 14. **No inicia la malla ni CFD.** Para la prueba de malla v2, conservar `c3d-better` y los experimentos anteriores como evidencia; usar una carpeta nueva.

**NUNCA interpretar esta aprobación de procedencia como aprobación de malla**. La reparación definitiva depende de `checkMesh -allGeometry -allTopology`, volumen, áreas de interfaz, contactos térmicos y BCs 3D.

## Ejecución nativa siguiente

Tras `git pull --ff-only` y `check_stl_v2.sh`, el mallador controlado de OpenFOAM Foundation 14 utiliza los dos STL nuevos en una carpeta **nueva**:

```bash
cd ~/OpenFOAM/MasterProject
git pull --ff-only
bash cases_3d/C3D_02_metal_sand_clean/scripts/check_stl_v2.sh
bash cases_3d/C3D_02_metal_sand_clean/Allmesh --stl-v2
```

Salida `~/OpenFOAM/c3d-better-stl-v2` y tabla `STL_V2_COMPARISON.tsv`. No se sobrescriben los experimentos anteriores; el script exige calidad de ambas regiones y **no ejecuta CFD**.
