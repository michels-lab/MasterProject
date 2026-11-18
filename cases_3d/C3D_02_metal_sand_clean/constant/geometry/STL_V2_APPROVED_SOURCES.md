# C3D-02 — Nuevas superficies STL de SolidWorks (v2)

**Origen:** los dos archivos finales aportados por el investigador el 17-11-2026. Nombres de origen: `metalmm(2).STL` (metal) y `QuickCupmm.STL` (arena). Los archivos `metal(2).STL`, `metal(3).STL`, `metalmm.STL`, `metalmm(1).STL`, `QuickCup(2).STL` y `QuickCup(3).STL` no son la pareja definitiva.

**ATENCIÓN — ESTADO DE SINCRONIZACIÓN:** esta bitácora y el script de verificación están versionados. Los **dos STL binarios aún no están subidos a GitHub**: la conexión actual permite escritura de archivos UTF-8, pero no recibe directamente los bytes de los adjuntos del chat. Los STL deben incorporarse como archivos binarios, con los nombres exactos de la tabla, en este mismo directorio; no reemplazar ni eliminar `metal.stl`, `mold.stl` o `mold_repaired.stl`.

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

Una vez presentes ambos archivos binarios bajo los nombres indicados:

```bash
cd ~/OpenFOAM/MasterProject
bash cases_3d/C3D_02_metal_sand_clean/scripts/check_stl_v2.sh
```

La comprobación utiliza SHA-256 y `surfaceCheck -checkSelfIntersection` de Foundation 14. **No inicia la malla ni CFD.** Para la prueba de malla v2, conservar `c3d-better` y los experimentos anteriores como evidencia; usar una carpeta nueva.

**NUNCA interpretar esta aprobación de procedencia como aprobación de malla**. La reparación definitiva depende de `checkMesh -allGeometry -allTopology`, volumen, áreas de interfaz, contactos térmicos y BCs 3D.
