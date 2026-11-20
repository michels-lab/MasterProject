# Operación Granada — C3D-05 Caso B: diagnóstico bilateral del flujo de calor en 12,636 caras

**Fecha:** 20 de noviembre de 2026. **Estado canónico:** etapa **3/7**, hitos **2/7 (29% de hitos técnicos del Caso B; NO porcentaje de tesis, CFD ni validación experimental)**. G1 STEP/CAD y G2 malla/contacto aceptados; **G3–G7 sin cerrar**.

## 1. Problema científico y corrección del método

El bloque anterior [energía regional por campos nativos](C3D05_T0_BALANCE_ENERGETICO_NATIVO_20261120_ES.md) cuantifica `E_r = rho_r Cv_r V_r ⟨T_r⟩` y tasas efectivas de transferencia, pero esas tasas **no prueban continuidad de flujo a través de cada cara** del contacto metal–arena. Una suma energética global puede esconder errores locales de signos, pares equivocados, normales o flujos compensados.

Se consultó el código fuente **OpenFOAM Foundation 14** y se confirmó que:

- [`solid/isotropic/isotropic.C`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/ThermophysicalTransportModels/solid/isotropic/isotropic.C) implementa la densidad de flujo conductivo en caras `q() = -interpolate(alpha*kappa)*snGrad(T)`, y en el T0 isotrópico `alpha=1`. La dimensión es W/m².
- [`solid.C`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/modules/solid/solid.C) usa el mismo modelo `solidThermophysicalTransportModel` para el término difusivo `divq`.
- [`wallHeatFlux.C`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/functionObjects/field/wallHeatFlux/wallHeatFlux.C) **no es la elección segura**: filtra parches a `wallPolyPatch` y depende de tener `thermophysicalTransportModel` previamente registrado. Los parches del caso están definidos como `mappedWall`; no marcar datos ausentes como un flujo de pared calculado.
- Los parches térmicos `metal_to_mold` y `mold_to_metal` requieren tener **ambas mallas y thermos cargadas simultáneamente al mismo instante**, para permitir que `coupledTemperature` acceda a su región vecina. Por eso el extractor es **un único programa nativo de dos regiones**, no dos procesos independientes.

## 2. Extracción directa y emparejamiento recíproco

Se añadieron:
- [`native_flux/c3d05PatchFlux.C`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/native_flux/c3d05PatchFlux.C), con los archivos `Make/` para Foundation14. Lee ambos `polyMesh`, construye en cada tiempo ambos `solidThermo` y ambos `solidThermophysicalTransportModel`, obtiene **el `q()` nativo por cara**, su normal exterior, centro, área e índice. **No resuelve ninguna ecuación ni modifica la malla**.
- [`scripts/run_native_t0_patch_flux.sh`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_native_t0_patch_flux.sh): copia el código del extractor a la carpeta **aislada** del caso, lo compila con `wmake` de Foundation14 usando `FOAM_USER_APPBIN` local, registra hash de binario y logs, y ejecuta la extracción simultánea de metal y arena en **una sola llamada**. La copia en GitHub y la malla aceptada permanecen sin alteración. Registros anteriores no se sobrescriben.
- [`scripts/analyze_t0_patch_flux.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/analyze_t0_patch_flux.py): lee los dos CSV de flujo nativo, exige 12,636 caras por lado para cada instante, empareja por centros en 3D bajo tolerancia geométrica explícita, exige correspondencia biyectiva, áreas congruentes y normales opuestas; no equipara índices de caras de metal y molde.

El diagnóstico por intervalo calcula:

```text
Q_metal_out(t) = Σ_faces q_metal,out(f,t) * A_f        [W]
Q_mold_out(t)  = Σ_faces q_mold,out(f,t)  * A_f        [W]
Q_net(t)       = Q_metal_out(t) + Q_mold_out(t)      [W]
L_face(t)      = Σ_pairs |q_metal,out*A_m + q_mold,out*A_d| [W]
R_total(t)     = |Q_net(t)| / (Σ|Q_m| + Σ|Q_d|)/2
R_local(t)     = L_face(t) / (Σ|Q_m| + Σ|Q_d|)/2
```

El resultado conserva **residuo global y suma de desajustes locales**, para evitar aceptar dos distribuciones de flujo que se cancelan solo en el balance total. Registra el mayor desajuste de un par individual y una estimación de integral temporal trapezoidal del flujo saliente frente a `ΔE_r` observado de `volAverage(T)`.

La tolerancia de centros `1e-7 m`, de área relativa `0.001` y de oposición de normales (producto punto ≤ `-0.995`) son **controles de identidad geométrica**, **no criterios de aceptación física**. Se rechazan tiempos duplicados/no coincidentes, caras repetidas o faltantes, CSV sin cabecera, NaN, normales incoherentes, fuentes SHA divergentes o log de solver no terminado.

## 3. Integración Granada de un solo comando

La guía autorizada sigue en [README T0](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/README.md) y la operación completa es:

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_c14_numerical_granada.sh --solve
```

Dentro de esa única invocación el flujo **cuando se ejecute localmente** reúne lectura de C14 archivado con SHA, preparación de caso aislado, verificación de 10 diccionarios, referencia energética ideal, intento `foamMultiRun` de 100 pasos, lectura de temperaturas regionales nativas y, por último, compilación/extracción/diagnóstico de `q()` de **las dos caras de cada contacto**. Si la ejecución anterior ya terminó y su log mantiene SHA, no vuelve a llamar al solver. Se conservan evidencia e informes anteriores.

Evidencias previstas **solo después de ejecución WSL real**:
- `T0_NATIVE_FACE_FLUX/metal.csv` y `T0_NATIVE_FACE_FLUX/mold.csv` — archivos completos por cara y tiempo.
- `T0_NATIVE_FACE_FLUX/log.c3d05PatchFlux` y `log.wmake.C3D05_T0_flux` (en la carpeta del caso) — extracción y compilación, respectivamente.
- `T0_NATIVE_FACE_FLUX/bilateral_diagnostics.json` y `T0_NATIVE_FACE_FLUX/manifest.sha256` — comparación de caras, energía y SHA de todos los artefactos. **La carpeta se publica mediante una única operación de renombrado solo si ambos CSV y el análisis están completos**; en caso contrario se conserva la carpeta temporal con la evidencia del error, sin declarar resultados.
- `T0_NATIVE_ENERGY_HISTORY.json` — balance de energía volumétrico ya implementado.

## 4. Estado honesto de la validación

El **programa C++ nativo todavía NO está compilado ni ejecutado en la WSL del investigador**. La CI de GitHub puede revisar código, sintaxis Bash, parser Python y usar CSV sintéticos; no tiene los campos CFD verdaderos ni demuestra comportamiento de las condiciones `coupledTemperature`. Si `wmake` o el acceso al vecino falla, el ejecutor detendrá el paquete **sin declarar flujo correcto ni borrar los registros originales**. No afirmamos que exista flujo bilateral real o resultados experimentales.

Incluso con CSV reales, las tasas de flujo y la energía deben someterse a análisis de sensibilidad en tiempo/malla/no ortogonalidad, definición de tolerancias de aceptación científicamente defendibles y comparación con termopares/curvas QuickCup. La referencia C14 (`Cp≈Cv`, `k=Cp*mu/Pr`) sigue siendo **solo un banco de prueba numérico**, no datos experimentales de hierro hipoeutéctico.

**Caso B permanece etapa 3/7, 2/7 hitos = 29% técnico**. Entrega de código con ensayos sintéticos, **no validación CFD ni cierre G3/G4**.

## 5. Mejoras posteriores de integridad y compilación (20-11-2026)

Se añadió [una CI de compilación **real** OpenFOAM Foundation14](../../.github/workflows/c3d05-foundation14-native-build.yml) en Ubuntu 24.04, además de la CI sintética existente. El compilador `wmake` encontró incompatibilidades de API no visibles en pruebas Python (se reemplazó el encabezado heredado `fvCFD.H` y el acceso `mesh.boundaryMesh()` por las interfaces reales Foundation14). Esta CI también debe comprobar dependencias dinámicas con `ldd` y arranque del binario con `-help`. **No documentar compilación verificada hasta obtener una ejecución PASS de esta CI**. El binario seguirá compilándose por separado en la WSL del investigador durante una ejecución numérica, no se distribuirá un binario fabricado por GitHub como si fuera resultado experimental.

El ejecutor [`run_native_t0_patch_flux.sh`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_native_t0_patch_flux.sh) se hizo transaccional: todos los CSV, log y reporte se crean primero en una ubicación temporal `.T0_NATIVE_FACE_FLUX_STAGING.*` de la copia aislada y se publican en `T0_NATIVE_FACE_FLUX/` con un renombrado único, solo después de pasar el análisis bilateral. Al reentrar, verifica `manifest.sha256` y coincidencia de entradas/solver, reutilizando sin volver a calcular o sobrescribir. Las [regresiones de transacción](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_native_flux_atomic_handoff.py) generan datos **sintéticos** de 12,636 pares por lado y prueban publicación completa, fallos parciales y reutilización; no ejecutan CFD.
