# masterproject ↔ FoamLens — integración estrictamente opcional

**masterproject (antes QuickCup-Solidification) es un proyecto científico autosuficiente.** El slug de GitHub conserva temporalmente el nombre histórico hasta que el propietario lo cambie en Settings. Sus casos OpenFOAM Foundation 14, simulaciones, reportes, scripts de análisis, protocolos y bitácoras no dependen de FoamLens ni de ningún hub de coordinación.

[FoamLens](https://github.com/michels-lab/FoamLens) es software genérico e independiente para visualizar y analizar datos OpenFOAM. Puede abrir datos de QuickCup **únicamente si el usuario así lo decide y si su importador soporta el formato**.

## Contrato de interoperabilidad
- Exportar solo archivos elegidos localmente, sin modificar los resultados originales ni reescribir valores físicos.
- Preservar caso, región, tiempo físico, unidades, hash de fuente, asociación (celda/cara/punto/sonda), parámetros y limitaciones.
- Ausencia de una variable no se interpreta como valor cero; no extrapolar tiempos en silencio.
- Las etiquetas RUN_VERIFIED, ANALYSIS_VERIFIED y EXPERIMENTALLY_VALIDATED pertenecen a las verificaciones del proyecto científico; un visor no puede afirmarlas por leer CSV.
- La licencia y los datos sensibles de cada proyecto continúan bajo sus respectivas reglas.
- Los tests de software de FoamLens jamás sustituyen validación termofísica o experimental de QuickCup.

## Gobierno documental
La fuente canónica está en [índice de documentación](DOCUMENTATION_INDEX.md), [RUN_MASTER_PROTOCOL](../RUN_MASTER_PROTOCOL.md), [PROJECT_AUDIT_LOG](../PROJECT_AUDIT_LOG.md) y [registro de casos](../RUN_CASE_REGISTRY.csv). Un repositorio central externo, si existe, **solo coordina** decisiones; jamás se requiere para correr el solver.
