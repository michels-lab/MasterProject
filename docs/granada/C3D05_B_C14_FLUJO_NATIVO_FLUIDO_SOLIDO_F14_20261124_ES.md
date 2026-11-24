## Actualización WSL — 24 nov 2026: compilación PASÓ, ejecución detuvo FOAM FATAL IO

**Evidencia real observada:** `git pull --ff-only` completó la actualización; **8/8 pruebas de auditoría del extractor PASS** (`Ran 8 tests in 1.178s, OK`); `--preflight` confirmó C14 original 10 s, 101 estados, metal-fluido/molde-sólido, hash SHA de la malla/reporte/log y ninguna reejecución CFD.

**Avance técnico significativo:** el cambio del encabezado C++ a `#include "linear.H"` desbloqueó `wmake`: el programa nativo fue compilado y alcanzó la fase de ejecución, pero terminó allí con `FOAM FATAL IO ERROR` y `rc=1`. **El terminal mostró únicamente la cabecera** porque la función `invoke()` imprimía solo líneas con la cadena `FOAM FATAL` y ocultaba las siguientes líneas que explican el archivo/diccionario o keyword causante. La causa específica es **DESCONOCIDA** y no se debe deducir a partir de la cabecera.

**Registro de error conservado (NO BORRAR):**

```text
/home/michel/OpenFOAM/.C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01.ATTEMPT_1lg4hihv/log.C3D05_B_C14_NATIVE_FLUX
```

**Correctivo publicado en GitHub:** `run_existing_case_b_c14_native_flux.py` ahora tiene `--diagnose-attempt`, lectura restringida y estrictamente **solo lectura** del intento anterior. Extrae el contexto de `FOAM FATAL IO ERROR` de las líneas relevantes. Además `invoke()` mostrará el tramo final íntegro de futuros errores sin ocultar sus causas. Se añadieron 2 pruebas sintéticas a las 8 previas: **10 pruebas en el código, aún no ejecutadas en WSL** después de este cambio.

**Siguiente comando único. No ejecutar extractor nuevo, wmake ni foamMultiRun hasta leer la causa:**

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 -B cases_3d/C3D_05_step_gmsh_conformal/c14_physics/run_existing_case_b_c14_native_flux.py --diagnose-attempt "$HOME/OpenFOAM/.C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01.ATTEMPT_1lg4hihv"
```

Alternativa sin `git pull` ni cambios de código, para mostrar **inmediatamente** el error desde la bitácora original:

```bash
sed -n '/FOAM FATAL IO ERROR/,+35p' "$HOME/OpenFOAM/.C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01.ATTEMPT_1lg4hihv/log.C3D05_B_C14_NATIVE_FLUX"
```

No hay `q(t)` autenticado, no hay informe térmico de las cuatro fronteras, no se puede inferir error de conservación por el inventario referencial -1352.9442013308708 J, y el Caso B sigue **3/7, 2/7=29% hitos aceptados**, G3–G7 físicos sin cerrar.

---

# Caso B C3D-05 — extractor térmico NATIVO C14 Foundation14: fluido + sólido, sin repetir CFD

**24 de noviembre de 2026.** **NUEVO CÓDIGO IMPLEMENTADO EN MASTERPROJECT, TODAVÍA NO COMPILADO NI EJECUTADO EN WSL REAL.** El anterior CFD F14, sus 101 estados y sus múltiples postprocesamientos **sí** se completaron en WSL. Evitar confundir estas dos afirmaciones.

## 1. Evidencia real previa que se conserva

- `foamMultiRun` original sobre el Caso B aceptado CAD STEP/Gmsh/HEX8 real, 270,788 celdas, **metal fluido 92,200** y **molde sólido 178,588**, 10 s y dt=0.001 s, fase `solidificationMeltingSource`, **101 estados nativos guardados**; no reejecutar.
- Interfaces `metal_to_mold` y `mold_to_metal`: **12,636 caras por lado**, `mappedWall`. Otras dos superficies: `metalTop` y `moldOuterUnclassified`.
- Primer cambio `alpha1 < .999` guardado en **0.3s** (anterior 0.2s), primera celda totalmente sólida `alpha1=0` a **5.1s** (anterior 5.0s); `alpha1` volumen ponderado a 10s **0.8917029860767621**, complemento sólido numérico **10.8297013923%**.
- Inventario de referencia a 10s por campos reales: `Delta E_mold,sensible=+20323.651945808975 J`, `Delta E_metal,sensible=-13576.397936155232 J`, `Delta E_metal,liquid-latent-content=-8100.198210984614 J`; suma combinada **-1352.9442013308708 J**, **NO error de conservación ni calor perdido medido**. El término `fvModel`, transporte de energía y flujos de frontera siguen pendientes.

## 2. Implementación nueva: transporte REAL fluido/sólido

A diferencia del extractor previo `t0_conduction/native_flux/c3d05PatchFlux.C` (dos sólidos), este avance **no fuerza al hierro a ser un sólido**.

- C++: `cases_3d/C3D_05_step_gmsh_conformal/c14_physics/native_flux/c3d05C14FluidSolidFlux.C`.
- `wmake`: `.../c14_physics/native_flux/Make/{files,options}`.
- Ejecutor aislado y protección de evidencia: `.../c14_physics/run_existing_case_b_c14_native_flux.py`, modos `--preflight` y `--extract`.
- Auditoría CSV/SHA y pares de caras: `.../c14_physics/analyze_existing_case_b_c14_native_flux.py`.
- Regresiones: `.../c14_physics/tests/test_existing_case_b_c14_native_flux.py` (**8 pruebas nuevas, ejecución real todavía no confirmada**).
- CI específico de compilación real F14 (NO solver): `.github/workflows/c3d05-b-c14-native-fluid-solid-q.yml`; **el resultado de la ejecución CI no está confirmado**.

A cada estado guardado `0, 0.1, ..., 10s`, el código intenta reconstruir los objetos originales:

1. Malla metal + molde presentes simultáneamente, 92,200/178,588 celdas; identidades originales de los cuatro parches y 12,636 caras de interfaz bilateral.
2. `fluidThermo::New(metal)` para `heRhoThermo/hConst/sensibleEnthalpy`; `solidThermo::New(mold)` para `heSolidThermo/eConst/sensibleInternalEnergy`.
3. `compressible::momentumTransportModel::New(...)` y `fluidThermoThermophysicalTransportModel::New(momentum(),thermo())` para `q` del **metal fluido**; `solidThermophysicalTransportModel::New(...)` para `q` de la **arena sólida**. Se seleccionan los modelos del runtime Foundation14; la construcción debe comprobarse en WSL/CI para demostrar compatibilidad efectiva.
4. `q_out_W/m2` se multiplica por la superficie nativa orientada para generar potencia `q_out_W` por cara o por parche. **Positivo significa saliente de esa región**, no necesariamente q de metal hacia arena ni energía perdida del dominio total.
5. Se extraen **101 × 4 = 404 registros integrados de q(t)** (metal-contacto, metalTop, molde-contacto, molde-exterior), y un registro de `q`, área, centro y normal **por cara** de las cuatro superficies a **t=10s**.
6. Audita que los registros sean finitos, completos, sin duplicados; compara suma por cara con q integrado; mide pares geométricos de contacto y oposición de normales; cuantifica desajuste de q bilateral pero **no impone un umbral físico inventado**.
7. Calcula trapecios de `q` sobre los **101 estados guardados cada 0.1s**. Esto es una **aproximación temporal**, NO la integral nativa de los **10,000 pasos solver de 0.001s**.

**Salida nueva aislada** (no dentro de la carpeta CFD):

`~/OpenFOAM/C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01`

Incluye `C3D05_B_C14_NATIVE_Q_101X4_PATCHES.csv`, `C3D05_B_C14_NATIVE_Q_T10_ALL_FACES.csv`, `C3D05_B_C14_NATIVE_Q_101_TIMES.csv`, informe JSON, manifiesto SHA y logs. Compila fuente desde copia temporal aislada, no altera `system`, `constant` ni `0..10` del CFD. Si `wmake`/el extractor falla, conserva un directorio **.ATTEMPT** separado con logs y evita publicar un reporte parcial.

## 3. Orden única para WSL — pruebas, preflight y extracción sin CFD

```bash
cd ~/OpenFOAM/MasterProject && \
git pull --ff-only && \
python3 -B -m unittest discover \
  -s cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests \
  -p "test_existing_case_b_c14_native_flux.py" -v && \
python3 -B cases_3d/C3D_05_step_gmsh_conformal/c14_physics/run_existing_case_b_c14_native_flux.py --preflight && \
bash -lc 'source /opt/openfoam14/etc/bashrc && python3 -B cases_3d/C3D_05_step_gmsh_conformal/c14_physics/run_existing_case_b_c14_native_flux.py --extract'
```

**Nunca ejecutar `run_case_b_c14_native.sh --run-full` de nuevo.** Es normal que el primer intento de compilar este código nuevo encuentre incompatibilidades de API F14: el CI y la WSL deben confirmar `wmake` y los cuatro parches. No reportar q ni progreso físico hasta ver la salida nativa real. Los registros del intento se preservan para corrección específica.

## 4. Lo que aun NO prueba

Aunque las 404 potencias de conducción lleguen a estar comprobadas, **no** demuestran por sí solas conservación de energía: quedan posibles componentes térmicos convectivos/radiativos, transporte entálpico advección y trabajo, fuente `solidificationMeltingSource` temporal y diferencias entre integración 0.1s guardada vs 0.001s resuelta. El `q()` del modelo fluido C14, que se verifica en los archivos `OpenFOAM-14`, es **conductivo**, no el flujo total de energía. Además faltan sensibilidad de 1,826 caras severamente no ortogonales, estudio dt/malla, `rho(T),Cp(T),k(T)` por JMatPro, comparación QuickCup, recalescencia validada y contracción.

**Estado: Caso B etapa 3/7, 2/7 hitos técnicos cerrados (29%).** El paso actual es **código del extractor publicado, WSL y CI sin verificación final**.
