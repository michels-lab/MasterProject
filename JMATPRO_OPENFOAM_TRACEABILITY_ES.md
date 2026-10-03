# Auditoría JMatPro → OpenFOAM — QuickCup Solidification

> **Actualización 2026-10-03 — baseline vigente:** `C11_topFixedFlux_airGapOF14` se conserva como baseline histórico congelado. `C14_topFixedFlux_explicitRef` fue verificado a 10 s y es su sucesor actual para trabajo/validación: mantiene `fixedFluxPressure + slip`, la misma física/materiales de C11 y añade la referencia explícita de presión solicitada por el director. Las observaciones de trazabilidad de propiedades hechas sobre C11 siguen aplicando a C14 mientras no se cambien sus propiedades termofísicas.


**Fecha:** 2026-09-29  
**Estado:** AUDITORÍA DE TRAZABILIDAD TERMODINÁMICA  
**Baseline OpenFOAM inspeccionada:** `C11_topFixedFlux_airGapOF14`  
**Caso de contraste:** `B11_topFixedFlux_airGapOF14`

## 1. Por qué existe esta auditoría

La propuesta de tesis define una secuencia explícita:

**composición química → simulación termodinámica JMatPro → OpenFOAM → fundiciones/curvas reales → comparación y ajuste físico.**

JMatPro no se planteó únicamente para suministrar densidad. La propuesta le asigna dos funciones:

1. **metalúrgica/termodinámica:** definir el contenido de Mn y estudiar estabilidad de fases, interacción Mn-S y posible formación de sulfuros;
2. **termofísica para CFD:** estimar `Cp(T)`, `k(T)`, `rho(T)`, `TL`, `TS`, `L` y `fL(T)`.

Por tanto, adoptar una formulación de volumen fijo con `rhoConst` en C11 no elimina a JMatPro del proyecto. Lo que obliga es a separar qué salidas de JMatPro se transfieren directamente al CFD, cuáles se transforman en parámetros equivalentes y cuáles se usan como referencia metalúrgica/termodinámica.

## 2. Qué usa realmente C11 hoy

Archivo:
`cases_controlled_buoyancy/C11_topFixedFlux_airGapOF14/constant/metal/materials/castIron`

### Termodinámica y transporte

```
transport       const;
thermo          hConst;
equationOfState rhoConst;
```

Valores actuales:

- `rho = 6820 kg/m3` constante;
- `Cp = 827 J/(kg K)` constante;
- `mu = 5.5e-3 Pa s` constante;
- `Pr = 0.14` constante.

Con `constTransport` y Pr especificado, OpenFOAM calcula:

`k = Cp*mu/Pr`

por lo que el caso actual implica:

`k ≈ 32.4893 W/(m K)`.

Es decir, **C11 no usa actualmente `Cp(T)`, `k(T)` ni `rho(T)` de forma tabulada**.

### Cambio de fase

Archivo:
`constant/metal/fvModels`

Valores actuales:

- `Tsol = 1423 K`;
- `Tliq = 1473 K`;
- `L = 2.286e5 J/kg`;
- `alpha1e = 0.8`;
- `beta = 1.13e-4 1/K`;
- `rhoRef = 6820 kg/m3`;
- `Cu = 1e5`;
- `q = 1e-3`;
- `relax = 0.1`.

Estos valores están presentes y activos, pero **la evidencia accesible no demuestra todavía una cadena documental directa desde un archivo/exportación JMatPro específico hasta cada valor**.

## 3. Hallazgo crítico sobre fL(T)

La propuesta presenta como formulación general:

- `fL=0` para `T<=TS`;
- `fL=(T-TS)/(TL-TS)` entre solidus y liquidus;
- `fL=1` para `T>=TL`.

Sin embargo, el caso real usa `solidificationMeltingSource` con:

`alpha1e = 0.8`.

En la implementación de OpenFOAM, `alpha1e` modifica directamente la relación de equilibrio entre temperatura y fracción líquida: la temperatura de fase queda limitada por `Tsol` por debajo de `alpha1e`, y solo la fracción restante entre `alpha1e` y 1 se distribuye entre `Tsol` y `Tliq`.

Por tanto:

**la relación de fase del caso real NO debe describirse simplemente como una interpolación lineal 0→1 entre TS y TL mientras `alpha1e=0.8`.**

Esto convierte a la curva JMatPro `fL(T)` en una comparación central, no decorativa.

## 4. Densidad: cómo conservar JMatPro sin reabrir el top

B11 contiene la tabla de densidad:

- 1473.15 K → 6820 kg/m3;
- 1573.15 K → 6740 kg/m3;
- 1773.15 K → 6580 kg/m3.

En el rango líquido 1473.15–1773.15 K la pendiente es aproximadamente:

`d(rho)/dT = -0.8 kg/(m3 K)`.

A partir de:

`beta = -(1/rhoRef) d(rho)/dT`

con `rhoRef=6820 kg/m3`:

`beta_liquid ≈ 1.1730e-4 1/K`.

El valor usado por C11 es:

`beta_C11 = 1.13e-4 1/K`.

Diferencia relativa:

**≈ 3.81 %.**

Esto es una consistencia interna muy buena: la formulación Boussinesq de C11 puede conservar la información de expansión térmica de una curva `rho(T)` sin introducir una EOS de densidad variable en la ecuación de continuidad.

**Advertencia:** esta concordancia no demuestra por sí sola que la tabla B provenga de JMatPro. Esa procedencia debe documentarse con el export/raw de JMatPro.

En el intervalo 1423.15–1473.15 K la tabla B tiene una pendiente más intensa, equivalente aproximadamente a `beta≈2.33e-4 1/K`. Por ello el valor de beta debe derivarse y justificarse sobre un rango térmico físicamente definido —preferentemente la fase líquida relevante para convección—, no sobre toda la curva indiscriminadamente.

## 5. Matriz de trazabilidad actual

| Magnitud | Papel propuesto de JMatPro | C11 actual | Transferencia actual | Estado |
|---|---|---|---|---|
| Mn / estabilidad Mn-S / sulfuros | selección metalúrgica | no pertenece al solver | interpretación/diseño experimental | **JMatPro sigue siendo central** |
| TL | obtener por composición | 1473 K | directo como `Tliq` | valor activo; procedencia raw por verificar |
| TS | obtener por composición | 1423 K | directo como `Tsol` | valor activo; procedencia raw por verificar |
| L | obtener por composición | 2.286e5 J/kg | directo | valor activo; procedencia raw por verificar |
| Cp(T) | curva dependiente de T | Cp=827 constante | simplificación constante | **no implementado como curva** |
| k(T) | curva dependiente de T | k≈32.49 constante | derivada de Cp, mu y Pr constantes | **no implementado como curva** |
| rho(T) | curva dependiente de T | rho=6820 constante | no directa en C11 | usar para `rhoRef` + derivar `beta` |
| beta | derivable de rho(T) | 1.13e-4 1/K | Boussinesq | compatible con pendiente líquida de tabla B |
| fL(T) / fS(T) | curva de solidificación | generada por `solidificationMeltingSource` | no se lee tabla JMatPro | **comparación obligatoria** |
| viscosidad líquida | si está disponible | mu=5.5e-3 Pa s constante | directa como constante | procedencia raw por verificar |
| fases (austenita, grafito, sulfuros...) | termodinámica metalúrgica | no representadas individualmente | análisis fuera del CFD de equilibrio actual | **resultado JMatPro/experimental** |
| fracción de austenita primaria | relevante a objetivo de tesis | no existe como campo independiente | comparar JMatPro ↔ Newton/Fourier/microestructura | **resultado metalúrgico** |

## 6. Puerta J0 — obligatoria antes de G1

C11 permanece congelado como baseline numérico/físico de volumen fijo. **No modificar C11.**

Antes de crear el caso G1 experimental, se debe completar J0.

### J0.1 — Archivar los resultados JMatPro por composición

Para cada condición del diseño experimental:

- CE = 3.9 / 4.2;
- S = 0.05 / 0.13 wt%;
- Mn = valor controlado definido termodinámicamente;

guardar:

- composición química completa;
- tipo de cálculo usado en JMatPro;
- curvas/tablas de fases vs T;
- líquido/sólido vs T;
- austenita primaria vs T;
- grafito vs T;
- sulfuros/MnS vs T si JMatPro los predice;
- TL y TS;
- entalpía/calor latente;
- Cp(T);
- k(T);
- rho(T);
- viscosidad líquida(T), si está disponible.

No basta una captura de pantalla: debe conservarse una exportación numérica reproducible cuando JMatPro permita exportarla.

### J0.2 — Convertir JMatPro a parámetros CFD trazables

Crear para cada composición:

- `rhoRef`: valor de referencia definido;
- `beta`: ajuste de `rho(T)` en el rango líquido seleccionado;
- `TL`, `TS`, `L`;
- comparación entre `fL_JMatPro(T)` y la relación de fase de OpenFOAM;
- curvas `Cp(T)` y `k(T)` listas para implementación.

Cada parámetro debe conservar:
- archivo fuente;
- composición;
- rango de T;
- método de ajuste/promedio;
- unidades;
- error del ajuste cuando aplique.

### J0.3 — Decisión de complejidad

Orden de decisión:

1. mantener `rhoConst + beta` para G1 salvo evidencia experimental que exija contracción/feeding;
2. evaluar primero `Cp(T)`, `k(T)`, TL, TS y L reales;
3. comparar `fL_JMatPro(T)` con `alphaL_OpenFOAM(T)`;
4. solo si la discrepancia de fase es importante, decidir si basta una relación de equilibrio más fiel;
5. solo después de agotar el modelo de equilibrio considerar cinética explícita para subenfriamiento/recalescencia.

## 7. Qué significa esto para la tesis

La arquitectura científica queda:

**Composición y CE/S/Mn**  
→ **JMatPro: estabilidad de fases + Mn-S + propiedades + solidificación de equilibrio**  
→ **transformación de propiedades a parámetros CFD trazables**  
→ **OpenFOAM: CHT + convección + entalpía-porosidad**  
→ **Quick-Cup real: curvas de enfriamiento**  
→ **Newton/Fourier + comparación numérica**  
→ **microestructura y cierre metalúrgico**.

JMatPro no desaparece cuando C11 usa densidad constante. Su curva `rho(T)` se transforma en `rhoRef + beta`, mientras otras salidas se transfieren directamente o se usan para auditar la física de fase.

## 8. Evidencia que falta

En la revisión del repositorio y archivos indexados no se localizó una exportación numérica raw claramente identificada de JMatPro que permita vincular de forma verificable los valores actuales de C11 con una corrida específica de JMatPro.

Por tanto, hasta incorporar esos exports:

- no etiquetar `Cp=827`, `k≈32.49`, `TL=1473`, `TS=1423`, `L=2.286e5`, `mu=5.5e-3` o `beta=1.13e-4` como “JMatPro-derived” sin su fuente;
- sí se pueden describir como **valores actuales del modelo**;
- la coincidencia de `beta` con la pendiente líquida de la tabla B se conserva como **chequeo de consistencia**, no como prueba de procedencia.
