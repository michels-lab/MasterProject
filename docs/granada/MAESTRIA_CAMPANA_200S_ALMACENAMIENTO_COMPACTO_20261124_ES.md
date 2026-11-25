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
