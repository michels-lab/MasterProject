# Uva + Granada — fidelidad C14 2D → 3D-A y diagnóstico temporal

Corte 27-11-2026. Etapa A 9/10, 8/10 hitos (80% técnico). Revisión estática del archivo científico de 10 s y contraste de observaciones WSL registradas; no nueva ejecución CFD ni validación física.

## Paridad de archivos

Base A: `cases_3d/C3D_04_rounded_multiblock_pilot/C14_3D_A_faithful/`. Referencia 2D: `cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/`.

| Ruta relativa | Resultado |
|---|---|
| system/controlDict | SHA idéntico; fijo .001 s, 10 s, escritura cada 100 pasos, maxCo .25 no adapta dt |
| system/fvSolution | SHA idéntico; PIMPLE global 3/2/1 |
| system/metal/fvSchemes | SHA idéntico; Euler, h upwind, laplaciano corrected |
| system/mold/fvSchemes | SHA idéntico; Euler, laplacian(kappa,T) corrected, interpolación armónica |
| system/mold/fvSolution | SHA idéntico; PCG/DIC |
| system/metal/fvSolution | Única diferencia ejecutable por comparación de líneas sin comentarios: pRefCell 0 sustituye pRefPoint (0.02 0.04 0.005); comentario histórico pRefPoint no describe el valor activo |
| constant/metal/fvModels | SHA idéntico; Tsol 1423 K, Tliq 1473 K, L 228600 J/kg, alpha1e .8, relax .1, beta 1.13e-4 |
| constant/metal/physicalProperties y materials/castIron | SHA idénticos; rhoConst 6820, Cp 827 |
| constant/mold/physicalProperties y materials/silica | SHA idénticos; rho 1500, Cv 700, kappa 2 |
| constant/metal/g | SHA idéntico; (0 -9.81 0) m/s² |
| 0/metal/T y 0/mold/T | Adaptación de parches y tipo externalTemperature en A; metal 1500 K, molde 300 K, h 10, Ta 300, emisividad .3/.5 y capa metal .0002 m/.1 W/(m K). No afirmar igualdad de área, flujo o implementación de BC por coincidencia de parámetros |
| 0/metal/U,p,p_rgh | Sin empty en A; tapa slip e interfaz noSlip; p calculated, p_rgh fixedFluxPressure, inicial 1e5 Pa |

No editar comentarios ni diccionarios dentro del archivo científico porque su manifiesto fija hashes. El comentario adjustTimeStep=no que dice que permite adaptar es incorrecto; no afecta ejecución. El pRefCell requiere trazabilidad geométrica y de partición antes de atribuir equivalencia hidrostática. No afirmar que nEnergyCorrectors determina el número efectivo de solves sin log.

## Evidencia archivada y alcance

GIT_PUBLICATION_MANIFEST.json, blob 0bd877829b9c390abc390731e0827fb0d9967b94: declara 3726 archivos, 176484972 bytes, 101 estados, 10001 muestras por variable de sonda, 1717 perfiles. Los campos volumétricos y polyMesh generado permanecen locales; no se verificaron los 3726 hashes en este bloque. Allrun exige destino nuevo y delega al ejecutor fiel; Allclean no borra resultados. run_c14_native_milestone.sh tiene modo por defecto --smoke, por lo que no es el comando para una auditoría sin solver; no ejecutarlo automáticamente.

## Contraste de fallos adaptativos

Fuente: docs/granada/C3D04_A_NATIVE_THERMAL_OBSERVED_20261127_ES.md (788aef70e32e33f87c8f8ebe2f28edc1399c9d6a) y docs/C3D04_CASE_A_STATUS.json (4fa01e88abd426522f89095147ae09725969a747).

- Adaptativo MPI8 con cap .025: 51 pasos completos, .66 s último aceptado, fallo .68 s con dt .020 s y Co previo .188631; temperatura negativa en thermophysicalPredictor. A .60 s Tmin 1147.97 y Tmax 1720.55 K. No es recalescencia demostrada.
- Control fijo MPI8 .001 s hasta .70 s: exit 0, End y Finalising parallel run reportados; Tmin 1459.57 K a .60 s y 1456.73 K a .70 s, Tmax 1499.98 K. A .70 s alpha1 min .936123. Se esperan 700 pasos, no contados independientemente. No se verificó identidad de cellProcAddressing. El contraste favorece sensibilidad temporal pero no demuestra causalidad exclusiva.
- checkMesh reportado OK: metal 8960 celdas y 276 caras >70°, molde 12352 y 232 caras >70°. No se comprobó que las celdas críticas sean las de mayor no ortogonalidad. Malla local ausente del archivo Git.
- Prohibido sustituir resultados de campaña, limitar T artificialmente o cambiar parámetros exclusivamente en A. Una sensibilidad común adaptativa de cuatro casos con cap candidato .005 s requiere aprobación explícita; no se garantiza estabilidad ni se preparó/ejecutó aquí. Mantener 6/8 publicaciones adaptativas originales y los dos fallos preservados.

## Pendientes

Verificar manifiesto de la corrida fija 200 s del laboratorio sin rerun, inspeccionar logs completos y partición del control .7 s cuando estén disponibles, estudiar conservación discreta y comparación a tiempos físicos comunes, y validar JMatPro/QuickCup. No confundir paridad de diccionarios con paridad de geometría, conservación o predicción experimental.
