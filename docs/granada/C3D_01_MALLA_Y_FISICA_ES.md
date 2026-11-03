# Operación Granada — C3D-01: criterios físicos antes de elegir la malla

**Estado: propuesta científica para revisión, NO decisión final de resolución ni caso mallado.**
**Fecha:** 2026-10-19. **Repositorio:** QuickCup-Solidification / OpenFOAM Foundation v14.

## 1. Qué se pretende resolver (y qué no)

El investigador confirma: hierro fundido **hipoeutéctico**, solidificación inicial con **austenita primaria**; considera **hierro gris** la microestructura esperada, pero no consta confirmación metalográfica del grafito laminar. Los valores exactos de composición de la colada no están verificados en las fuentes inspeccionadas; véase `COMPOSICION_Y_PROCEDENCIA_ES.md`.

La simulación 3D de C3D-01 busca transferencia de calor conjugada metal–arena y evolución de campos macroscópicos como temperatura, fracción líquida y, si se activa fluidodinámica, velocidad del líquido. La nucleación/eutéctica, recalescencia y composición son objetivos científicos que requieren formulaciones y evidencias adicionales. Ni `blockMesh` ni el actual `solidificationMelting` garantizan por sí solos reproducirlos.

## 2. Por qué la observación dendrítica del director importa

- Cuando solidifica austenita primaria, una red de dendritas puede resistir el flujo interdendrítico: zona pastosa o *mushy zone*.
- Es **porosidad efectiva de la zona pastosa durante la solidificación**; no confundir con cavidades reales por contracción, porosidad gaseosa o los espacios geométricos del molde.
- Entalpía-porosidad suele representar esta resistencia mediante una fuente volumétrica, no mediante una geometría STL de brazos dendríticos individuales.
- Las correlaciones de permeabilidad pueden depender de fracción líquida, espaciamiento de brazos dendríticos y morfología. La formulación real, sus unidades y coeficientes deben verificarse para la aleación y su implementación en OpenFOAM14.
- Por ello **una imagen más detallada en FoamLENS no demuestra mayor validez física**. La visualización no recupera estructuras dendríticas no resueltas por el solver.

Para un continuo promediado, una escala de celda defendible debería ser mayor que la microestructura que promedia y menor que la escala espacial de los gradientes macroscópicos relevantes. Esto es un **criterio conceptual**, no una prohibición automática de celdas de 0.5 mm. Hoy no hay SDAS, REV ni longitud térmica caracterizada para imponer una cota numérica a partir de las dendritas.

## 3. Estado de la decisión de malla

**Se suspende como requisito científico la decisión previa «0.5 mm como máximo en TODO metal y TODO molde» hasta contrastarla con el director y con evidencia de convergencia.** Esta nota NO modifica ni invalida automáticamente el borrador PR #18, que permanece aislado/abierto; no cambia sus archivos ni su estado.

Candidatas a estudiar, sin seleccionar aún una malla definitiva:

| Longitud nominal | Objetivo de prueba | Advertencia |
|---|---|---|
| 2 mm | Malla de fondo, exploración | Puede omitir frentes y gradientes macroscópicos importantes |
| 1 mm | Primera comparación de resolución macroscópica | No es un resultado validado |
| 0.5 mm | Comparador de refinamiento | No representa dendritas individuales |
| 0.25 mm | Solo donde una sensibilidad lo justifique | Coste elevado y posible falta de justificación física |

La resolución **no tiene que ser idéntica** en todas las regiones si las observables de interés convergen con una distribución no uniforme. Una malla refinada solo en la interfaz tampoco basta para afirmar que temperatura, fracción líquida o convección del núcleo metálico convergieron. Verificar tamaño mínimo y máximo **real**, no únicamente niveles objetivo declarados en `snappyHexMeshDict`.

## 4. Ensayos que sustentan una decisión

1. Antes de mallar: confirmar sólidos STL, orientación, unidades mm nativas OpenFOAM14, región del metal y región de arena, volúmenes sin doble conteo y puntos semilla.
2. Comprobar malla de fondo con `blockMesh` y `checkMesh`, **exclusivamente en el Ubuntu del investigador**. No interpretar malla de fondo como malla física metal–arena.
3. Diseñar manualmente y explicar `snappyHexMeshDict`; definir refinamiento superficial y volumétrico, interfaces multi-región y reglas de selección de celdas; no generar un diccionario opaco sin comprensión del investigador.
4. Verificar mallas por región: número de celdas y volúmenes, contactos térmicos, no-ortogonalidad, skewness, calidad topológica, rango de tamaños y conservación geométrica.
5. Definir observables comparables: curvas de temperatura en coordenadas físicas del termopar; tiempo de inicio de solidificación, temperaturas características, duración de etapa primaria/eutéctica, fracción líquida y flujo de calor en interfaz, balances energético y, cuando aplique, continuidad.
6. Comparar resoluciones de forma **pareada**, conservando modelo físico, BC, propiedades y malla de comparabilidad adecuada; estudiar también sensibilidad al paso temporal y parámetros de zona pastosa.
7. Establecer un umbral de aceptación **antes de juzgar resultados** con datos experimentales y con el director; cuantificar cambio relativo de observables al refinar. Ninguna malla se declara independiente por una sola ejecución.
8. Mantener abierta la validación de **recalescencia**: una fuente latente con fracción de fase de equilibrio no demuestra subenfriamiento/nucleación/cinética eutéctica.

## 5. Alcance y obligaciones

- `cases_3d/C3D_01_metal_mold` permanece **PREPARED / NO OPENFOAM RUN / NO CFD** en la evidencia conocida.
- C14/B14 y campañas V15/V16 no se alteran. El cierre J0 JMatPro es independiente y continúa abierto.
- Ningún GitHub Action instala/ejecuta OpenFOAM, `blockMesh`, `snappyHexMesh`, `foamRun` ni `foamMultiRun`; GitHub solo revisa archivos, documentación y pruebas estáticas.
- Materiales químicos, SDAS, resultados metalográficos y curvas reales **no se inventan**. No copiar la composición de publicaciones ajenas al caso del investigador.
- FoamLENS permite visualizar y comparar campos **calculados**; no sustituye convergencia ni valida morfología dendrítica a partir de una interpolación.

## 6. Puertas abiertas / dueño de la evidencia

| Puerta | Dato necesario | Estado |
|---|---|---|
| MAT-01 | Composición medida de la(s) colada(s), fuente y unidades | ABIERTA |
| MAT-02 | Confirmación de tipo de grafito y observación microestructural | ABIERTA |
| MAT-03 | SDAS/escala dendrítica o fundamento explícito de promediado | ABIERTA |
| J0 | Archivo/export JMatPro por composición y procedencia propiedades | ABIERTA |
| MESH-01 | Mallado 3D nativo y chequeo de interfaz metal–arena | NO EJECUTADO |
| MESH-02 | Convergencia espacio/tiempo/latente y validación térmica | NO EJECUTADO |
| PHYS-01 | Ruta física/numérica que modele recalescencia primaria/eutéctica | PENDIENTE DE DISEÑO |

Referencias dentro del repositorio: `JMATPRO_OPENFOAM_TRACEABILITY_ES.md`, `NEXT_RESEARCH_ROADMAP_ES.md`, `cases_3d/C3D_01_metal_mold/geometry_reference.json`, `analysis_results/jmatpro_openfoam_audit/current_model_matrix.csv`.
