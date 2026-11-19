> **19-11-2026 | PROJECT_PROGRESS_CONTRACT_20261119:** La localización de errores de malla debe ejecutarse dentro del hito completo, no como una cadena de tests entregados por separado. Siempre reportar etapa/avance y estado con evidencia; rige para TODOS los casos. [Política](POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md) · [Estado](PROJECT_STAGE_STATUS.json).

> **ACTUALIZACIÓN CANÓNICA C3D-02 / 18-11-2026 — aclaración de alcance:** este documento describe el contrato del **constructor Python experimental** de C3D-02, no la ruta principal vigente. El flujo prioritario de mallado y diagnóstico del caso activo es Foundation 14 **nativo** mediante `Allmesh`, `checkMesh` y lectura de `log.snappyHexMesh`/`log.splitMeshRegions`. Las ablaciones STL v2 **ya se ejecutaron** y fallaron (1 celda metal en una variante, cero mold en la otra); no pedir nuevas corridas para diagnosticar el formato de un resumen. El análisis de zonas deberá utilizar primero logs existentes y preservar fuentes/casos. [Bitácora](C3D_02_ABLACION_STL_V2_20261118_ES.md) · [alternativa a investigar](C3D_02_REFERENCIA_DOCTOR_Y_OPCIONES_MALLADO_20261118_ES.md). La exigencia de evidencia automática sigue como objetivo de diseño, **no evidencia de que el builder Python haya corrido en WSL**.

# Política permanente: localizar automáticamente errores durante OpenFOAM

**Estado de la regla:** obligatoria para el comando integral de C3D-02 desde el cambio del 17 de noviembre de 2026. Se exige como requisito de diseño para los futuros comandos integrales del proyecto. **No significa que todos los casos históricos hayan sido migrados.**

## Contrato de un solo comando

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 cases_3d/C3D_02_metal_sand_clean/scripts/build_c3d02.py
```

El usuario no debe ejecutar otra cadena de diagnósticos después del fallo del pipeline. El punto de entrada principal llama internamente a `run_error_localization()` y crea automáticamente:

- `~/OpenFOAM/C3D02_DELIVERY_01/BUILD_STATUS.json`: etapa, éxito/bloqueo y error principal.
- `~/OpenFOAM/C3D02_DELIVERY_01/ERROR_ZONES.json`: clasificación por `global`, `metal` y `mold`; número de celdas, fallos de `checkMesh`, conjuntos de errores, estadísticas y rutas a VTK.
- `~/OpenFOAM/C3D02_DELIVERY_01/ERROR_ZONES.md`: informe legible, con rangos X/Y/Z en milímetros, intervalos de Y, resumen y ubicación de los errores.
- `~/OpenFOAM/C3D02_DELIVERY_01/error_diagnostics/{global,metal,mold}/`: **copias físicas** de los `polyMesh` disponibles y sus archivos VTK obtenidos mediante `checkMesh -allGeometry -allTopology -writeSurfaces -writeSets` de Foundation 14.

**Activación obligatoria:** se generan informes desde `PREFLIGHT` (incluso si aún no existe `polyMesh`), y se actualizan automáticamente en la salida del comando tanto si se detiene por error como si consigue avanzar. Los fallos tempranos sin malla se documentan con etapa y logs **sin inventar coordenadas**; los fallos con malla se localizan usando exportación VTK real. No se deben pedir al usuario comandos adicionales de diagnóstico.

## Qué se debe reportar, no ocultar

1. Etapa exacta del fallo y material afectado, si se conoce.
2. Fallos reales de `checkMesh`, incluso cuando su código de retorno sea cero.
3. Conteos de `concaveCells`, `underdeterminedCells`, `twoInternalFacesCells` y otros conjuntos exportados cuando existan.
4. Rangos XYZ y distribución axial de los **vértices VTK**, especificando que no son centroides exactos ni números de celdas defectuosas por franja.
5. Rutas a logs y archivos VTK para reproducibilidad. No crear ni alterar físicamente celdas durante el diagnóstico.
6. Mantener bloqueado `foamMultiRun` si fallan geometría, calidad, volúmenes o contacto `mappedWall`.

## Seguridad e integridad

La inspección trabaja exclusivamente sobre copias de malla generadas dentro del **nuevo directorio de entrega**, sin modificar los casos históricos de `C3D02_materials`, ni los STL, ni los materiales controlados C14. Cada comando integral produce un `BUILD_STATUS.json`; si se ejecuta sobre un destino existente, el programa protege los datos y no los sobrescribe.

Los checks de CI verifican la conexión del diagnóstico con `build_c3d02.py`, su uso de `-writeSets`/`-writeSurfaces`, la creación de reportes antes de disponer de malla y su compilación Python. **No confundir CI verde con una ejecución real de OpenFOAM 14 en WSL.**

## Alcance a futuro

Todo nuevo constructor/runner científico de OpenFOAM dentro de `MasterProject` deberá seguir este contrato antes de considerarse listo para uso. La adopción en otros casos es una tarea de implementación verificable, no una afirmación de que ya se haya aplicado.

**Referencia:** `cases_3d/C3D_02_metal_sand_clean/scripts/mesh_error_zones.py`; guía técnica [Foundation 14 checkMesh](https://cpp.openfoam.org/v14/applications_2utilities_2mesh_2manipulation_2checkMesh_2checkMesh_8C.html).
