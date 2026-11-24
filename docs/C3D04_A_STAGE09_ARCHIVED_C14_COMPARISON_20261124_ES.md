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
