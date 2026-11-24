# Caso B — primer cálculo de fracción líquida ponderada por volumen usando 92,200 HEX8 nativos

**Fecha de bitácora: 24 de noviembre de 2026.** **Estado: cálculo nuevo IMPLEMENTADO en GitHub, aún NO ejecutado en la WSL real.** Los valores numéricos de fracción ponderada por volumen no se conocen todavía y NO deben inventarse. El CFD original y sus postprocesamientos son inmutables.

## 1. Evidencia REAL del usuario: cronología ejecutada correctamente

El usuario actualizó `MasterProject` y ejecutó la secuencia de 9 pruebas y la cronología de `summarize_existing_case_b_c14_phase_timeline.py`. **Las nueve pruebas pasaron** (`Ran 9 tests in 0.021s, OK`), y la cronología derivada del CSV/JSON nativo ya generado devolvió:

```json
{
  "status": "C3D05_B_C14_ARCHIVED_PHASE_TIMELINE_NUMERICAL_ONLY",
  "out": "/home/michel/OpenFOAM/C3D05_B_C14_PHASE_TIMELINE_01",
  "saved_states": 101,
  "first_alpha1_below_0_999": {
    "first_saved_s": 0.3,
    "previous_saved_s": 0.2,
    "exact_onset_unknown": true
  },
  "first_any_cell_fully_solid_by_model": {
    "first_saved_s": 5.1,
    "previous_saved_s": 5.0,
    "exact_onset_unknown": true
  },
  "mean_solid_complement_unweighted": 0.1575794367375163,
  "latent_heat_balance_verified": false,
  "physical_validation": false,
  "NO_CFD_RUN": true
}
```

**Interpretación:** la primera celda que cumple `alpha1<0.999` aparece entre dos salidas guardadas 0.2–0.3 s; la primera que alcanza `alpha1=0` aparece entre 5.0–5.1 s. El complemento sólido medio **15.75794367375163 %** es media aritmética por **92,200 celdas**, **no** proporción de volumen solidificado. La cronología C14 conserva umbrales originales `Tsol=1423 K` y `Tliq=1473 K`, NO validados para todas las composiciones QuickCup. La interpretación temporal es de muestreo de 0.1s, no de instante continuo exacto.

## 2. Desarrollo siguiente publicado: usar volúmenes de la malla real

Archivo implementado:
`cases_3d/C3D_05_step_gmsh_conformal/c14_physics/volume_weighted_existing_case_b_c14.py`

Su objetivo NO es producir más gráficas del mismo promedio, sino estimar:

```text
alpha1_V(t) = sum_i [V_i * alpha1_i(t)] / sum_i V_i
solid_complement_V(t) = 1 - alpha1_V(t)
```

donde `V_i` corresponde a **cada celda metálica del `polyMesh` real**, no al tamaño promedio ni a una celda sintética. Como el C14 original mantiene densidad metálica `rhoConst`, la ponderación por masa del **propio modelo C14** coincide con la volumétrica; no equivale a validar contracción ni cambio real de densidad con temperatura.

Para obtener `V_i` **sin alterar ni ejecutar OpenFOAM**:

1. Verifica el reporte nativo original de 10s `C3D05_B_C14_FLUID_SOLID_STAGE_REPORT.json`, `End/10s`, firma SHA del log, modelo original C14 y cinco archivos finales. Verifica también SHA del CSV/JSON de los 101 estados.
2. Abre `constant/metal/polyMesh/points`, `faces`, `owner`, `neighbour` ASCII **originales** con firma SHA frente al informe de materialización; exige exactamente **92,200** celdas de metal y caras **QUAD4** de la malla HEX8. No genera ni modifica malla.
3. Por cada cara cuadrilateral orientada de propietario hacia vecino, triangula `(v0,v1,v2)` y `(v0,v2,v3)` y acumula volumen de pirámides tetraédricas `(1/6) det(a,b,c)` sumando al `owner` y restando al `neighbour` para caras internas. Todas las celdas deben dar volumen positivo y finito.
4. Exige que la suma por volumen de celdas coincida con el volumen metálico **nativo previamente observado** `4.79754032229e-05 m³`, dentro de **0.5%**. La tolerancia es un **gate de integridad**, no prueba de exactitud de geometría en celdas no planas. Si falla, se detiene, no sustituye por valor medio, no altera datos originales.
5. Relee **101 campos reales `phaseChangeSource:alpha1`** mediante el lector OpenFOAM ASCII archivado y comprueba que el promedio aritmético de cada salida sigue coincidiendo con el CSV original. Luego calcula media ponderada, volumen con `alpha1<0.999` y volumen con `alpha1=0`. No interpreta una derivada de `alpha1` como potencia latente.

Genera solo una carpeta NUEVA de evidencia:
`~/OpenFOAM/C3D05_B_C14_VOLUME_WEIGHTED_PHASE_01`, con CSV de 101 tiempos, JSON de resumen y manifiesto SHA separado. Se rechaza cualquier destino previo. Los archivos `C3D05_B_C14_FLUID_SOLID_FULL_10S_01`, `C3D05_B_C14_FLUID_SOLID_10S_ANALYSIS_01`, `C3D05_B_C14_PHASE_TIMELINE_01` permanecen intactos.

**Pruebas unitarias añadidas (8):** geometría de dos HEX8 contiguos de volumen conocido (1 unidad cúbica por celda), inversión de orientación de cara, caras no cuadrangulares, encabezado ASCII inválido, diferencia entre promedio ponderado/no ponderado, fracciones fuera de rango, SHA ausente y protección del archivo original. Este ensayo geométrico **no se presenta como CFD de la pieza real**. La ejecución de estos ocho tests y el cálculo real en WSL están pendientes de observación.

## 3. Orden para el siguiente procesamiento WSL sin CFD

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 -B -m unittest discover -s cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests -p "test_volume_weighted_existing_case_b_c14.py" -v && python3 -B cases_3d/C3D_05_step_gmsh_conformal/c14_physics/volume_weighted_existing_case_b_c14.py
```

Este comando solo lee geometría y estados existentes; requiere CPU/memoria para leer las caras y ~9.3 millones de valores de `alpha1` entre 101 salidas, pero **no reinicia foamMultiRun**.

## 4. Límites y etapa canónica

Un `alpha1_V` calculado sobre la malla real es una mejora **espacial-numérica** respecto al promedio por celdas, pero **todavía no equivale a validación experimental de la solidificación**. Quedan por resolver: contraste del volumen integrado por celda con geometría nativa detallada si hay caras no planas, conservación integrada sensible + latente, flujo por interfaz y exterior, comparación QuickCup, propiedades `rho(T),Cp(T),k(T)` por fundición, sensibilidad dt/malla especialmente por las **1,826 caras severamente no ortogonales**, recalescencia y modelo real de contracción/alimentación.

**Estado:** Caso B etapa **3/7**, **2/7=29% hitos técnicos cerrados**. CFD C14 de 10s real, 101 estados y cronología completados; **no** G3/G4 físicos, **no** cierre G5 energía latente/experimental, **no** G6 contracción ni G7 sensibilidad/experimento.
