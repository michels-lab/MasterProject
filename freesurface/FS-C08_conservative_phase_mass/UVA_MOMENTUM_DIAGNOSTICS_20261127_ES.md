# Uva + Granada — atribución de velocidad y presión en el arranque FS-C08

Corte 27-11-2026. Sin CFD nueva. Auditoría focalizada de código y diagnóstico, no validación física.

## Contrato observado en C++
- fsC08PressureCorrector.C (bfcdcb8dac5b04f7d3f1d6dfe44f5c690842e34c), líneas 840–987: HbyA, contribución de presión (-rAU*reconstruct(snGrad(p_rgh)*magSf)) y contribución conjunta gravedad/tensión superficial (rAU*reconstruct(phig/rAUf)) en la celda de máxima rapidez. Las tres tienen unidades de m/s, no N ni m/s2. Su suma vectorial representa el objetivo directo de la matriz congelada, no necesariamente la velocidad conservativa reconstruida. La diferencia de magnitudes no es la norma de una diferencia vectorial.
- MOMENTUM_CONSISTENCY contrasta U aceptada con ese objetivo, máximos internos de caras y gas puro; FRESH_MOMENTUM_DEFECT reconstruye la matriz sin resolver U, solo cuando momentumPredictor es falso. No es residual completo de la PDE. No restar máximos de celdas distintas como si fueran contribuciones de una misma celda.
- fsC08ConservativeVoF.C (644d771c61f3e6cf1c039b481328463e9bc8a75f), líneas 674–695: extremos maximumSpeed y maximumGasDominatedHeating, con centro, alphaGas, inventarios, p/pOld, T/Told y contribuciones energéticas volumétricas. No identificarlos automáticamente como la misma celda.
- FS_C08_VolumeProjection.C (602873105843c2ecd92c372994d5d38ec35dd725): registros de descomposición de presión inicial y superposición del operador congelado, con dt_s pero sin time_s. La prueba auxiliar de compliance ocurre solo para !finiteK; no es una simulación física ni un cambio de EOS aceptado.
- fsC08MushyMomentum.C (c3ef6b05932ac56ac1f094bc7a2194d34718c0e2): sumidero implícito R=(ml+ms)*Cu*fS²/(fL³+q) condicionado a fase metálica; el código calcula disipación con U final posteriormente. No se modifica.

## Implementación
Nuevo analysis_tools/fs_c08_momentum_diagnostics.py: lee siete familias de marcadores, conserva vectores y magnitudes, calcula objetivo directo congelado como suma vectorial, conserva extremos por razón y distingue startup sin marca temporal. Detecta claves duplicadas, datos no finitos, vectores inválidos y duplicidad por marcador/tiempo/razón. Los registros no son certificados de pasos aceptados. El runner escribe FS_C08_MOMENTUM_DIAGNOSTICS.json antes de evaluar el código de salida, también para intentos incompletos. Tres pruebas de software y cobertura en workflow nativo; no ejecución confirmada en esta sesión.

## Estado y límites
Lote 12 reportado: 4/4, 75/75 pasos hasta 5 microsegundos, Umax 75.2783 a 12.8225 m/s para dt 1 a .125 microsegundos. Reducción entre extremos ~83%; no constituye orden de convergencia, ni prueba de causalidad. Sin logs WSL crudos no se atribuye la velocidad a presión, gravedad, capilaridad, defecto de matriz o transporte. No se modifican ecuaciones, EOS, tolerancias ni condiciones iniciales. Siguiente análisis: cruzar JSON con ledger de estados aceptados a tiempos comunes y comparar contribuciones en las mismas celdas físicas. Cierre CHT global y calibración de aleación pendientes.
