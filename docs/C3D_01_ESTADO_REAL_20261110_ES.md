# MasterProject — C3D-01: estado experimental y numérico al 10-11-2026

**Tipo de registro:** transcripción técnica de salidas que el investigador ejecutó en su laptop con OpenFOAM Foundation 14, más comprobaciones de objetos versionados en GitHub. **No es una corrida CFD ni validación experimental.** El directorio local de prueba `~/OpenFOAM/C3D01_snappy_NTC8Dj` y sus logs completos no se han incorporado al repositorio; los números de esa prueba proceden de la terminal compartida por el investigador y requieren importación de archivos fuente antes de una auditoría reproducible.

## Identidad, material y conservación
- Repositorio: `michels-lab/MasterProject`; ruta local confirmada: `~/OpenFOAM/MasterProject`; OpenFOAM **Foundation 14**.
- Línea científica Plan D `case3d-01`; árbol técnico histórico `cases_3d/C3D_01_metal_mold`. Son **el mismo estudio**, no dos casos CFD independientes.
- `constant/geometry/metal.stl`: STL original de SolidWorks con coordenadas numéricas en **mm**, SHA-256 `fc8e6b7f3c229369b856aca7dab936347732028d9cd695499bf0e249363fb810`.
- `constant/geometry/mold.stl`: original en mm, SHA-256 `2e62e31875dc3c86dd7e6f2efe60d4c173ee4cee5e4f6ff63205c08efee3a638`.
- `constant/geometry/mold_repaired.stl`: copia derivada de `surfacePointMerge`, SHA-256 `860525e8a9fb2de483cf90f331f2753a339d82c5eee706ecfc1b8186bf49e9fe`. Conserva 3,084 triángulos. No reemplaza al original. Los dos originales fueron publicados en `main` mediante `e391f7591`; el reparado con sus registros se incorporó, tras un rebase, en `06426781f`.
- **Advertencia de difusión:** estos STL están en un repositorio GitHub público; evitar publicar otras exportaciones CAD sin revisar propiedad intelectual/permisos.

## OpenFOAM: geometría (evidencia local + logs versionados)
| Comprobación | Metal original | Molde original | Molde reparado |
|---|---:|---:|---:|
| Triángulos | 3,896 | 3,084 | 3,084 |
| Superficie cerrada | Sí | No | Sí |
| Aristas incidentes a una sola cara | 0 | 74 | 0 |
| Aristas incidentes a más de dos caras | 0 | 0 | 0 |
| Puntos casi coincidentes reportados | 0 | 16 parejas | 0 |
| Autointersecciones | No | No comprobadas aquí | No |
| `surfaceInertia` volumen con coordenadas mm | 47,987.4896432 mm³ | — | 102,843.09608 mm³ |
| Volumen expresado en cm³ | 47.9874896 | — | 102.8430961 |

El `Mass` de `surfaceInertia` se interpreta como volumen geométrico a densidad unitaria; no es una masa física del metal o la arena. El `surfaceCheck` del molde reparado y del metal acabó con `End` y sin autointersecciones. Los registros de la reparación están versionados bajo `surfaceCheck_outputs/mold_repair_trial/`. El nombre `mold_merged.stl` designa el candidato local; el archivo versionado permanente es `mold_repaired.stl`.

## Malla 3D: primera prueba local, NO ACEPTADA
1. `blockMesh` generó la caja de fondo de 58 × 72 × 58 mm (29 × 36 × 29 = **30,276 hexaedros**, nominalmente 2 mm). El caso técnico publicado tiene `units [mm];` en `system/blockMeshDict`.
2. En la prueba independiente `/home/michel/OpenFOAM/C3D01_snappy_NTC8Dj`, el investigador utilizó **copias temporales escaladas a metros con `surfaceTransformPoints`** y `snappyHexMeshConfig` para generar `snappyHexMeshDict`. La prueba **no** verifica todavía un `snappyHexMesh` ejecutado sobre STL originales con `units [mm];` en `geometry`; esa es la convención **preferida para el siguiente caso** y debe comprobarse en ejecución real.
3. `snappyHexMesh` finalizó y `checkMesh -allGeometry -allTopology` informó **1,505,847 celdas**, malla 3D, un componente conectado, volumen total **0.000242201 m³ = 242.201 cm³**, malla de **toda la caja**, no exclusivamente metal + arena.
4. `refinementSurfaces`: `mold_repaired` nivel (2 2) como pared externa; `metal` nivel (2 2), `faceZone metal`, `cellZone metal`, `mode inside`. `refinementRegions` configuró ambas superficies con `mode inside; level 2`. `insidePoints`: `(0.0259 -0.02 0.0259)` y `(0.003 -0.02 0.0259)` m.
5. La zona `metal` aparece con **383,788 etiquetas de celda**, pero su **volumen físico, pertenencia, interfaz y no solapamiento NO están demostrados**; tampoco hay `cellZone mold` comprobada ni separación multirregión. `Number of regions: 1` en `checkMesh` es el número de componentes conectados, no una certificación de acoplamiento térmico.
6. Resultado de calidad: máximo de no ortogonalidad **68.2102°**, máximo skewness **2.60187**, **23 caras** con tetraedros de descomposición deficientes y **6,974 celdas cóncavas**; `checkMesh` termina con **Failed 2 mesh checks**. También se informaron avisos de snapping con desplazamientos que atraviesan caras cercanas. **Esta malla no está aceptada para CFD.**
7. La resolución de **0.5 mm** es el objetivo nominal de dos niveles octree desde celdas de 2 mm; no es una cota máxima garantizada, ni prueba de independencia de malla. La propuesta de refinamiento del PR #18 sigue pendiente de integrar y contrastar.

## Reglas de reproducibilidad y errores aprendidos
- `snappyHexMeshConfig` en Foundation 14 **no admite `-case`**; ejecutar desde el directorio del caso (`cd "$TRIAL"`). Las opciones deben comprobarse con `snappyHexMeshConfig -help`.
- No activar `set -u` antes de `source /opt/openfoam14/etc/bashrc`: se observó el error `ZSH_NAME: unbound variable`.
- Los `*.STL` originales con extensión mayúscula no fueron leídos correctamente por el `surfaceCheck` usado; las copias `*.stl` minúsculas se analizaron sin problemas.
- Para próximas pruebas preferir los **STL originales en mm** y declarar `units [mm];` en la geometría del diccionario Foundation 14, **sin doble escalado**; no presentar como comprobada una ejecución todavía no realizada bajo esa modalidad.
- Ejecutar mallas y CFD **solo en la laptop**; GitHub almacena fuentes, scripts, logs seleccionados y auditorías estáticas. Las carpetas de pruebas `~/OpenFOAM/C3D01_snappy_*` están fuera del repositorio y no se sincronizan automáticamente.
- No sobrescribir `constant/polyMesh`, no ejecutar `Allclean` sobre casos históricos y no hacer `git push --force` si existen nuevos commits remotos.

## Próximas puertas técnicas (abiertas)
1. Archivar `log.blockMesh`, `log.snappyHexMesh`, `log.checkMesh.final` y `snappyHexMeshDict` de la prueba local en un paquete nuevo e identificado por SHA, sin sustituir evidencia previa; cotejar cantidad y volumen real de `cellZone metal`.
2. Construir un segundo ensayo explícito con STL originales `units [mm]`, zonas metal y arena complementarias, interfaz/faceZones para transferencia de calor conjugada y eliminación correcta del aire exterior; demostrar que el sólido NO incluye el volumen del metal.
3. Diagnosticar los **23 face tets** y **6,974 concave cells**; comparar etapas castellated/snap sin relajar artificialmente los criterios de aceptación.
4. Verificar `splitMeshRegions`/patches conjugados, volúmenes, áreas, `checkMesh` por región, conservación de energía y sensibilidad de malla. Solo después preparar solver y curvas de enfriamiento.
5. Mantener puertas **J0** (propiedades JMatPro reales) y **G1** (validación experimental) **ABIERTAS**. No cambiar estados históricos B/C ni declarar un 3D `RUN_VERIFIED`.

## Puente a documentos vivos
[README](../README.md) · [Manual ES](../OPENFOAM_COMMAND_MANUAL_ES.md) · [Manual EN](../OPENFOAM_COMMAND_MANUAL_EN.md) · [Guía de casos](../CASE_GUIDE_ES.md) · [Índice documental](DOCUMENTATION_INDEX.md) · [Bitácora ES](../PROJECT_AUDIT_LOG_ES.md) · [Bitácora EN](../PROJECT_AUDIT_LOG_EN.md) · [Validación ES](../VALIDATION_MATRIX_ES.md) · [Plan D](../cases_3d/README.md).
