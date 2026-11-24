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
