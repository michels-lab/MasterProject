# Uva + Granada — integridad de ejecución y postproceso histórico Caso B (2026-11-27)

Alcance: scripts C14 10 s, no campaña adaptativa 200 s, sin alterar física ni resultados. Caso B etapa 3/7, 2/7 hitos técnicos (29%); sin cambio de puertas científicas.

## Hallazgos y cambios
- POSTPROCESAR_CASO_B_C14_EXISTENTE.py: rutas canónicas y aislamiento tanto en staging como resume; rechazo de enlaces en árboles copiados y en copia reanudada; comprobación de identidad de salida y tres hashes originales; lock cooperativo exclusivo; DONE requiere log no vacío; retorno 1 ante etapas incompletas. No se recuperan sondas de 1 ms a partir de muestras de 0.1 s.
- EJECUTAR_CASO_B_C14_COMPLETO.sh: aridad estricta, rutas no solapadas, lock cooperativo, rechazo de symlinks en salida post-only, publicación sin clobber, preservación de logs con nombres únicos y validación DONE/log.
- Diez regresiones sintéticas Python; workflow con sintaxis Bash/Python y caso negativo de argumentos. No ejecuta CFD ni requiere intervención WSL.

## Procedencia y límites
Base observada 85f2030d101d454fc1bb0af0419d1dbe32756f84; correcciones efcd580e265a3fd8589ecd5efcda60d5093753d1, b09f9fe8c3a9d2e1fb97674a9a4d5a7ca0e797ea y a81c55126695c59877d79abf71f4e89768716691; pruebas 0396fca15dcf93215c466f7e564ec1189456c33d; workflow 2599cc81788f4a99f33f559c09a8fe793fa6120d. SHA de blobs comprobados tras publicación. CI pendiente de evidencia de ejecución al corte. Locks solo coordinan estas invocaciones, no procesos externos; no equivalen a protección ante cambios hostiles concurrentes ni a manifiesto integral de todos los campos. DONE/log no certifica contenido científico. No ejecutar scripts históricos sobre campañas activas. No se modificaron mallas, resultados, ecuaciones ni criterios físicos.

Siguiente hito: auditar comparadores y exportadores de energía/masa/perfiles del Caso B por blob y dependencia; distinguir cierre energético global y diagnóstico parcial, y revisar pruebas CI sin repetir CFD.
