# Uva + Granada — Caso B: fidelidad, energía y protección de análisis

Corte 2026-11-27. B etapa 3/7, 2/7 hitos (29% técnico); A etapa 9/10, 8/10 (80%). No nueva CFD ni validación física.

## Geometría y fidelidad

El preparador c14_physics/stage_c14_3d_case_b.py verifica contrato C14, malla fuente aceptada, 92,200 celdas metal + 178,588 molde, 12,636 caras mappedWall por lado, parches esperados y zona metal. La transferencia parte del generador C14 3D común: fusiona cinco cuerpos térmicos iguales en moldOuterUnclassified, sustituye referencia de presión por pRefCell 0 y crea zona completa solo si falta o está vacía. Conserva el control de 10 s y dt .001 s por comparación de bytes. Esto verifica el contrato del código, no los hashes de cada diccionario del caso WSL ejecutado. No se encontró el archivo C14_3D_B_faithful/README.md en main; no inferir inexistencia de otras publicaciones.

A reporta 21,312 celdas y 508 caras >70 grados; B 270,788 celdas y 1,826 caras severas. El cociente de celdas ~12.71 no implica convergencia ni superioridad física. La malla B no se descargó.

## Energía y masa

Fuente directa: docs/granada/C3D05_B_C14_CRUCE_101_ESTADOS_CONFIRMADO_Y_AUDITORIA_TERMINOS_20261124_ES.md, blob 419981fb0d8e4ad364a752b2d0f203023b34509d. Registra 101 estados, q nativo Foundation14 en copia sombra con interpolación armónica explícita; no integral al paso .001 s. A 10s interfaz +1581.564663/-1581.538327 W, suma firmada +.026336 W; suma absoluta por caras 1.870336 W. Integrales +20283.452365/-20283.567649 J; desajuste firmado -.115283 J. Inventarios de referencia: metal sensible -13576.397936 J, latente líquido -8100.198211 J, molde +20323.651946 J; combinado -1352.944201 J; exterior +1341.507907 J; diferencia -11.436294 J, NO residuo. C14 10s conserva 101 estados; h/e/rho faltantes según observaciones registradas en README de física; no rellenar datos. El complemento sólido volumétrico reportado a 10s es .1082970139, no fracción másica independiente ni contracción geométrica.

## Correcciones

- stage_c14_3d_case_b.py: protección resuelve rutas y ancestros antes de comprobar superposición; usa ruta canónica para staging, ejecución y reporte. No modificar malla fuente. Regresión de enlaces de ancestro y dotdot añadida.
- analyze_existing_case_b_c14_metal_mass_phi.py: interrumpe integración cuando falta cualquiera de los dos flujos, no solo metalTop. Cuenta intervalos integrados; un estado aislado no es integración disponible. Conserva prefijo válido, no puentea lagunas. Dos regresiones nuevas; no ejecución verificada.
- Scripts shell de revisión, preflight/materialize/run-full y postprocesamiento inspeccionados; no usar comandos de CFD en una auditoría. El postproceso offline no reconstruye las 10,001 muestras de paso solver desde 101 estados. No ejecutar git pull en worktree activo.
- Se mantiene el registro de ambas publicaciones adaptativas B a 200 s, 15,013/15,012 pasos, campos volumétricos no incluidos según índice general. No mezclar sus resultados con el original fijo de 10 s.

Pendientes: ejecutar regresiones de software, verificar artefactos locales y hashes de B, completar masa/energía discreta y comparar A/B/2D con coordenadas y cadencia consistentes. La reconstrucción de términos energéticos ausentes no queda demostrada. Sin cambios de parámetros físicos, datos originales o hitos.
