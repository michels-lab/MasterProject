# FS-C08 — tercera ejecución real B14: cierre presión-volumen bloqueante

## Evidencia WSL (24-nov-2026, hora local)
Fuente fcf45eb06 con arreglos de matrices hasta b6f3018f1. Reporte local:
`~/OpenFOAM/FS_C08_DIAGNOSTICS/FS_C08_REAL_CFD_DIAGNOSTICS_20261125T023736Z_79e2ebf4/FS_C08_REAL_CFD_REPORT.json`.
wmake=0, foamMultiRun=1, sin timeout. Los tres hashes auditados del origen C07 permanecen iguales.
Primera etapa t=1.19999904e-7 s: MULES y masa líquida diagonal completadas, GammaMax=0. Siete solves lineales DICPCG de T, último residuo 1.41101331825e-11. El bucle térmico llega a refreshAfterEnergy, que llama reconstructFractions ANTES del corrector de presión. En celda 0 alphaL=1.00000690418, alphaS=0: exceso 6.90418e-6. No se completó ningún paso. No se demostró el cierre energético por el residuo lineal ni existe contracción física validada.

Diccionarios aportados: PISO (1 outer corrector, 3 pressure correctors, 0 non-orthogonal correctors); Euler, laplacian Gauss linear corrected, temperatura PCG/DIC con tolerancia 1e-10. Horizonte 1 s, dt inicial 1e-7 s, maxDeltaT 1e-4 s, maxCo/maxAlphaCo .1, writeInterval .05 s. No cambiar estos valores como remedio de la saturación.
El Q inicial de pared fluido es -519822.175369 W y el molde 0: inicialización/flujo CHT sin reconciliar; no inferir calentamiento o pérdida física a partir de esta sola instantánea.

## Causa arquitectónica
mL y mS están en kg/m3 de volumen de celda. En cada iteración de prueba:

    mL* = mL^n - dt div(F_L) - dt Gamma
    mS* = mS^n + dt Gamma
    aMetal* = mL*/rhoL(T*) + mS*/rhoS(T*)

En una celda llena, aun con Gamma=0 y flujo de masa nulo, un cambio de rhoL puede hacer aMetal*>1. El corrector de presión actual se ejecuta después de la reconstrucción estricta; su flujo de metal además queda congelado antes de corregir phi. No se puede corregir la masa por presión si no se vuelve a transportar el flujo de metal corregido. Más correctores exteriores no eliminan el fallo anterior al corrector. No recortar masa/VOF, no permitir aGas<0, no fijar densidades ni ampliar el epsilon para aprobar.

## Puerta de implementación siguiente (NO implementada aún)
Separar estado de prueba (mL*,mS*,T*,p*) de estado físico aceptado. Para cada celda, la capacidad de líquido a T* es

    capL = rhoL(T*) [1 - mS*/rhoS(T*)]
    massExcess = max(0, mL* - capL)
    Rvol = mL*/rhoL(T*) + mS*/rhoS(T*) + mGas*/rhoGas(p*,T*) - 1

La ecuación de corrección debe resolver continuidad de volumen a partir de Rvol con flujos de presión/velocidad y EOS gas. La capacidad de líquido solo expresa la restricción local y no sustituye a la ecuación de presión. Si capL<0, el sólido estacionario ocupa más del volumen y se requiere un modelo mecánico adicional; no puede repararse expulsando líquido. Una proyección conservativa de flujo metálico debe transportar el exceso por caras reales hacia celdas con capacidad, preservar BC y no atravesar molde. La corrección de flujo debe formar parte de la solución de momento/presión, no una redistribución artificial desconectada. El líquido transportado lleva su energía uL; reensamblar energía con los mismos flujos corregidos, y recalcular Gamma desde el mismo estado n, evitando doble conversión. La fase gaseosa necesita su continuidad con los flujos corregidos y EOS. Iterar acoplamiento hasta residuo de volumen, masa, energía y presión aceptables, y solo entonces reconstruir fracciones físicas y publicar el estado n+1. Incorporar restricciones de MULES de manera compatible con esta formulación, no depender únicamente de MULES ejecutado antes del cambio de densidad. Aumentar outer correctors solo cuando exista esa separación y reensamblaje conservativo.

Criterios: no sobrellenado ni fases negativas, conservación metal/gas con flujos de frontera reales, energía incluyendo advección corregida y trabajo de presión; comprobar celda llena y volumen/interfaz durante enfriamiento. Después de compilar la nueva implementación, una ejecución real B14 aislada desde t=0. No pedir nueva corrida solamente para producir el mismo fallo.

## Qué se cambió en este bloque
Diagnóstico nativo: reconstrucción identifica fase de ejecución, cuenta celdas sobrellenadas y cuantifica exceso de volumen y masa líquida por encima de capacidad, volumen libre geométrico y T/rho/m por peor celda. La actualización de fuentes térmicas precede al gate de saturación en refreshAfterEnergy. Se mantiene el rechazo estricto, sin modificar B14. La nueva instrumentación todavía no está compilada en Foundation14. NO es la solución al acoplamiento y NO habilita una cuarta corrida como paso inmediato.
