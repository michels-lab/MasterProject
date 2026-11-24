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
