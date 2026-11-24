# Caso B C3D-05 — C14 completo, 10 s nativos y auditoría posterior sin recalcular

**Evidencia proporcionada por el investigador el 23 de noviembre de 2026** (se debe conservar el reporte y el log reales dentro de su WSL, no sustituirlos por el resumen de este documento).

## Confirmación real: la simulación terminó

La corrida aislada de OpenFOAM Foundation 14 en la malla CAD STEP–Gmsh HEX8 aceptada **270,788 celdas** (metal 92,200; arena 178,588; 12,636 caras recíprocas de interfaz; 1,826 caras severamente no ortogonales) devolvió este resultado de su **ejecutor nativo**:

```json
{
  "status": "C3D05_B_C14_ORIGINAL_FLUID_SOLID_FULL_10S_NATIVE_COMPLETED_NOT_PHYSICALLY_VALIDATED",
  "stage_report": "/home/michel/OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01/C3D05_B_C14_FLUID_SOLID_STAGE_REPORT.json",
  "native_C14_F14_solver_run": true,
  "solidification_or_experiment_accepted": false
}
```

La ejecución original (no el T0 de dos sólidos) activó explícitamente `Selecting solidificationMeltingSource with name phaseChangeSource`, resolvió `metal h, mold e, metal p_rgh` y reportó la terminación de su horizonte **10 s / deltaT 0.001 s** tras verificar el log/ficheros finales. **Se confirma CFD real completado; no se infiere todavía cómo evolucionó `alpha1` ni se certifica balance de calor latente o validación QuickCup/JMatPro**.

### ¡NO ejecutar de nuevo!

El usuario incluyó por accidente una segunda línea con `run_case_b_c14_native.sh --run-full` después de la salida exitosa. El ejecutor **rechaza** una carpeta de destino que existe antes de rematerializar, así que se preserva el CFD original. No borrar, remallar, reiniciar ni volver a ejecutar el modelo para conseguir estadísticas.

## Avance del desarrollo: auditoría de solo lectura integrada para Caso B

Archivos nuevos:

- `cases_3d/C3D_05_step_gmsh_conformal/c14_physics/analyze_existing_case_b_c14.py`
- `cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests/test_existing_case_b_c14.py` (nueve pruebas de fuente)

El analizador reutiliza el lector **real** del Caso A `analyze_existing_c14_3d_results.py`; no inventa datos, otro solver, propiedades, malla o dinámica.

**Bloqueos previos obligatorios:** estado `NATIVE_COMPLETED_NOT_PHYSICALLY_VALIDATED` del reporte C3D05 B; SHA del `controlDict` original, de 10 elementos `polyMesh` y de cinco campos finales; geometría 92,200+178,588 y 12,636 contactos; SHA y contenido completo del log de 10 s con `End`, `fluid/solid/solidificationMeltingSource`, solución `h/e/p_rgh`; todos los estados `0`…`10`. Un fallo o una corrida todavía en curso **bloquea el análisis** y preserva todo.

**Mediciones nativas si pasa:**

1. Serie de `T` metálico y de arena, `p_rgh` y `phaseChangeSource:alpha1` a cada tiempo guardado.
2. Fracción de **celdas** metálicas con `T<Tliq`, `T<Tsol`, `alpha1<0.999`; promedio de `alpha1` **por celdas, no ponderado por volumen**.
3. Primer estado guardado que observa cada condición, con el estado anterior como intervalo; **NO** instante exacto de inicio.
4. Máximo Courant de **todo el log**, residuos de `h,e,p_rgh`, continuidad y derivadas de promedios entre estados guardados.
5. CSV `C3D05_B_C14_REAL_10S_TIME_SERIES.csv`, JSON completo `C3D05_B_C14_REAL_10S_ANALYSIS.json`, manifiesto SHA independiente, en nuevo directorio de análisis; nunca dentro del CFD.

Para ejecutar **solamente el análisis** en la WSL, con `MasterProject` actualizado:

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 -B cases_3d/C3D_05_step_gmsh_conformal/c14_physics/analyze_existing_case_b_c14.py
```

**Importante:** este comando **no corre solver**. Destino: `~/OpenFOAM/C3D05_B_C14_FLUID_SOLID_10S_ANALYSIS_01`; se rehúsa a reemplazar resultados o análisis previo. No se ha observado esta orden ejecutada en WSL ni sus valores reales de `alpha1`.

## Qué falta para aceptar científicamente

La fuente original C14 `Tsol=1423 K`, `Tliq=1473 K`, `L` original y otros parámetros conservan su naturaleza de **referencia heredada**. No son datos JMatPro/QuickCup calibrados para las ocho fundiciones. Ver `alpha1<1` demostraría evolución calculada de la fracción líquida del **modelo C14**, no prueba por sí solo liberación/balance del calor latente físico, recalescencia, ausencia de errores por no ortogonalidad ni convergencia. Por ello permanecen abiertos **G3/G4 físicos, G5 de verificación de cambio de fase/calor latente, G6 contracción y G7 sensibilidad/experimental**.

**Estado canónico del Caso B: etapa 3/7, 2/7=29 % de hitos técnicos completados, aunque el hito de ejecución de CFD nativo C14 ya ocurrió.** No es porcentaje global de maestría/tesis.
