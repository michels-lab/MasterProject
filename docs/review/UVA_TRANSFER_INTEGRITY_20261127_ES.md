# Operación Uva — transferencia de campaña 200 s (2026-11-27)

Corte inspeccionado: `eac980dd4e68621067ff5a172dece5c72e7d1c76`. Alcance: mantenimiento de software y trazabilidad, sin nuevas corridas ni cambio de física.

## Hallazgos y correcciones

- `input_hashes` no rechazaba el directorio inicial 0/constant/system si era un enlace; ahora valida la raíz inmediata, existencia de los tres directorios y cada componente bajo ella. La copia de snapshots y la comprobación de inputs de casos intentados usan el mismo guard.
- La extracción tar rechazaba la ruta final enlazada y escapes de la raíz resuelta, pero aceptaba enlaces intermedios que apuntaban dentro de la raíz. Ahora rechaza todo componente enlazado bajo la raíz. Se mantiene apertura exclusiva de archivos.
- La reutilización de una publicación solo comparaba el SHA del log. Ahora exige identidad, tipo, 200 s, 200000 pasos fijos y SHA de log y reporte. No modifica publicaciones existentes.
- La vista previa podía lanzar un error no controlado al redondear un tiempo no finito. Ahora lo rechaza explícitamente.
- La recepción de resultados rechaza raíces/destinos enlazados y verifica directorios de inputs antes de copiarlos.

## QA y límites

Se añadieron seis métodos de regresión a la suite existente: raíces enlazadas, enlace anidado, extracción con enlace intermedio, extracción regular, identidad y dos hashes, tiempo no finito. La CI existente incluye esta suite. Ejecución pendiente al publicar este informe; no se declara PASS. Los guards no pretenden proteger contra cambios concurrentes hostiles del sistema de archivos ni enlaces por encima de la raíz suministrada. La transferencia histórica sigue fijada a su solver de referencia; no se reescriben ramas de resultados, archivos nativos ni mallas. Los tests adaptativo y compacto se leyeron completos; no se ejecutaron ni certifican el comportamiento de OpenFOAM. Próximo bloque: auditoría integral de scripts adaptativo/compacto, comparar tiempos y validar CI en el SHA correspondiente.

Estado científico sin cambio: Caso B etapa 3/7, 2/7 hitos técnicos (29%); Uva no tiene porcentaje global de cobertura (árbol truncado).
