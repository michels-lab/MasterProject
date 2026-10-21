# C3D-01 — Composición real, datos de diseño y parámetros heredados: NO mezclarlos

**Operación Granada | Estado: revisión de procedencia / no validación de aleación.**
**Fecha:** 2026-10-19.

## Hallazgo auditado en este repositorio

El documento `JMATPRO_OPENFOAM_TRACEABILITY_ES.md` indica como **niveles de diseño experimental**:

- Carbono equivalente (CE) objetivo: **3.9 / 4.2**.
- Azufre (S) objetivo: **0.05 / 0.13 wt%**.
- Manganeso (Mn): valor controlado a definir termodinámicamente.

**Esto NO equivale a una tabla completa de composición química medida de una colada.** Es incorrecto inventar los porcentajes de C, Si, P, Ni, Cr, Cu, Mg, etc. a partir de esos factores o atribuir automáticamente esos valores a una muestra.

El archivo `analysis_results/jmatpro_openfoam_audit/current_model_matrix.csv` y los materiales 2D del repositorio contienen, a modo de **parámetros activos heredados** (con procedencia por confirmar):

| Parámetro en el caso | Valor | No confundir con |
|---|---:|---|
| `Tliq` | 1473 K | Mediciones reales de liquidus de cada colada |
| `Tsol` | 1423 K | Solidus experimental de cada colada |
| `L` | 228600 J/kg | Latente calibrado y trazable para cada muestra |
| `rhoRef` | 6820 kg/m³ | Densidad medida de todas las muestras |
| `Cp` | 827 J/(kg K) | Curva específica `Cp(T)` de JMatPro |
| `alpha1e` | 0.8 | Fracción de austenita primaria experimental |

La matriz **no** contiene la composición completa de la colada. `alpha1e` es un parámetro operativo del modelo de fase, no una medición explícita de dendritas ni del eutéctico. El que los números estén en `fvModels` o `materials` no prueba su origen en JMatPro.

## Estado metalúrgico sustentado por el investigador

- Confirmado verbalmente: **hierro fundido hipoeutéctico** con solidificación **primaria de austenita (γ)**.
- Hipótesis expresada por el investigador: **hierro gris**; la morfología laminar de grafito esperada requiere respaldo microestructural/experimental. No etiquetar como verificada.
- Posible evolución: formación dendrítica de austenita y solidificación del líquido residual por reacción eutéctica estable (austenita + grafito) o rutas alternativas según composición e historia térmica. No etiquetar una ruta como observada sin evidencia.
- Una zona pastosa con flujo interdendrítico restringido **no es sinónimo** de defectos de porosidad por gas o contracción.

## Fuente errónea que NO debe reutilizarse

En la conversación se atribuyó erróneamente al investigador una composición tomada de un **artículo externo, Quick Cup test-2**: C 3.08, Si 2.14, Mn 0.82, S 0.06, P 0.05 wt%, CE aproximado 3.81. **ESOS DATOS NO SON LA TESIS/LA COLADA DEL INVESTIGADOR.** Se registran aquí *exclusivamente* como ejemplo de atribución rechazada para evitar su repetición. Nunca usar esas cifras como propiedades o entradas del caso, como evidencia de composición de QuickCup-Solidification ni como CE del investigador.

## Protocolo de incorporación de química experimental (puerta MAT-01/J0)

Para cada muestra o colada registrar, *solo después de recibir evidencia*:

1. Identificador de muestra y su relación exacta con la curva de enfriamiento/Quick Cup real.
2. Documento de análisis químico primario, método analítico, fecha y unidad (wt%, ppm; detección/censura cuando aplique).
3. Vector completo de elementos analizados, con incertidumbre si existe; no deducir ausentes por balance sin hacerlo explícito.
4. Carbono equivalente: declarar ecuación y rango de validez antes de computarlo; un CE objetivo de DOE no equivale a CE medido.
5. Archivos JMatPro/export por composición y condiciones de cálculo, `f_L(T)`, fases y termofísica con rangos y unidades.
6. Datos de microestructura (grafito, eutéctico, SDAS) si están disponibles, sin exigir que necesariamente existan.
7. Fecha y aprobación del investigador antes de modificar cualquier material, `fvModels`, dict, caso B/C o C3D.

**Estado de los datos químicos medidos: NO VERIFICADO.** Cierre de J0 sigue **ABIERTO**. Documentación preparada no equivale a validación física.
