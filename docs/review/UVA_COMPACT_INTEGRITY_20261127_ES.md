# Uva + Granada — compactación 200 s y límites de ejecución (2026-11-27)

Base: `0b002f56459ba4ee0ed314a7e8813e3facd99b8d`. Lectura completa de compact_campaign_200s.py (349 líneas), tests y comparación con la transferencia de cuatro casos autorizados.

- Se mantiene la preparación histórica de seis entradas, pero se limita --run y execute a los cuatro casos autorizados en transfer_campaign_200s.py. B14-3DA/B14-3DB quedan como entradas históricas, no ejecución automática.
- Rechazo de raíces de entrada enlazadas o inexistentes, rutas enlazadas de casos, informes y locks; escritura JSON con temporal único. La generación de perfiles canónicos admite relectura idéntica sin sobrescribir resultados y rechaza divergencia.
- Tiempos numéricos no finitos se rechazan. Cinco regresiones sintéticas nuevas. La configuración de tiempo fijo, las mallas, parámetros y archivos de salida originales permanecen sin cambios.

Alcance parcial: auditoría del contenido completa como lectura, correcciones focalizadas de aislamiento e integridad; quedan pendientes ejecución CI, recuperación integral poscorrida, cobertura de enlaces en todas las lecturas auxiliares y coordinación de variantes MPI. Sin ejecución CFD ni validación científica. Hitos técnicos A 8/10 etapa 9/10; B 2/7 etapa 3/7. No hay porcentaje de tesis.