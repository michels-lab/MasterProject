# Operación Granada C3D-05/B — integración nativa de `foamPostProcess`, diez diccionarios y expediente energético único

**Fecha:** 20 de noviembre de 2026. **Caso B etapa 3/7; 2/7 hitos técnicos cerrados (29 %, NO porcentaje de tesis, CFD ni convergencia)**. G1 CAD/STEP y G2 HEX8/contacto aceptados. **G3 a G7 continúan abiertos**. Este bloque busca detectar fallos reales de postprocesamiento Foundation14 ANTES del hito local WSL, sin fingir haber ejecutado la malla de 270,788 celdas.

## Evidencia previa al nuevo bloque

El extractor bilateral C++ de `q()` **ya compiló, enlazó y arrancó** con el paquete **Foundation14 real** en Ubuntu24.04, con `wmake`, `ldd` y `-help` ([CI #44828749324 PASS](https://github.com/michels-lab/MasterProject/actions/runs/44828749324)). Esto NO significa que se hayan ejecutado `foamMultiRun` o los dos campos de temperatura T de la malla de la tesis.

La revisión nueva detectó un segundo punto sin verificar: el flujo de código `postprocess_t0_energy.py` esperaba nombres, encabezados, volúmenes y temperaturas en los archivos `volFieldValue.dat` de `foamPostProcess`, pero antes se habían probado con archivos fabricados en Python, **nunca con la salida nativa real**.

## Bloque 1. Integración con OpenFOAM Foundation 14 real, sin solver

Se añadió [`tests/smoke_native_foundation14_energy.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/smoke_native_foundation14_energy.py) y [CI correspondiente](../../.github/workflows/c3d05-foundation14-energy-smoke.yml), con `gerlero/setup-openfoam@v1` y `openfoam-version: 14` en `ubuntu-24.04`.

En un directorio temporal de runner (NO geometría STEP ni copia aceptada), este test:

1. Reconstruye la **referencia numérica C14** desde cinco fuentes versionadas, con hipótesis `Cv≈Cp` del hierro declarada, y genera **las diez plantillas actuales de T0** usando `prepare_t0.file_map`.
2. Abre con `foamDictionary` **real** de Foundation14 los diez diccionarios de producción, y rechaza cualquier fallo de sintaxis. No realiza materialización de la malla real.
3. Para cada región `metal` y `mold` genera de cero un cubo de **una sola celda** `blockMesh -region` (volumen 1 m³), asigna `T_metal=400 K` y `T_mold=300 K` uniformes y condiciones externas `zeroGradient`. Estos valores son datos completamente **sintéticos de QA**, NO mediciones de hierro fundido/arena.
4. Lanza `foamPostProcess -region metal/mold -dict system/T0_energy_<region> -time 0:` con el diccionario del programa actual, y alimenta los archivos nativos `volFieldValue.dat` al lector `read_volume_average`/buscador `inspect_outputs`.
5. Exige **volumen=1 m³, temperatura=400/300 K, tiempo=0**, presencia y lectura del encabezado real; un programa que produce CSV sintético sin llamar a OpenFOAM no satisface esta prueba.

**No se ejecuta CFD ni `foamMultiRun`**. El test exclusivamente comprueba la integración de utilidades postpro y gramática F14. La condición `coupledTemperature` de la interfaz 3D no es ejercitada por este test de dos cubos aislados; eso requiere la futura corrida numérica en WSL.

### Error real descubierto en la primera ejecución de Foundation14

La [primera CI nativa de postprocesamiento #44829892575](https://github.com/michels-lab/MasterProject/actions/runs/44829892575) llegó correctamente a `blockMesh` y a los diez diccionarios de producción, pero **falló** al construir `volFieldValue`. El error F14 fue `request for objectRegistry region0 ... available objects ... 1(metal)`: pasar `foamPostProcess -region metal` **no basta** para configurar el objeto de función en esta versión; éste debe incluir `region metal;` o `region mold;` dentro de su propio bloque. Se corrigió **en el generador original `functions_dict()`**, no con un cambio superficial de mensajes o una excepción ignorada. Se incorporó un test que exige explícitamente la región del objeto. La repetición [CI real Foundation14 #44830571389 — PASS](https://github.com/michels-lab/MasterProject/actions/runs/44830571389) demostró **ambos volúmenes y temperaturas desde archivos OpenFOAM auténticos** y confirmó la corrección del problema `region0`. El hito 3D en la malla aceptada permanece pendiente.

## Bloque 2. Comprobación estricta del estado inicial para el balance

[`postprocess_t0_energy.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/postprocess_t0_energy.py) ahora requiere **`t=0` observado y al menos dos instantes de muestra en metal y molde**, además de constatar que `volAverage(T)` del primer instante corresponde a `T_initial_K` de ambas regiones (tolerancia solo de redondeo de salida numérica). Sin este control se podía calcular `ΔE(t)=E(t)-E_0` respecto a un estado inicial que jamás se había observado. Se agregaron regresiones de casos negativos en [`test_postprocess_native_energy.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_postprocess_native_energy.py).

No se fija arbitrariamente un porcentaje aceptable de conservación. El balance sigue calculando `E_r(t)=rho_r Cv_r V_r ⟨T_r⟩_V`; los valores `rho,Cv` de C14 son banco numérico, no JMatPro experimental.

## Bloque 3. Un solo resumen del expediente numérico cuando exista corrida

[`finalize_t0_granada.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/finalize_t0_granada.py) ahora corre automáticamente como **fase 6/6** del mismo [`run_c14_numerical_granada.sh --solve`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_c14_numerical_granada.sh) después de energía regional y flujo bilateral:

- Verifica que la preparación corresponda a la entrada C14 SHA, que el log `foamMultiRun` haya sido clasificado como terminado y que la referencia de equilibrio, las temperaturas, el informe de 12,636 caras y los dos CSV identifiquen los **mismos datos**.
- Revalida los cuatro SHA `manifest.sha256` de la publicación transaccional `T0_NATIVE_FACE_FLUX/`, tiempos 0 a 0.1 s y **12,636 pares por instante**.
- Escribe `T0_GRANADA_EVIDENCE_SUMMARY.json` con los hashes, máximos errores de cierre energético y de distribución bilateral de flujo, número de muestras, y los campos de estado **`numerical_energy_accepted=false`, `numerical_flux_continuity_accepted=false`, `experimental_validation=false`**. No cambia G3/G4 ni el avance técnico de 29 %. La salida es exclusiva/idempotente y no sobreescribe un expediente incompatible.
- [Pruebas negativas](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_finalize_t0_granada.py) verifican la detección de alteración de CSV y manifiestos, falta de identidad del solver/entrada, tiempos incongruentes, conteo de caras y ausencia de aceptación científica falsa. Estas pruebas usan objetos **sintéticos** y no ejecutan CFD.

## Qué está comprobado y qué falta

| Evidencia | Situación |
|---|---|
| Compilación `c3d05PatchFlux` en Foundation14 real, `wmake/ldd/-help` | PASS documentado, [CI 44828749324](https://github.com/michels-lab/MasterProject/actions/runs/44828749324) |
| `foamDictionary` real sobre **10** diccionarios actuales de T0 | **PASS 10/10**, [CI real Foundation14 #44830571389 — PASS](https://github.com/michels-lab/MasterProject/actions/runs/44830571389) |
| `blockMesh` y `foamPostProcess` Foundation14 sobre dos regiones sintéticas | **PASS**: metal 1 m³ / 400 K, arena 1 m³ / 300 K, y lectura nativa `volFieldValue.dat`, [CI real Foundation14 #44830571389 — PASS](https://github.com/michels-lab/MasterProject/actions/runs/44830571389) |
| Validaciones negativas de estado inicial, cadena SHA y resumen numérico | Verificar CI integrada |
| CFD real de la malla 3D aceptada en WSL | **NO EJECUTADO** |
| Conservación, continuidad de flujo real, sensibilidad no ortogonal, JMatPro/curvas QuickCup | **PENDIENTE** |

No modificar C14, la malla HEX8 aceptada ni el `T0_INPUTS.json` físico con valores todavía no documentados. La próxima Granada científica requerirá una sola corrida numérica integrada, no otra sucesión de preflights manuales.
