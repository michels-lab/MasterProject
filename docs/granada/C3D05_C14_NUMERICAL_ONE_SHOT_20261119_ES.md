# Caso B C3D-05 — Operación Granada: referencia numérica C14 de extremo a extremo

**Fecha:** 19-11-2026. **ETAPA 3/7 T0 | AVANCE 2/7 hitos técnicos = 29 %**. No es porcentaje de tesis ni validación física. Este bloque entrega código/QA para la siguiente prueba térmica, no datos CFD ya corridos.

## Problema que resuelve

El modelo T0 tenía la malla aceptada (270,788 HEX8 y contacto recíproco, con 1,826 caras >70°) y `fvSolution` rastreable a C14, pero `T0_INPUTS.json` seguía `null`. Esto obligaba a preparar propiedades y ejecutar controles separados para cada intento. La operación conserva **intacta** la plantilla física nula y crea **otra** referencia, explícitamente de **validación NUMÉRICA de funcionamiento**, sin fingir entradas JMatPro.

## 1. Datos heredados, cálculo derivado y límites

Archivo fuente: `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/`. Se releen **cinco archivos originales versionados**, con SHA-256 individual:

- `constant/metal/materials/castIron`: `rho=6820 kg/m³`, `Cp=827 J/(kg K)`, `mu=0.0055 Pa s`, `Pr=0.14`, `molWeight=56`. La conducción equivalente heredada `k=Cp*mu/Pr ≈ 32.4893 W/(m K)` es derivada matemáticamente de C14, **no una medición**. **`Cv=Cp` es una hipótesis numérica explícita** para la región metal tratada como sólido a densidad constante, NO una equivalencia termodinámica demostrada.
- `constant/mold/materials/silica`: `rho=1500 kg/m³`, `Cv=700 J/(kg K)`, `k=2 W/(m K)`, `molWeight=28` del modelo C14. No equivalen a propiedades certificadas de la arena QuickCup real.
- `0/metal/T` y `0/mold/T`: temperaturas **numéricas iniciales** `1500 K` y `300 K`, no valores medidos del experimento.
- `system/controlDict`: se hereda **`deltaT=0.001 s`**, pero el alcance del diagnóstico aislado se limita deliberadamente a **100 pasos (0.1 s)** y salidas cada 20 pasos. No reproduce la corrida completa C14 de 10 s ni su física fluida.

Las condiciones externas de T0 siguen **adiabáticas** y la interfaz metal–arena de contacto idealizado; esta prueba no incluye aire, pérdidas al ambiente, calor latente, convección, recalescencia, contracción ni alimentación. `fvSolution` conserva la adaptación previamente aprobada desde C14: global PIMPLE 3/2/1, región sólida PCG+DIC, energía 2 de intención C14 sin eficacia demostrada.

## 2. Paquete funcional Granada

**Archivos incorporados:**

- [`c14_numerical_reference.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/c14_numerical_reference.py): lectura de fuentes C14, reglas dimensionales, hashes, hipótesis, bloqueo de valores ambiguos, salida no destructiva/idempotente. Se cotejan otra vez **todos los números** y los hashes antes de materializar T0; modificar cualquier valor o dejar una procedencia falsa provoca rechazo.
- [`run_c14_numerical_granada.sh`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_c14_numerical_granada.sh): **una sola orden WSL** para fuente C14 → copia de malla aceptada → 10 diccionarios parseados → objetivo energético → (solo con `--solve`) intento nativo corto `foamMultiRun`; no vuelve a ejecutar Gmsh/checkMesh ni sobreescribe referencias.
- [`t0_energy_reference.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/t0_energy_reference.py): lee los **volúmenes reales preservados** de `log.checkMesh.metal/mold` (con `Mesh OK`) y calcula `C_i = rho_i Cv_i V_i`, `E_0 = Σ C_i T_i(0)` y `T_eq = E_0 / Σ C_i` como **expectativa matemática del sistema cerrado**, con SHA-256 de entradas y logs. No presupone un valor de equilibrio obtenido por el solver ni una tolerancia universal inventada.
- [`audit_t0_numerical_run.py`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/audit_t0_numerical_run.py): interpreta la **salida real** del solver, comprueba código de salida, avance temporal, tiempo final, finalización y patrones FATAL/NaN; guarda un reporte por intento, sin confundir `run completed` con `energy closed`.
- [Regresiones C14](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_c14_numerical_reference.py) y [regresiones energéticas/forenses](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_t0_energy_forensics.py); ejecutadas mediante el workflow integrado C3D-05 con `bash -n`, sin ejecutar CFD en CI.

**Único comando disponible para el futuro hito local** (este documento no pide al investigador hacer pruebas por separado):
```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_c14_numerical_granada.sh --solve
```

El modo por defecto `--prepare` genera y comprueba los ficheros sin resolver; `--solve` reúne toda la preparación anterior y lanza únicamente el diagnóstico numérico de 100 pasos en **`~/OpenFOAM/C3D05_T0_C14_SHK_01`**, distinto de `C3D05_T0_CONDUCTION_01` del caso físico. La salida y reporte previos no se sobreescriben. Si falta Foundation14 o cambia el SHA del caso aceptado se bloquea antes de ejecutar. La carpeta original CAD/malla sigue protegida.

## 3. Qué falta y qué NO se afirma

Al cierre de esta publicación **no se ha ejecutado la orden en WSL del investigador**. No hay prueba de que `foamMultiRun` haya terminado 100 pasos con la malla real, ni de que conserve energía o tenga flujo interfacial continuo. El auditor de logs solo comprueba la integridad básica de la ejecución; **energía e interfaz requerirán evidencia de campos/postprocesamiento**. Se mantienen abiertas las incertidumbres de estabilidad numérica asociadas con las 1,826 caras severamente no ortogonales.

La fuente física experimental continúa pendiente: densidad, `Cv/Cp`, `k`, condiciones térmicas iniciales y externas, resistencia térmica de contacto, datos JMatPro y curvas QuickCup. Por tanto **G3 del caso físico y G4 siguen abiertos**; el avance sigue en **2/7 = 29% de hitos técnicos**.

**Límites de Operación Granada:** no inventar propiedades, no ejecutar CI como si fuera una corrida OpenFOAM, no remallar lo aceptado y no someter al investigador a cadenas de comandos de depuración. El hito local tiene un solo punto de entrada y los bloqueos aparecen juntos en su salida.
