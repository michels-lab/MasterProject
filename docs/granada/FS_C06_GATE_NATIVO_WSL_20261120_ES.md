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
