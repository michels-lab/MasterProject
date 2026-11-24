> **23-11-2026 — FS-C08: núcleo conservativo en C++17 también compilado y probado localmente:** [`ConservativePhaseExchange.H`](../freesurface/FS-C08_conservative_phase_mass/native_cpp/ConservativePhaseExchange.H), [tests C++17](../freesurface/FS-C08_conservative_phase_mass/native_cpp/test_ConservativePhaseExchange.C) y [README de FS-C08](../freesurface/FS-C08_conservative_phase_mass/README.md). Balance de masa líquido/sólido con fuentes `±Γ`, flujo de frontera y volumen de contracción/expansión, compilado con `g++ -std=c++17 -Wall -Wextra -Werror -pedantic`, **PASS sintético**. Además 18 pruebas Python de energía/masa y cierre pastoso pasaron localmente. **No equivale a compilar con `wmake` ni ejecutar OpenFOAM 14 3D.**

> **23-11-2026 — FS-C08: primera implementación conservativa EJECUTABLE (rama aislada, NO CFD 3D aún):** [código y bitácora de masa líquido/sólido/gas, energía, Γ y volumen](../freesurface/FS-C08_conservative_phase_mass/README.md) · [`STATUS.json`](../freesurface/FS-C08_conservative_phase_mass/STATUS.json). Se probó en contenedor Linux: **18/18 pruebas sintéticas OK** con `rho_l(T),rho_s(T),cp(T)`, `Γ` de fuente opuesta, transporte entre celdas, frentes abiertos, calor latente contabilizado una vez y cierre pastoso `f_s(T)` lineal solo de demostración. **Presión de mezcla, advección de interfaz, energía mecánica, propiedades JMatPro de la aleación y compilación OpenFOAM 14 siguen PENDIENTES.** Rama `research/fs-c08-conservative-phase-mass-20261123` para no tocar FS-C07.

> **23–24/11/2026 — FS-C07 gate espacial nativo 20/20 completamente ejecutado:** [reporte de las 20 instantáneas y contrato siguiente de formulación conservativa](granada/FS_C07_GATE_20DE20_VOF_Y_RUTA_MODELO_CONSERVATIVO_20261123_ES.md) · [20 registros reales en JSON estructurado](../freesurface/FS-C07_thermal_transition/evidence/FS_C07_PHASE_ALLOCATION_20_NATIVE_STATES_20261123.json). Se comprobaron **0** excesos `alphaSolid>alphaMetal+1e-8` donde `alphaMetal>=0.5` en los 20 estados; **7,692 incidencias** celda×tiempo fuera del núcleo, 99.26% con `alphaMetal<1e-3`. El criterio global de fases **sigue FAIL**. FS-C07 no simula contracción física: siguiente hito es `Gamma`, `rho_l/rho_s`, continuidad líquido/sólido y balances discretos de energía, masa y fronteras. Sin nueva corrida ni clip de campos originales.

> **23-11-2026 — FS-C07: fallo de reparto sólido/metal localizado en VOF bajo (tres tiempos reales):** [coordenadas nativas, 187/598/378 defectos, nulos en alpha_metal>=0.5 y orden del código oficial Foundation14](granada/FS_C07_ORIGEN_ESPACIAL_ALLOCATION_Y_ORDEN_NATIVE_C14_20261123_ES.md). El modelo se corrige ANTES del transporte `alphaPredictor` y el campo sólido puede quedar desfasado respecto al VOF al escribir: mecanismo plausible, no exclusivo verificado. El [analizador de solo lectura](../analysis_tools/locate_fs_c07_phase_violation.py) ya tiene modo **`--all-saved --compact`** para validar 20/20 estados; todavía no ejecutado en WSL. No hay contracción física aprobada.

> **23-11-2026 — FS-C07 volumen sólido y metal RAW recuperados en WSL:** [auditoría de 20 estados, discrepancia nativa mínima e inventario de error](granada/FS_C07_AUDITORIA_VOLUMETRICA_NATIVE_1S_20261123_ES.md). A 1s, `V_solid_raw=2.40359109 cm³`, `V_metal_raw=48.01103827 cm³`, razón `5.00633%`; exceso `alphaSolid>alphaMetal` integrado a 1s `0.00176807 mm³`. **Local 1e-8 boundedness FAIL**; variación `-0.878 mm³` de VOF no representa contracción física demostrada. [Diagnóstico espacial nativo de solo lectura preparado](../analysis_tools/locate_fs_c07_phase_violation.py) para analizar el reparto por tamaño de `alpha.metal` a 0.2/0.4/1.0s, todavía no corrido en WSL.

> **23-11-2026 — FS-C07 evolución real de fase:** [análisis de los 20 estados OpenFOAM nativos](granada/FS_C07_20_ESTADOS_REALES_FRACCION_SOLIDA_Y_VOF_20261123_ES.md) confirma `max(alpha.metal.solid)=0.500401` y `1160` celdas núcleo bajo `1473 K` (C14 provisional) a 1s. La primera violación de reparto metal/sólido superior a 1e-8 aparece a t=0.05s; máximo 6.181e-6 a 0.2s. [Recuperador raw volumétrico de solo lectura](../analysis_tools/recover_fs_c07_native_phase_metrics.py) integra originales sin clip/CFD y mide volumen de error; no ejecutado aún en WSL. **Solidificación nativa observada; contracción y aceptación física abiertas.**

> **23-11-2026 — FS-C07: solver nativo COMPLETÓ 1.0 s, postproceso de fases BLOQUEADO:** [informe del solver completado y fallo exacto del gate VOF/sólido](granada/FS_C07_NATIVE_1S_SOLVER_COMPLETADO_POSTPROCESO_BLOQUEADO_20261123_ES.md). Hay 20 estados nativos y 10,868 directorios; el primer filtro de asignación de fracciones falló fuera de tolerancia 1e-8, sin reporte de celda específica aún. [Forensic de solo lectura](../analysis_tools/diagnose_fs_c07_phase_allocation.py) evita repetir CFD y permite identificar los valores. **No declarar solidificación aceptada, contracción ni cierre de energía/masa.**

> **20-11-2026 — FS-C06: revisión cuantitativa de 10 monitores nativos reales:** [datos originales, diez SHA-256, discrepancia térmica +0.04326368 W y masa de mezcla +5.2e-12 kg](granada/FS_C06_AUDITORIA_MONITORES_20261120_ES.md). Los campos `alpha.metal.solid=0` y volumen metal estable; **no** hay evidencia de contracción o cierre conservativo global.

> **20-11-2026 FS-C06 — campos cuantificados y diagnóstico Foundation14:** [bitácora de VOF/metal sólido 0 y cambio de `system/controlDict.functions` a `system/functions`](granada/FS_C06_GATE_NATIVO_WSL_20261120_ES.md). El solver ya ejecutó la prueba de 2 pasos en WSL y escribió `alpha.metal.solid`, pero la instrumentación corregida aún no se ha probado. No hay contracción física ni balance de masa/energía.

> **20-11-2026 — FS-C06: primer gate WSL Foundation14 reportado PASS:** [bitácora de ejecución nativa y límites físicos](granada/FS_C06_GATE_NATIVO_WSL_20261120_ES.md). `foamMultiRun` 2 pasos, campo `alpha.metal.solid` y `checkMesh fluid/mold` aprobados según consola del investigador; no hay evidencia revisada de contracción real, balance global o curva QuickCup. Los informes anteriores de «código no ejecutado» son históricos.

> **15-11-2026 — C3D-02 extracción validada por volumen, calidad fallida:** [bitácora de `moldVolume` (274,788 celdas, 103.409 cm³, outerBox=0)](C3D_02_DOS_MALLAS_20261112_ES.md), 22,737 cóncavas + un determinante bajo; [script de diagnóstico de defectos en copias](../cases_3d/C3D_02_metal_sand_clean/scripts/inspect_extracted_mesh_quality.sh). Aún no hay interfaz CHT ni CFD.

> **15-11-2026, C3D-02:** [medición local de moldVolume 103.409 cm³ y protocolo de extracción en copia](C3D_02_DOS_MALLAS_20261112_ES.md). Nuevo `scripts/extract_mold_zone_copy.sh` usa `subsetMesh -cellZone moldVolume -noFields` exclusivamente en carpeta nueva. Pendientes fronteras/convexidad, no CFD.

> **13-11-2026 — C3D-02:** [geometric zoning result](C3D_02_DOS_MALLAS_20261112_ES.md): `moldVolume` 274,788 cells and `moldInterface` 97,492 faces, but global box volume 242.208 cm³ and checkMesh failure. Next operation is **read-only zone-volume measurement** through `scripts/measure_mold_zone_volume.sh`, *not* new meshing or CFD.

> **13-11-2026, C3D-02:** el aumento de refinamiento a L3 conservó el volumen total de la caja (242.208 cm³) y eliminó solo seis celdas. [Registro y nueva prueba explícita de cellZone en L2](C3D_02_DOS_MALLAS_20261112_ES.md); no se publican mallas CHT ni CFD sin checks.

> **12-11-2026, actualización real C3D-02:** el nuevo punto interior de arena no cambió el fallo (568,134 celdas y 242.142 cm³; `outerBox=15164`). [Bitácora científica del intento y lecciones](C3D_02_DOS_MALLAS_20261112_ES.md), [script de auditoría sin remallado](../cases_3d/C3D_02_metal_sand_clean/scripts/inspect_mold_leak.sh). Próximo paso: comprobar autointersecciones y conectividad.

> **12-11-2026, C3D-02 retry1:** la malla del hierro alcanzó **47.9621 cm³** sin exterior (pero 2,422 cóncavas); la arena retuvo **242.142 cm³ y 15,164 caras exteriores**, calidad fallida. [Resultado real, condición insidePoint y prueba solo del molde](C3D_02_DOS_MALLAS_20261112_ES.md). El punto x=3 mm de arena se encontraba sobre una cara de la malla de fondo; corrección candidata **NO ejecutada**.

> **12-11-2026, actualización C3D-02:** [error y corrección de `allowFreeStandingZoneFaces` en las dos mallas materiales](C3D_02_DOS_MALLAS_20261112_ES.md), [manual OF14 con comando de reanudación](../OPENFOAM_COMMAND_MANUAL_ES.md). `snappyHexMesh` se detuvo sin malla física; el único reintento previsto preserva el workspace existente.

> **C3D-02 12-11-2026:** [siguiente etapa — mallas geométricas independientes hierro/arena](C3D_02_DOS_MALLAS_20261112_ES.md), seguida del diseño y validación de contacto térmico. Esta ruta está **preparada, NO CORRIDA**; no reemplaza la evidencia del primer mallado fallido.

> **Estado 12-11-2026:** primera malla local C3D-02 rechazada, 242.130 cm³ / 589,701 celdas / 2 checks fallidos. [Resultado y decisiones](C3D_02_MALLADO_INICIAL_20261112_ES.md) · [Script de diagnóstico sin remallar](../cases_3d/C3D_02_metal_sand_clean/scripts/diagnose_mesh_readonly.sh). No confundir configuración fuente con solver 3D verificado.

> **Nuevo 12-11-2026:** [Guía de primer mallado físico C3D-02](C3D_02_MALLADO_INICIAL_20261112_ES.md), con comando único, selección `insidePoints`, prueba de calidad exhaustiva y condiciones de aceptación. **No confundir candidato no ejecutado con resultados.**

> **12-11-2026:** [Reinicio de C3D y consolidación de pruebas](C3D_REINICIO_20261112_ES.md) · [Lecciones y comandos verificables de OpenFOAM 14](OPENFOAM14_LECCIONES_C3D_20261112_ES.md) · [Nuevo caso fuente 3D](../cases_3d/C3D_02_metal_sand_clean/README.md). Las notas fechadas 10-11 se conservan como evidencia histórica; las actualizaciones posteriores tienen prioridad de estado.

# MasterProject — índice de documentación científica

> **Estado científico actualizado, 10-11-2026 — C3D-01:** recorte local metal + arena: **1,209,777 celdas; 151.230 cm³; 15 celdas cóncavas, 8 face-tets deficientes, 17 celdas de determinante pequeño; 3 fallos `checkMesh`**. `splitMeshRegions -disconnected` separó `region1` (probable arena, **825,994 celdas; 103.256 cm³; 3 fallos**) y `region2` (probable metal, **383,783 celdas; 47.9735 cm³; 2 fallos**); **`No interfaces to add`**. **Sin interfaz CHT, sin CFD 3D ni malla aprobada.** El ensayo `-cellZones 'metal'` aún **NO** se ejecutó. [Evidencia](C3D_01_ESTADO_REAL_20261110_ES.md) · [Manual](../OPENFOAM_COMMAND_MANUAL_ES.md).


Este índice organiza la documentación **sin mover ni reemplazar** archivos existentes. Este proyecto es completamente independiente de FoamLens y de cualquier repositorio coordinador.

- [Identidad canónica de MasterProject y conservación de nombres de casos](MASTERPROJECT_IDENTITY_ES.md)

- [Auditoría de documentación viva al 10-11-2026](DOCUMENTATION_AUDIT_20261110_ES.md) — cobertura real, comandos registrados, discrepancias y límites de evidencia

## Empezar / operación
- [README](../README.md) — descripción y estado por confirmar en cada actualización
- [RUN_MASTER_PROTOCOL](../RUN_MASTER_PROTOCOL.md) — reglas obligatorias antes/después de cada corrida **local**
- [Manual de comandos y selector ES/EN](../OPENFOAM_COMMAND_MANUAL.md)
- [Manual práctico español](../OPENFOAM_COMMAND_MANUAL_ES.md)
- [OpenFOAM command manual English](../OPENFOAM_COMMAND_MANUAL_EN.md)
- [Guía técnica de casos](../CASE_GUIDE_ES.md)
- [Guía interactiva](../CASE_GUIDE_INTERACTIVE_ES.html)

## Física, propiedades y validación
- [Guía de campos/posproceso](../POSTPROCESSING_FIELD_GUIDE_ES.md)
- [Trazabilidad JMatPro](../JMATPRO_OPENFOAM_TRACEABILITY_ES.md)
- [Matriz de validación ES/EN](../VALIDATION_MATRIX.md)
- [Hoja de ruta física](../NEXT_RESEARCH_ROADMAP_ES.md)
- [Casos tridimensionales](../cases_3d/README.md)

## Registro, resultados y bitácoras
- [Inventario de casos CSV](../RUN_CASE_REGISTRY.csv) — estados físicos/numericos independientes
- [Bitácora auditada ES/EN](../PROJECT_AUDIT_LOG.md) — registro histórico canónico
- [Granada](../.michelslab/GRANADA.md) — protocolo local de continuación
- [Granada coordinación 2026-10-20](granada/GRANADA_GRANDE_GOVERNANCE_20261020.md)
- [Resumen de campaña histórica](../analysis_results/full_campaign_audit/README.md)
- [Evidencia V15/V16 2026-10-20](../analysis_results/granada_v15v16_postrun_20261020/summary.md)
- [Granada: auditoría de procedencia B11/C11 energy2 y documentos duplicados](granada/B11_C11_ENERGY2_DOCUMENTATION_AUDIT_20261021.md) — hallazgo documental, no validación CFD

## Relación voluntaria con otros proyectos
- [FoamLens](https://github.com/michels-lab/FoamLens) es un **visor genérico e independiente**. No es requisito para resolver, validar o publicar este trabajo.
- [Contrato público de límites](OPENFOAM_ECOSYSTEM.md). La coordinación externa nunca gobierna los cálculos ni sustituye este registro.

**Norma:** cambios científicos aquí, manuales científicos aquí, resultados reales aquí. Un informe de GitHub/CI no equivale a validación experimental. Para reubicar un documento debe existir un inventario de referencias y una migración revisada por separado.
- [Granada: constancia de acceso coordinador en modo lectura](granada/OPENFOAM_HUB_READ_ACCESS_20261021.md)
