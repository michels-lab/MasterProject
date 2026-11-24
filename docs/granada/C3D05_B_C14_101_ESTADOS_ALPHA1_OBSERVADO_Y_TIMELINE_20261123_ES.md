# Caso B C3D-05 — solidificación numérica C14 observada en 101 estados de CFD real

**Fecha: 23 de noviembre de 2026.** Resultados tomados literalmente de la salida de WSL del investigador después de la ejecución **ya completada** `C3D05_B_C14_ORIGINAL_FLUID_SOLID_FULL_10S_NATIVE_COMPLETED_NOT_PHYSICALLY_VALIDATED`. La observación procede del análisis nativo **solo lectura**, ejecutado en `/home/michel/OpenFOAM/C3D05_B_C14_FLUID_SOLID_10S_ANALYSIS_01`; no se reemplaza el informe real, CSV o SHA con valores calculados externamente.

## 1. Evidencia reportada por la WSL real

```json
{
  "status": "CASE_B_C14_REAL_10S_POSTRUN_NATIVE_FIELDS_AUDITED_NOT_PHYSICALLY_VALIDATED",
  "native_10s_complete": true,
  "saved_snapshots": 101,
  "first_C14_Tliq_crossing": {
    "first_observed_saved_time_s": 0.3,
    "previous_saved_time_s": 0.2,
    "cannot_infer_exact_onset_within_saved_interval": true
  },
  "first_alpha1_below_0_999": {
    "first_observed_saved_time_s": 0.3,
    "previous_saved_time_s": 0.2,
    "cannot_infer_exact_onset_within_saved_interval": true
  },
  "any_saved_alpha1_change": true,
  "final_alpha1_mean_cell_based": 0.8424205632624837,
  "min_saved_alpha1": 0.0,
  "max_Courant_all_logged_steps": 0.267133,
  "physical_energy_or_experiment_accepted": false
}
```

La CFD real es la del **Caso B** basada en CAD STEP→Gmsh→HEX8 aceptada: 270,788 celdas nativas, repartidas 92,200 hierro y 178,588 arena; interfase `mappedWall` con 12,636 caras recíprocas por lado; **1,826 caras severamente no ortogonales**. `OpenFOAM Foundation14`, metal `fluid`, molde `solid`, `solidificationMeltingSource` C14; `10 s`, `dt=0.001 s`; 101 carpetas de estados archivados a intervalos 0.1 s.

## 2. Interpretación técnicamente defendible

- **Modelo de cambio de fase realmente activado y evolucionado:** el fuente `solidificationMeltingSource` fue seleccionado durante la corrida nativa; el campo `phaseChangeSource:alpha1` muestra al menos una celda con fracción líquida **menor que 0.999** en el estado guardado a **0.3 s**.
- **Ventana de primer cambio observado:** en el estado guardado **0.2 s** no se cumplió el criterio de detección, pero en el de **0.3 s** sí. El evento se localiza entre esos dos muestreos, **NO a un instante exacto de 0.3 s**. Se observó también el primer cruce guardado de `T<Tliq` original C14 = **1473 K** a 0.3 s (estado anterior 0.2 s). No se extrapola a las ocho composiciones reales.
- **Fracción líquida media FINAL:** `0.8424205632624837` como **promedio aritmético de las 92,200 celdas metálicas**, NO ponderado por volumen/masa.
- **Complemento sólido medio FINAL por celdas:** `1−0.8424205632624837=0.1575794367375163`, equivalente a **15.75794367375163% de promedio de complemento sólido**, **no** fracción de volumen sólido del hierro real. En una HEX8 de tamaño variable, la media por celdas no es un promedio físico espacial.
- **Fracción mínima:** `min(alpha1)=0.0` en **al menos uno de los 101 estados**. El modelo predijo al menos una celda totalmente sólida en algún estado. La salida condensada **NO identifica todavía el primer tiempo ni garantiza que esa celda permanezca sólida al final**.
- **Courant máximo en el log completo:** `0.267133`; esto es una comprobación de la magnitud máxima informada por el solver, **no** prueba de convergencia de dt/malla, estabilidad de todas las ecuaciones ni conservación de energía.

## 3. Desarrollo posterior: cronología derivada solo de datos archivados

**Publicado en el repositorio, pendiente de ejecución sobre WSL real:**

- `cases_3d/C3D_05_step_gmsh_conformal/c14_physics/summarize_existing_case_b_c14_phase_timeline.py`
- `cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests/test_existing_case_b_c14_phase_timeline.py` (**9 pruebas de origen/contrato/negativos**, además de los 9 tests del analizador original).

La nueva cronología **no abre el CFD**, sino únicamente la carpeta de análisis que ya fue certificada por el investigador. Requiere **SHA-256 de CSV y JSON coincidentes con el manifiesto nativo**, `native_CFD_solved_full_10s=true`, material fuente original C14 `metal 92200/mold 178588`, 101 estados y consistencia del primer cruce de `alpha1` con el informe previo. Rechaza datos modificados, fuente errónea, intervalos incompletos y sobrescritura de informes anteriores.

Genera en una carpeta **nueva e independiente** `~/OpenFOAM/C3D05_B_C14_PHASE_TIMELINE_01`:

1. JSON de eventos: primer estado guardado con `alpha1 < 0.999`, primer `alpha1=0`, umbrales de complemento sólido medio por celdas 5/10/20%, temperaturas por debajo de las referencias líquidus/sólidus C14; todos con intervalo anterior.
2. CSV de **100 intervalos entre 101 estados**: velocidades promedio de enfriamiento del metal y calentamiento de arena, descenso firmado de `alpha1` medio, número de celdas con `alpha1<0.999`, fracción sólida media **por celdas**.
3. JSON con SHA de los archivos analizados, para procedencia reproducible.

Para ejecutarlo **sin CFD ni ninguna escritura sobre la corrida o el primer análisis**:

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 -B cases_3d/C3D_05_step_gmsh_conformal/c14_physics/summarize_existing_case_b_c14_phase_timeline.py
```

Esta orden **no ha sido ejecutada aún en la WSL** y ningún resultado de su cronología puede presentarse como observado hasta recibir evidencia nativa.

## 4. Qué evidencia científica sigue abierta

**No se puede afirmar todavía** conservación con energía latente, potencia térmica transferida, evolución de entalpía absoluta del metal, balance con el exterior, sensibilidad a malla/dt (en especial 1,826 caras de alta no ortogonalidad), propiedades `rho(T), Cp(T), k(T)` de cada composición QuickCup mediante JMatPro, recalescencia, contracción/alimentación ni validación experimental.

El siguiente salto físico relevante después de la cronología es construir **promedios ponderados por volumen** y **balance integrado de energía (sensible + latente e intercambio con arena/exterior)**, con fuente y discretización verificables. Ello requiere datos espaciales del caso y/o posprocesamiento nativo, pero **no una nueva simulación**.

**Estado de hitos canónicos, sin inflación:** Caso B etapa **3/7**, **2/7=29%** hitos técnicos cerrados. G3/G4 físicos y G5 de verificación numérico-energética siguen abiertos; G6 contracción y G7 convergencia/experimento también. **Se confirma evolución numérica de fase, no validación física**.
