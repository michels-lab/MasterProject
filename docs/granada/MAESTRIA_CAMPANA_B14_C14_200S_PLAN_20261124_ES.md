> **27-11-2026 | Estado vigente integrado:** campaña adaptativa laptop 6/8 combinaciones calculadas, 3/8 publicadas con manifiesto completo, 3/8 pendientes de auditoría de perfiles duplicados, 2/8 A fallidas. C14-2D sin tope es serial, no MPI. A fijo laptop llegó a 200 s; publicación laboratorio no confirmada. FS-C08 lote 12: 4/4 variantes, 75/75 pasos a 5 μs, sin independencia temporal ni validación física. A etapa 9/10, 8/10=80%; B etapa 3/7, 2/7=29%; 2D histórica 26/26. No porcentaje global de tesis. [Historia y evidencia](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261127_ES.md) · [Estado JSON](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_STATUS.json). Las entradas previas conservan su valor histórico.

> **Corrección de alcance autorizada por el investigador, 24-11-2026:** B14 NO es candidato 3D. Campaña activa exclusivamente C14-3DA-200s, C14-2D-200s, B14-2D-200s, C14-3DB-200s (4 corridas, 800000 pasos); B14-2D referencia de contracción, C14 candidato 3D. Excluir B14-3DA-200s, B14-3DB-200s de ejecución y descarga. El paquete histórico de seis entradas ya publicado permanece intacto; no es autorización para correr seis. Transferidor actualizado 3deb781c0f1a87cb84244fdb3c748b39dbce3fa4; no modifica física, mallas, almacenamiento, rama FS ni resultados previos. Proyección para cuatro casos 103865500374 bytes; no consumo medido. 4/4 entradas autorizadas publicadas; 0/4 CFD completos confirmados. Foundation 14 laboratorio confirmado por consola (14-a4867fc914c1); importación y CFD pendientes. Interrupción local A fue manual según investigador, no prueba de estabilidad. A 8/10=80%, B 2/7=29% históricos.

> **24-11-2026 | Campaña 200 s — prioridad nueva: almacenamiento compacto.** Autorizado por el investigador. Mantener dt=.001 s, 200 s, 200001 muestras de sonda, perfiles/reducciones/topFlow/nearTop online cada .1 s (2001 estados previstos), volúmenes completos y momentum nativo cada 1 s (201 estados previstos); ASCII original, sin compresión o cambio físico. Los seis casos densos preparados permanecen intactos; nuevo preparador independiente `tools/compact_campaign_200s.py`, verifica hashes, requiere casos densos no ejecutados, audita el primer segundo real de la corrida y reserva disco. 6/6 densos preparados, 0/6 compactos observados, 0/6 CFD de 200 s observados. CI estática en cola al revisar #45516133349; no se afirma PASS, ejecución WSL ni ahorro total medido. A etapa 9/10, 8/10=80%; B etapa 3/7, 2/7=29%. [Plan compacto](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_CAMPANA_200S_ALMACENAMIENTO_COMPACTO_20261124_ES.md).

> **24-11-2026 | Campaña 200 s: preparación WSL 6/6 confirmada.** Consola del investigador, HEAD 3ffe0b56a: las seis variantes PREPARED_NOT_RUN, ALL_SIX_PREPARED_NO_CFD. Proyección con margen: 677717076556 bytes; espacio libre reportado por WSL: 931037851648 bytes; all_six_fit_estimate=true. Confirmar también espacio físico del volumen Windows que aloja el VHDX; la estimación no garantiza capacidad real. 3DB 270788 HEX8, 12636 caras de contacto por lado, 1826 caras no ortogonales severas (advertencia conservada). 0/6 CFD ejecutados; A 8/10=80%, B 2/7=29% hitos. Prioridad actual A C14-3DA-200s según registro A, usar ejecutor específico sobre caso ya preparado, sin repetir preparación. [Plan](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_CAMPANA_B14_C14_200S_PLAN_20261124_ES.md).

# Campaña de 200 s — plan acordado 24-11-2026

## Propósito científico
C14: línea principal de solidificación. B14: referencia para investigación de contracción, no solver de rechupe físico validado. El investigador acepta hacer también B14 en las tres geometrías dentro de esta campaña. FS-C08 permanece en rama independiente; no sustituir la formulación conservativa líquido/sólido/gas por B14.

| Geometría | Solidificación C14 | Referencia de contracción B14 |
|---|---|---|
| 2D original | C14-2D-200s | B14-2D-200s |
| C3D04 A V4/T02 | C14-3DA-200s | B14-3DA-200s |
| C3D05 B STEP/Gmsh | C14-3DB-200s | B14-3DB-200s |

## Fuentes y fidelidad
Fuentes 2D: `cases_controlled_buoyancy/{B14,C14}_topFixedFlux_explicitRef`. B14 rho(T), beta=0 para flotabilidad explícita del fvModel, rhoRef=6930; C14 rho constante, beta=1.13e-4, rhoRef=6820. Ambos Tsol=1423 K, Tliq=1473 K, L=228600 J/kg, alpha1e=.8, relax=.1, Cu=1e5, q=.001. Transferir íntegramente cada familia física, no solo beta. A/B actuales reproducen C14. Conservar mallas, materiales, BC y configuración originales; documentar exclusivamente adaptaciones geométricas. No confundir geometría Caso B con formulación B14. Las seis corridas son nuevas variantes, no sobrescribir datos de 10 s.

## Controles propuestos (pendientes de auditoría)
endTime=200, startTime=0, deltaT=.001, adjustTimeStep=no, writeInterval=100: 200000 pasos, 200001 tiempos de sonda (incluido cero), 2001 estados volumétricos si se retiene cadencia .1 s. Esto es un objetivo inicial de fidelidad, no autorización para cambiar almacenamiento o dt. Estimar costo/espacio desde evidencia de 10 s, incluyendo volumen de campos, topFlow, perfiles y logs; evaluar esquema de escritura común si fuese necesario y documentar cualquier desviación antes de ejecutar. Conservar sondas, perfiles/ángulos, reducciones, energía, momentum, Courant, phi, rho, alpha1 y diagnósticos disponibles compatibles con FoamLens. Auditar no ortogonalidad, estabilidad a largo tiempo, cobertura y conservación; no asumir solidificación completa a 200 s. No extrapolar registros ni considerar el máximo Co configurado un límite activo con dt fijo.

## Secuencia
1. Preparar fuentes y auditoría integrada de recursos para 2D C14/B14 y variantes A/B; sin remallar ni tocar las corridas archivadas.
2. Ejecutar 2D como referencias de largo plazo; 3D C14 para solidificación, B14 como referencias de contracción. Orden concreto y concurrencia a decidir según recursos; solo en WSL del investigador y en destinos independientes.
3. Comparar enfriamiento, fracción sólida/tiempos de liquidus y solidus, velocidad y amortiguamiento, balance térmico y masa/volumen con distinción entre fracciones y contracción física. Validación QuickCup/JMatPro e independencia pendientes.

Estado: PLANNED_NOT_STAGED_NOT_RUN. A etapa 9/10, 8/10=80% operativo; B etapa 3/7, 2/7=29% técnico. No se cierran hitos por planificación. No se ejecutó CFD ni se cambió ningún diccionario en esta entrega.


## Entrega del preparador integrado (24-11-2026)
Publicado `tools/prepare_campaign_200s.py` (988cc0753957). Verifica diferencias de familias en los árboles system/constant (solo castIron y fvModels), conserva campos iniciales primarios idénticos, excluye diagnósticos archivados del t=0. 2D reconstruye las mallas originales con blockMesh/splitMeshRegions en copia; 3D usa los stagers aceptados y coteja hashes de malla con las corridas de 10 s. Transfiere física B14 completa, no solo beta. Conserva dt=.001, escribe cada .1s, cambia endTime a 200; sondas/perfiles nativos y diagnósticos originales, 17 líneas 3D, adapta momentum y nearTop a coordenadas reales. La preparación materializa las seis variantes SIN solver, registra recursos por caso y total mediante estimación de campos/diagnósticos de 10 s reales, margen 50% y reserva de 10 GiB; estimación no es cota garantizada. Ejecución explícita `--run NOMBRE` de una variante preparada, serial por bloqueo, verifica espacio e integridad, preserva parciales y audita tiempos, probes, perfiles, derivados y topFlow. Sin confirmación de compilación Python/ejecución WSL del nuevo preparador aún. No se modifica CFD previo ni rama FS-C08.

```bash
REPO="$HOME/OpenFOAM/MasterProject"
DEV="$HOME/OpenFOAM/CAMPAIGN_200S_CODE_01"
source /opt/openfoam14/etc/bashrc
git -C "$REPO" fetch origin &&
git -C "$REPO" worktree add --detach "$DEV" origin/main &&
python3 -B "$DEV/tools/prepare_campaign_200s.py"
``

El índice de recursos se escribe en `~/OpenFOAM/CAMPAIGN_200S_01/CAMPAIGN_RESOURCES.json`. Tras confirmar recursos, una ejecución explícita de la referencia principal: `python3 -B "$DEV/tools/prepare_campaign_200s.py" --run C14-2D-200s`. No lanzar otras corridas sin revisar espacio agregado. A 9/10, 8/10=80%; B 3/7, 2/7=29%. Campaña 200 s: código publicado; materialización 0/6 observada, ejecución 0/6 observada.
