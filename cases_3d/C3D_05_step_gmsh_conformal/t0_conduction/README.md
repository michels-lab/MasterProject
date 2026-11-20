# C3D-05 / Caso B — T0 térmico, Operación Granada

**Estado al 20-11-2026:** **etapa 3/7; 2/7 hitos técnicos completos = 29%**. G1 geometría CAD/STEP/procedencia PASS; G2 malla HEX8 y contacto metal–arena aceptados con advertencia de no ortogonalidad. G3–G7 ABIERTOS. El 29% NO corresponde al avance global de la tesis, calidad CFD o validación física.

**Regla permanente `PROJECT_PROGRESS_CONTRACT_20261119`:** el investigador NO debe ejecutar rondas de tests por pieza. Se entrega cada hito completo con QA interno, estado explícito y una sola ejecución WSL cuando sea necesaria. Consultar el [estado canónico](../../../docs/PROJECT_STAGE_STATUS.json) y el [contrato Granada](../../../docs/POLITICA_ENTREGA_INTEGRAL_Y_ESTADO_ES.md).

## Hipótesis del T0 y evidencia existente

Dos regiones tratadas temporalmente como **sólidos**, con energía sensible y propiedades constantes:

`rho * Cv * dT/dt = div(kappa*grad(T))`.

Interfaz `metal_to_mold` ↔ `mold_to_metal`: `coupledTemperature` y contacto ideal. Fronteras externas `metalTop` y `moldOuterUnclassified`: `zeroGradient` para un experimento NUMÉRICO de sistema cerrado, no para reproducir enfriamiento de fundición real. No hay movimiento de metal, aire, calor latente, cambio de fase, recalescencia, contracción, alimentación ni experimentos calibrados.

Malla original aceptada e **inmutable**: `~/OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02`, 270,788 HEX8 (92,200 metal; 178,588 molde), 12,636 caras de contacto por lado y 1,826 caras con no ortogonalidad mayor que 70°. La aceptación topológica no demuestra estabilidad del solver, independencia de malla ni exactitud térmica.

## Parámetros: separar modelo numérico de física experimental

El modelo FÍSICO sigue en [`T0_INPUTS.json`](T0_INPUTS.json) con propiedades/temperaturas nulas hasta disponer de valores SI respaldados, idealmente JMatPro/experimento. **No reemplazar esa plantilla por valores ilustrativos**.

La referencia de diagnóstico archivada C14 es **otra entrada**, generada fuera del repositorio por [`scripts/c14_numerical_reference.py`](scripts/c14_numerical_reference.py), con SHA-256 de cinco archivos originales C14. Incluye los valores archivados `rho_metal=6820`, `Cp_metal=827`, `mu=0.0055`, `Pr=0.14`, `rho_mold=1500`, `Cv_mold=700`, `k_mold=2`, `T_metal=1500 K`, `T_mold=300 K`; **`Cv_metal≈Cp_metal` es una hipótesis numérica y `k_metal=Cp*mu/Pr` es un cálculo del modelo fluido original, no valores medidos ni parámetros experimentales de hierro/arena**.

Las tres plantillas `fvSolution` provienen explícitamente del Caso C14; [manifiesto con SHA Git](C14_FVSOLUTION_PROVENANCE.json). Se conservaron parámetros pertinentes de C14 pero se excluyeron `p_rgh` y `U` porque T0 no incluye región fluida. El efecto real de correctores de energía y no ortogonalidad aún necesita evaluación nativa.

## Único punto de entrada (NUMÉRICO, NO CFD validado)

**`GRANADA_C3D05_T0_INTEGRAL_20261119` + `GRANADA_C3D05_NATIVE_ENERGY_20261120` + `GRANADA_C3D05_PATCH_Q_12636_20261120`**

El script [`scripts/run_c14_numerical_granada.sh`](scripts/run_c14_numerical_granada.sh) es el único flujo vigente del candidato numérico C14. Una vez que decidas ejecutar la prueba diagnóstica corta en tu WSL con Foundation14:

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_c14_numerical_granada.sh --solve
```

**No se solicita este comando como una ronda de QA del desarrollador.** Está disponible para el hito local cuando corresponda. Se ejecutará solo por decisión del investigador, nunca desde GitHub.

En una sola invocación:
1. Relee los originales C14 con SHA/hipótesis y genera la referencia numérica exclusiva.
2. Valida malla topológica ya aceptada **sin rehacer STEP, Gmsh o checkMesh**, copia los `polyMesh` fuera de la fuente y parsea **10 diccionarios** con `foamDictionary`.
3. Calcula el equilibrio energético previo de dos sólidos desde los volúmenes registrados en `log.checkMesh.metal/mold`, sin inventar volúmenes.
4. Con `--solve`, lanza un experimento de **100 pasos de `deltaT=0.001 s`**, audita el log `foamMultiRun` y sus SHA.
5. Si el solver termina verificablemente, `foamPostProcess -region metal/mold` extrae `volAverage(T)` y volumen; calcula `E_r(t)=rho_r Cv_r V_r⟨T_r(t)⟩`, error de energía total relativo al intercambio inicial y pérdida metal/ganancia arena.
6. Después del balance volumétrico, compila un extractor **Foundation14 C++ en la carpeta aislada**: carga **ambas regiones simultáneamente** para respetar `mappedWall`, extrae `q_n=-k snGrad(T)` en **12,636 caras por lado** y empareja centros, áreas y normales sin asumir orden idéntico. Reporta residuos de flujo globales **y** por cara, comparados con variaciones de energía temporal. **Esta parte todavía no está compilada/ejecutada en la WSL real.**
7. Si existe una corrida completa con reporte y SHA concordantes, no vuelve a ejecutar el solver: retoma o compara el postprocesamiento. No sobreescribe entradas, meshes, logs ni reportes incompatibles.

## Reportes esperados, no observados aún

- `T0_PREPARATION_REPORT.json` y `T0_GRANADA_REPORT.json`: integridad de la preparación.
- `T0_CLOSED_ENERGY_REFERENCE.json`: objetivo ideal anterior a una corrida.
- `T0_NUMERICAL_RUN_STATUS.json`: clasificación del log nativo; sin aceptar energía por un mero `End`.
- `T0_NATIVE_ENERGY_HISTORY.json`: datos reales de energía por región **solo después de una corrida válida y su postprocesamiento**.
- `T0_FACE_FLUX_METAL.csv` y `T0_FACE_FLUX_MOLD.csv`: flujo normal nativo en 12,636 caras por región, pendiente de extracción WSL.
- `T0_FACE_FLUX_BILATERAL_DIAGNOSTICS.json`: pares por centro/área/normal, desequilibrios locales/globales y contraste con energía; **no es aceptación física**.

Las tasas energéticas obtenidas de los volúmenes NO son flujos normales directos: el nuevo extractor toma `q()` nativo de OpenFOAM para ello, cuando existan campos de una corrida. **Continúan pendientes la ejecución del extractor C++ en WSL, la evaluación científica real de continuidad cara-cara, pruebas de sensibilidad `dt`/malla/correctores, propiedades físicas y validación QuickCup**. Ni el CI verde ni el equilibrio teórico cierran G3/G4.

## Evidencia, pruebas y documentación

- [Informe Granada C14](../../../docs/granada/C3D05_C14_NUMERICAL_ONE_SHOT_20261119_ES.md).
- [Informe de energía real por campos F14](../../../docs/granada/C3D05_T0_BALANCE_ENERGETICO_NATIVO_20261120_ES.md).
- [Diagnóstico de flujo nativo por 12,636 caras (código pendiente de verificación WSL)](../../../docs/granada/C3D05_T0_FLUJO_INTERFAZ_12636_CARAS_20261120_ES.md), [extractor C++](native_flux/c3d05PatchFlux.C) y [pruebas de mapeo](tests/test_t0_patch_flux.py).
- [Regresiones sin CFD](tests/test_postprocess_native_energy.py) y [workflow CI](../../../.github/workflows/c3d05-t0-granada-static.yml).
- [Configuración fuente oficial OpenFOAM14: `volFieldValue`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/functionObjects/field/fieldValues/volFieldValue/volFieldValue.H).

Para consultar la secuencia de preflights históricos (T0a/T0b, documentos de nueve diccionarios) sin confundirla con instrucciones actuales, existe la [copia de archivo histórico](../../../docs/granada/C3D05_T0_README_HISTORICAL_BEFORE_SINGLE_FLOW_20261120.md). **No deben usarse esas instrucciones antiguas como flujo de trabajo presente**.
