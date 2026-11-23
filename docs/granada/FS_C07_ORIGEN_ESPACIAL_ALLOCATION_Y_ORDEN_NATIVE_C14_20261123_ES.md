# FS-C07 — causa localizada en VOF muy bajo y orden de actualización nativo Foundation14

Fecha: **23 de noviembre de 2026**. Esta nota registra resultados **nativos reales aportados por el investigador** mediante `analysis_tools/locate_fs_c07_phase_violation.py` ejecutado en WSL en el caso original `/home/michel/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4`; dicho diagnóstico informa `case_modified=false`, `solver_rerun=false`. La transcripción recibida se conserva como evidencia conversacional y tiene SHA256 **`80429d631fbccd4d5dc1dfb0061263a8d1a05cb183bf18a2a03329672fbcaad8`**; no confundir este hash del texto con SHA256 de campos originales.

## Hallazgo espacial comprobado en 3 de 20 tiempos guardados

Criterio de defecto `alpha.metal.solid-alpha.metal>1e-8`. Las **34,368 celdas fluidas** se clasificaron según **alpha.metal REAL** guardado, sin clip ni sustitución:

| t [s] | celdas >1e-8 | con alpha<1e-6 | con 1e-6<=alpha<1e-3 | con 1e-3<=alpha<0.5 | con alpha>=0.5 | exceso integrado [mm³] |
|---:|---:|---:|---:|---:|---:|---:|
| 0.2 | **187** | 62 | 123 | 2 | **0** | 0.002974383439616884 |
| 0.4 | **598** | 217 | 377 | 4 | **0** | **0.0061272893715684775** |
| 1.0 | **378** | 171 | 200 | 7 | **0** | 0.0017680724185913683 |

No hay violaciones >1e-8 en `alpha.metal<=0` ni en `alpha.metal>1` en estos tres tiempos. La condición **`alpha.metal>=0.5`** se satisface respecto al exceso sólido local en los estados seleccionados; **aún no se ha examinado esta clasificación de 20/20 estados**.

En `t=0.2s`, `89.98%` del exceso integrado proviene del rango `1e-6..1e-3`; a `t=0.4s` `85.42%`, y a `t=1.0s` `71.66%`. Estas son **zonas de muy bajo VOF**, pero `alpha<0.5` por sí solo **no localiza geométricamente una superficie libre** y NO permite declarar contaminación restringida a una frontera particular.

Ejemplos de celdas y ubicaciones de la **malla nativa** (promedio de 8 vértices, no coordenada de interfaz exacta):

- 0.2s celda **30580**, `(x,y,z)=(0.01869765625,0.003,0.00669375) m`, `alpha_m=0.00134523317659`, `alpha_s=0.00135141451949`, exceso `6.181342900000129e-6`, `T.metal=1394.36566941 K`.
- 0.4s celda **7304**, `(0.052098998,-0.0385,0.04227437375) m`, `alpha_m=3.49437489642e-5`, `alpha_s=3.90103974951e-5`, exceso `4.066648530900001e-6`, `T.metal=260.252113784 K`.
- 1.0s celda **12400**, `(-0.0017317275,-0.0035,0.043169829625) m`, `alpha_m=3.47762515e-6`, `alpha_s=3.97433778811e-6`, exceso `4.967126381099997e-7`, `T.metal=392.780743258 K`.

Estas temperaturas tan bajas en células con `alpha_metal≈1e-6..1e-5` son compatibles con que las celdas pertenezcan a aire o a una zona casi vacía de metal; **no** deben interpretarse como 260 K en un núcleo de metal sólido. Sí justifican examinar si `alpha_solid` se está actualizando con temperatura de una región no ocupada significativamente por metal.

## Hallazgo **estático** en el código exacto OpenFOAM Foundation 14

Archivos oficiales inspeccionados:

1. [`applications/solvers/foamMultiRun/foamMultiRun.C`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/solvers/foamMultiRun/foamMultiRun.C): dentro de `while(pimple.loop())`, se ejecuta `solvers[i].fvModels().correct()` **antes** de `solvers[i].prePredictor()`; solo después se resuelven transporte/energía/presión y fuera de PIMPLE se llama `runTime.write()`.
2. [`applications/modules/twoPhaseSolver/twoPhaseSolver.C`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/modules/twoPhaseSolver/twoPhaseSolver.C): `twoPhaseSolver::prePredictor()` llama `alphaPredictor()`, y luego `mixture.correct()`. [`compressibleVoF.C`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/modules/compressibleVoF/compressibleVoF.C) delega en `twoPhaseVoFSolver::prePredictor()`.
3. [`applications/modules/compressibleVoF/fvModels/VoFSolidificationMelting/VoFSolidificationMelting.C`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/modules/compressibleVoF/fvModels/VoFSolidificationMelting/VoFSolidificationMelting.C): en `correct()` primero `alphaSolid_.oldTime()` y `alphaSolid_[celli]=min(relax_*alphaVoF[celli]*alphaSolidT(TVoF[celli])+(1-relax_)*alphaSolid_[celli],alphaVoF[celli])`, seguido de `alphaSolid_.correctBoundaryConditions()`.

**Inferencia técnica fuerte, aún no prueba dinámica directa**: `alphaSolid` se limita contra el `alphaVoF` presente al invocar `fvModels.correct()`; luego `alphaPredictor()` cambia `alphaVoF` antes de la escritura, y es posible que `alphaSolid>alphaVoF` en el estado guardado. La actual instrumentación no guardó campos inmediatamente *antes* y *después* de cada llamada; no puede demostrarse causalidad exclusiva solo con esta coincidencia de código y evidencia final.

**No** modificar ni truncar las instantáneas originales para forzar `alphaSolid<=alpha`. No convertir un modelo `VoFSolidificationMelting` (calor latente + Darcy) en un modelo de contracción meramente cambiando el orden de operaciones: la fase sólida no lleva continuidad conservativa independiente ni densidades por fase JMatPro. Incluso una sincronización `alphaSolid` posterior al transporte debería revisarse con el término temporal de calor latente, transporte de cantidad de movimiento y presupuesto de masa, para no introducir pseudofísica.

## Acción integrada — completar cobertura 20/20 sin CFD

Se amplió [`analysis_tools/locate_fs_c07_phase_violation.py`](../../analysis_tools/locate_fs_c07_phase_violation.py) con:

- `--all-saved` descubre exactamente los 20 directorios reales que contienen **los tres archivos** `alpha.metal`, `alpha.metal.solid`, `T.metal`, ignorando miles de carpetas solo de functionObjects.
- `--compact` imprime una fila por tiempo, máximos por fracción, volumen de exceso y si hay violaciones en núcleo `alpha>=0.5`; guarda el peor caso local sin alterar el caso.
- Ocho pruebas sintéticas totales (se añadieron dos para verificar exclusión de tiempos espurios y para **rechazar** una conclusión 20/20 cuando un estado del núcleo sí tiene defecto). **CI y ejecución WSL todavía no verificadas.**

```bash
cd ~/OpenFOAM/FS_C02_WORKTREE
git fetch origin research/fs-c02-metal-air-vof-20261117
git switch --detach FETCH_HEAD
python3 analysis_tools/locate_fs_c07_phase_violation.py \
    --all-saved --compact \
    ~/OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4
```

El resultado no aceptará automáticamente el encaje sólido–metal global. Si se corrobora **20/20** sin defectos de núcleo, el hito siguiente será instrumentar en **una copia aislada futura** el VOF *antes* y *después* del `alphaPredictor` y `alphaSolid` antes/después de `correct`, con validación del balance volumétrico y luego implementar la continuidad metal líquido/sólido, cambio de fase `Gamma` y acoplamiento de `rho_l/rho_s` a presión, energía y alimentación. No se ha implementado todavía solver de contracción conservativa.
