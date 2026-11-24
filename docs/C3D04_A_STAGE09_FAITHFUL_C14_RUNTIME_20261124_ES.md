# Caso A — réplica fiel C14 con diagnósticos nativos
24-11-2026. Etapa 09/10, 8/10 hitos operativos (80%). Prioridad expresa del investigador: copiar fielmente C14 en 3D, incluyendo diagnóstico en ejecución, antes de sensibilidad numérica.

## Entrega integral
`cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics/run_c14_a_faithful_runtime.py` prepara y ejecuta una **nueva corrida autorizada** desde t=0 sobre V4/T02 aceptada (8960 celdas metal, 12352 arena). Conserva el CFD previo, su postproceso, barridos y comparación. Ninguna modificación de los casos B o contracción ni FoamLens.

- `system/controlDict` idéntico byte a byte tanto a C14 original como a la corrida base; 10 s, dt=.001 s, writeInterval=100. Las propiedades y los diccionarios físicos y numéricos se cotejan con la corrida base; se mantiene su pRefCell y metal cellZone. Los hashes de malla deben coincidir.
- `researchDiagnostics` original íntegro, sin cambiar ecuaciones ni frecuencias. `functions` y `lineProfiles` conservan objetos, campos y frecuencias; únicamente coordenadas 3D y una inclusión adicional. El probe central se ubica a 20 mm desde la base, en centro XZ real.
- Perfiles originales tres horizontales y vertical central, 80 posiciones solicitadas cada uno. Adicionales: 9 líneas a 45/90/135° y cuatro verticales desplazadas ±10 mm; familia independiente `additional3DProfiles`. Se conserva soporte parcial si puntos nominales quedan fuera del metal, sin rellenarlos. Coordenadas globales y proyección de diagonales en el informe.
- Objetivos nativos: 10000 pasos, 10001 muestras de T/U/p_rgh/rho/alpha1, 101 estados guardados y series de reducciones y perfiles del C14. Incluye dTdt, dAlphaLdt, coolingRate, solidificationRate, latentHeatRateVol, diagnóstico Darcy/flotación, energía, vorticidad, Courant. Distinguir disponibilidad a t0 y cobertura temporal; no certificar derivadas o datos no producidos.
- Log completo guardado y progreso visible. foamLog si disponible. Archivos nativos postProcessing conservados, copia .xy con encabezado completo (27 columnas del archivo C14 original, nombres no truncados), marcador .foam. Manifiesto SHA y reporte de cobertura; fallo conserva intento y log. No pruebas unitarias manuales. Sin HTML.
- Diagnóstico latente nativo no es automáticamente demostración de cierre discreto de energía. No se promete 10001 muestras ni paridad hasta inspeccionar la ejecución real. No se repite el CFD anterior ni se cambia su estado de comparación.

## Una intervención WSL
```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
P="$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics"
source /opt/openfoam14/etc/bashrc
export HWLOC_COMPONENTS=-gl
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$P/run_c14_a_faithful_runtime.py"
```
Destino nuevo `~/OpenFOAM/C3D04_A_C14_FAITHFUL_RUNTIME_10S_01`. No sobrescribe destino existente. Reporte `C14_A_FAITHFUL_RUNTIME_REPORT.json`. Si éxito, abrir `C3D04_A_C14_FAITHFUL.foam` en ParaView o importar carpeta en FoamLens. La nueva ejecución local todavía no se ha observado; código publicado no equivale a CFD realizado.


## Evidencia real WSL — ejecución exitosa 24-11-2026
El investigador aportó la salida completa de `run_c14_a_faithful_runtime.py` tras fast-forward d838d5fab..97463be12. Estado **FAITHFUL_C14_RUNTIME_READY**, solver rc=0, 10000 pasos, t final=10 s, controlDict idéntico, input_hashes_unchanged=true, base_evidence_unchanged=true, native_diagnostic_parity=true, missing_or_incomplete=[].
- Corrida: `/home/michel/OpenFOAM/C3D04_A_C14_FAITHFUL_RUNTIME_10S_01`; original `C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01` intacta. SHA-256 log c1a0028504e04397bc00b7ecdb40eafa3cf5c046a8b0b0d73f6859946843676a.
- controlDict original/nuevo SHA c6db4389d758c31259285e18c8b3cef9fe945767ace1ee3fe147a8e286d7a9ec; researchDiagnostics original/nuevo SHA 58cf0db3e07fce65ba7b2cb797ef9cb62949dc233a716ad63d64af491a6d1ff3.
- Probe central global (0.0259,-0.02,0.0259) m, altura 20 mm desde base. T,U,p_rgh,rho,phaseChangeSource:alpha1: cada archivo tiene 10001 muestras finitas, 0..10 s, cadencia nativa exacta .001 s.
- Las 12 reducciones exigidas tienen 101 registros cada una. Los 15 campos derivados auditados (dTdt,coolingRate,dAlphaLdt,solidificationRate,latentHeatRateVol,gradT,magGradT,gradRho,magGradRho,CoCell,vorticity,flowType,magSqrDevGradU,phaseChangeDarcyCoeff,phaseChangeBuoyancyAcceleration) existen en los 101 estados, incluido t0.
- 17 líneas, cada una con 101 archivos, 1717 perfiles canónicos, 101 archivos topFlow nativos. Cobertura horizontal 0/45/90/135°: h10 68/80/68/80; h20 70/80/70/80; h30 72/80/72/80 puntos válidos de 80 solicitados, constante en tiempo. Las cinco verticales 80/80. No extrapolación; cobertura de los tramos solicitados, no del diámetro real completo. Diagonales proyectadas en X.
- foamLog rc=0 y carpeta logs existente. Paridad de diagnóstico operativa confirmada por auditoría WSL; no equivale a valores físicamente validados. No se han recuperado directamente los CSV/campos de esta nueva corrida, por lo que no se atribuyen las cifras térmicas de la corrida anterior a esta réplica.

**Referencia 3D-A preferente para análisis posterior: nueva corrida fiel.** Siguiente: comparar campos primarios de las dos corridas de idéntica malla/control, curvas probe nativas 2D/3D a .001 s, magnitudes de diagnóstico y balances; conservar originales, sin repetir CFD. Independencia malla/tiempo y cierre discreto siguen pendientes, QuickCup no validado. Etapa09/10, 8/10=80% hitos. FoamLens importación efectiva no observada.
