# Publicación científica del caso A fiel C14
24-11-2026. Etapa 09/10, 8/10 hitos operativos (80%). El investigador autoriza subir los resultados reales a MasterProject siguiendo los estándares de los casos 2D. La fuente local es C3D04_A_C14_FAITHFUL_RUNTIME_10S_01; WSL confirmó FAITHFUL_C14_RUNTIME_READY.

Destino: cases_3d/C3D_04_rounded_multiblock_pilot/C14_3D_A_faithful. Se copia 0, constant y system (excepto malla generada), postProcessing completo (incluidos 1717 perfiles canónicos y originales), logs, log.foamMultiRun, log.foamLog y reportes. Se agregan Allrun/Allclean adaptados, README, CASE_VARIANT y manifiesto SHA-256 por archivo y hashes de malla. Si está disponible, se incluye el análisis anterior C14 2D vs A base con procedencia explícitamente separada; no atribuirlo a la corrida fiel. Misma política .gitignore: no subir tiempos volumétricos calculados, polyMesh generado, dynamicCode, marcadores gráficos. Los originales locales no se borran. Allrun depende de V4/T02 y baseline local aceptados; no reconstruye automáticamente la geometría desde Git.

El publicador verifica reporte, log, hashes, 10001 muestras por campo, 101 reducciones por serie y perfiles nativos/canónicos. Verifica inventario de Git y blobs sin alterar la política de exclusión ni omitir archivos grandes silenciosamente. Usa un worktree de publicación separado desde origin/main; no cambia los checkouts de otros casos, hace commit acotado, push normal sin force, verifica ascendencia remota. Si main rechaza el push, publica rama de archivo explícita y no afirma merge. Conserva el worktree ante fallo. No ejecuta CFD. Actualiza estados y bitácoras ES/EN en el commit de datos.

Comando WSL:
```bash
A="$HOME/OpenFOAM/C3D04_A_WORKTREE"
P="$A/cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics"
git -C "$A" fetch origin &&
git -C "$A" merge --ff-only origin/main &&
python3 -B "$P/publish_case_a_to_git.py"
```

Código publicado; datos locales aún no transferidos. Esperar evidencia CASE_A_GIT_MAIN_PUBLISHED y commit verificado, o CASE_A_ARCHIVE_BRANCH_PUBLISHED_MAIN_PENDING para revisión. No declarar publicación de resultados antes de push real.
