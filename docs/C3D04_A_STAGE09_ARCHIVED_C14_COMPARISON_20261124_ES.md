# Caso A — comparación real de referencia C14 2D archivada
24-11-2026. Etapa 09/10; 8/10 hitos operativos (80%). Trabajo exclusivamente OpenFOAM/MasterProject; FoamLens no modificado.

## Evidencia cuantitativa inicial
Se inspeccionaron los archivos versionados de `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/postProcessing/metal`: temperatureProbe/0/T (SHA blob fd158909490dfd7de7a368096cc6017a91f307e9, 10001 valores 0–10 s a dt=0.001), temperatureProbe/0/phaseChangeSource:alpha1 (383995c6ab8153d6f21cf1bb5a0b7ad45e406a9e), metalMeanLiquidFraction/0/volFieldValue.dat (b47a098efabe021aaf8ce556317092f0bc9e4c75), metalSensibleEnthalpy/0/volFieldValue.dat (02cb3d0a03d09bbd67eb99910c273b8d83d9a503), potencias top/contacto y perfiles representativos 0/0.1/5/10 s. La referencia archivada existe aunque no estén los campos volumétricos 2D completos. Resultados A proceden de stdout WSL ya documentado, no de acceso directo a los archivos locales.

| Magnitud a 10s | C14 2D | A |
|---|---:|---:|
| T media K | 1465.159331 (reconstruida desde deltaH, rho=6820, Cp=827, V=1.6e-5) | 1450.709163 |
| Fracción sólida volumétrica | 0.0379407 | 0.102755025 |
| Volumen metal m³ | 1.6e-5 | 4.792144700666e-5 |
| Área contacto m² | 0.0012 | 0.006343771874 |
| Área contacto/volumen m^-1 | 75 | 132.3785543 |
| q contacto W | 277.4151 | 1524.644329 |
| q contacto/volumen W/m³ | 17338443.75 | 31815490.23 |

Diferencia T media −14.450168 K; fracción sólida 2.708306 veces; A/V contacto 1.765047 veces. Geometría distinta: comparación no prueba independencia de malla. Probe 2D central real T(10)=1464.19 K, alpha=0.964815; primer T<1473 K y primera alpha<1 observados a 4.720 s (no extrapolar a 3D). Primer decremento volumétrico 2D guardado a 0.2 s. No comparar un probe local con una media volumétrica.

## Nuevo comparador de archivos existentes
`compare_c14_archived_results.py` usa las series y perfiles originales 2D versionados y los CSV de barridos A previamente generados. No usa solver, compilador ni muestreo nuevo. 101 tiempos, tres centros, 12 diámetros frente a los 3 perfiles 2D, vertical central; interpolación espacial únicamente entre muestras contiguas válidas, sin extrapolar. Direcciones rotadas comparan escalares; componentes globales directas solo 0° y vertical. Reporta cobertura, sesgo, RMSE y máximos de diferencias; curvas de enfriamiento y evolución alpha, flujos normalizados por área/volumen, energía latente nominal por volumen. Datos persistentes en analysis del caso visual. No HTML obligatorio, no cambios en FoamLens. Código publicado; ejecución local pendiente y requiere archivo de barridos A exitoso, no se afirma disponer del contenido local.

```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
P="$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics"
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$P/compare_c14_archived_results.py"
```

Salida: `~/OpenFOAM/C3D04_A_C14_VISUALIZATION_01/analysis/C14_2D_3D_ARCHIVED_COMPARISON_01`. No repetir CFD, no tocar B/FS. Conservación discreta, independencia y QuickCup pendientes.


## Resultado real WSL — comparación completa 24-11-2026

El investigador aportó stdout del comando `compare_c14_archived_results.py` tras fast-forward 0d67f4814..d838d5fab: **ARCHIVED_C14_2D_3D_COMPARISON_READY**, 101 tiempos y 10001 muestras probe 2D; sin repetir CFD ni muestreo. Evidencia primaria: salida de terminal aportada; CSV locales no descargados al repositorio.

| Altura desde base | T2D final K | T3D final K | RMSE temporal K | Sesgo 3D−2D K | Máx abs K | Primer cruce Tliq 2D / 3D s |
|---|---:|---:|---:|---:|---:|---|
| 10 mm | 1456.14 | 1457.06 | 4.05268 | −1.19079 | 14.17 | 3.3–3.4 / 2.7–2.8 |
| 20 mm | 1464.19 | 1466.73 | 6.55483 | −1.50921 | 20.84 | 4.7–4.8 / 3.5–3.6 |
| 30 mm | 1471.45 | 1470.34 | 13.15520 | −9.62208 | 25.02 | 9.3–9.4 / 4.5–4.6 |

El cruce térmico Tliq no es por sí solo inicio metalúrgico demostrado de una fase. Adelantos entre puntos medios de intervalos: 0.6, 1.2, 4.8 s. Fracción líquida central final 2D/3D respectivamente: 0.932608/0.936289; 0.964815/0.974945; 0.993894/0.989398. Cerca del centro las temperaturas finales se aproximan pese a diferencias transitorias y volumétricas importantes.

### Perfiles espaciales finales
| Altura | 0° RMSE / puntos | 45° | 90° | 135° |
|---|---|---|---|---|
| 10 mm | 18.67486 / 66 | 13.26893 / 80 | 18.67690 / 66 | 13.29974 / 80 |
| 20 mm | 14.16025 / 68 | 10.63234 / 80 | 14.16044 / 68 | 10.69139 / 80 |
| 30 mm | 12.14032 / 70 | 9.29798 / 80 | 12.14032 / 70 | 9.26529 / 80 |

Vertical central 80/80, RMSE 3.7499475 K, sesgo −0.883625 K, máximo absoluto 8.44 K. En 0°/90° el soporte común es menor; no comparar RMSE de distintos soportes como si fueran idénticos. La semejanza 0°/90° no demuestra axisimetría. 45°/135° tienen 80/80 puntos en el tramo común solicitado, no prueba cobertura completa del ancho real 3D. Máxima diferencia horizontal reportada 35.19 K a 10 mm, 0°/90°. Conclusión: gradientes espaciales y geometría deben distinguirse de historia central.

### Separación de efecto geométrico y flujo superficial a 10 s
q/A contacto 2D=231179.25 W/m²; A=240337.193624 W/m² (+3.96%). q/A top 91399.925 vs 88419.843 W/m² (−3.26%). q/V contacto 17.33844 vs 31.81549 MW/m³ (1.83497 veces). Identidad q/V=(q/A)(A/V): la razón A/V=1.7650474 explica gran parte de la razón de extracción instantánea por volumen; no prueba causalidad temporal ni validez del modelo. T global y sólido coinciden con comparación inicial. Energía latente nominal volumétrica 59.151524 vs 160.200427 MJ/m³.

**Comparación 2D–3D-A operativamente completada.** Permanecen abiertos conservación discreta del solver (dt=.001 s), independencia espacial/temporal sobre misma geometría y QuickCup. Etapa 09/10, 8/10=80% de hitos; no elevar porcentaje. Siguiente: verificación de sensibilidad con criterio científico y mismo dominio físico, no usar A vs 2D/B como estudio de malla. No repetir comparación exitosa ni CFD base. FoamLens importación independiente aún no observada.
