# Caso B C3D-05 — Granada numérica C14 terminada sobre 270,788 HEX8 reales (WSL)

**Fecha de evidencia proporcionada por el investigador:** 20 de noviembre de 2026, Saltillo.  
**Caso:** `C3D_05_step_gmsh_conformal` / B.  
**Etapa de proyecto:** **3/7, 2/7 = 29 % de hitos técnicos**; esto **NO** es porcentaje de tesis, de exactitud numérica ni de validación experimental.  
**Alcance:** **T0 numérico de conducción en dos regiones sólidas**, con parámetros archivados C14; **NO** es solidificación ni enfriamiento experimental QuickCup con propiedades JMatPro.

## Resultado observado de la última ejecución WSL

La salida de terminal compartida por el investigador muestra que el comando integrado `run_c14_numerical_granada.sh --solve` **completó sus seis fases** sobre la geometría original aceptada, **sin reconstruir la malla ni volver a invocar** `foamMultiRun` o el extractor nativo `q()`:

1. Parámetros: `ALREADY_GENERATED_IDENTICAL`.
2. Caso 3D: `ALREADY_PREPARED`; malla original preservada.
3. Referencia de energía: `ALREADY_PRESENT_IDENTICAL`, temperatura ideal de equilibrio adiabático **1157.70809 K** (**solo meta analítica**, NO temperatura observada a 0.1 s).
3b. Auditoría: `RUN_REPORT_EXISTS_IDENTICAL REVIEWED_PRESERVED_SOLVER_RUN_COMPLETE_NO_RERUN`; informe anterior recuperado y protegido mediante SHA.
4. `ALREADY_REPORTED_IDENTICAL samples 6`: temperaturas de seis tiempos y cierre energético calculados anteriormente mediante `foamPostProcess` nativo metal/molde.
5. `REUSE_COMPLETE_NATIVE_PATCH_EXTRACTION_STAGE_UNVERIFIED` seguido de `NATIVE_FACE_Q_DIAGNOSTICS_WRITTEN_NO_VALIDATION`: los CSV ya extraídos se verificaron y se **emparejaron geométricamente 12,636 caras recíprocas por lado**, con publicación `NATIVE_BILATERAL_FACE_Q_PUBLISHED_NO_PHYSICAL_VALIDATION`.
6. `CASE_B_NUMERICAL_EVIDENCE_SUMMARY_GENERATED_NO_SCIENTIFIC_ACCEPTANCE`: expediente íntegro de entradas/log/energía/q SHA publicado. Marcador ParaView `C3D05_T0_REAL_ACCEPTED_HEX8.foam` creado.

**Malla:** **270,788 celdas HEX8**, metal **92,200**, arena **178,588**; 12,636 caras de contacto por lado; volúmenes de malla verificados anteriormente: metal **4.79754032229e-05 m³**, molde **1.02843380345e-04 m³**. **1,826 caras >70° de no ortogonalidad**, advertencia de estabilidad que aún requiere sensibilidad.

## Resultados de temperatura y balance

| Tiempo (s) | Metal, T promedio volumétrico (K) | Molde, T promedio volumétrico (K) |
|---:|---:|---:|
| 0.00 | 1500 | 300 |
| 0.02 | 1497.3709 | 306.58804 |
| 0.04 | 1495.2176 | 311.98353 |
| 0.06 | 1493.3664 | 316.62239 |
| 0.08 | 1491.7257 | 320.73368 |
| 0.10 | 1490.2409 | 324.45414 |

El **máximo error energético relativo respecto a la escala de intercambio inicial** reportado por el postprocesador fue **4.320292500161304×10⁻⁸**. Este resultado corresponde a `max |E(t)-E(0)| / Q_ref`; **no es error porcentual respecto a la energía total absoluta** y no debe confundirse con la variación térmica de las regiones.

## Transferencia térmica por caras acopladas

- `Paired 12636 real native patch faces per side`; emparejamiento basado en **centro de cara, área y oposición de normales**, NO en asumir índices coincidentes.
- **Máxima discrepancia relativa local agregada por pares**, normalizada con el flujo bruto de intercambio: **1.8239733799046786×10⁻¹⁶** (salida literal `peak local relative face-q discrepancy` del finalizador). El valor es esencialmente precisión de máquina para la **consistencia bilateral de flujo en las BC acopladas de este T0**.
- El dato **NO** certifica exactitud de `q` frente a mediciones, flujo de fusión real, independencia temporal/espacial, ni ausencia de dispersión por caras severamente no ortogonales.
- No se proporcionó aún en el chat el **contenido del JSON `bilateral_diagnostics.json` o del `T0_GRANADA_EVIDENCE_SUMMARY.json`**, por lo que se reportan únicamente valores que el comando imprimió; perfiles por cara, totales W y tasas energéticas no se inventan.

## Expediente local generado (fuera del repositorio)

Raíz de caso: `/home/michel/OpenFOAM/C3D05_T0_C14_SHK_01`.

- `log.foamMultiRun.C14_NUMERICAL_T0`: log original inmutable del solver.
- `T0_NUMERICAL_RUN_STATUS.json` y `T0_NUMERICAL_RUN_STATUS_REVIEWED.json`: clasificación previa y recuperación con SHA.
- `T0_NATIVE_ENERGY_HISTORY.json`: temperaturas regionales, energía y cierre numérico.
- `T0_NATIVE_FACE_FLUX/metal.csv`, `mold.csv`, `bilateral_diagnostics.json`, `manifest.sha256`: muestras de caras y trazabilidad íntegra, publicadas transaccionalmente.
- `T0_GRANADA_EVIDENCE_SUMMARY.json`: resumen consolidado verificado por hash según el código del ejecutor; **contenido completo no inspeccionado desde este chat**.
- `C3D05_T0_REAL_ACCEPTED_HEX8.foam`: marcador de lectura de campos nativos en ParaView.

**Cadena de confianza:** la evidencia procede del **terminal WSL proporcionado por el investigador**, no de la ejecución directa del asistente ni de acceso remoto a sus archivos. El generador del expediente reportó éxito, pero el material SHA original no se ha copiado aquí ni adjuntado al repositorio; esto limita cualquier afirmación de verificación independiente.

## Estado y siguiente hito científico

**Completado:** diagnóstico numérico T0 en malla real, solver auditado, temperatura, conservación diagnóstica, extracción bilateral y emparejamiento de caras, expediente SHA y marcador de visualización.

**Sin cerrar:** G3 (`T0 materializado con propiedades físicas documentadas`) y G4 (`T0 con acoplamiento y balance físico revisados`); **G5 solidificación/calor latente, G6 contracción/alimentación, G7 sensibilidad y experimentos**. G1 y G2 siguen cerrados.

**Prioridad inmediata:** analizar campos de `T` en ParaView y revisar el expediente físico completo, especialmente magnitudes y distribución espacial de `q` y efectos de no ortogonalidad, **sin volver a correr el diagnóstico C14**. Para cerrar G3, incorporar parámetros documentados y trazables de metal/molde y curvas térmicas reales (JMatPro/QuickCup); después modelar intercambio con la física adecuada, sensibilidad de `Δt`/malla y validación experimental. Ni el error energético `4.32e-8` ni la discrepancia bilateral `1.82e-16` prueban esos objetivos por sí solos.
