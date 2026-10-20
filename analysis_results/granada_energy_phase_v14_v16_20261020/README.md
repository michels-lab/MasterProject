# GRANADA GRANDE — evidencia termoenergética B/C V14–V16

Fuente: [CI run #39392339903](https://github.com/michels-lab/QuickCup-Solidification/actions/runs/39392339903), SHA 058c9ceb1bf9fb0f2c57e3ba4b0375a534153b01, 2026-10-20. Artefacto original quickcup-energy-phase-evidence (ID 12249634193). Nueve tests sintéticos y análisis de seis casos versionados terminaron SUCCESS; **no hubo nuevas simulaciones OpenFOAM**. El artefacto JSON conserva las rutas y los SHA-256 de los 36 archivos originales. Estos valores solo prueban un cribado de consistencia numérica reducido.

| Caso | αL medio final | ΔH sensible (J) | Energía frontera integrada (J) | Potencia latente integrada (J) | Residual condicionado (J) |
|---|---:|---:|---:|---:|---:|
| B14 | 0.9606902 | -2543.0 | 4069.488 | 984.527 | +541.961 |
| B15 | 0.9609920 | -2548.1 | 4070.468 | 977.627 | +544.741 |
| B16 | 0.9606523 | -2542.3 | 4069.536 | 985.404 | +541.832 |
| C14 | 0.9620593 | -3144.1 | 4055.580 | 945.299 | -33.819 |
| C15 | 0.9626339 | -3157.2 | 4056.198 | 938.495 | -39.497 |
| C16 | 0.9620001 | -3142.7 | 4055.673 | 948.124 | -35.151 |

**Cobertura:** 101 tiempos compartidos entre 0 y 10 s por caso, sin alertas del parser/partición energéticas de este cribado. Las cifras completas sin redondear están en case_metrics.csv.

## Pares padre-hijo: diferencias controladas

| Par | Δfracción líquida media final | Δenergía frontera integrada (J) | Δresidual condicionado (J) |
|---|---:|---:|---:|
| B15−B14 | +0.0003018 | +0.98047 | +2.78041 |
| C15−C14 | +0.0005746 | +0.61858 | −5.67764 |
| B16−B14 | −0.0000379 | +0.04786 | −0.12912 |
| C16−C14 | −0.0000592 | +0.09310 | −1.33179 |

## Interpretación científica restringida

La familia B exhibe un residual condicionado alrededor de +542 a +545 J; C presenta de -34 a -39 J. **No permite concluir que C conserve energía o masa mejor que B**, porque la expresión ΔH_sensible + ∫energyFlux_boundary dt − ∫latentHeatRateVol dV dt es solo una hipótesis de contabilidad parcial. Faltan verificación del signo y formulación del término latente, fuente adicional, cierres del molde, orientación y áreas de normales e interfaces, y transporte másico. El antecedente de continuidad acumulada B ≈ -0.031 tampoco queda explicado por esta tabla.

La media volumétrica αL no identifica un frente dendrítico ni prueba recalescencia. La sonda térmica aislada tampoco. Los DAT no certifican sus unidades; se tomaron de la guía técnica del proyecto y han de comprobarse contra el solver/fvModels. El componente energyFlux ya suma advective+heatFlux; no se debe contar dos veces.

Las puertas experimentales G1 y de propiedades J0 siguen abiertas. Un CI exitoso no equivale a validación de física, resultados de Ubuntu, condiciones de frontera ni comparación experimental.

## Reproducir y reanudar

El programa analysis_tools/granada_energy_phase_evidence.py genera JSON de trazabilidad SHA256, CSV y summary.md en un directorio vacío fuera de los casos; la acción CI correspondiente también produce un artefacto descargable. Este README conserva los datos derivados para permitir reevaluación sin depender de la retención del artefacto. No se alteraron el solver, las carpetas CFD, los STL ni los casos históricos.

Siguiente bloque grande independiente: inspección bilateral de interfaz metal/molde con procedencia de superficies, signos y flujos por cara, después balance integral completo, sin interferir con C3D PR #18/#19 ni termómetros/Courant PR #20. Las bitácoras científicas ES/EN deben reconciliarse cuando cese la edición concurrente de esos PR, sin adjudicar estados RUN_VERIFIED/ANALYSIS_VERIFIED por este solo cribado.
