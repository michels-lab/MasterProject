# Granada Grande — B-FS-01: banco VOF agua–aire, previo al metal

**2026-10-20 · Etapa B-FS-01 parcial; NO simulación metal–aire ni contracción de solidificación ejecutadas.**

## Antecedentes y decisión de arquitectura

La investigación B-FS/B-SH quedó registrada en docs/granada/B_FS_B_SH_OPENFOAM_FOUNDATION14_RESEARCH_20261020.md. La ruta B persigue: interfaz metal–aire, transferencia térmica, cambio de fase y reducción de volumen/feeding. Son etapas físicas distintas. Antes de construir una geometría metalúrgica que aún no está respaldada por toda la termodinámica y la verificación del solver, se construye un **banco hidrodinámico análogo agua–aire** basado directamente en un tutorial REAL y versionado de Foundation v14.

Fuente técnica oficial: https://github.com/OpenFOAM/OpenFOAM-14/tree/master/tutorials/compressibleVoF/damBreak. Se usan sus entradas auténticas para solver compressibleVoF, dos fases water/air, propiedades termofísicas, fronteras, discretizaciones y modelos originales, y se sustituyen de forma explícita SOLO la geometría, la inicialización volumétrica de agua y controles numéricos/diagnóstico. Este banco es un control de integración de software, NO una parametrización del hierro.

## Entregables ejecutables

1. **Preparación segura de input 2D reproducible** — analysis_tools/granada_bfs01_vof_benchmark.py, subcomando stage. Acepta una carpeta local de tutorial Foundation 14, comprueba archivos imprescindibles, identidad del solver, fases y gravedad, rechaza enlaces simbólicos, prohíbe sobreescribir carpetas originales y escribe un caso nuevo en una carpeta separada. Los archivos CFD históricos jamás se editan. El manifiesto calcula SHA-256 de los archivos originales y derivados.
2. **Banco de fluido/aire con atmósfera y malla** — rectángulo 40×60×10 mm, 80×120×1 celdas; 2D con caras frontAndBack empty; paredes izquierda/derecha/inferior impermeables y salida atmosférica arriba. Agua inicial hasta y=40 mm; aire en la zona superior; gravedad Foundation14 en −Y. Intervalo objetivo 0–0.1s, escritura cada 0.01s y Co/AlphaCo nominales 0.25. El volumen inicial analítico es 1.6×10⁻⁵ m³. Añade el diagnóstico volFieldValue/volIntegrate(alpha.water), pero NO corre malla ni solver.
3. **Auditoría científica de salidas auténticas** — subcomando audit. Cuando OpenFOAM cree postProcessing/waterVolume/0/volFieldValue.dat, valida cabecera original, valores finitos/no negativos, tiempos estrictamente crecientes, presencia de medición inicial, llegada a 0.1s y desviación relativa respecto al volumen inicial analítico. Exporta volume_screen.json y volume_times.csv en carpeta NUEVA y externa. El umbral de deriva de volumen es configurable (0.005 por defecto como tolerancia de cribado propuesta, NO criterio experimental). La altura equivalente V/A NO es altura interfacial local ni medida de topología de superficie.
4. **QA integrado e insumos upstream reales** — trece pruebas sintéticas cubren procedencia, control de seguridad, parser, falseamiento de deriva/cobertura y rechazos. En GitHub Actions se clona en sparse checkout el ejemplo original de OpenFOAM Foundation14 y se prepara el input B-FS-01 sin instalar ni ejecutar OpenFOAM. El artefacto es ÚNICAMENTE el caso de entrada; el hecho de generarlo no prueba blockMesh/checkMesh/foamRun.

## Comandos para el investigador (solo en Ubuntu con OpenFOAM 14 instalado)

Con el repositorio QuickCup clonado y ejecutando Python3:

    python3 analysis_tools/granada_bfs01_vof_benchmark.py stage \
      --tutorial "$FOAM_TUTORIALS/compressibleVoF/damBreak" \
      --out /tmp/quickcup-BFS01-hydro

Revisar que el directorio no existiera antes y no apuntara a un caso de investigación. Abrir una terminal del entorno Foundation v14 y ejecutar **en el caso nuevo**:

    cd /tmp/quickcup-BFS01-hydro
    blockMesh
    checkMesh
    foamRun

Si hay error de implementación, no declarar la simulación completada; guardar stdout/errores, estado de malla y campos iniciales. Si foamRun llega al final con datos reales:

    python3 /RUTA/QuickCup-Solidification/analysis_tools/granada_bfs01_vof_benchmark.py audit \
      --case /tmp/quickcup-BFS01-hydro \
      --out /tmp/quickcup-BFS01-hydro-audit

La auditoría indica fallos numéricos mediante código distinto de cero, no corrige CFD ni rellena mediciones ausentes. Solo verifica **integral de volumen VOF agua** en este análogo; la mezcla compresible significa que NO es automáticamente un balance de masa. El diagnóstico adicional masa de líquido requerirá integrar alpha·rho desde campos auténticos, contabilizar flujos abiertos y verificar dependencias de presión/T. Adicionalmente habrá que revisar los mínimos/máximos de alpha, evolución de Courant, presión, superficie y convergencia; esta versión no certifica esos aspectos.

## Por qué NO lo llamamos simulación de contracción todavía

- Agua–aire no es hierro líquido–aire: las propiedades, energía, tensiones superficiales, mojado, densidad y escala hidrostática difieren.
- El banco no usa VoFSolidificationMelting, ni liberación latente, ni variación sólido/líquido, ni molde CHT. Si el nivel cambia durante el banco puede ser respuesta hidráulica/transitoria o error VOF, no contracción metalúrgica.
- B14 usa metal con densidad tabulada y sólido mediante solidificationMeltingSource, dentro de una región fija sin aire. No se debe sustituir/mezclar alpha.water por phaseChangeSource:alpha1 ni trasladar rho(T) directamente como ley de densidad de mezcla.
- El control 0.5% de deriva solo es una puerta numérica elegida para diagnóstico, no certificado de conservación de masa o exactitud física. También se requiere un ensayo de presión/superficie hidrostática equilibrada.
- La siguiente etapa independiente B-FS-02 debe sustituir el análogo por metal–aire con propiedades realmente obtenidas y ensayar la compatibilidad con foamMultiRun y el molde sólido. B-SH solo empieza después de demostrar conservación de masa por fase, balance energético, fase sólida y ley de volumen específico. Para hierro fundido evaluar grafitización/posible expansión antes de asumir contracción neta.

## Integración científica con FoamLens

Contrato propuesto: quickcup-bfs01-hydro-analogue-v1 para manifiesto y quickcup-bfs01-volume-screen-v1 para cribado de series reales. FoamLens podrá comparar trayectorias cuando exista un importador probado; **no se afirma que actualmente lo reconozca**. Los originales de OpenFOAM siempre son fuente de verdad; la exportación ofrece rutas/hashes y advertencias explícitas.

## Operación Granada — QA, claims y siguiente entrada

Evitar tocar PR #18/#19 C3D, PR #20 V15/V16, ambos casos base históricos B14/C14, bitácoras de ese PR o resultados versionados. Este documento es bitácora separada. No se ejecutó CFD, no se demostró free-surface ni se produjo dato experimental en GitHub.

**Para cerrar B-FS-01** falta: ejecutar blockMesh y checkMesh sobre Ubuntu Foundation14 en este caso; ejecutar foamRun, examinar el campo alpha/pressure e interpretar volumen/masa y estabilidad contra resultados reales. Si alguna puerta depende de la laptop, aparcarla y continuar con el próximo paquete seguro de física o herramientas, sin afirmar que B-FS-01 ha sido validada experimentalmente.
