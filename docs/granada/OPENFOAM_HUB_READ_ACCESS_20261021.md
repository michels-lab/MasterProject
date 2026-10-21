# Granada — constancia de consulta opcional desde el hub OpenFOAM
Fecha: 2026-10-21 · Alcance: gobernanza documental, no simulación.

## Evidencia
Se verificó que el repositorio de coordinación OpenFOAM — PROJECTS puede **leer**, por ruta y SHA de commit, documentos y código textual público de este proyecto. La auditoría del hub registra únicamente nombre de archivo, tamaño, hashes e incidencias, no copia datos CFD ni modifica casos.

Cobertura comprobada inicialmente: README, protocolo de corridas, inventario CSV, bitácora central, manuales ES/EN, guía de caso, postproceso, validación, JMatPro y herramientas de auditoría de código. La lectura no significa validación numérica/física/experimental.

## Garantías de independencia
- Este repositorio continúa siendo la **única autoridad científica** para QuickCup, ejecutable con OpenFOAM Foundation 14 sin FoamLens ni hub.
- Corridas CFD únicamente en la laptop del investigador, nunca GitHub Actions del hub.
- El hub no tiene permiso de escritura desde su workflow en este repositorio y no altera `RUN_CASE_REGISTRY.csv`, modelos, geometrías ni evidencia.
- No almacenar aquí enlaces privados al hub, secretos, ni credenciales. Los estándares de software existentes siguen en Michel-Software-Standards.
- Compatibilidad futura con FoamLens significa formatos de datos opcionales, no transferencia automática de resultados.
- PRs activos #18/#19/#20, bitácoras ES/EN y casos asociados se dejan intactos, con sus propios gates y dueños.

## Auditoría y punto de retorno
Esta entrada documenta **acceso verificado de lectura**, no merge de los PRs abiertos ni trabajos de malla/energía/J0/G1 completados. Para un cambio técnico real, usar PR propio en este repositorio y actualizar sus registros científicos según RUN_MASTER_PROTOCOL.
