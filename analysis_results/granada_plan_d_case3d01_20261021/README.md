# Plan D / case3d-01 — Auditoría de fuentes 3D

**21 de octubre de 2026.** Fuente: `cases_3d/C3D_01_metal_mold/geometry_reference.json` y `system/blockMeshDict` versionados en main (que todavía utilizan el nombre heredado). Están pendientes las mediciones auténticas de mallado.

| Parámetro | Valor en fuente |
|---|---:|
| Identificador oficial del caso | `case3d-01` |
| Malla de fondo propuesta | 29 × 36 × 29 = **30,276 celdas** |
| Extensión nominal caja | 58 × 72 × 58 mm |
| Celdas uniformes fondo | 2 mm |
| Volumen STL metal de referencia | 47.987490 cm³ |
| Volumen STL arena de referencia | 102.843165 cm³ |
| Proyección ideal uniforme 0.5 mm, metal | ≈383,900 celdas |
| Proyección ideal uniforme 0.5 mm, arena | ≈822,746 celdas |
| Proyección ideal combinada 0.5 mm | ≈1,206,646 celdas |
| Revisión real de STL con `surfaceCheck` | NO EJECUTADA |
| `blockMesh` y `checkMesh` | NO EJECUTADOS EN LA EVIDENCIA VISIBLE |
| Malla Snappy metal + arena | NO EXISTE RESULTADO VALIDADO |
| Balance térmico y solidificación | NO VALIDADOS |

**Proyecciones, no hallazgos de malla.** Se usa volumen CAD sobre volumen cúbico nominal; no incluye celdas exteriores, transiciones, superficie conformada, snaps, mala calidad, celdas interfaciales ni particionado. El requisito físico de toda la malla a 0.5 mm está actualmente en revisión científica, pese a haberse solicitado como configuración. El código emite 2/1/0.5/0.25 mm para contrastar costo, no para elegir resolución.

**Nomenclatura:** el caso es `case3d-01`. Hasta reconciliar los PR #18 y #19, los datos fuente del Git permanecen temporalmente en `C3D_01_metal_mold`. Una carpeta canónica `cases_3d/case3d-01/` permite preparar una copia de prueba sin mover esos archivos ni invalidar los cambios de PR.

**Reproducción:** `analysis_tools/granada_plan_d_case3d01_mesh_gate.py --root . --out /tmp/case3d-01-evidence`; genera JSON de fuentes SHA-256 y CSV de estimación, y reporta los datos de campo como NO OBSERVADOS cuando no existen. `--require-stls` y `--require-mesh-logs` son puertas de fallo para el experimento local real. Ver `docs/granada/PLAN_D_CASE3D_01_MESH_GATE_20261021.md`.

**Sin intervención en CFD:** este documento no ha producido logs OpenFOAM, STL modificados, interfaces térmicas, recalescencia ni cálculos numéricos físicos.
