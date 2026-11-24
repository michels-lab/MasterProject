# Caso A C3D04 — error real F14 cellZone y recuperación nativa honesta

**23 de noviembre de 2026 · Etapa 7/10 en proceso · 6/10 hitos (60 %)**.

## Observación real, no inferida

El investigador ejecutó el analizador **de solo lectura** sobre `~/OpenFOAM/C3D04_A_C14_SOLVER_BACKED_POSTPROCESS_02`. Su salida WSL mostró:

- `EXISTING_COMPLETE_NATIVE_POSTPROCESS_REPORT_REUSED_NO_NEW_RUN`: el informe final previo existe, está firmado por SHA de fuente, y hay seis logs completos de subprocesos. En esta invocación no se ejecutó solver ni `foamPostProcess`, y no se modificó el CFD.
- El informe anterior dice `native_groups_passed = core, energy, phase, flow, profiles, momentum` y `native_groups_failed=[]`, **pero esta interpretación es falsa**: en los logs reales de `core`, `energy`, `flow` y `momentum` se repite `FOAM FATAL IO ERROR`, con **`Cannot find cellZone metal`** y **`Available cellZones: 0()`**, desde `constant/metal/fvModels!phaseChangeSource/cellZone`. Los códigos de salida cero y el texto `End` al final de los logs no anulan los errores fatales.
- Los logs de `phase` y `profiles` no presentan esas marcas de error fatal. La media de alpha1 impresa al t10 por el objeto nativo es `0.897245`. La ausencia de FATAL **no** demuestra todavía que todos los perfiles tengan sus 80 puntos finitos.
- El viejo resumen energético da `NATIVE_SURFACE_POWER_TABLES_MISSING_OR_INCOMPATIBLE`, `need 101 native saved time rows`. Hay que inspeccionar las **filas y tiempos reales de cada tabla** en lugar de asumir falta de información o de inventar t=0.
- En total había seis subprocesos ejecutados y registrados, **pero cuatro no se aceptan como éxito nativo por los FATAL IO**. El CFD original C14 de 10s y la cinética 101 estados continúan preservados y son diferentes a los diagnósticos fallidos. No hay evidencia de fallo de la CFD solo por esto.

## Corrección científica nueva

El código `cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_stage07_solver_backed_recovery.py` incorpora:

1. **Éxito semántico:** busca `FOAM FATAL ERROR`, `FOAM FATAL IO ERROR` y `FOAM aborting` en el log completo. Un código de sistema `0` **no** marca PASS si aparece cualquiera de estas señales. Si encuentra la antigua carpeta `_02`, vuelve a clasificar los cuatro grupos como error **sin cambiar su informe original ni reejecutar funciones**.
2. **Metadatos originales de malla comprobados:** reutiliza `stage_c14_3d_case_a.region_cells` y `whole_region_zone`/ `audit_existing_zone` para validar el metal real (C14 A, 8960 celdas). Antes de clonar, comprueba el total; en nueva copia comprueba hashes byte a byte de `points`, `faces`, `owner`, `neighbour`, `boundary`.
3. **Corrección exclusivamente en nueva carpeta:** si el `constant/metal/polyMesh/cellZones` original no existe, escribe un `cellZones` válido de **una sola zona metal que cubre exactamente las 8960 celdas** en el clon NUEVO, no en CFD original ni en `_01`/`_02`. Si ya hay zona íntegra, preserva la copia exacta; si hay zona existente inválida, bloquea para evitar manipular mallas reales. No modifica geometría, conectividad, propiedades C14, `fvModels`, `controlDict` ni el campo `phaseChangeSource:alpha1` original.
4. **Cobertura de salidas:** comprueba la presencia de las tres tablas de potencia de superficie, sus verdaderas cantidades de filas y extremos temporales, así como cuatro perfiles primitivos a t10 con 80 puntos finitos cada uno. Permite reconciliar las potencias top/contact/total en **101 tiempos** (0–10s) o **100 tiempos** (0.1–10s) sin falsificar la potencia inicial t=0. Rechaza 99 o menos tiempos o ejes temporales incompatibles. Ninguna suma de fronteras del metal constituye conservación global metal+arena ni validación QuickCup.
5. **Seis grupos nativos aislados:** core, energy, phase, flow, profiles, momentum. Fallos individuales no bloquean la recopilación de errores de otros grupos y nunca declaran éxito por mero código de salida; las derivadas C14 originales `ddt(T)`, `ddt(alpha1)` no pueden recuperarse desde 0.1s.

## Prueba Foundation14 NATIVA: causa reproducida y corregida (PASS)

**GitHub Actions [F14 smoke 45318181439](https://github.com/michels-lab/MasterProject/actions/runs/45318181439) — SUCCESS.** Se preparó un caso C14 sintético completado de **27 celdas metálicas y 27 del molde** (dos pasos hasta 0.002 s) y una copia independiente sin zona `metal`:

- En la copia sin zona, `foamPostProcess -region metal -solver fluid -latestTime` devolvió efectivamente `exit_code=0` **a pesar** de imprimir `FOAM FATAL IO ERROR: Cannot find cellZone metal; Available cellZones: 0()`. Esto reproduce el mismo falso positivo que observamos en la WSL real.
- Se ejecutó el generador original de zona, escribiendo `cellZones` **solo en un clon nuevo**, con cobertura exacta de las 27 celdas sintéticas, sin cambiar la conectividad del mesh.
- La siguiente ejecución nativa `foamPostProcess` resultó **sin errores fatales**, exit 0, y produjo el `volFieldValue.dat` de `metalSensibleEnthalpy` original C14. El expediente sintético inicial quedó intacto.
- **Límite:** se validó funcionalidad del mecanismo y de las comprobaciones del código, no se ha reejecutado sobre V4/T02 de 8960 celdas ni aceptado energía de metal + arena.

Las regresiones Python de la rama también aprobaron la clasificación de cuatro falsos PASS reales, rechazan materializar zonas en origen, verifican SHA del polyMesh y aceptan 100 o 101 estados guardados **solo con marca de tiempo exacta**.

## Regla de ejecución

`_02` es evidencia histórica **protegida**. Para analizarla de nuevo solo leer, usar el ejecutor sin `--out`; este no escribirá ni modificará nada. Para ejecutar la corrección en datos reales, el destino **debe ser NUEVO y explícito**: `~/OpenFOAM/C3D04_A_C14_SOLVER_BACKED_POSTPROCESS_03`:

```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_stage07_solver_backed_recovery.py" \
  --out "$HOME/OpenFOAM/C3D04_A_C14_SOLVER_BACKED_POSTPROCESS_03"
```

**Sólo usar cuando este código esté fusionado con CI aprobado.** Si `_03` ya existe, se inspeccionará primero de manera no destructiva; nunca se sobrescribe. La nueva copia puede ser grande: no se vuelve a correr `foamMultiRun` ni a recalcular los 10s de CFD; se reprocesan solo los campos guardados de A. B y FS permanecen separados.

## Estado científico

`C3D04_A_C14_STAGE07_RECOVERY_KINETICS_01` continúa con 101 estados y primer descenso de alpha1 observado en (0.2, 0.3]s, potencia latente por diferencias 1038.8813 W en (7.2, 7.3]s, metal a t10 `1450.7092 K` y masa sólida nominal `0.03358 kg`. Estas son cifras del **modelo C14**, no comparación QuickCup ni prueba de balance energético. **Etapa 07/10, 6/10=60% hitos** hasta que las salidas nativas reales y la validación física indiquen algo distinto.
