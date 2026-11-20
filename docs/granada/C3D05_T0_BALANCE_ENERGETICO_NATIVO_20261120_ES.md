# Operación Granada C3D-05/B — balance energético **observado** de T0 desde campos nativos OpenFOAM 14

**Fecha: 20-11-2026. Caso B etapa 3/7; 2/7 hitos cerrados = 29 % de hitos técnicos, no de tesis ni de CFD.** Estado actual: código y controles de lectura preparados; **no** se ha ejecutado la simulación térmica 3D en la WSL del investigador y no existen datos termofísicos JMatPro aquí que permitan cerrar el T0 experimental.

## Alcance y trazabilidad

El paquete anterior [Granada C14 numérico de un solo comando](C3D05_C14_NUMERICAL_ONE_SHOT_20261119_ES.md) ya calculaba una **referencia ideal de equilibrio** usando los volúmenes almacenados en los registros nativos \`log.checkMesh.metal/mold\`. Eso NO verifica que OpenFOAM realmente conserve energía; faltaba extraer temperaturas reales de las dos regiones sin falsificar datos.

Se añadió [\`scripts/postprocess_t0_energy.py\`](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/postprocess_t0_energy.py), basado en la API real Foundation 14:
- [\`foamPostProcess\`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/applications/utilities/postProcessing/foamPostProcess/foamPostProcess.C) con \`-region metal\`, \`-region mold\` y \`-dict system/T0_energy_<region>\`. **No lanza** el solver ni ejecuta \`checkMesh\`.
- [\`volFieldValue\`](https://github.com/OpenFOAM/OpenFOAM-14/blob/master/src/functionObjects/field/fieldValues/volFieldValue/volFieldValue.H) para \`cellZone all\`, \`operation volAverage\`, \`writeVolume true\`, \`fields (T)\`, con función independiente por región.

Se preservan registros nativos y SHA256 del archivo de entrada, reporte del solver y archivos \`volFieldValue.dat\`. Se rehúsa reutilizar una corrida cuyo log SHA o entradas no coincidan con el reporte inicial verificado. Datos con tiempos no coincidentes, sin encabezado, duplicados, NaN, volumen incompatible o archivo no existente **se clasifican como bloqueo**, no como resultados positivos. La copia de malla, STEP, C14 original y el registro físico \`T0_INPUTS.json\` siguen intactos.

## Ecuaciones auditables (modelo T0 constante, dos sólidos, sin pérdidas externas)

Para cada región \`r\`, a partir de los volúmenes **reales aceptados** \`V_r\` de checkMesh y \`⟨T_r(t)⟩_V\` producido por el postprocesador de OpenFOAM:

\`\`\`text
C_r          = rho_r * Cv_r * V_r                              [J/K]
E_r(t)       = C_r * <T_r(t)>_V                               [J]
E_total(t)   = E_metal(t) + E_mold(t)                         [J]
E0           = Σ(C_r*T_r(0))
ΔE(t)        = E_total(t) - E0                               [J]
T_eq_ideal   = E0 / (C_metal + C_mold)                      [K]
Q_ref        = C_metal * |T_metal(0) - T_eq_ideal|           [J]
epsilon_E(t) = |ΔE(t)|/Q_ref                                [dimensionless]
q_metal,eff  = -ΔE_metal/Δt                                [W]
q_mold,eff   = +ΔE_mold/Δt                                 [W]
r_Q          = (ΔE_metal + ΔE_mold)/Δt                      [W]
\`\`\`

Se informa \`epsilon_E\` para todos los tiempos de escritura y su máximo; el uso de \`Q_ref\` evita ocultar errores con un denominador de energía absoluta excesivamente grande. **No se fija un umbral de aceptación de energía sin estudio de sensibilidad de \`dt\`, malla, correctores no ortogonales y precisión de salida**. El control de concordancia de volúmenes (0.5 % relativo) solo detecta un caso equivocado/malla distinta, NO es un criterio de convergencia energética.

La tasa \`q_metal,eff/q_mold,eff\` es el cambio de energía **volumétrico** entre muestras. **No es el flujo de calor normal calculado en las 12,636 caras de interfaz**, por lo tanto no sustituye la comprobación de continuidad de flujo parche por parche ni detecta distribuciones locales anómalas. No se afirma recalescencia, liberación de calor latente ni una curva de enfriamiento validada.

## Un solo punto de entrada y recuperación sin relanzar el solver

La única operación local del candidato NUMÉRICO (si se decide ejecutarlo) sigue siendo:

\`\`\`bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/scripts/run_c14_numerical_granada.sh --solve
\`\`\`

El propio script prepara el modelo C14 de cinco fuentes con SHA, crea una copia separada de la malla aceptada, valida los diez diccionarios, genera la energía inicial teórica, ejecuta el diagnóstico de 100 pasos **únicamente con \`--solve\`**, audita su log, procesa los campos T regionales con \`foamPostProcess\` y produce:

- \`T0_CLOSED_ENERGY_REFERENCE.json\` — referencia previa sin CFD.
- \`T0_NUMERICAL_RUN_STATUS.json\` — estado observado del solver y hash del log.
- \`T0_NATIVE_ENERGY_HISTORY.json\` — serie real de energía y diferencia de intercambio, si existe una corrida nativa válida.

Si el reporte de la corrida existente demuestra que terminó y coincide con las entradas y el log SHA, la misma opción \`--solve\` **no vuelve a correr \`foamMultiRun\`**, sino que completa o verifica el postprocesamiento pendiente. Se preservan salidas ya creadas; discrepancias bloquean sin borrar ni sobreescribir datos.

## Regresiones y criterio de verdad

[Pruebas estáticas y sintéticas](../../cases_3d/C3D_05_step_gmsh_conformal/t0_conduction/tests/test_postprocess_native_energy.py) cubren contrato de \`volFieldValue\`, lectura de encabezados Foundation, tiempos coincidentes, cambio de energía exacto/corrupto, volumen discordante, datos NaN, preservación de reportes y verificación de SHA del run log. Se ejecutan junto con todas las regresiones de T0 en [CI](../../.github/workflows/c3d05-t0-granada-static.yml). La CI no tiene ni necesita los bytes de la malla local; NO prueba una corrida F14.

**Estado científico actual, sin inflarlo:** G1 y G2 PASS; G3/G4 ABIERTOS. El cálculo numérico **no se ha ejecutado en la laptop**. La próxima evidencia válida sería el trío de reportes de la corrida real, después el análisis térmico espacial, continuidad de flujo interfacial directa, y finalmente parámetros experimentales/JMatPro y curvas reales QuickCup. Avance: **2/7 = 29 % de hitos técnicos del Caso B**, no de la tesis.
