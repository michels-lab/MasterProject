> **27-11-2026 | Estado vigente integrado:** campaña adaptativa laptop 6/8 combinaciones calculadas, 3/8 publicadas con manifiesto completo, 3/8 pendientes de auditoría de perfiles duplicados, 2/8 A fallidas. C14-2D sin tope es serial, no MPI. A fijo laptop llegó a 200 s; publicación laboratorio no confirmada. FS-C08 lote 12: 4/4 variantes, 75/75 pasos a 5 μs, sin independencia temporal ni validación física. A etapa 9/10, 8/10=80%; B etapa 3/7, 2/7=29%; 2D histórica 26/26. No porcentaje global de tesis. [Historia y evidencia](https://github.com/michels-lab/MasterProject/blob/main/docs/granada/MAESTRIA_ESTADO_INTEGRADO_20261127_ES.md) · [Estado JSON](https://github.com/michels-lab/MasterProject/blob/main/docs/MAESTRIA_STATUS.json). Las entradas previas conservan su valor histórico.

> **Corrección de alcance autorizada por el investigador, 24-11-2026:** B14 NO es candidato 3D. Campaña activa exclusivamente C14-3DA-200s, C14-2D-200s, B14-2D-200s, C14-3DB-200s (4 corridas, 800000 pasos); B14-2D referencia de contracción, C14 candidato 3D. Excluir B14-3DA-200s, B14-3DB-200s de ejecución y descarga. El paquete histórico de seis entradas ya publicado permanece intacto; no es autorización para correr seis. Transferidor actualizado 3deb781c0f1a87cb84244fdb3c748b39dbce3fa4; no modifica física, mallas, almacenamiento, rama FS ni resultados previos. Proyección para cuatro casos 103865500374 bytes; no consumo medido. 4/4 entradas autorizadas publicadas; 0/4 CFD completos confirmados. Foundation 14 laboratorio confirmado por consola (14-a4867fc914c1); importación y CFD pendientes. Interrupción local A fue manual según investigador, no prueba de estabilidad. A 8/10=80%, B 2/7=29% históricos.

> **24-11-2026 | Campaña compacta: preparación WSL 6/6 confirmada.** Consola del investigador: `ALL_SIX_COMPACT_PREPARED_NO_CFD`, seis casos `PREPARED_COMPACT_NOT_RUN`. Proyección total 195999917264 bytes frente a 677717076556 bytes (reducción 71.0793893%); espacio libre WSL 930909974528 bytes; `all_fit_WSL_estimate=true`. Por caso: 2D 5865541742 bytes, 3DA 6722248179 bytes, 3DB 85412168711 bytes, iguales estimaciones por familia. CI estática #45516133349 completada con success; no equivale a CFD. Capacidad física Windows todavía no verificada. 0/6 corridas, cadencias nativas pendientes de validar en el primer segundo real. Prioridad C14-3DA-200s, utilizar únicamente el ejecutor compacto; conservar casos densos y originales. A 9/10, 8/10=80%; B 3/7, 2/7=29% hitos históricos.

# Campaña 200 s — política compacta autorizada

> **24-11-2026 | Campaña 200 s — prioridad nueva: almacenamiento compacto.** Autorizado por el investigador. Mantener dt=.001 s, 200 s, 200001 muestras de sonda, perfiles/reducciones/topFlow/nearTop online cada .1 s (2001 estados previstos), volúmenes completos y momentum nativo cada 1 s (201 estados previstos); ASCII original, sin compresión o cambio físico. Los seis casos densos preparados permanecen intactos; nuevo preparador independiente `tools/compact_campaign_200s.py`, verifica hashes, requiere casos densos no ejecutados, audita el primer segundo real de la corrida y reserva disco. 6/6 densos preparados, 0/6 compactos observados, 0/6 CFD de 200 s observados. CI estática en cola al revisar #45516133349; no se afirma PASS, ejecución WSL ni ahorro total medido. A etapa 9/10, 8/10=80%; B etapa 3/7, 2/7=29%.


## Cadencias
- CFD: 200000 pasos, dt=.001 s, sin cambios en física, mallas ni BC.
- Sondas: .001 s, 200001 registros previstos por campo.
- Perfiles, reducciones y topFlow: .1 s, 2001 instantes previstos (topFlow positivo 2000); añadir nearTopInternalLine nativo .1 s con coordenadas ya corregidas. Los productores de gradientes, ddt, energía, fase y Co se ejecutan .1 s pero escriben sus campos volumétricos solo a writeTime global.
- Volúmenes: 1 s, 201 tiempos, ASCII original para conservar compatibilidad de formato. Momentum codificado escribe campos explícitamente, se mantiene a 1 s. No reconstruir perfiles volumétricos/derivados a .1 s no archivados. Momentum y face-fields adicionales offline no ejecutados por defecto, recuperables solo a tiempos disponibles 1 s. No afirmar paridad completa 0.1s.

## Preservación y evidencia
Copias nuevas en CAMPAIGN_200S_COMPACT_01; solo 0/constant/system de seis casos densos sin solver, verificadas contra manifiestos SHA. Se rechaza cualquier caso iniciado, modificación no prevista o enlace simbólico. No se borra nada ni se toca rama FS-C08. El nuevo script usa los locks del origen y destino, conserva estados parciales; no relanza automáticamente. Chequeo de cadencia durante la corrida real tras 1 s (perfiles a .1, volúmenes a 1, ausencia de volúmenes no enteros), auditoría posterior de cobertura y guardado de perfiles canónicos. La prueba real aún pendiente, CI estática no equivale a CFD.

## Estimación de almacenamiento
Usar el desglose de cada informe denso; volumen 201/2001 del estimado anterior, conservar diagnóstico/logs con 10% extra para nearTop/aliases, margen global 50%. No afirmar que el total baja 90%; solo los estados volumétricos. Costo CFD se mantiene. Comprobar capacidad real Windows además de WSL. Reserva de 10 GiB durante solver; sin garantía de consumo.

## Comando de preparación (no solver)
```bash
REPO="$HOME/OpenFOAM/MasterProject"
SCRIPT="$HOME/OpenFOAM/compact_campaign_200s.py"
source /opt/openfoam14/etc/bashrc
git -C "$REPO" fetch origin &&
git -C "$REPO" show 50d3bbd7750756d7d854eaa2a6f8d69157a3341f:tools/compact_campaign_200s.py > "$SCRIPT" &&
python3 -B "$SCRIPT"
```
Leer CAMPAIGN_RESOURCES.json en la nueva carpeta. Solo si termina ALL_SIX_COMPACT_PREPARED_NO_CFD y espacio físico suficiente, ejecutar explícitamente C14-3DA-200s con `python3 -B "$SCRIPT" --run C14-3DA-200s`. No usar el ejecutor denso anterior. No se requiere nuevo worktree completo.

## Auditoría de almacenamiento medida en A (24-11-2026)
Consola du del investigador: postProcessing 110 MiB, logs 12 MiB, log.foamMultiRun 28 MiB; snapshots 0.1/5/10 s 5.1/5.9/6.3 MiB. C14CanonicalProfiles 53 MiB; perfiles adicionales 41, horizontales 8.7, verticales 3.6 MiB (53.3 MiB originales). topFlow 3.2 MiB, probe 1.6 MiB, reducciones pequeñas. Proyección ilustrativa A: 201*6.3 + 20*(110+12+28) = 4266.3 MiB (~4.17 GiB), antes de margen y sin validar nueva cadencia; excluir duplicación canónica ahorraría ~1060 MiB si se conserva una sola representación de las tablas. El estimador anterior escaló todos los diagnósticos/logs por razón de celdas B/A=270788/21312; eso es inadecuado para perfiles de tamaño fijo, sondas y reducciones. No se midió B aún. Mantener campos primarios y diagnósticos temporales nativos; evaluar campos redundantes, compresión y compatibilidad de FoamLens antes de editar configuración. No se modifica física, casos locales, FS ni rama de transferencia ya publicada. C14-3DA compacto local RUN_INCOMPLETE_PRESERVED: causa todavía no inspeccionada; no iniciar campaña lab hasta revisar. A 8/10=80%; B 2/7=29%, 6/6 entradas publicadas, 0/6 CFD completos.

## Decisión del investigador (24-11-2026)
Conservar campaña compacta ya publicada: ASCII, sin compresión, sin retirar campos derivados ni diagnósticos existentes; dt .001 s, perfiles .1 s, volúmenes 1 s. No modificar paquete de transferencia ni física por optimización adicional. Estimación previa conservadora por escalamiento inadecuado de diagnósticos, no consumo medido; duplicación de perfiles aceptada por ahora. Se mantiene como pendiente identificar error del C14-3DA compacto local RUN_INCOMPLETE_PRESERVED antes de arrancar lote del laboratorio; no afirmar cadencias nativas verificadas. Preparación/publicación 6/6; CFD completo 0/6; A 8/10=80%, B 2/7=29%.
