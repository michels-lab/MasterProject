# Caso B C3D-05 — ¡flujo conductivo Foundation14 nativo COMPLETO! 101 estados y comparación energética nueva

**24 de noviembre de 2026.** Bitácora de evidencia observada en la terminal real del investigador. **La extracción de flujos C14 original está confirmada**; la comparación cruzada de flujos con almacenamiento energético **está implementada en código pero aún NO ejecutada en WSL**. No inflar hitos de conservación o validación científica.

## 1. Resultado WSL CONFIRMADO: CFD original y extracción solo lectura

Secuencia observada: `git pull --ff-only`, **14/14 pruebas** `test_existing_case_b_c14_native_flux.py` aprobadas (Ran 14 tests in 1.928s, OK), `--preflight` aprobó malla/física/reporte/log SHA y **101 estados originales**, y `--extract` compiló el C++ específico Foundation14 de **hierro fluido y molde sólido**, generando y auditando q conductiva a **t=0,0.1,...,10s**. No se ejecutó `foamMultiRun` ni se alteraron los campos CFD.

Salida auténtica:

```text
/home/michel/OpenFOAM/C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01
```

Estado final del ejecutor:

```text
C3D05_B_C14_REAL_FLUID_SOLID_NATIVE_Q_EXTRACTED_ANALYZED_NOT_ENERGY_CLOSURE
```

Cuatro parches por tiempo, **101×4=404 registros integrados**; mapa espacial final de las cuatro superficies, con 12,636 caras conformales por cada lado de la interfaz.

## 2. Resultados de potencia conductiva a t=10 s — reales de WSL

| Patch, normal SALIENTE de la región correspondiente | Potencia q saliente [W] |
| --- | ---: |
| `metal/metal_to_mold` | **+1581.5646631744044** |
| `mold/mold_to_metal` | **−1581.5383267429747** |
| Suma firmada de ambas caras internas | **+0.026336431429626828** |
| `metal/metalTop` | **+117.06292503343666** |
| `mold/moldOuterUnclassified` | **+34.38628817469787** |
| Exteriores, suma saliente | **+151.44921320813452** |

Desajuste de interfaz relativo instantáneo = **8.326137818963252×10⁻⁶**, es decir **0.0008326138%** con denominador `abs(q_metal)+abs(q_mold)`. Esa cifra representa muy buena **concordancia global de potencia conductiva instantánea**, no residuo físico de conservación.

A `t=10s`: **12,636 / 12,636** caras apareadas por centros redondeados a 10⁻⁸ m, **12,636 normales opuestas** (`dot<−0.99`) y **12,636 áreas coincidentes**. La suma de las **diferencias absolutas locales por cara** es `1.8703362871771045 W`, mayor que el desajuste firmado global de `0.0263364 W`; no borrar este dato mediante cancelación entre caras.

El extractor original usa `fluidThermoThermophysicalTransportModel::q()` sobre el metal C14 (laminar `unityLewisFourier`) y `solidThermophysicalTransportModel::q()` sobre la arena (`isotropic`). Tras el error F14 `interpolate(kappa)`, la reconstrucción funciona por **un caso sombra 101-times** con `interpolate(kappa) harmonic;` añadido **solo en la COPIA del sistema del posprocesamiento**, coherente con la intención armónica `interpolate((kappa|Cv)) harmonic;` original. **No afirmar que la línea añadida estuvo presente durante el CFD original**: es una regla explícita del posprocesamiento para evaluar `q()`.

## 3. Inventarios previos de referencia C14, 10 s: no mezclarlos con q instantánea

| Cambio de inventario relativo a t0 | Energía [J] |
| --- | ---: |
| Energía sensible del molde | +20323.651945808975 |
| Energía sensible del metal | −13576.397936155232 |
| Cambio del contenido latente líquido de referencia | −8100.198210984614 |
| **Suma de referencia** | **−1352.9442013308708** |

**Los 151.449 W de potencia exterior a t=10s no son 151.449 J de energía, ni equivalen automáticamente a 1514.49 J transferidos durante 10 s.** Es imprescindible integrar `q(t)`; y aun después, un trapecio a intervalo de guardado 0.1s no es la integral de los pasos CFD reales 0.001s.

La fuente `solidificationMeltingSource` del solver no está integrada en tiempo, y no se verificaron todos los términos advectivos, de trabajo, presión, convección/radiación exterior. Tampoco se han cerrado sensibilidad de malla/dt, JMatPro/QuickCup ni contracción. **No interpretar `−1352.944 J` como fuga ni el desajuste instantáneo `0.026336 W` como error de conservación global.**

## 4. Siguiente avance creado y registrado (código fuente, NO ejecutado en WSL todavía)

Script de unión con SHA y tiempo real:

```text
cases_3d/C3D_05_step_gmsh_conformal/c14_physics/compare_existing_case_b_c14_native_q_and_storage.py
```

12 pruebas de integridad, temporalidad, signos, procedencia y no sobrescritura en:

```text
cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests/test_existing_case_b_c14_q_storage_join.py
```

Lee exclusivamente **los dos directorios de resultados anteriores**: q Foundation14 nativa (101 tiempos) e inventario metal/molde C14 (101 tiempos). Se exige coincidencia de SHA del reporte original y log CFD para demostrar **la misma simulación C14**; verifica SHA de ambos CSV e informes. Se integran con trapecios de los **101 tiempos guardados** los cuatro q_out, la suma de ambas caras de interfaz y la suma de los exteriores. Se guarda CSV por tiempo y JSON con la comparación de almacenamiento de referencia e integrales de q, con una columna final etiquetada **`NOT_ENERGY_RESIDUAL`**.

**Comando WSL, SIN ejecutar CFD ni otro extractor nativo:**

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && \
python3 -B -m unittest discover \
  -s cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests \
  -p "test_existing_case_b_c14_q_storage_join.py" -v && \
python3 -B cases_3d/C3D_05_step_gmsh_conformal/c14_physics/compare_existing_case_b_c14_native_q_and_storage.py
```

Salida nueva aislada esperada:

```text
~/OpenFOAM/C3D05_B_C14_Q_VS_REFERENCE_STORAGE_01
```

Se rechaza sobrescribir cualquier salida anterior. El programa **NO** ejecuta `foamMultiRun`, `wmake` ni la extracción `q()` otra vez. Los números de integración temporal **NO se conocen hasta que se ejecute** el script sobre los CSV reales en la WSL. Las 12 pruebas se añadieron, pero aún no hay confirmación WSL de su paso.

## 5. Siguiente verdadero hito científico

Con la historia de q real y el inventario combinado cotejados, falta **estimar fuentes y transportes reales**: `fvModels` de calor latente y sus términos energéticos según discretización original, entalpía transportada por el metal líquido, trabajo/presión, condiciones `externalTemperature` y capas/contacto, términos radiativos/convectivos, y comparar con el balance del solver a pasos 0.001s. **No promover G3-G7 hasta verificar cierre y sensibilidad/experimentación.**

**Estado del Caso B:** etapa 3/7, **2/7 hitos técnicos (29%)** aceptados. Extracción conductiva F14 101/101 y geometría de interfaz completadas; conservación físico-numérica completa pendiente.
