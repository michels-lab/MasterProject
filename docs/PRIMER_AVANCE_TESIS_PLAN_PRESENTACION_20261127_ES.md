# Primer avance de tesis — plan de presentación
27-11-2026. Duración propuesta: 20 min. Alcance: resultados CFD preliminares, no validación experimental. Fecha de exposición no confirmada. Fuente de requisitos: [director](PRIMER_AVANCE_REQUISITOS_DIRECTOR_20261118_ES.md). [Auditoría meseta](granada/C14_2D_AUDITORIA_MESETA_SOLIDUS_20261127_ES.md).
## Guion
1. Portada; pregunta, objetivo y alcance (2 min).
2. Solidificación hipoeutéctica: austenita primaria, transformación eutéctica, calor latente, QuickCup; diseño CE/S y validación prevista (2 min).
3. Modelo matemático: masa, momento con flotación y Darcy, energía metal, conducción molde, actualización de fase; contrastar con fuente Foundation14 antes de cerrar (3 min).
4. Geometría y mallas 2D/A/B, IC/BC, propiedades activas y trazabilidad (3 min).
5. Solución numérica, Courant medido, residuos/continuidad, sensibilidad relax C14/C16 (3 min).
6. Resultados: T(t), alpha local y volumétrica, perfiles/frentes, sensibilidad posición, extracción específica de calor y discrepancia aproximada (5 min).
7. Conclusiones, limitaciones y validación (2 min).
## Casos seleccionados
Alias FINAL_C14_2D_200s, FINAL_C14_3DA_200s, FINAL_C14_3DB_200s (comparación principal); FINAL_B14_2D_200s (contraste densidad, no baseline validado). C14/C16 histórico de 10s para sensibilidad obligatoria. FINAL identifica selección para presentación, no validación física. Directorio local previsto ~/OpenFOAM/PRIMER_AVANCE_TESIS; traslado no confirmado. No tocar rutas ni resultados. Ramas results/campaign-200s-fixed-lab-v2/<caso>; [índice](MAESTRIA_RESULT_MANIFEST_INDEX_20261127.json).
## Indicadores verificados
|Caso|T central 200s K|Sólido medio vol %|max CoCell en 2001 muestras cada .1s|t del max s|
|---|---:|---:|---:|---:|
|B14-2D|1423|81.71276|.06732006|2.7|
|C14-2D|1423|82.34848|.06504965|3|
|C14-3DA|1243.46|100|.9099937|22.2|
|C14-3DB|1237.46|100|.2670542|2.9|
CoCell: analysis_preview/postProcessing/metal/metalMaxCourant/0/volFieldValue.dat, máximo espacial en instantes guardados; NO máximo de todos los pasos. A requiere inspección de log completo y celda crítica; maxCo .25 inactivo con dt fijo. No confundir con estabilidad garantizada.
C14/C16 10s: relax .10/.25, T1464.19/1464.22 K, alpha .964815/.964914, Co de series históricas .0650864/.0651054, RMSE T .020079761 K sobre 1001 tiempos. Fuente [cribado](../analysis_results/v15_v16_postpush_20261015/README.md); auditoría integral C16 pendiente.
## Checklist entrega
- [x] Selección de cuatro datasets completos fijos 200s (4 manifiestos verificados).
- [x] IC/BC/propiedades registradas; tablas comparativas, sonda X20 adicional y balance aproximado.
- [x] Recuperación de máximos CoCell muestreados 200s y cribado C14/C16 histórico.
- [ ] Ecuaciones contrastadas término por término contra fuente nativa, citas y signos.
- [ ] Co real todos los pasos, residuos, continuidad y costo desde logs completos. Auditoría local A Co=.91.
- [ ] C16 paridad y sensibilidad integral; no repetir automáticamente.
- [ ] Figuras definitivas: misma escala, T y alpha local/volumétrica, mapas T/alpha a tiempos iguales, leyendas, malla y perfiles, dT/dt con cadencia y método declarados.
- [ ] Diagnóstico centro 2D, JMatPro alpha1e, validación experimental, independencia espacial/temporal.
- [ ] Diapositivas y ensayo 20 min. No fecha inventada.
No se generó pptx ni se ejecutó CFD; esta revisión organiza contenido, no certifica resultados físicos.