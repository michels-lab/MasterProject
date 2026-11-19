# Caso A C3D-04 — Hito integral T0 de conducción (PRE-CFD)

**Estado al 19-11-2026: `CODE_COMMITTED / STATIC_REVIEWED_NOT_WSL_RUN / REAL_INPUTS_BLOCKED / NO_CFD`.**  
**Etapa global Caso A: 5/10; avance operativo: 4/10 hitos = 40 %.** Valor derivado de [estado canónico](../../../docs/C3D04_CASE_A_STATUS.json): **no** es porcentaje de precisión física ni de tesis finalizada.

## Objetivo y límites

Un solo paquete para pasar del mallado aceptado preliminarmente a **un experimento numérico T0 de conducción transitoria entre dos SÓLIDOS**, pensado únicamente para revisar acoplamiento térmico, diccionarios, conservación de energía y sensibilidad numérica. **NO es un modelo de vaciado ni solidificación real**; no representa hierro líquido, convección de metal, calor latente, transformaciones, recalescencia ni transferencia convectiva externa real. Éstas pertenecen a etapas posteriores, con datos experimentales y modelo de entalpía.

Base de geometría (SOLO LECTURA): `~/OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02`.
Referencia ya medida: 21,312 celdas (8,960 hierro + 12,352 arena), `Mesh OK` 3/3, contacto recíproco `mappedWall` 2,496 caras por lado, área 6,343.771874 mm². Distancia superficial STL–malla máxima **muestreada** 0.104973 mm, no Hausdorff certificado. No ortogonalidad >70°: 572 global, 276 hierro, 232 arena; diferencia 64/64 **identificada sobre interfaz**, investigación cerrada. Máximo global 82.92°; **no hay demostración de estabilidad o independencia de malla**.

## Archivos entregados

- [`T0_INPUTS.json`](T0_INPUTS.json): **valores materiales e iniciales explícitamente `null`**, fuentes de cada propiedad igualmente nulas; seleccionar valores trazables y justificar conversiones `c_p`/`C_v` antes de continuar. Nunca usar números sintéticos como datos de fundición.
- [`scripts/prepare_case_a_t0.py`](scripts/prepare_case_a_t0.py): controlador único Python para validar entradas, verificar los datos guardados nativos del Caso A y los nombres reales de los parches, generar **nueve archivos** OpenFOAM Foundation 14 orientativos en memoria y, **solo con autorización explícita `--materialize` y entradas completas**, crear una **carpeta separada** con copia física de `polyMesh`.
- [`run_integrated_milestone.sh`](run_integrated_milestone.sh): **orquestador único** que integra verificación de contrato de avance, regresiones, preflight de caso nativo y propiedades, y entorno F14; `--materialize` únicamente para etapa futura autorizada. Jamás invoca `foamMultiRun`, `blockMesh` ni `checkMesh` y nunca cambia V4/T02.
- [`scripts/report_case_a_progress.py`](../scripts/report_case_a_progress.py): recalcula `Etapa N/10` y `Avance D/10=P%`, valida consistencia con el JSON canónico.

### Campos térmicos y BC de C3D-04

**Metal:** `metalTop` (**malla nativa `type wall`**) usa `zeroGradient` en T0; `metal_to_mold` (`mappedWall`) usa `coupledTemperature`.

**Arena:** `moldTop`, `moldExterior`, `moldBottom`, `moldRecessWall` y `moldRecessRoof` son paredes `zeroGradient` SOLO para el experimento cerrado de conservación. `mold_to_metal` tiene `coupledTemperature`. Los dos materiales se aproximan mediante `heSolidThermo / constIsoSolid / eConst / rhoConst / sensibleInternalEnergy`, con `rho`, `Cv`, `kappa`, `molWeight` y temperaturas iniciales trazables. El solver orientativo es `foamMultiRun` con dos regiones `solid`, discretización de difusión corregida y número configurable de correctores no ortogonales, pendiente de contraste con instalación real y prueba de sensibilidad. No hay resistencia térmica de interfaz en T0: acoplamiento idealizado, NO medición QuickCup.

**Precaución crítica:** el estado `CODE_COMMITTED` **no demuestra** que Foundation14 haya parseado los nueve archivos ni que el solver arranque. Los requisitos reales de los módulos, diccionarios y estabilidad solo podrán validarse en el entorno WSL cuando existan entradas auténticas. No se debe hacer correr CFD con valores de prueba.

## Flujo único por hito, no por subpieza

*Preparado para uso cuando el hito esté íntegro y haya fuentes reales, pero no se solicita al investigador ejecutar nada ahora:*

```bash
cd ~/OpenFOAM/MasterProject && git pull --ff-only && bash cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/run_integrated_milestone.sh --preflight
```

El modo de preflight verifica archivos guardados sin generar o ejecutar CFD. Con `T0_INPUTS.json` nulo imprime `BLOCKED_PENDING_REAL_INPUTS` y no crea un caso. No se repiten las tres auditorías de V4/T02 que ya están cerradas; únicamente se reusan sus resultados como puertas de seguridad. El modo `--materialize` es **posterior**, requiere autorización y nunca ejecuta solver.

## Próximas obligaciones de ingeniería (agrupar en una sola entrega)

1. Fuente científica/experimental para `rho(T)`, `c_p(T)`, `k(T)` y consistencia `C_v`; condiciones iniciales realistas, calor latente y cinética para T1 por separado.
2. Parámetros de contacto metal–arena (ideal vs resistencia) y de intercambio exterior con el ambiente `h`, no sustituirlos por las paredes adiabáticas T0 en un modelo físico final.
3. Verificar sintaxis real Foundation14 en WSL, compatibilidad de `coupledTemperature`, presupuesto temporal, esquemas y correctores; después pruebas de conservación de energía y estabilidad cuando existan condiciones experimentales justificadas.
4. Solo tras T0 verificable avanzar T1: entalpía/cambio de fase, curvas de termopares, estabilidad, sensibilidad espacial/temporal e independencia de malla.

### Reglas persistentes de entrega

Rigen [`AGENTS.md` del caso](../AGENTS.md) y [`AGENTS.md` raíz](../../../AGENTS.md). Toda actualización incluye **etapa, avance de hitos, evidencias, pendientes y bloqueos**. Prohibido volver a un script nuevo/una orden WSL por cada pequeña comprobación. Trabajar por entregas integrales y conservar el caso geométrico.
