# Caso A — aislar el error del registro en foamPostProcess Foundation14

**24 de noviembre de 2026.** Etapa 7/10, seis hitos de diez completados (60 % operativo). No se ha cerrado balance energético ni validación QuickCup.

## Hallazgo real de WSL: la zona metálica no está dañada

El investigador ejecutó en WSL `audit_c14_stage07_active_cellzone.py` sobre el CFD C14 A terminado (10 s, 101 estados, 8960 celdas metálicas) y la copia de postprocesamiento `C3D04_A_C14_SOLVER_BACKED_POSTPROCESS_03`.

La auditoría reportó `CONSTANT_METAL_ZONE_VALID_BUT_F14_REGISTRY_EMPTY_ROOT_CAUSE_UNRESOLVED`:

- Original y copia tienen exactamente el **mismo SHA-256 de cellZones**: `e0826b5fa0f3dac433d239dceee10896f251b97f1e950dd224406381e8baa89e`.
- Ambas contienen una `cellZone metal` que cubre **las 8960 celdas**, validada en lectura. Los cinco archivos `points, faces, owner, neighbour, boundary` tienen SHA originales idénticos.
- Los 101 tiempos guardados NO contienen directorios `polyMesh` temporales. Una superposición de otra malla por tiempo **no aparece en la evidencia examinada**.
- Se registran **100 FOAM FATAL IO ERROR por grupo** en core, energy, flow y momentum. Todos repiten `Cannot find cellZone metal; Available cellZones: 0()`; el código de salida es cero, pero el éxito nativo es FALSO.
- Los tres archivos de potencia top/contact/total contienen una única fila a `t=0`; no existe la serie native requerida para balance.
- Phase y profiles no tienen errores fatales. La media volumétrica de alpha1 a 10 s es `0.897245`; tres perfiles horizontales tienen 80 puntos y el vertical solo 27, por tanto cobertura científica insuficiente.

**Conclusión:** no reconstruir ni cambiar nuevamente `cellZones`, geometría, `fvModels` o solver original. El mecanismo de creación ya está demostrado en el smoke sintético C14; lo que falló es el **postprocesamiento multitemporal real**.

## Hipótesis fundada en el código de OpenFOAM 14

El código fuente Foundation14 `foamPostProcess.C` — `https://cpp.openfoam.org/v14/foamPostProcess_8C_source.html` — construye `fvMesh` una vez; dentro del bucle de tiempos llama `mesh.readUpdate()`, construye un solver con `solver::New`, ejecuta las funciones y después ejecuta `mesh.objectRegistry::clear()`. Al terminar una iteración puede capturar `IOerror` e imprimir advertencia; el proceso podría devolver cero **a pesar de errores fatales por tiempo**. Estos hechos en el fuente coinciden con un resultado válido en `t=0` seguido de cien errores en los tiempos siguientes.

**No es lícito declarar todavía que objectRegistry::clear causa la pérdida de zonas**: es una hipótesis causal, no evidencia de cómo funcionó la malla real. Una prueba de diferencia controlada de CLI determinará si falla únicamente al mantener varios tiempos dentro de un proceso.

## Herramienta implementada: cuatro procesos, solamente tres estados auténticos

`cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/probe_c14_native_f14_single_vs_multi_time.py`

En una carpeta **nueva, explícita y fuera de repositorios y corridas**, clona físicamente solo `system`, `constant` y **tres** instantáneas guardadas:

- `t=0` solamente; `foamPostProcess -region metal -solver fluid -time 0`
- `t=0.1` solamente; `foamPostProcess -region metal -solver fluid -time 0.1`
- `t=10` solamente; `foamPostProcess -region metal -solver fluid -time 10`
- Los mismos tres tiempos en un solo comando `-time '0,0.1,10'`.

Cada prueba ocupa su propio clon dentro del nuevo directorio y utiliza **exactamente** el objeto original `metalSensibleEnthalpy`, los modelos físicos C14, mesh y zona ya aceptados. Inspecciona código de retorno, marcas FATAL, última porción del log y las filas/tiempos verdaderos de la integral volumétrica nativa `rho*h`.

Si las tres pruebas independientes pasan y el comando combinado presenta los errores de zona, quedará verificada la diferencia de comportamiento multitemporal a esos tiempos y podremos implementar recuperación nativa **por tiempo** en otra copia nueva, sin recomputar el CFD. Si fallan también las pruebas independientes, será otro problema de modelo/tiempo y lo informará sin atribuirlo falsamente al bucle.

Antes de crear una carpeta valida fuente física, `controlDict` original (8960 celdas), zona `metal` nativa, log auténtico `foamMultiRun`, campos guardados, directorios contra symlinks y destinos no ocupados. Al terminar revalida SHA de archivos críticos. No ejecuta `foamMultiRun`, `blockMesh`, `topoSet` ni altera `_01`, `_02`, `_03`, CFD original o worktrees B/FS.

El reporte nuevo será `C3D04_A_F14_NATIVE_SINGLE_VS_MULTITIME_PROBE_REPORT.json`, sin sobrescribir resultados previos. Este diagnóstico **no corre los 101 estados**, ni reclama conservación global, independencia de malla/tiempo o validación QuickCup.

## QA nativa: corrección de una ruta de ejecución incorrecta

La primera corrida sintética Foundation14 de tres tiempos ([run 45350301865](https://github.com/michels-lab/MasterProject/actions/runs/45350301865)) NO proporciona evidencia sobre el registro multitemporal: el primer ejecutor construía la ruta de trabajo con la carpeta del diccionario `system/` en vez de la raíz del caso. La traza real decía `Case: .../combined_three_times/system` y `cannot find file .../system/system/controlDict`. Por tanto, el resultado `SINGLE_TIME_NATIVE_FAILURE_PRESENT_NOT_ONLY_MULTITIME` de esa corrida se **descarta para inferencias físicas**; el error era del propio diagnosticador, no del caso C14.

La herramienta se corrigió para usar `trial_case = dictionary.parent.parent` (directorio raíz de la copia), y sus regresiones ahora exigen la presencia de `system/controlDict` y `constant/metal/polyMesh/cellZones` desde el cwd real del subproceso. La siguiente corrida de CI y cualquier diagnóstico WSL usarán este ejecutor corregido. **No atribuir un error de ruta a cellZone ni a foamPostProcess.**

## Evidencia Foundation14 sintética

Se añadió al workflow original C14 F14 nativo una prueba reutilizando el caso 27+27 celdas, dos pasos de solver ya terminados en CI. **Solo después de terminar** esos dos pasos sintéticos, prueba `0`, `0.001`, `0.002` por separado y juntos mediante postproceso C14, conservando logs de todos los experimentos. Las regresiones Python prueban además un error fatal que aparece exclusivamente en multitiempo y protegen el expediente original. La CI sintética y la WSL real son experimentos distintos; no presentar la primera como prueba del V4/T02.

## Ejecución propuesta en WSL una vez integrado y validado el código

```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/probe_c14_native_f14_single_vs_multi_time.py" \
  --out "$HOME/OpenFOAM/C3D04_A_C14_F14_THREE_TIME_ISOLATION_PROBE_01"
```

La salida trae un `verdict` y un JSON compacto de las tres pruebas individuales y la prueba conjunta. **No utilizar destinos existentes, no reejecutar los 10 s y no fabricar curvas energéticas de 101 tiempos mientras la causa permanezca desconocida.**

**Avance oficial:** Caso A etapa **7/10**, hitos **6/10 = 60 %**. El próximo resultado permitirá elegir el mecanismo de recuperación del postprocesamiento energético; todavía no es aceptación física.
