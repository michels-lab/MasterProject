# FS-C06 — primer gate nativo WSL Foundation 14 aceptado (20/11/2026, hora Saltillo)

## Evidencia disponible y alcance

**Origen:** salida literal de terminal aportada por el investigador el 20/11/2026. Es evidencia externa reportada por quien ejecutó el caso; **los archivos crudos de WSL NO se han transferido ni verificado de forma independiente en GitHub**. No atribuir hashes de archivos no leídos ni tiempos térmicos no medidos.

- Repositorio ejecutado: `michels-lab/MasterProject`.
- Worktree: `~/OpenFOAM/FS_C02_WORKTREE`, HEAD `99dfe9cc1` (rama remota `research/fs-c02-metal-air-vof-20261117`, HEAD detached).
- Entrada FS-C05 original conservada: `~/OpenFOAM/FS_C05_VOF_CHT_RUNS/FS_C05_VOF_CHT_SCREEN_20261119T063448Z_84d08b6e`.
- Ejecutor: `bash freesurface/FS-C06_vof_solidification/run_native_gate.sh <ruta FS-C05>`.
- Caso FS-C06 aislado producido: `/home/michel/OpenFOAM/FS_C06_RUNS/FS_C06_VOF_SOLID_SMOKE_20261121T031743Z_200ccb63`.

### Salida original reportada

```text
HEAD is now at 99dfe9cc1 ci(fs-c06): syntax-check consolidated native bash gate on every branch update
FS-C06: FS_C06_NATIVE_TWO_STEP_MODEL_FIELD_OBSERVED_NOT_SHRINKAGE
ISOLATED CASE: /home/michel/OpenFOAM/FS_C06_RUNS/FS_C06_VOF_SOLID_SMOKE_20261121T031743Z_200ccb63
NO PHYSICAL SHRINKAGE/FEEDING OR GLOBAL MASS/ENERGY CLOSURE.
FS-C06 NATIVE GATE PASS: Foundation14 model fields and both checkMesh regions
PHYSICAL ACCEPTANCE: OPEN; no shrinkage, feeding or global mass-energy balance
ISOLATED NATIVE EVIDENCE: /home/michel/OpenFOAM/FS_C06_RUNS/FS_C06_VOF_SOLID_SMOKE_20261121T031743Z_200ccb63
```

## Interpretación técnica sin exagerar

**Acreditado por la consola y controles implementados:** el ejecutor informó `foamMultiRun` terminado sin error, dos pasos temporales hasta `t=2e-7 s` desde `T_metal=1500 K` de cribado, observación de los campos nativos `alpha.metal.solid` y `T.metal`, integridad del overlay OpenFOAM `controlDict`/`fvModels` y `checkMesh -allGeometry -allTopology` aceptado en `fluid` y `mold`. Un PASS de esta puerta es real a nivel numérico/configuración, **no una prueba de contracción física**.

**NO acreditado aún:** cuánto cambió la fracción sólida, descenso térmico significativo por debajo de `Tliq=1473 K`, ley constitutiva `rho_l(T)` y `rho_s(T,f_s)`, desplazamiento de superficie por contracción, alimentación entre regiones líquidas, balance global de masa por especie, cierre de entalpía y flujo de atmósfera, grafitización respaldada o validación QuickCup.

**Evidencia aún local, por inspeccionar sin relanzar solver:** 
- `FS_C06_REPORT.json`, hashes y métricas `native_fraction_diagnostics.snapshots`;
- `log.FS_C06_foamMultiRun`, que debería contener la evolución de modelos/módulos;
- `log.FS_C06_checkMesh_fluid`, `log.FS_C06_checkMesh_mold`;
- campos `1e-07/fluid/{alpha.metal,alpha.metal.solid,T.metal}` y `2e-07/fluid/{alpha.metal,alpha.metal.solid,T.metal}` (los tiempos pueden tener representación equivalente).

## Decisión de ingeniería

El arranque FS-C06 (configuración de solver) se considera **superado según salida de WSL**; no se repite por defecto. Se inicia la fase de **transición positiva** y modelo constitutivo conservativo, con el siguiente orden:

1. Leer el informe original ya generado y determinar si el metal cruzó el liquidus; con dos intervalos de `1e-7 s` no se debe inferir solidificación macroscópica.
2. Adoptar densidades líquido/sólido **de la composición elegida**, trazadas a JMatPro o mediciones, con dependencia de temperatura y fracción; **no usar por defecto 6820 kg/m³ de FS-C05** como densidad sólida.
3. Diseñar/acoplar la ecuación conservativa de masa para las fracciones metal líquido/sólido; auditar el papel del sólido inmóvil y alimentación por el líquido y cómo cambia `alpha.metal` y el nivel libre.
4. Ejecutar un transitorio de enfriamiento que atraviese `Tliq`, evaluar signos y magnitudes `rho_s-ρ_l` (posible expansión por grafitización en hierro fundido) y cerrar masa/energía, con malla y paso temporal independientes.
5. Comparar contra curvas y datos QuickCup trazables; no cambiar C14, FS-C05 ni casos 3D-A/B.

**Clasificación de esta etapa:** `FS_C06_NATIVE_GATE_PASS_USER_CONSOLE_ONLY__NO_SHRINKAGE`. No es un porcentaje del avance de la tesis.


## 20-11-2026 — Lectura REAL del informe guardado y reparación de monitorización Foundation 14

El investigador consultó directamente el `FS_C06_REPORT.json` de la corrida
`FS_C06_VOF_SOLID_SMOKE_20261121T031743Z_200ccb63` (mismo caso y sin reejecutar CFD):

| Tiempo (s) | VOF metal (m³) | V sólido (m³) | V líquido (m³) | fracción sólida | T.metal media (K) | ΔV metal/VOF |
|---:|---:|---:|---:|---:|---:|---:|
| 1e-7 | 4.801191628e-5 | 0 | 4.801191628e-5 | 0 | 1499.9970068022385 | 0 |
| 2e-7 | 4.801191628e-5 | 0 | 4.801191628e-5 | 0 | 1499.9965640713197 | 0 |

`V0=4.801191628e-5 m³` (48.01191628 cm³). El hierro se enfría
`-0.00343592868 K` de 0 a 2e-7 s (media T.metal); permanece por encima
del liquidus **en promedio** de cribado `1473 K`. No se observaron
volúmenes sólidos en el informe, ni desplazamiento VOF. El informe no
contiene extremos T.metal en todas las celdas, de modo que el promedio solo
no excluye zonas locales bajo liquidus. Los ceros son **medidos** para estas
instantáneas, no supuestos constitutivos.

También consultó cuatro carpetas concretas bajo `postProcessing`:
`FS_C06_atmosphereMassFlux`, `FS_C06_mixtureMass`,
`FS_C06_wallHeatFluxFluid`, `FS_C06_wallHeatFluxMold`.
El comando de lectura encontró **0 archivos `.dat` en cada una**.
Ello NO prueba el fracaso del solver ni que otros monitores tampoco
escribieran: solo que esas rutas no produjeron los archivos solicitados.

**Causa de configuración corroborada por documentación oficial Foundation:**
desde OpenFOAM 12, los functionObjects deben declararse en
`system/functions`, y el código de Foundation14 los lee desde ese archivo:
- https://openfoam.org/release/12/
- https://cpp.openfoam.org/v14/namespaceFoam_1_1functionObjects.html
- https://github.com/OpenFOAM/OpenFOAM-14/blob/master/tutorials/multiphaseEuler/boilingBed/system/functions

La configuración original de FS-C06 había colocado los 10 monitores en
`system/controlDict.functions` (formato histórico), sin archivo
`system/functions` nativo. Se trasladaron los **mismos 3 volFieldValue,
5 surfaceFieldValue y 2 wallHeatFlux** a
`native/system/functions`, manteniendo el `controlDict` original de solver,
sin alterar `fvModels`, termofísica, malla ni el caso exitoso original.
El stager exige ahora un `system/functions` con cabecera Foundation14,
copiado íntegramente y protegido con hash. El gate nativo exige los diez
archivos de monitorización no vacíos antes de anunciar aprobación de
instrumentación. Las pruebas estáticas CI se actualizan al esquema nativo.

**Estado científico tras esta corrección en Git:** datos FS-C06 anteriores
CONFIRMADOS = 0 sólido y 0 cambio VOF hasta 2e-7 s. Instrumentación
CORREGIDA EN CÓDIGO, **todavía no reejecutada ni demostrada en WSL**.
No declarar balances energéticos y de masa a partir de monitores aún
inexistentes. Futuro: comprobar el nuevo esquema de funciones en una
ejecución aislada, idealmente al integrar la siguiente física de transición;
conservar copia del caso anterior sin cambios.
