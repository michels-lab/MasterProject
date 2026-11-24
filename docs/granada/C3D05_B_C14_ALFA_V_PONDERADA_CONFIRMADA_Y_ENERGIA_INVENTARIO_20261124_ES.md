# Caso B C3D-05 — fracción líquida ponderada por volumen CONFIRMADA; inventario sensible/latente-equivalente PREPARADO

**24 de noviembre de 2026.** Se documentan los valores REALMENTE OBTENIDOS en la terminal WSL del investigador. No se confunden con validación física, cierre energético ni resultados aún no calculados.

## 1. Evidencia WSL nativa confirmada (sin nueva CFD)

El usuario ejecutó `git pull --ff-only`, las ocho pruebas de geometría (`Ran 8 tests in 0.012s — OK`) y `volume_weighted_existing_case_b_c14.py`. El proceso leyó las **101 carpetas de tiempos** de CFD C14 nativo completado, comprobó `polyMesh` y cerró en:

```json
{
  "status": "C3D05_B_C14_NATIVE_HEX8_VOLUME_WEIGHTED_ALPHA1_NOT_PHYSICALLY_VALIDATED",
  "output": "/home/michel/OpenFOAM/C3D05_B_C14_VOLUME_WEIGHTED_PHASE_01",
  "geometry": {
    "source": "REAL_ORIGINAL_POLYMESH_QUAD_FACE_ORIENTED_TRIANGLE_PYRAMID_DIVERGENCE",
    "nCells": 92200,
    "nFaces": 283389,
    "nInternalFaces": 269811,
    "nPoints": 106529,
    "cell_volume_min_m3": 6.174996903303957e-11,
    "cell_volume_max_m3": 4.3881731333931845e-09,
    "total_volume_m3": 4.797539547720032e-05,
    "native_checkMesh_total_volume_m3": 4.79754032229e-05,
    "relative_discrepancy_vs_checkMesh": 1.6145147646629957e-07,
    "nonplanar_quad_triangulation_difference_possible": true
  },
  "saved_states": 101,
  "first_alpha1_change": {"first_saved_s": 0.3, "previous_saved_s": 0.2},
  "first_fully_solid_cell": {"first_saved_s": 5.1, "previous_saved_s": 5.0},
  "final_liquid_volume_weighted": 0.8917029860767621,
  "final_solid_complement_volume_weighted": 0.10829701392323787,
  "physical_or_energy_balance_accepted": false,
  "NO_CFD_REEXECUTION": true
}
```

**Interpretación defendible:** `alpha1_V = sum(Vi*alpha1_i)/sum(Vi)`, donde `Vi` procede de la **geometría real HEX8**, es **0.8917029861** de líquido medio ponderado a `t=10s`. El complemento sólido volumétrico del modelo es **0.1082970139 (10.8297%)**. El promedio simple por celdas antes informado, **0.1575794367 (15.7579%)**, es **4.9282423 puntos porcentuales mayor**, y NO debe llamarse fracción física de volumen solidificado.

El error relativo en el **volumen total** respecto a `checkMesh` es **1.6145×10^-7**, aproximadamente **0.00001615%**. Esto confirma una excelente concordancia global de geometría, **no verifica por sí sola cada volumen individual frente al algoritmo nativo OpenFOAM**. Se conserva explícitamente el posible error de triangulación de cuadriláteros no planos.

**Tiempo de cambio de fase modelado observado:** primer `alpha1<0.999` en el registro guardado de 0.3 s (anterior 0.2 s), primera celda `alpha1=0` en 5.1 s (anterior 5.0 s), eventos acotados por muestreo 0.1 s, no instantes exactos. No equivale a constatación experimental de nucleación/recalescencia.

## 2. Siguiente avance de código preparado: inventarios de energía sensible y latente-equivalente

Nuevo módulo:

`cases_3d/C3D_05_step_gmsh_conformal/c14_physics/quantify_existing_case_b_c14_energy_inventory.py`

Con **9 pruebas de regresión** en:

`cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests/test_existing_case_b_c14_energy_inventory.py`.

Este script nuevo **no ha sido ejecutado aún en la WSL** y, por tanto, **no hay resultado de almacenamiento de energía nativo observado todavía**.

A partir de cada uno de los 101 campos reales `T_i(t)`, `alpha1_i(t)` y `V_i`, usando exclusivamente los parámetros originales C14 respaldados por el contrato `rho=6820 kg/m³`, `Cp=827 J/(kg K)`, `L=228600 J/kg`, estima:

```text
Q_sensible_C14(t) = rho*Cp * sum_i (V_i*[T_i(t)-T_i(0)])                  [J]
Q_latente_equiv_C14(t) = rho*L * sum_i (V_i*[alpha_i(0)-alpha_i(t)])     [J]
```

- `Q_sensible_C14` es un **cambio de inventario sensible respecto a la temperatura real inicial** del modelo, no un balance integrado de `h` con todos los flujos.
- `Q_latente_equiv_C14` es un **equivalente potencial del cambio de fracción calculada** a parámetros constantes del C14. **NO** demuestra energía latente efectivamente liberada ni iguala la integral `fvModels` del solver.
- No se suman estas magnitudes para afirmar conservación. La fase original contiene `relax`, `alpha1e`, `Tliq/Tsol` C14 y sus propias ecuaciones; la fuente energética real de OpenFOAM requiere auditoría independiente.
- Valida SHA del reporte original de 10 s, log, CSV/JSON del primer postrun y CSV/JSON del análisis volumétrico. Relee cada estado real, comprueba promedios `T`/`alpha1` contra el primer análisis y `alpha1_V` contra la ponderación ya certificada. Rechaza salida previa y no escribe en ninguna carpeta de CFD.

**Comando integrado para WSL, PENDIENTE de confirmación:**

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && python3 -B -m unittest discover -s cases_3d/C3D_05_step_gmsh_conformal/c14_physics/tests -p "test_existing_case_b_c14_energy_inventory.py" -v && python3 -B cases_3d/C3D_05_step_gmsh_conformal/c14_physics/quantify_existing_case_b_c14_energy_inventory.py
```

El resultado, solo si pasa, se depositará en una carpeta NUEVA:
`~/OpenFOAM/C3D05_B_C14_SENSIBLE_LATENT_EQUIVALENT_01`, con CSV 101 tiempos, JSON de resumen y manifiesto SHA. No corre `foamMultiRun`, no recalcula el modelo, no altera malla, y no sobrescribe salidas previas.

## 3. Lo pendiente antes de promover hitos científicos

Para reclamar **balance de energía** hay que integrar apropiadamente los términos de la ecuación real de `h`, el intercambio en `mappedWall`, flujo exterior, energía del molde, transporte advectivo y tratamiento temporal de calor latente, con verificación dimensional y temporal. El presente inventario es solo una referencia. Las propiedades `Cp/rho/k(T)` de JMatPro para las ocho fundiciones y las curvas experimentales QuickCup, la recalescencia, la no ortogonalidad (1,826 caras severamente no ortogonales), sensibilidad de `dt` y malla, contracción y alimentación permanecen pendientes.

**Estatus canónico: Caso B en etapa 3/7, 2/7 hitos técnicos aceptados (29%).** La terminación del CFD C14 y observación numérica de `alpha1` no son equivalentes a cierre de G3/G4/G5 físicos.
