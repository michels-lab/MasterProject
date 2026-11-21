# Operación Granada — Caso B C3D-05: energía real en WSL y recuperación del flujo interfacial

**20 de noviembre de 2026, ejecución local del investigador.** **Etapa 3/7, avance 2/7 = 29 % de hitos técnicos.** No representa avance de tesis, porcentaje de CFD validado ni convergencia de solidificación.

## Evidencia real entregada

El investigador compartió la salida de `run_c14_numerical_granada.sh --solve` en WSL, con OpenFOAM Foundation14 sobre la malla QuickCup **270,788 HEX8 reales (metal 92,200 / molde 178,588, 12,636 caras de contacto por lado)**. El ejecutor:

1. Reconoció `ALREADY_GENERATED_IDENTICAL`, `ALREADY_PREPARED` y `ALREADY_PRESENT_IDENTICAL`, sin generar otra malla ni otro caso.
2. Recuperó el log original de `foamMultiRun` con `REVIEWED_PRESERVED_SOLVER_RUN_COMPLETE_NO_RERUN`. **No repitió los 100 pasos**.
3. Corrió `foamPostProcess/volFieldValue` realmente en metal y molde, con **6 instantes por región** y volúmenes concordantes con el `checkMesh` aceptado.
4. Registró `MAX observed closure discrepancy / initial exchange = 4.320292500161304e-08`, valor de diagnóstico del modelo **C14 archivado, de dos sólidos y propiedades constantes**, **sin aceptación física ni sensibilidad temporal/espacial**.
5. Compiló realmente el extractor `c3d05PatchFlux` con `wmake` en su WSL. El log nativo terminó con `NATIVE_BILATERAL_PATCH_FLUX_EXTRACTED_NOT_VALIDATED`, registrando **12,636 caras por región** en 6 tiempos. Los CSV bilaterales quedaron preservados en una carpeta temporal local, **todavía no publicaron reporte de pares ni manifest final**.

### Temperatura nativa promedio volumétrica (K)

| t (s) | Metal (K) | Molde (K) |
|---:|---:|---:|
| 0.00 | 1500 | 300 |
| 0.02 | 1497.3709 | 306.58804 |
| 0.04 | 1495.2176 | 311.98353 |
| 0.06 | 1493.3664 | 316.62239 |
| 0.08 | 1491.7257 | 320.73368 |
| 0.10 | 1490.2409 | 324.45414 |

**Diferencias medias 0–0.1 s:** metal **−9.7591 K**, molde **+24.45414 K**. Son promedios volumétricos sobre dos regiones sólidas y una referencia numérica C14; no son curvas de termopar ni resultados JMatPro de solidificación.

## Bloqueo observado en la fase 5/6

```text
ValueError: Native face flux times do not match volumetric energy times
```

A partir del código reproducible se localizó el defecto en `scripts/analyze_t0_patch_flux.py`: exigía que los tiempos leídos de los CSV nativos fueran **idénticos como `Decimal`** a los del JSON energético. Pero `native_flux/c3d05PatchFlux.C` guarda `runTime.value()` con `%.17g`, la representación decimal de ida/vuelta de un número `double`; por ejemplo, el mismo tiempo matemático puede serializarse como `0.040000000000000001` (CSV) y `0.04` (JSON). **Este diagnóstico de formato es deducción del código y compatible con la excepción; los bytes originales de los CSV WSL no se han recibido aquí para verificar cada diferencia.**

### Corrección de raíz

- Se añadió emparejamiento **biyectivo, cronológico y con igual cardinalidad** entre tiempos nativos de flujo y energía; tolerancia máxima estricta de representación de `1e-12 s`, además limitada al **10 % del menor intervalo registrado**. No interpola, no rellena tiempos faltantes, ni admite saltos físicos o series distintas.
- Se usa la clave temporal nativa asociada a la fila energética tanto en la integral por intervalos como al comparar `q` metal/molde. El reporte conserva la máxima discrepancia de representación observada y la tolerancia efectivamente usada.
- Regresiones: seis tiempos reales representados como `%.17g`; faltantes, duplicados, cambios de tiempo y proximidad ambigua deben bloquear. La prueba transaccional reproduce también `0.10000000000000001` con Python.
- El ejecutor `run_native_t0_patch_flux.sh` puede **recuperar la ÚNICA carpeta de staging completo previamente extraída** si encuentra ambos CSV nativos, su log y marcador de terminación. **No declara confianza antes de pasar parseo completo, recuento de 12,636 caras por lado, emparejamiento geométrico de centros/áreas/normales, sincronía de tiempos, chequeo SHA y publicación atómica.** Si el staging está incompleto, preserva la evidencia y utiliza una carpeta nueva sin sobrescribir.
- La reentrada del programa mantiene inmutables log `foamMultiRun`, evidencia de auditoría anterior, malla STEP/HEX8, diccionarios y campos; no lanza nuevamente el solver en el caso ya existente.
- No cambia el protocolo científico ni convierte la discrepancia energética baja en un PASS físico.

### Próxima y única ejecución local integrada

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_c14_numerical_granada.sh --solve
```

La ejecución debe reutilizar los datos guardados y terminar fases 5/6–6/6 (diagnóstico bilateral `q`, manifiesto SHA, `T0_GRANADA_EVIDENCE_SUMMARY.json` y marcador `.foam` ParaView) **solo si pasan verificaciones nuevas**. Si hay un desajuste físico/nativo verdadero de caras, se conserva la evidencia y se muestra el error. No repetir STEP, Gmsh, malla ni solver.

## Límites / estado canónico

- **Observado:** solver F14 real sobre geometría aceptada (100 pasos previos), temperaturas metal/molde reales de la corrida numérica, desequilibrio volumétrico cuantificado, `wmake` y extractor bilateral nativos completos.
- **Pendiente:** comparación geométrica de los 12,636 pares, residuos locales y globales de `q`, contraste entre integración de flujo y energía de regiones, manifest SHA y resumen final.
- **No validado:** condiciones termofísicas JMatPro/QuickCup, calor latente, austenita/solidificación, contracción, alimentación, sensibilidad `dt`/malla/no ortogonalidad, comparación con curvas experimentales.
- **Hitos:** G1/G2 cerrados; G3–G7 abiertos. **Etapa 3/7 · 2/7=29 %**, sin incremento por una prueba numérica de referencia.
