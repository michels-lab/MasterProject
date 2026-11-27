# Uva + Granada — ejecutor adaptativo y reanudación segura (2026-11-27)

Base inmutable: `0767bd29e8f0df50847e44d40ed2508b6f0c97da`. Se reabre el ejecutor adaptativo serial uncapped tras la modificación de transfer_campaign_200s.py. No se aplican estos cambios a las ramas históricas de resultados ni a otros ejecutores MPI/capped por inferencia.

## Hallazgos y correcciones
- Rutas de casos existentes, informes y bloqueo: usar checked_relative de transfer y rechazar enlaces. Los informes usan temporales únicos y reemplazo atómico; no seguir un .tmp preexistente.
- Perfiles canónicos: relectura idempotente de contenido idéntico, rechazar contenido divergente, publicar nuevos archivos completos sin reemplazar evidencia. Rechazar directorios temporales numéricos no finitos o enlazados.
- Publicación: comparar identidad de caso, modo, pasos, tiempo final, hashes de log/informe y alcance de cobertura; no dar por equivalente una publicación solo por el hash del log.
- Estado final: un bloqueo durante el bucle no se puede ocultar detrás de solver_completed.
- Se incorporan seis regresiones sintéticas de integridad al módulo adaptativo existente. Pendiente ejecución CI exact-head; revisión de código no implica prueba ejecutada.

## Alcance y limitaciones
No cambia controlDict físico/numerico, malla, fuentes de fase, configuración de paso, tolerancias, resultados nativos ni ramas de campañas. No se ejecuta OpenFOAM. La revisión del ejecutor es de contenido y compatibilidad focalizada; quedan por estudiar precisión temporal de probes, recuperación integral de auditoría poscorrida, cadencia real, cobertura espacial y variantes MPI/capped. No se promete que el nuevo control permita reutilizar automáticamente manifests de otros modos. Las comprobaciones de enlaces cubren rutas específicas, no protegen frente a un actor concurrente que cambie directorios durante una operación.

Hitos técnicos científicos sin cambio: A 8/10 (etapa 9/10), B 2/7 (etapa 3/7), adaptativo 6/8 publicaciones completas según registro de estado. No es porcentaje de tesis.

Siguiente: compact_campaign_200s.py, compatibilidad de variantes y verificación CI. El ledger conserva las versiones inspeccionadas y el ref resultante.
