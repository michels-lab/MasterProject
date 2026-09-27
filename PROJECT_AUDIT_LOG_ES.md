# QuickCup-Solidification — Bitácora de auditoría del proyecto

**Idioma:** 🇪🇸 Español | [🇬🇧 English](./PROJECT_AUDIT_LOG_EN.md) | [↩ Selector de idioma](./PROJECT_AUDIT_LOG.md)

> Registro técnico persistente del proyecto de tesis de OpenFOAM de Michel Duarte.
>
> **Regla del proyecto (2026-09-24):** cada vez que se actualice la bitácora de trabajo en ChatGPT, la misma entrada técnica debe añadirse también a esta bitácora en Git. Las entradas deben distinguir evidencia verificada de interpretación y nunca presentar supuestos como hechos.

## Etiquetas de evidencia

- **[CHAT-RECOVERED]** Recuperado de conversaciones previas o del historial de auditoría del proyecto.
- **[RUN-VERIFIED]** Respaldado por salida de terminal/log preservada en el historial del proyecto.
- **[GIT-VERIFIED]** Confirmado contra archivos actualmente rastreados en el repositorio.
- **[INTERPRETATION]** Interpretación técnica; no es por sí misma un resultado observado directamente.
- **[OPEN]** Pendiente de verificación o simulación adicional.

---

# 0. Contexto del proyecto previo a la auditoría

## 2026-07-27 — Secuencia metodológica
**[CHAT-RECOVERED]**

La metodología de trabajo quedó definida como:

1. Composición química.
2. Datos termofísicos/de solidificación de JMatPro.
3. Modelo OpenFOAM.
4. Coladas reales / curvas térmicas Quick-Cup.
5. Comparación numérico–experimental y ajuste del modelo.

JMatPro debía proporcionar propiedades como ρ(T), cp(T), k(T), liquidus TL, solidus TS, calor latente y datos de fracción líquida para alimentar el modelo de OpenFOAM.

## 2026-07-28 — Arquitectura numérica inicial
**[CHAT-RECOVERED]**

La arquitectura numérica inicial se identificó como transferencia de calor conjugada (metal + molde), basada en el caso del doctor, con cambio de fase mediante el enfoque entalpía–porosidad / `solidificationMeltingSource`.

Características base recuperadas:

- Sección metálica: aproximadamente 40 × 40 mm.
- Configuración cuasi-2D con fronteras frontal/posterior `empty` y una celda en profundidad.
- Malla fina posteriormente verificada como 6400 celdas de metal + 5480 celdas de molde.
- Δx ≈ 0.5 mm en el metal.
- Tsol ≈ 1423 K.
- Tliq ≈ 1473 K.
- L = 2.286×10^5 J/kg.
- Cu = 10^5.
- `alpha1e = 0.8`.
- Capas interfaciales: espesor 2×10^-4 m y conductividad 0.1 W/(m·K).

Se identificaron desde temprano dos riesgos:

1. Las geometrías de `createZonesDict` podían superponerse.
2. `emmisivity` estaba mal escrito en una condición de frontera temprana de temperatura.

## 2026-07-29 — Casos de referencia del doctor
**[CHAT-RECOVERED]**

El material del doctor contenía un caso `bcFourier` y un caso CHT metal/molde. El modelo de tesis debía conservar:

- transferencia de calor conjugada,
- evolución de fase líquido/sólido,
- calor latente,
- resistencia de zona pastosa,
- probes térmicos,
- comparación con curvas experimentales de enfriamiento.

## 2026-09-03 — Dirección futura del modelo de recalescencia
**[CHAT-RECOVERED]**

Se definió una posible extensión futura: reemplazar una fracción líquida puramente definida por temperatura, fl(T), por una evolución cinética df/dt, conservando CHT, energía, momento, resistencia por porosidad y calor latente.

Se trató como una extensión posterior de física, no como justificación para modificar prematuramente la línea base validada.

## 2026-09-07 — Regla de interpretación de recalescencia
**[CHAT-RECOVERED]**

La auditoría estableció que un rebote numérico de temperatura, por sí solo, no es evidencia suficiente de recalescencia física.

Regla recuperada:

- Una recalescencia física debe surgir de cinética de transformación / subenfriamiento / liberación de calor latente.
- La formulación estándar de fracción de fase en OpenFOAM puede refundir material cuando la temperatura aumenta.
- `relax` dentro de `solidificationMeltingSource` es un parámetro de relajación numérica, no una constante cinética física.
- La validación debe demostrarse primero en el modelo reducido antes de migrar a un caso 3D completo.

## 2026-09-11 — Verificación dimensional de la fuente de calor latente
**[CHAT-RECOVERED]**

Para una formulación cinética futura, la fuente de calor latente se escribió como:

`S_L = -ρ L ∂f_l/∂t`

con unidades requeridas de W/m³.

Se consideró explícitamente que una ley simple fs(T) no es suficiente por sí sola para reproducir física genuina de subenfriamiento/recalescencia.

---

# 1. Bitácora numerada de auditoría del proyecto

## 2026-09-15

### AUD-001 — Versión de OpenFOAM
**[CHAT-RECOVERED] [GIT-VERIFIED current case headers]**

El entorno de trabajo se identificó como **OpenFOAM Foundation v14**, parche **20260724**.

Los archivos actuales del repositorio todavía contienen una mezcla de encabezados heredados de v13 y archivos actualizados a v14; la configuración de ejecución auditada en septiembre corresponde a Foundation v14.

**Impacto:** los comandos y el comportamiento de diccionarios deben verificarse contra Foundation v14 y no asumirse desde documentación de v13 u OpenCFD.

**Estado:** ✅ confirmado.

---

### AUD-002 — Estructura independiente del proyecto de trabajo
**[CHAT-RECOVERED]**

Se estableció una estructura de trabajo independiente bajo `QuickCup_Solidification/cleanproy` en lugar de modificar directamente el caso fuente original del doctor.

**Estado:** ✅ línea base histórica establecida.

---

### AUD-003 — Discrepancia en la documentación del tamaño de malla
**[CHAT-RECOVERED]**

Un valor documentado de **0.05 mm** no coincidía con la malla ejecutada.

La discretización real del metal correspondía aproximadamente a:

`Δx = Δy = 0.0005 m = 0.5 mm`

**Impacto:** la documentación previa exageraba la resolución espacial por un factor de 10.

**Estado:** ✅ discrepancia identificada; la documentación debe usar la malla realmente ejecutada salvo que se cambie la malla.

---

### AUD-004 — Tamaño global de malla
**[CHAT-RECOVERED]**

La malla contenía **11,880 celdas**.

Dimensiones recuperadas aproximadas del dominio:

- 54 mm en x,
- 55 mm en y,
- 10 mm en z.

**Estado:** ✅ confirmado durante la auditoría de malla.

---

### AUD-005 — Carácter cuasi-2D
**[CHAT-RECOVERED] [GIT-VERIFIED]**

El caso tiene una sola celda en la dirección z y patches frontal/posterior de tipo `empty`.

Por tanto, el problema numérico es cuasi-2D aunque el bloque tenga una profundidad geométrica finita de 10 mm.

**Estado:** ✅ confirmado.

---

### AUD-006 — cellZones preexistentes
**[CHAT-RECOVERED]**

Antes de ejecutar `createZones`, la malla ya contenía los cellZones `metal` y `mold`.

Esto motivó comprobar específicamente si `createZones` realmente estaba modificándolos.

**Estado:** ✅ investigado en AUD-012–014.

---

### AUD-007 — blockMesh en OpenFOAM 14
**[CHAT-RECOVERED]**

`blockMesh` terminó limpiamente bajo el entorno auditado de OpenFOAM 14.

**Estado:** ✅.

---

### AUD-008 — checkMesh
**[CHAT-RECOVERED]**

`checkMesh` devolvió:

`Mesh OK.`

Totales recuperados:

- 24,198 puntos,
- 47,738 caras,
- 11,880 celdas hexaédricas.

**Estado:** ✅.

---

### AUD-009 — Direcciones geométricas de solución
**[CHAT-RECOVERED]**

`checkMesh` identificó direcciones geométricas activas equivalentes a:

`(1 1 0)`

consistentes con la solución 2D prevista en x-y.

**Estado:** ✅.

---

### AUD-010 — Calidad de malla
**[CHAT-RECOVERED]**

Métricas recuperadas:

- no ortogonalidad: **0°**,
- skewness máximo: aproximadamente **6.94×10^-14**.

**Impacto:** una mala calidad geométrica de malla quedó descartada como causa probable del comportamiento numérico investigado.

**Estado:** ✅.

---

### AUD-011 — Conectividad y zonas
**[CHAT-RECOVERED]**

La malla sin dividir era una sola región conectada que contenía dos cellZones: `metal` y `mold`.

**Estado:** ✅.

---

### AUD-012 — Conteo de celdas por zona antes de createZones
**[CHAT-RECOVERED]**

Antes de `createZones`:

- `metal` = **6400 celdas**,
- `mold` = **5480 celdas**,
- total = **11,880 celdas**.

Los conteos coincidían exactamente con el total global.

**Estado:** ✅.

---

### AUD-013 — createZones no modificó los cellZones
**[CHAT-RECOVERED]**

`createZones` terminó sin error de ejecución, pero el archivo `cellZones` presentó el mismo hash MD5 antes y después:

`6b858d42fedaa8f291432cd603c1c890`

**Conclusión:** en esa prueba, el paso ejecutado de `createZones` **no** modificó los cellZones existentes.

**Estado:** ✅ verificado en la corrida histórica.

---

### AUD-014 — Riesgo de superposición en createZonesDict
**[CHAT-RECOVERED] [GIT-VERIFIED]**

`createZonesDict` definía:

- caja de metal: `(-0.001 -0.001 -0.001)` a `(0.041 0.041 0.011)`,
- caja de molde: `(-0.008 -0.016 -0.001)` a `(0.048 0.041 0.011)`.

Estas cajas se superponen geométricamente.

En el `Allrun` actualmente rastreado, `runApplication createZones` está comentado y los cellZones ya son creados por `blockMesh`, por lo que la superposición está inactiva en el flujo actual.

**Estado:** ⚠️ el diccionario sigue siendo potencialmente inseguro si se reactiva; actualmente no forma parte de `Allrun`.

---

### AUD-015 — Cambió la sintaxis de splitMeshRegions en OF14
**[CHAT-RECOVERED]**

Comando histórico:

`splitMeshRegions -cellZones metal mold`

falló en OpenFOAM 14 con:

`Wrong number of arguments, expected 0 found 1`

Al fallar la separación, el `foamMultiRun` posterior no encontraba la malla regional esperada `metal/polyMesh`; ese error posterior no era por tanto una falla independiente del solver.

Comando corregido:

`splitMeshRegions -cellZones all`

**Estado:** ✅ corregido.

---

### AUD-016 — Separación de regiones verificada
**[CHAT-RECOVERED] [GIT-VERIFIED workflow]**

`splitMeshRegions -cellZones all` funcionó y produjo:

- metal: **6400 celdas**,
- molde: **5480 celdas**,
- interfaz metal/molde: **240 caras**.

Los scripts `Allrun` actuales usan esta sintaxis corregida.

**Estado:** ✅.

---

### AUD-017 — Falla inicial de foamMultiRun al leer frontera
**[CHAT-RECOVERED]**

`foamMultiRun` falló leyendo `0/metal/T`, específicamente la entrada `metalTop/h`, con un fallo de lectura de diccionario tipo `attempt to read beyond EOF`.

La causa se rastreó a sintaxis de condición de frontera, no a la física CHT o de cambio de fase.

**Estado:** ✅ causa raíz identificada.

---

### AUD-018 — Corrección de sintaxis de externalWallHeatFluxTemperature
**[CHAT-RECOVERED]**

Entradas escritas como escalares:

`h 50;`

`Ta 300;`

se corrigieron a sintaxis de campo/función compatible con la condición de frontera auditada:

`h uniform 50;`

`Ta constant 300;`

Después de la corrección, el caso pudo ejecutarse.

**Estado:** ✅.

---

### AUD-019 — Ortografía de emissivity
**[CHAT-RECOVERED] [GIT-VERIFIED historical cases]**

Los casos tempranos contenían:

`emmisivity`

en lugar de:

`emissivity`

Los archivos de temperatura posteriores B2–B5/C2–C5 usan la ortografía corregida.

**Estado:** ✅ corregido en los casos posteriores; los archivos históricos tipo B1/C1 conservan la ortografía anterior como parte del historial.

---

### AUD-020 — Corrida base 0–300 s
**[CHAT-RECOVERED]**

Después de corregir los diccionarios, el caso base de OpenFOAM 14 corrió de 0 a **300 s** y terminó con:

`End`

Los conteos regionales permanecieron:

- metal 6400,
- molde 5480,
- interfaz 240 caras.

**Estado:** ✅ línea base ejecutable.

---

### AUD-021 — Buoyancy dentro de solidificationMelting
**[CHAT-RECOVERED]**

La inspección del código fuente confirmó que `solidificationMelting` agrega una contribución explícita de flotación térmica de la forma:

`Sb = ρref g β ΔT`

(referencia recuperada: `solidificationMelting.C`, alrededor de la línea 379 en el código inspeccionado).

**Impacto:** `beta` dentro del modelo de cambio de fase es dinámicamente importante; no es simple metadata.

**Estado:** ✅ comportamiento del código fuente identificado.

---

### AUD-022 — Identificada una posible doble ruta de buoyancy
**[CHAT-RECOVERED]**

Se identificaron dos rutas independientes hacia la ecuación de momento en la formulación original:

1. `icoTabulated → rho(T) → -gh∇rho → netForce → U`
2. `solidificationMelting → rhoRef*g*beta*ΔT → fvModels().source(rho,U) → U`

**Conclusión de ese momento:** la configuración original representaba la flotación térmica por dos rutas.

**Decisión controlada:** separar ambas formulaciones en vez de mantener las dos activas simultáneamente.

**Estado:** ✅ diagnóstico histórico establecido; posteriormente refinado por la auditoría de código fuente AUD-051.

---

### AUD-023 — Formulación B: buoyancy impulsada por densidad
**[CHAT-RECOVERED] [GIT-VERIFIED descendants]**

Caso controlado histórico: `B_icoTabulated_only`.

Configuración:

- `icoTabulated` / ρ(T) tabulada activa,
- `beta = 0` en `solidificationMeltingSource`,
- resistencia pastosa y calor latente activos,
- fuente Boussinesq del modelo de cambio de fase deshabilitada.

La prueba histórica completó 0–300 s.

Los descendientes actuales de la familia B conservan esta separación física: densidad tabulada + `beta 0`.

**Estado:** ✅.

---

## 2026-09-21

### AUD-024 — Formulación C: solo fuente Boussinesq
**[CHAT-RECOVERED] [GIT-VERIFIED descendants]**

Caso controlado histórico: `C_Boussinesq_only`.

Configuración:

- `rhoConst`,
- ρ = 6930 kg/m³,
- `beta = 1.13e-4 1/K` en `solidificationMeltingSource`,
- ruta de flotación por densidad dependiente de temperatura deshabilitada,
- fuente Boussinesq del modelo de cambio de fase activa.

El caso histórico completó 0–300 s.

Los descendientes actuales de la familia C conservan esta separación física.

**Estado:** ✅.

---

### AUD-025 — Comparación térmica inicial A/B/C
**[CHAT-RECOVERED]**

Ubicación del probe:

`(0.02 0.02 0.005)`

Comparación recuperada:

| Métrica | A | B | C |
|---|---:|---:|---:|
| T = 1473 K | ~0.00918 s | ~0.00918 s | ~0.00923 s |
| T = 1423 K | ~4.901 s | ~4.901 s | ~5.000 s |
| intervalo pastoso nominal | ~4.892 s | ~4.892 s | ~4.991 s |
| T ≈ 1422 K | ~21.45 s | ~21.50 s | ~21.85 s |
| T(300 s) | ~1144.46 K | ~1144.50 K | ~1144.96 K |

Diferencias máximas recuperadas:

- max ΔT A-B ≈ **0.22 K**,
- max ΔT A-C ≈ **2.05 K**.

**Interpretación en esa etapa:** cambiar la formulación de buoyancy tenía relativamente poco efecto sobre la curva térmica central frente al error de inicialización mucho mayor identificado después.

**Estado:** ✅ comparación histórica recuperada.

---

### AUD-026 — Colapso térmico inicial no físico
**[CHAT-RECOVERED]**

Todas las formulaciones A/B/C mostraban un enfriamiento inicial extremadamente rápido de aproximadamente:

`1500 K → 1473 K`

en cerca de **0.009 s**.

Como aparecía independientemente de la formulación de buoyancy, esta se descartó como causa primaria.

**Estado:** ✅ anomalía aislada; investigada en AUD-027.

---

### AUD-027 — Inconsistencia del estado inicial de alpha1
**[CHAT-RECOVERED]**

El estado de cambio de fase era inconsistente al inicio:

- T0 = 1500 K,
- T0 > Tliq = 1473 K,
- pero la fracción líquida se inicializaba efectivamente como αl = 0 cuando el campo `phaseChangeSource:alpha1` estaba ausente/no inicializado de forma consistente.

Razonamiento recuperado del código fuente: `solidificationMelting::update` recalcula la fracción líquida desde temperatura e introduce la corrección energética latente correspondiente.

Con los parámetros auditados:

- L = 2.286×10^5 J/kg,
- Cp = 827 J/(kg·K),
- `alpha1e = 0.8`,
- `relax = 0.1`,

la primera corrección de fracción líquida se estimó en Δα ≈ 0.02786, correspondiente a un cambio artificial de temperatura por energía latente de aproximadamente **7.70–7.72 K**.

**Estado:** ✅ causa principal del colapso inicial identificada.

---

### AUD-028 — alpha1 inicializada como líquido
**[CHAT-RECOVERED] [GIT-VERIFIED current normal cases]**

Un caso corregido inicializó:

`phaseChangeSource:alpha1 = 1.0`

para el metal inicialmente por encima del liquidus.

Resultado: desapareció el colapso artificial inicial de ~7.7 K.

Los casos normales actuales B1–B5/C1–C5 rastreados en Git contienen un campo inicial `phaseChangeSource:alpha1` con `internalField uniform 1.0`.

**Estado:** ✅ corrección adoptada.

---

### AUD-029 — Fase inicial termodinámicamente consistente
**[CHAT-RECOVERED]**

Con αl(0)=1 y T0>Tliq, la simulación ya no comienza con fracción sólida artificial por encima del liquidus.

Esto se convirtió en la convención requerida de estado inicial para los casos normales de cambio de fase.

**Estado:** ✅.

---

### AUD-030 — Sin entrada recuperada
**[CHAT-RECOVERED]**

No se encontró contenido histórico para AUD-030. La numeración de la conversación original saltó de AUD-029 a AUD-031.

El identificador se deja intencionalmente sin uso en vez de inventar retroactivamente una entrada.

**Estado:** — hueco de numeración preservado.

---

### AUD-031 — El rebote de temperatura estuvo acompañado por refusión
**[CHAT-RECOVERED]**

En el caso corregido D:

- mínimo local T ≈ 1455 K cerca de **4.90 s**,
- la temperatura subió a aproximadamente **1461.18 K** alrededor de **11.6 s**,
- durante el rebote, la fracción líquida aumentó aproximadamente **0.9283 → 0.9527**.

**Conclusión:** el rebote involucró **refusión parcial** dentro de la formulación estándar de equilibrio/relajada de `solidificationMelting`.

No debe etiquetarse automáticamente como recalescencia física.

**Estado:** ✅ interpretación corregida.

---

### AUD-032 — Comportamiento de solidificación corregido en corrida larga
**[CHAT-RECOVERED]**

Para el caso D corregido con αl(0)=1:

- cruce de liquidus 1473 K: aproximadamente **3.2506 s**,
- αl = 0.99: aproximadamente **3.5624 s**,
- cruce de temperatura solidus 1423 K: aproximadamente **104.9 s**,
- αl = 0.50: aproximadamente **207.56 s**,
- αl = 0.01: aproximadamente **227.59 s**,
- a 300 s: αl = 0,
- T(300 s) ≈ **1329.77 K**.

**Impacto:** corregir la inicialización de fase transformó la escala aparente de solidificación, de un colapso inmediato no físico a un proceso largo de cambio de fase.

**Estado:** ✅.

---

# 2. Cronología adicional recuperada después de la auditoría numerada

## 2026-09-18 — Arquitectura de validación
**[CHAT-RECOVERED]**

Se separaron conceptualmente tres niveles de modelo:

1. **Nivel 1:** fs(T) base.
2. **Nivel 2:** fs(T) informado por JMatPro/Scheil.
3. **Nivel 3:** cinético fs(T,t,ΔT,nucleación/crecimiento).

La validación no debe depender solo de RMSE. Las cantidades objetivo incluyen:

- temperaturas de liquidus / transformación,
- temperatura mínima antes del rebote,
- temperatura recuperada/de rebote,
- ΔTrec,
- dT/dt,
- tiempo de inicio,
- duración,
- evolución de fracción de fase.

Los parámetros no deben ajustarse simplemente para forzar coincidencia.

---

## 2026-09-21 — Auditoría de convergencia y loops del solver B2/C2
**[CHAT-RECOVERED] [RUN-VERIFIED historical logs]**

Se estableció una distinción de control multi-región:

- `system/fvSolution` raíz controla el acoplamiento PIMPLE global de `foamMultiRun` (`nOuterCorrectors`, `nEnergyCorrectors`),
- `system/metal/fvSolution` y `system/mold/fvSolution` controlan los solvers lineales regionales y sus correctores locales.

La configuración C2 recuperada incluía `nOuterCorrectors 1` en raíz, mientras metal tenía sus propios correctores de presión/velocidad.

Valores representativos de C2 alrededor de t≈0.1 s:

- Courant medio ≈ 0.00054–0.00057,
- Courant máximo ≈ 0.00466–0.00488,
- residual de energía reducido a ~10^-10–10^-8 en los pasos muestreados,
- residuales finales de presión alrededor de ~10^-7 después de corrección.

Evidencia recuperada al final de B2:

- energía metal aproximadamente 4.68×10^-5 → 1.42×10^-11,
- energía molde aproximadamente 3.73×10^-5 → 3.69×10^-10,
- error acumulado de continuidad aproximadamente -1.7486×10^-7,
- corrida terminó con `End`.

Un diagnóstico de flujo de B2 también encontró media volumétrica |U| de aproximadamente:

- **0.0115–0.0116 m/s** cerca de 2 s,
- **0.0079 m/s** alrededor de 6.5 s.

Se observaron picos de velocidad antes de rebotes térmicos, pero no se consideró demostrada una relación causal convectiva.

---

## 2026-09-22 — B3_docFV / C3_docFV
**[CHAT-RECOVERED] [GIT-VERIFIED configuration]**

B3/C3 se crearon como descendientes de convergencia/documentación de B2/C2 con estructura revisada de `fvSolution`.

Corrida B3 recuperada:

- 0–10 s,
- Δt = 0.001 s,
- 10,000 pasos temporales,
- ~189.5 s CPU / ~197 s wall time,
- sin fallo,
- `nOuterCorrectors=2` en raíz,
- `nEnergyCorrectors` omitido → default 1,
- aproximadamente 2 soluciones de h, 2 de e y 4 de p_rgh por timestep,
- Courant máximo ≈ **0.175912**,
- Courant final ≈ **0.0607**,
- continuidad acumulada ≈ **1.66260×10^-4**.

Corrida C3 recuperada:

- 0–10 s,
- misma estructura Δt = 0.001 s,
- ~192.6 s CPU,
- sin fallo,
- mismas 2 h / 2 e / 4 p_rgh por timestep,
- Courant máximo ≈ **0.0701958**,
- Courant final ≈ **0.0245**,
- continuidad acumulada ≈ **1.78365×10^-4**.

**Estado:** ✅ B3/C3 completados y convertidos en referencia de convergencia para las siguientes pruebas controladas.

---

## 2026-09-22 — B4_energy2 / C4_energy2
**[CHAT-RECOVERED] [GIT-VERIFIED configuration]**

B4/C4 se crearon copiando B3/C3 y cambiando el acoplamiento multi-región raíz para incluir:

`nEnergyCorrectors 2;`

manteniendo el resto de configuraciones B3/C3.

**Propósito experimental:** aislar el efecto de repetir la corrección de energía en el acoplamiento multi-región global.

**Importante:** en ese punto histórico todavía no había evidencia recuperada que estableciera resultados cuantitativos B4/C4. No debía inventarse una conclusión antes de inspeccionar logs/resultados reales.

**Estado histórico:** 🟡 configuración verificada; el resultado cuantitativo se documentó posteriormente.

---

# 3. Auditoría del repositorio actual — 2026-09-24

## Estado del repositorio
**[GIT-VERIFIED]**

Repositorio:

`realmichelduarte/QuickCup-Solidification`

Último commit auditado en ese momento:

`614ee6e186a3dfbbbec159b27c4d89015703a95f`

Mensaje:

`Add convergence tests and update buoyancy cases`

El directorio `cases_buoyancy` contenía **12 casos** y **382 archivos de caso rastreados**.

Los casos normales B1–B5/C1–C5 contenían 32 archivos rastreados cada uno; los dos casos de control contenían 31.

### Linaje de casos en ese momento

- `B1_alphaini`
- `B2_test`
- `B3_docFV`
- `B4_energy2`
- `B5_outer3`
- `B_betazero`

y

- `C1_alphaini`
- `C2_test`
- `C3_docFV`
- `C4_energy2`
- `C5_outer3`
- `C_rhoconstant`

---

## 2026-09-24 — Auditoría SHA completa de todos los casos buoyancy
**[GIT-VERIFIED]**

Todos los archivos rastreados bajo `cases_buoyancy` se compararon por ruta relativa y blob SHA.

Solo estas rutas relativas variaban entre generaciones:

1. `0/metal/T`
2. `0/metal/phaseChangeSource:alpha1` (ausente en los dos casos de control)
3. `constant/metal/fvModels`
4. `constant/metal/materials/castIron`
5. `system/controlDict`
6. `system/functions`
7. `system/fvSolution`
8. `system/metal/fvSolution`
9. `system/mold/fvSolution`

Todos los demás archivos correspondientes eran idénticos dentro de sus grupos SHA.

---

## 2026-09-24 — Separación física B/C en ese momento
**[GIT-VERIFIED]**

### Familia B

La configuración B5 preservaba:

- `equationOfState icoTabulated`,
- ρ(T) tabulada,
- `beta 0` en `solidificationMeltingSource`,
- g=(0,-9.81,0),
- modelo de momento laminar,
- coeficiente externo de transferencia de calor en `metalTop`: h=10 W/(m²·K).

### Familia C

La configuración C5 preservaba:

- `equationOfState rhoConst`,
- ρ=6930 kg/m³,
- `beta 1.13e-04` en `solidificationMeltingSource`,
- misma aceleración gravitacional,
- coeficiente externo `metalTop`: h=50 W/(m²·K).

---

## 2026-09-24 — Secuencia de convergencia en ese momento
**[GIT-VERIFIED]**

### B3/C3 — referencia
`system/fvSolution` raíz:

- `nOuterCorrectors 2`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`

### B4/C4 — experimento de corrector de energía
Misma estructura de referencia más:

- `nEnergyCorrectors 2`

### B5/C5 — experimento de outer correctors
`system/fvSolution` raíz:

- `nOuterCorrectors 3`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`

Por tanto, B5/C5 **no** eran descendientes acumulativos del cambio B4/C4. Eran un experimento independiente respecto a B3/C3: el corrector de energía volvía al valor por defecto y el acoplamiento exterior global aumentaba de 2 a 3.

Configuración regional de metal en B5/C5:

- `momentumPredictor no`
- `nOuterCorrectors 1`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 0`

---

## 2026-09-24 — Asimetría startFrom en B5/C5
**[GIT-VERIFIED]**

- B5: `startFrom latestTime;`
- C5: `startFrom startTime;`

Si ambos casos se limpian antes de ejecutarse, esta diferencia no debería cambiar una corrida fresca desde el directorio `0`. Sin limpieza, B5 puede reanudar una solución previa mientras C5 inicia explícitamente desde el tiempo configurado.

**Impacto:** debe controlarse al comparar B5 y C5.

**Estado:** ⚠️ diferencia conocida de reproducibilidad.

---

## 2026-09-24 — Configuración de probes
**[GIT-VERIFIED]**

Los casos normales B1–B5/C1–C5 contienen un `temperatureProbe` en:

`(0.02 0.02 0.005)`

que registra:

- `T`
- `phaseChangeSource:alpha1`

en cada timestep.

Los dos casos de control solo registran `T`.

---

## 2026-09-24 — Solicitud del asesor de perfiles lineales
**[CHAT-RECOVERED] [GIT-VERIFIED absence in current cases]**

El asesor pidió perfiles de velocidad/temperatura directamente mediante OpenFOAM en vez de ParaView.

En ese momento los casos actuales **todavía no contenían un function object de muestreo lineal**.

OpenFOAM v14 dispone de mecanismos de muestreo line/graph apropiados para extraer campos sobre una línea. Entre las salidas candidatas para la tesis:

- T(x,t),
- U(x,t),
- |U|(x,t),
- αl(x,t),

y relaciones derivadas como |U|=f(T) en posiciones muestreadas coincidentes.

Líneas centrales potenciales de la sección metálica 40 × 40 mm:

- horizontal: (0,0.020,0.005) → (0.040,0.020,0.005)
- vertical: (0.020,0,0.005) → (0.020,0.040,0.005)

**Estado:** 🟡 solicitado; implementación todavía no añadida en ese momento.

---

# 4. Reglas permanentes de interpretación y reproducibilidad

1. **No llamar “recalescencia” a un rebote de temperatura únicamente porque dT/dt > 0.** Revisar evolución de fase y si el modelo está solidificando o refundiendo.
2. **No mezclar cambios del modelo físico con cambios de convergencia numérica en una misma comparación controlada.**
3. **Registrar siempre nombre exacto del caso, caso padre, archivos modificados, parámetro numérico cambiado, intervalo de corrida y diagnósticos relevantes.**
4. **Para comparaciones B/C, preservar la separación de buoyancy prevista:** B = ruta impulsada por densidad; C = ruta de fuente Boussinesq.
5. **Metal líquido inicial por encima de Tliq debe inicializarse consistentemente con αl=1.**
6. **Una salida exitosa del solver no basta como validación.** Seguir Courant, residuales, continuidad, evolución energética, fracción de fase y comparación con curvas experimentales.
7. **Cada vez que se actualice esta bitácora en el hilo de trabajo de ChatGPT, actualizar también el archivo Git correspondiente.**
8. **Si una entrada antigua no puede recuperarse exactamente, marcar explícitamente la incertidumbre en vez de rellenar el hueco por inferencia.**

---

# 5. Elementos abiertos en ese punto

- [ ] Inspeccionar/recuperar resultados cuantitativos B4/C4 si sus logs todavía existen fuera de Git.
- [ ] Ejecutar/analizar B5/C5 y compararlos contra B3/C3 y B4/C4 con las mismas métricas.
- [ ] Añadir muestreo lineal nativo de OpenFOAM para U, T y αl sin cambiar la física del solver.
- [ ] Definir una pipeline reproducible para graficar perfiles velocidad/temperatura.
- [ ] Continuar validación experimental/JMatPro y mantener separada la interpretación de recalescencia respecto a la refusión de equilibrio.

---

## 2026-09-24 — AUD-033 — La comparación B/C contenía una diferencia térmica adicional
**[GIT-VERIFIED]**

Una auditoría del repositorio encontró que los descendientes B2–B5 y C2–C5 diferían no solo en la formulación de buoyancy, sino también en el coeficiente externo de transferencia de calor de `metalTop`:

- B2–B5: `h = 10 W/(m²·K)`
- C2–C5: `h = 50 W/(m²·K)`

Esta diferencia ya estaba presente en el commit inicial del repositorio (`206f9594`) y seguía presente en los archivos.

**Impacto:** si B y C pretendían ser una comparación controlada de formulaciones de buoyancy, las curvas térmicas B/C no podían atribuirse únicamente a buoyancy mientras `h` también fuera distinto.

**Acción requerida antes de interpretar:** determinar si la diferencia B/C de coeficiente de transferencia era una representación intencional de dos condiciones físicas/experimentales distintas o una variable de confusión no intencional. Hasta resolverlo, reportar B/C como comparación multiparámetro.

**Estado:** ⚠️ asunto metodológico abierto; no modificar retroactivamente los casos históricos.

---

## 2026-09-24 — AUD-034 — El cambio térmico B2 no tenía justificación de diseño recuperada
**[CHAT-RECOVERED] [GIT-VERIFIED]**

El contexto histórico confirmó que:

- `B2_test` fue creado copiando `B1_alphaini`.
- `C2_test` fue creado copiando `C1_alphaini`.
- B2/C2 se diseñaron como pruebas numéricas/de convergencia cortas (~10 s).
- Los cambios documentados posteriores se referían al timestep, por ejemplo un intento `deltaT=0.1` que falló, seguido por retorno a `deltaT=0.001`, además de la cadencia de salida.

El historial Git mostraba:

- `B1_alphaini/0/metal/T`: `metalTop h = 50 W/(m²·K)`
- `B2_test/0/metal/T`: `metalTop h = 10 W/(m²·K)`
- `C1_alphaini/0/metal/T`: `metalTop h = 50 W/(m²·K)`
- `C2_test/0/metal/T`: `metalTop h = 50 W/(m²·K)`

No se recuperó ninguna entrada de bitácora o decisión conversacional que documentara una razón física deliberada para cambiar la rama B de 50 a 10 al crear B2.

**Regla de interpretación:** el cambio B1→B2 en `h` debe tratarse como un **cambio de modelo no documentado**, no como una decisión validada. Tampoco debe asumirse accidental sin evidencia adicional.

**Impacto:** B2–B5 vs C2–C5 están térmicamente confundidos salvo que se cree una comparación controlada con `h` común.

**Estado:** ⚠️ origen no resuelto; conservar casos históricos e investigar antes de interpretar físicamente.

---

## 2026-09-24 — AUD-035 — Coeficiente convectivo común recomendado para rerun B/C controlado
**[GIT-VERIFIED] [LITERATURE-SUPPORTED] [DECISION]**

Para la comparación B/C controlada planeada, el coeficiente de convección de la superficie superior debe ser idéntico en ambas ramas.

Línea base recomendada:

`metalTop h = 10 W/(m²·K)`

Razones:

- OpenFOAM trata `h` como coeficiente convectivo externo y `emissivity` como contribución radiativa separada.
- La geometría Quick-Cup representa una pequeña muestra abierta de metal fundido expuesta al aire ambiente.
- Correlaciones de convección natural para una placa horizontal caliente orientada hacia arriba sitúan el orden esperado alrededor de ~10 W/(m²·K) para esta longitud característica; `h = 50 W/(m²·K)` sería más consistente con flujo de aire forzado significativo o con un coeficiente efectivo que agrupe otros modos de transferencia.
- Como la radiación ya se representa explícitamente con `emissivity = 0.3`, el `h` convectivo no debería inflarse para representar radiación.

**Regla de implementación:** conservar B5/C5 históricos sin cambios. Crear una nueva comparación controlada derivada de B5/C5 donde la única diferencia física intencional sea la formulación de buoyancy y ambos usen `metalTop h = 10 W/(m²·K)`.

**Estado:** ✅ elección de línea base establecida; nuevos casos controlados todavía no creados/ejecutados en ese momento.

---

## 2026-09-24 — AUD-036 — La serie controlada B/C debe repetirse con frontera térmica común
**[METHODOLOGICAL DECISION] [GIT-VERIFIED BASIS]**

Debido a que los linajes B2–B5 y C2–C5 usaban coeficientes `metalTop` diferentes (`h=10` en B y `h=50` en C), esos casos históricos no eran válidos para una comparación controlada directa de las formulaciones de buoyancy.

### Consecuencia

- B2–B5/C2–C5 históricos siguen siendo útiles como historial de desarrollo y para observaciones numéricas dentro de cada familia.
- **No** son adecuados para atribuir diferencias B-vs-C únicamente a buoyancy.
- La secuencia de convergencia debe repetirse con `metalTop h` común si la tesis requiere comparación objetiva.

### Regla de nueva serie controlada

Usar la misma frontera térmica en ambas familias:

`metalTop h = 10 W/(m²·K)`

y reproducir simétricamente:

1. referencia,
2. referencia documentada con `nOuterCorrectors=2`,
3. prueba de energía con `nEnergyCorrectors=2`,
4. prueba de outer correctors con `nOuterCorrectors=3`.

Todas las demás configuraciones deben permanecer igualadas salvo la propia formulación de buoyancy.

### Regla de preservación

No sobrescribir ni borrar los B2–B5/C2–C5 históricos. Conservarlos como registro auditable y crear un nuevo linaje controlado limpio.

**Estado:** ✅ corrección metodológica establecida; reruns pendientes en ese momento.

---

## 2026-09-24 — AUD-037 — Auditoría B/C par a par identifica la serie limpia
**[GIT-VERIFIED] [METHODOLOGICAL CORRECTION]**

Se realizó una auditoría SHA completa para:

- `B2_test ↔ C2_test`
- `B3_docFV ↔ C3_docFV`
- `B4_energy2 ↔ C4_energy2`
- `B5_outer3 ↔ C5_outer3`

### B2/C2

B2 y C2 diferían en **seis** archivos rastreados:

1. `0/metal/T`
2. `constant/metal/fvModels`
3. `constant/metal/materials/castIron`
4. `system/controlDict`
5. `system/fvSolution`
6. `system/metal/fvSolution`

Desajuste numérico importante:

- B2 raíz: `nOuterCorrectors 1`
- C2 raíz: `nOuterCorrectors 4`, `nEnergyCorrectors 1`

Por tanto, B2/C2 eran casos transicionales de desarrollo, no un par B-vs-C controlado.

### B3/C3

B3/C3 diferían solo en **cuatro** archivos:

1. `0/metal/T`
   - B3: `h = 10 W/(m²·K)`
   - C3: `h = 50 W/(m²·K)`
2. `constant/metal/fvModels`
   - B3: `beta = 0`
   - C3: `beta = 1.13e-04`
3. `constant/metal/materials/castIron`
   - B3: `icoTabulated` con densidad dependiente de temperatura
   - C3: `rhoConst = 6930 kg/m³`
4. `system/controlDict`
   - B3: `startFrom latestTime`
   - C3: `startFrom startTime`

Todos los demás archivos eran idénticos por SHA.

### B4/C4

B4/C4 diferían en exactamente los mismos cuatro archivos.

Ambos usaban:

- `nOuterCorrectors 2`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`
- `nEnergyCorrectors 2`

### B5/C5

B5/C5 diferían también en esos mismos cuatro archivos.

Ambos usaban:

- `nOuterCorrectors 3`
- `nCorrectors 2`
- `nNonOrthogonalCorrectors 1`

### Clasificación de diferencias B3–B5/C3–C5

**Diferencias físicas intencionales a conservar:**

1. `fvModels/beta`
2. `castIron/equationOfState`

**Diferencias no físicas a normalizar:**

3. `metalTop/h`
4. `controlDict/startFrom`

Para el rerun controlado:

- `metalTop h = 10 W/(m²·K)` en ambas familias.
- `startFrom startTime` en ambas.
- correr desde estado limpio.

### Plan corregido

La serie de convergencia científicamente útil comienza en B3/C3. B2/C2 permanecen como casos históricos transicionales y **no** deben recrearse como si fueran un par controlado.

Se requieren seis casos:

- B3-controlled / C3-controlled — referencia
- B4-controlled / C4-controlled — `nEnergyCorrectors=2`
- B5-controlled / C5-controlled — `nOuterCorrectors=3`

Dentro de cada par, todos los inputs deben ser idénticos excepto las dos diferencias de modelo de buoyancy.

Esta entrada reemplaza la redacción más amplia de AUD-036 que sugería repetir B2–B5/C2–C5 como una sola secuencia controlada.

**Estado:** ✅ auditoría par a par completa; construcción de casos controlados pendiente en ese momento.

---

## 2026-09-24 — AUD-038 — La rama C controlada usará rhoConst = 6820 kg/m³
**[USER DECISION] [GIT-CONTEXT VERIFIED] [SOURCE-CHECKED]**

Para la nueva serie controlada de comparación de buoyancy, la familia C usará:

`rho = 6820 kg/m³`

en vez de 6930 kg/m³.

Razón desde la definición material B:

- B usa `icoTabulated` con `rho0 = 6820 kg/m³` a `T0 = 1473 K`.
- La tabla también da aproximadamente ρ = 6820 kg/m³ cerca del liquidus (~1473 K).

Esto convierte 6820 kg/m³ en la densidad de referencia seleccionada para los nuevos casos C.

### Parámetro acoplado importante

La fuente de buoyancy de `solidificationMelting` usa:

`Sb = rhoRef * g * beta * deltaT`

por lo que `rhoRef` escala directamente la fuente Boussinesq.

Si la rama C debe ser internamente consistente con una única densidad de referencia 6820 kg/m³, `constant/metal/fvModels` también debe usar:

`rhoRef 6820;`

en lugar del valor histórico 6930.

**Estado:** ✅ `rhoConst=6820` decidido; `rhoRef=6820` recomendado y posteriormente implementado.

---

## 2026-09-24 — AUD-039 — Serie controlada de comparación de buoyancy creada
**[GIT-VERIFIED] [IMPLEMENTED]**

Se creó una nueva familia fuera de `cases_buoyancy/`:

`cases_controlled_buoyancy/`

Los casos históricos permanecieron sin cambios.

### Casos controlados

- `B3_reference` — derivado de `B3_docFV`
- `C3_reference` — derivado de `C3_docFV`
- `B4_energy2` — derivado de `B4_energy2`
- `C4_energy2` — derivado de `C4_energy2`
- `B5_outer3` — derivado de `B5_outer3`
- `C5_outer3` — derivado de `C5_outer3`

### Normalizaciones aplicadas

1. `metalTop h = 10 W/(m²·K)`
2. `startFrom startTime`
3. Los ajustes numéricos históricos de los experimentos 3/4/5 se preservaron.

### Rama C

- `equationOfState rhoConst`
- `rho = 6820 kg/m³`
- `beta = 1.13e-04 1/K`
- `rhoRef = 6820 kg/m³`

### Rama B

- `equationOfState icoTabulated`
- densidad dependiente de temperatura
- `beta = 0` en `solidificationMeltingSource`

### Regla de reproducibilidad

Los pares 3/4/5 deben ser idénticos en todos los inputs rastreados excepto:

- `constant/metal/fvModels`
- `constant/metal/materials/castIron`

**Estado:** ✅ serie controlada creada; auditoría SHA posterior requerida.

---

## 2026-09-24 — AUD-040 — La serie controlada pasa la verificación SHA par a par
**[GIT-VERIFIED] [VALIDATED INPUT SET]**

Se auditó cada par:

- `B3_reference ↔ C3_reference`
- `B4_energy2 ↔ C4_energy2`
- `B5_outer3 ↔ C5_outer3`

En los tres pares, los únicos archivos diferentes fueron:

1. `constant/metal/fvModels`
2. `constant/metal/materials/castIron`

### Ajustes comunes verificados

Ambas ramas usan:

- `metalTop h = 10 W/(m²·K)`
- `startFrom startTime`

### Rama C verificada

- `rhoConst`
- `rho = 6820 kg/m³`
- `beta = 1.13e-04 1/K`
- `rhoRef = 6820 kg/m³`

### Rama B verificada

- `icoTabulated`
- densidad dependiente de temperatura
- `beta = 0`

### Conclusión

La serie 3/4/5 quedó adecuada para una comparación B-vs-C objetiva porque cada par era idéntico salvo los archivos que implementan las dos formulaciones de buoyancy/densidad.

**Estado:** ✅ auditoría del set de inputs aprobada.

---

## 2026-09-24 — AUD-041 — Regla de sincronización README + Audit Log
**[PROCESS RULE] [IMPLEMENTED]**

La documentación de la serie controlada adoptó una regla de dos documentos:

1. La bitácora preserva la historia cronológica: qué cambió, por qué, evidencia, impacto y estado.
2. `cases_controlled_buoyancy/README.md` describe la configuración y flujo actualmente aceptados.

Cada cambio relevante en física, propiedades, fronteras, numerics, malla, timestep, probes, postproceso, nomenclatura o metodología de comparación debe reflejarse en ambos.

El README se amplió con:

- propósito de la serie B/C limpia,
- matriz de casos,
- configuraciones comunes,
- formulaciones B y C,
- `h = 10 W/(m²·K)`,
- `startFrom startTime`,
- `rho = rhoRef = 6820 kg/m³` en C,
- validación SHA,
- orden recomendado de ejecución,
- cantidades a comparar,
- trabajo planeado de perfiles,
- regla de mantenimiento.

**Estado:** ✅ regla activa.

---

## 2026-09-24 — AUD-042 — Los logs controlados pasan a versionarse
**[PROCESS RULE] [IMPLEMENTED]**

Se refinó la política de logs para simulaciones controladas.

Los logs generales seguían ignorados por defecto, pero esta ruta pasó a rastrearse explícitamente:

`cases_controlled_buoyancy/**/log.foamMultiRun`

### Razón

El log primario de `foamMultiRun` forma parte de la evidencia numérica porque contiene Courant, residuals, continuidad, progreso del solver y tiempos.

Los directorios temporales calculados, mallas generadas, logs generales y otros outputs grandes permanecían ignorados salvo selección deliberada.

**Estado:** ✅ `log.foamMultiRun` controlado incorporado al registro científico versionado.

---

## 2026-09-24 — AUD-043 — Logs de simulación rastreados por defecto
**[PROCESS RULE] [IMPLEMENTED]**

La política de retención se amplió.

Política anterior:

- logs generales ignorados,
- solo `cases_controlled_buoyancy/**/log.foamMultiRun` exento.

Política actual:

- logs de simulación y runtime **no se ignoran por defecto**,
- se eliminaron reglas amplias como `**/log.*`, `**/*.log` y `**/nohup.out`,
- los logs se consideran parte de la evidencia numérica/científica,
- logs temporales de editor como `.vscode/*.log` pueden seguir ignorados.

Directorios de tiempos calculados, mallas, postProcessing, media y builds siguen ignorados salvo selección deliberada.

**Impacto:** futuros logs OpenFOAM pueden añadirse a Git normalmente sin `git add -f`.

**Estado:** ✅ regla activa.

---

## 2026-09-24 — AUD-044 — Logs B3/C3 controlados guardados
**[GIT-VERIFIED] [RUN ARTIFACTS PRESERVED]**

Se ejecutaron localmente `B3_reference` y `C3_reference` y sus logs primarios se subieron a Git.

Archivos:

- `cases_controlled_buoyancy/B3_reference/log.foamMultiRun`
- `cases_controlled_buoyancy/C3_reference/log.foamMultiRun`

Commit:

`d6c307c8ac62755bf103fc15f4505874904c9bb9`

Tamaños aproximados:

- B3: 19.61 MB
- C3: 19.61 MB

Todavía no se registró interpretación cuantitativa en esa entrada. Debían extraerse Courant, residuals, continuidad, tiempo, temperatura y fracción de fase.

**Estado:** ✅ artefactos preservados; análisis cuantitativo pendiente en ese punto.

---

## 2026-09-24 — AUD-045 — Análisis de solver logs B3/C3
**[RUN-VERIFIED] [GIT-VERIFIED]**

Los `log.foamMultiRun` de `B3_reference` y `C3_reference` fueron analizados sobre los 0–10 s completos.

Ambos:

- ejecutaron 10,000 pasos con `deltaT = 0.001 s`,
- alcanzaron `Time = 10`,
- terminaron con `End`,
- sin `FOAM FATAL`,
- sin `WARNING`.

### Courant

B3:

- pico `Co_max = 0.175912` cerca de t = 0.283 s,
- Co medio en ese instante = 0.00742715,
- último `Co_max = 0.0606638`.

C3:

- pico `Co_max = 0.0700709` cerca de t = 2.510 s,
- Co medio = 0.0205809,
- último `Co_max = 0.0241928`.

Ambos picos están por debajo de `maxCo = 0.25`; como `adjustTimeStep no`, ese valor era umbral de comparación y no controlador activo.

### Continuidad

B3:

- máximo absoluto acumulado ≈ 1.70032e-4,
- final = 1.66260e-4.

C3:

- máximo absoluto acumulado ≈ 1.78360e-4,
- final = 1.78349e-4.

En la corrección final:

- B3: ~-1.14209e-11,
- C3: ~1.25471e-13.

### Residuales finales a 10 s

B3:

- h metal: 8.73216e-11,
- e molde: 3.73694e-10,
- p_rgh final: 3.88108e-8.

C3:

- h metal: 2.46231e-11,
- e molde: 3.76994e-10,
- p_rgh final: 2.68792e-8.

Después del transitorio inicial t≥0.1 s, los máximos residuales finales de las ecuaciones térmicas permanecieron por debajo de aproximadamente:

- B3: 4.27e-7 para h metal, 6.03e-8 para e molde,
- C3: 3.76e-7 para h metal, 6.01e-8 para e molde.

### Costo computacional

B3:

- ExecutionTime = 249.556 s,
- ClockTime = 258 s.

C3:

- ExecutionTime = 224.372 s,
- ClockTime = 225 s.

En estas corridas concretas, B3 consumió ~11.2% más CPU y ~14.7% más wall time. Es descriptivo de estas ejecuciones y no debe generalizarse sin repeticiones/control de carga.

### Límite interpretativo

Los logs demuestran que ambos casos completaron numéricamente sin fallo. Por sí solos no establecen la diferencia térmica/de fase.

Se requerían los probes de:

- T(t) central,
- `phaseChangeSource:alpha1(t)` central.

**Estado:** ✅ auditoría de solver logs completa; comparación térmica/de fase pendiente en ese punto.

---

## 2026-09-24 — AUD-045 — Corridas B3/C3 revisadas cuantitativamente
**[RUN-VERIFIED] [GIT-VERIFIED]**

Se revisaron los logs versionados del par controlado.

### B3_reference

- CPU: **249.556 s**
- Clock: **258 s**
- Courant máximo: **0.175912**
- Courant final: media **0.0154644**, máximo **0.0606638**
- continuidad acumulada final: **1.66260e-4**
- h metal final representativo: 4.54417e-05 → 9.91429e-09
- segundo solve h final: 8.43592e-08 → 8.73216e-11
- p_rgh final: **3.88108e-08**

### C3_reference

- CPU: **224.372 s**
- Clock: **225 s**
- Courant máximo: **0.0700709**
- Courant final: media **0.00934688**, máximo **0.0241928**
- continuidad acumulada final: **1.78349e-4**
- h metal final: 5.6893e-05 → 9.49871e-09
- segundo solve h final: 3.18791e-08 → 2.46231e-11
- p_rgh final: **2.68792e-08**

### Comparación

B3 usó ~11.2% más CPU que C3 y alcanzó un Courant máximo ~2.51× mayor.

Ambos permanecieron cómodamente por debajo de Courant 1 y terminaron sin divergencia.

Los errores acumulados de continuidad son del mismo orden (~1e-4), con C3 ligeramente mayor.

**Límite:** un Courant mayor en B3 es compatible con velocidades más altas en alguna zona, pero el log no establece la topología espacial ni su importancia térmica.

**Estado:** ✅ comparación a nivel solver completa.

---

## 2026-09-24 — AUD-046 — Análisis de probes centrales B3/C3
**[RUN-VERIFIED] [GIT-VERIFIED]**

Se compararon directamente:

- `postProcessing/metal/temperatureProbe/0/T`
- `postProcessing/metal/temperatureProbe/0/phaseChangeSource:alpha1`

Cada archivo contiene 10,001 muestras entre 0 y 10 s con Δt=0.001 s en `(0.02 0.02 0.005) m`.

### Métricas principales

B3:
- primer cruce descendente de liquidus 1473 K: **6.666 s**,
- primera desviación de `alpha1` respecto a 1: **6.668 s**,
- `alpha1 = 0.99`: ~**9.619 s**,
- T centro a 10 s: **1467.45 K**,
- `alpha1` final: **0.978184**.

C3:
- primer cruce descendente de 1473 K: **3.386 s**,
- primera desviación de `alpha1`: **3.388 s**,
- `alpha1 = 0.99`: ~**3.654 s**,
- T mínima central: **1456.25 K a 4.822 s**,
- `alpha1` mínimo: **0.932983 a 4.878 s**,
- T final: **1461.60 K**,
- `alpha1` final: **0.954394**.

Diferencias:

- C3 alcanza liquidus ~**3.280 s antes**.
- máxima diferencia absoluta de T central: ~**33.42 K a 4.644 s**.
- máxima diferencia absoluta de fracción líquida: ~**0.067017 a 4.878 s**.
- a 10 s, B3 está **5.85 K más caliente** y tiene ~**0.02379** más fracción líquida.

### Comportamiento no monótono

C3 presenta rebote:

- T: 1456.25 K a 4.822 s → 1461.60 K a 10 s (**+5.35 K**),
- alpha1: 0.932983 a 4.878 s → 0.954394 a 10 s (**+0.021411**).

El aumento simultáneo de T y fracción líquida es evidencia directa de **refusión local en el modelo numérico**.

B3 presenta una reversión menor:

- primer cruce descendente liquidus: 6.666 s,
- mínimo local inicial `alpha1 = 0.997042` a 7.045 s,
- retorno a `alpha1 = 1.0` a 7.460 s,
- cruce ascendente de 1473 K ~7.447 s,
- segundo cruce descendente ~9.069 s.

### Límite interpretativo

La comparación demuestra historias térmicas y de fase materialmente distintas aunque solver y fronteras estén controlados.

Los rebotes **no deben llamarse recalescencia física** a partir de estos datos. La formulación actual puede producir transporte convectivo y refusión local. Hace falta analizar perfiles/campo de velocidad y comparar con curvas experimentales.

**Estado:** ✅ comparación solver + térmica/fase completa; 🟡 validación experimental aún pendiente.

---

## 2026-09-24 — AUD-047 — Prueba B4/C4 de nEnergyCorrectors
**[RUN-VERIFIED] [GIT-VERIFIED]**

Los casos `B4_energy2` y `C4_energy2` y sus probes se compararon contra B3/C3. El único cambio intencional era aumentar `nEnergyCorrectors` raíz de 1 a 2.

Ambos:

- llegaron a 10 s,
- terminaron con `End`,
- sin `FOAM FATAL`,
- sin warnings.

B4:
- Co máximo = **0.176643** cerca de 0.290 s,
- Co final máximo = **0.0602696**,
- continuidad final = **1.67018e-4**,
- ExecutionTime = **240.667 s**,
- ClockTime = **248 s**.

C4:
- Co máximo = **0.0700709** cerca de 2.510 s,
- Co final máximo = **0.0241928**,
- continuidad final = **1.78349e-4**,
- ExecutionTime = **225.476 s**,
- ClockTime = **226 s**.

El aumento duplicó los solves de h metal y e molde de 20,000 a 40,000.

### Sensibilidad central

B3 vs B4:
- max |ΔT| = **0.19 K**,
- max |Δalpha_l| = **5.22e-4**,
- liquidus: 6.666 s → **6.678 s**,
- alpha_l=0.99: 9.619 s → **9.636 s**.

C3 vs C4:
- max |ΔT| = **0.01 K**,
- max |Δalpha_l| = **1.0e-6**,
- liquidus = **3.386 s** en ambos,
- alpha_l=0.99 = **3.654 s** en ambos,
- T mínima = **1456.25 K a 4.822 s** en ambos,
- alpha_l mínimo = **0.932983 a 4.878 s** en ambos.

B4 vs C4 conserva ~**33.42 K** de diferencia máxima central y ~**0.067017** en fracción líquida.

### Interpretación

Duplicar `nEnergyCorrectors` no cambia materialmente la solución térmica/de fase central en 0–10 s. La diferencia B-vs-C y la refusión/rebote de C persisten.

Los tiempos de una sola corrida no son benchmark estricto; B4 incluso fue ligeramente más rápido que B3 pese a más solves, mostrando variabilidad de máquina.

**Estado:** ✅ prueba completa; la solución B3/C3 es robusta frente a `nEnergyCorrectors=2`.

---

## 2026-09-24 — AUD-047 — Verificación redundante de convergencia B4/C4
**[RUN-VERIFIED] [GIT-VERIFIED]**

El conteo de logs confirmó:

- B3/C3: 20,000 solves de h metal y 20,000 de e molde,
- B4/C4: 40,000 solves de h y 40,000 de e,
- los cuatro: 40,000 solves de p_rgh.

Esto confirma que `nEnergyCorrectors=2` estuvo activo.

Métricas y conclusiones coincidieron con la entrada anterior: cambios centrales de temperatura ≤0.19 K en B y ~0.01 K en C, sin modificar la diferencia cualitativa B/C.

**Estado:** ✅ comprobación redundante preservada en el historial original.

---

## 2026-09-24 — AUD-047 — Comparación controlada B4/C4
**[RUN-VERIFIED] [GIT-VERIFIED]**

La comparación final B4/C4 preservó la misma conclusión:

- B4 peak Co **0.176643**, ExecutionTime **240.667 s**.
- C4 peak Co **0.0700709**, ExecutionTime **225.476 s**.
- B3→B4 max ΔT central ~**0.19 K**.
- C3→C4 max ΔT central ~**0.01 K**.
- B4 vs C4 max separación central ~**33.42 K**.
- C4 conserva Tmín=1456.25 K a 4.822 s y alpha1mín=0.932983 a 4.878 s, seguido por calentamiento/refusión.

**Conclusión:** el corrector extra de energía tiene impacto despreciable en la historia central; no explica la separación B/C.

**Estado:** ✅ comparación completa.

---

## 2026-09-24 — AUD-048 — Convergencia B5/C5 con nOuterCorrectors=3 y conclusión 3/4/5
**[RUN-VERIFIED] [GIT-VERIFIED]**

`B5_outer3` y `C5_outer3` se compararon contra B3/C3 y B4/C4.

Ambos:

- completaron 10,000 pasos hasta 10 s,
- terminaron con `End`,
- sin `FOAM FATAL`,
- sin warnings,
- ejecutaron 30,000 solves de h metal y 30,000 de e molde, confirmando el tercer outer correction.

### Solver

B5:
- peak Co = **0.175874 a 0.284 s**,
- Co final medio **0.0154835**, máximo **0.0602937**,
- máximo absoluto continuidad acumulada ~**1.70120e-4**,
- continuidad final **1.65205e-4**,
- h final **4.72045e-12**,
- e final **5.80792e-10**,
- p_rgh final **9.77911e-8**,
- ExecutionTime **291.137 s**,
- ClockTime **298 s**.

C5:
- peak Co = **0.0700712 a 2.510 s**,
- Co final medio **0.0093466**, máximo **0.0241931**,
- máximo absoluto continuidad acumulada ~**1.78180e-4**,
- continuidad final **1.78172e-4**,
- h final **1.19093e-10**,
- e final **5.78841e-10**,
- p_rgh final **5.2433e-8**,
- ExecutionTime **272.125 s**,
- ClockTime **273 s**.

### Sensibilidad térmica/fase

B3→B5:
- max |ΔT| **0.22 K** a 7.443 s,
- max |Δalpha_l| **6.48e-4**,
- liquidus 6.666 → **6.683 s**,
- alpha_l=0.99 9.619 → **9.633 s**,
- T final 1467.45 → **1467.52 K**,
- alpha1 final 0.978184 → **0.978433**.

C3→C5:
- max |ΔT| **0.01 K**,
- max |Δalpha_l| **4e-6**,
- liquidus **3.386 s**,
- alpha_l=0.99 ~**3.654 s**,
- Tmín **1456.25 K a 4.822 s**,
- alpha_lmín **0.932984 a 4.876 s**,
- T final **1461.60 K**,
- alpha1 final **0.954397**.

B5 vs C5:
- max diferencia T central **33.42 K**,
- max diferencia fracción líquida ~**0.067016**.

### Conclusión de convergencia 3/4/5

1. B4/C4 (`nEnergyCorrectors=2`) cambia de forma despreciable la solución central frente a B3/C3.
2. B5/C5 (`nOuterCorrectors=3`) también cambia de forma despreciable la solución central.
3. B5/C5 requiere más solves y en estas corridas ~**16.7%** más CPU en B y ~**21.3%** más en C frente a B3/C3.
4. La gran diferencia B-vs-C se reproduce en las tres configuraciones.

Para los cálculos controlados 0–10 s, B3/C3 queda aceptado como baseline numérica eficiente.

Esto es una conclusión de sensibilidad numérica, no una selección física de la formulación B o C.

**Estado:** ✅ serie 3/4/5 de sensibilidad numérica completa.

---

## 2026-09-24 — AUD-049 — Perfiles horizontales de OpenFOAM configurados
**[CONFIG-VERIFIED] [GIT-VERIFIED]**

Se añadió un function object de muestreo lineal común en `system/functions` de los seis casos controlados 3/4/5.

Se usa el objeto `sets` de OpenFOAM v14 con sets `lineUniform`, mecanismo subyacente de `graphUniform`.

### Geometría

Ambas líneas están en el plano medio del metal, z=0.005 m, y corren horizontalmente en x de 0.00025 a 0.03975 m.

1. `line_y20mm`
   - y=0.020 m,
   - altura geométrica central del metal.

2. `line_y30mm`
   - y=0.030 m,
   - 10 mm debajo de la superficie superior y=0.040 m.

Cada línea usa 80 puntos uniformes y `axis x`. Con la malla controlada de 80 celdas / 40 mm, el espaciamiento entre centros es 0.5 mm.

### Campos

- `U`: contiene Ux, Uy, Uz,
- `T`,
- `phaseChangeSource:alpha1`.

La magnitud se deriva en análisis como:

`|U| = sqrt(Ux² + Uy² + Uz²)`

para conservar la información direccional.

### Salida

- región: `metal`,
- interpolación: `cellPoint`,
- formato: `raw`,
- `writeControl writeTime`.

Es una adición de postproceso únicamente; no cambia malla, propiedades, fronteras, modelo, timestep ni correctores.

**Estado:** ✅ configuración común comprometida; extracción pendiente en ese punto.

---

## 2026-09-25 — AUD-050 — Ejecución de perfiles y análisis espacial B3/C3
**[RUN-VERIFIED] [GIT-VERIFIED]**

Se ejecutaron los perfiles horizontales para todos los tiempos guardados de 0 a 10 s en los seis casos.

Cada caso generó:

- 101 tiempos,
- 2 líneas por tiempo,
- 202 archivos por caso.

Total: **1,212 archivos de perfil**.

Columnas:

- x,
- Ux,
- Uy,
- Uz,
- T,
- `phaseChangeSource:alpha1`.

Uz observado es cero en los perfiles inspeccionados, consistente con la configuración cuasi-2D.

### Reversión de flujo central B3/C3

En x≈19.75 mm, B y C presentan direcciones verticales opuestas durante el intervalo temprano de cambio de fase.

A 3.4 s:
- 20 mm: B3 Uy = -0.01437 m/s; C3 Uy = +0.00962 m/s.
- 30 mm: B3 Uy = -0.02419 m/s; C3 Uy = +0.00357 m/s.

A 4.8 s:
- 20 mm: B3 Uy = -0.01104 m/s; C3 Uy = +0.01821 m/s.
- 30 mm: B3 Uy = -0.01492 m/s; C3 Uy = +0.00299 m/s.

B3 tiene flujo central descendente en ambas alturas; C3 flujo central ascendente.

### Estratificación térmica vertical

A 4.8 s y x≈19.75 mm:

- B3: T(20 mm)=1489.50 K; T(30 mm)=1485.99 K.
- C3: T(20 mm)=1456.46 K; T(30 mm)=1483.24 K.

C3 muestra ~26.78 K de separación vertical, frente a ~3.51 K en B3 y con signo opuesto.

A ese tiempo, la máxima diferencia B3/C3 en la línea 20 mm es ~33.05 K cerca de x≈20.25 mm.

### Diferencias de Uy

Valores representativos máximos |ΔUy|:

- 3.4 s, 20 mm: ~0.02399 m/s,
- 3.4 s, 30 mm: ~0.02776 m/s,
- 4.8 s, 20 mm: ~0.02925 m/s,
- 6.7 s, 30 mm: ~0.02949 m/s,
- 10 s, 30 mm: ~0.02916 m/s.

La formulación B puede mostrar velocidades locales/superiores mayores aunque C enfríe y solidifique el centro antes. Por tanto, Courant global o velocidad pico no bastan como proxy del transporte térmico central.

### Convergencia espacial

A perfiles representativos de 4.8 y 10 s:

- C3/C4/C5 son prácticamente coincidentes a la precisión muestreada, con diferencias T ≤ ~0.01 K y velocidad generalmente ~1e-6 m/s o menores.
- B3/B4/B5 tienen sensibilidad espacial pequeña pero medible: diferencias T hasta ~0.6–0.7 K y Uy hasta ~0.0015 m/s.
- Estas diferencias son mucho menores que B-vs-C y no cambian la estructura cualitativa de circulación.

### Interpretación

La diferencia térmica B-vs-C está asociada con una topología de flujo y redistribución vertical de calor materialmente diferente, no simplemente con mayor o menor magnitud escalar de velocidad.

C desarrolla flujo central ascendente persistente y fuerte estratificación vertical temprana, consistente con una ruta convectiva distinta que puede explicar por qué el centro alcanza liquidus y cambio de fase antes.

Es una interpretación mecanística numérica, no validación física.

**Estado:** ✅ perfiles y análisis espacial inicial completos; 🟡 figuras de tesis y validación experimental pendientes.

---

## 2026-09-25 — AUD-051 — Auditoría de implementación de buoyancy a nivel código fuente
**[SOURCE-VERIFIED] [INTERPRETATION-CORRECTION]**

Se auditó el código fuente después de observar grandes diferencias B-vs-C.

### Implementación B verificada

`B3_reference/constant/metal/materials/castIron` usa:

- `equationOfState icoTabulated`,
- tabla de densidad dependiente de T,
- de 6900 kg/m³ a 1423.15 K a 6820 kg/m³ a 1473.15 K.

`B3_reference/constant/metal/fvModels` usa:

- `beta 0`,
- `rhoRef 6930`.

La corrección de presión buoyant de Foundation v14 para p_rgh incluye explícitamente:

`ghGradRhof = -ghf*fvc::snGrad(rho)*mesh.magSf()`

y añade esa contribución de gradiente de densidad a la corrección presión/velocidad.

Por tanto, B **no es un caso sin buoyancy**. La flotación surge del campo de densidad dependiente de temperatura y la formulación nativa p_rgh. `beta=0` solo desactiva la fuente explícita adicional de `solidificationMelting`.

### Implementación C verificada

`C3_reference/constant/metal/materials/castIron` usa:

- `rhoConst`,
- ρ = 6820 kg/m³.

`C3_reference/constant/metal/fvModels` usa:

- `beta = 1.13e-4 1/K`,
- `rhoRef = 6820 kg/m³`.

Con densidad constante, el término nativo `-ghf*snGrad(rho)` se anula salvo roundoff.

`solidificationMelting` añade:

`Sb = rhoRef*g*beta*deltaT`

Por tanto, C **no es doble buoyancy**: su flotación térmica proviene de la fuente explícita mientras la ruta nativa está inactiva.

### Por qué B y C difieren tanto

No son formulaciones equivalentes.

La tabla B da una expansión térmica efectiva variable. Entre 1423.15–1473.15 K:

- ρ disminuye 80 kg/m³ en 50 K,
- beta efectivo ≈ 2.3e-4 1/K,

aproximadamente el doble de C.

Entre 1473.15–1573.15 K:

- ρ disminuye 80 kg/m³ en 100 K,
- beta efectivo ≈ 1.2e-4 1/K,

más cercano a C.

Además, la fuente C usa el `deltaT` interno del modelo de fase, definido respecto a la relación de equilibrio vigente y dependiente de fracción líquida; no es simplemente un término Boussinesq global lineal T-Tref.

### Impacto

Las diferencias B-vs-C siguen siendo numéricamente reales, pero deben interpretarse como consecuencias de **dos modelos distintos de buoyancy**, no como “sin buoyancy” en B o “doble buoyancy” en C.

La selección física requiere comparación con curvas experimentales y comportamiento termofísico esperado.

**Estado:** ✅ mecanismo verificado en código v14; 🟡 selección física pendiente.

---

## 2026-09-25 — AUD-052 — Auditoría de divergencia de configuración posterior a sesión con asesor
**[CONFIGURATION-AUDIT] [TRACEABILITY] [CONTROLLED-SERIES]**

Los seis casos controlados se reauditaron después de sincronizar cambios locales hechos durante/después de la sesión con el asesor.

### Matriz encontrada

| Caso | nOuterCorrectors | nEnergyCorrectors | adjustTimeStep | EOS metal | beta |
|---|---:|---:|---|---|---:|
| B3_reference | 2 | default (1) | **yes** | icoTabulated | 0 |
| C3_reference | 2 | default (1) | no | rhoConst | 1.13e-4 |
| B4_energy2 | 2 | 2 | no | icoTabulated | 0 |
| C4_energy2 | 2 | 2 | no | rhoConst | 1.13e-4 |
| B5_outer3 | 3 | default (1) | no | icoTabulated | 0 |
| C5_outer3 | 3 | default (1) | **yes** | rhoConst | **0** |

### B3 ya no correspondía a la referencia original fija

`B3_reference/system/controlDict` tenía `adjustTimeStep yes`.

Los nuevos logs B3 mostraban 2811 tiempos reportados, primero 0.0012 s y final 9.999798 s; `logs/deltaT_0` confirmaba timestep adaptativo.

Por tanto, esos outputs eran de un rerun adaptativo y no del dataset B3 fijo usado en la comparación anterior. Los datos originales seguían recuperables desde Git.

### C5 actual tampoco coincidía con el C5 analizado

El C5 analizado previamente había usado:

- `rhoConst = 6820`,
- `beta = 1.13e-4`,
- `adjustTimeStep no`,
- `nOuterCorrectors = 3`.

La configuración encontrada después tenía:

- `rhoConst = 6820`,
- `beta = 0`,
- `adjustTimeStep yes`,
- `nOuterCorrectors = 3`.

Con `rhoConst` y `beta=0`, la buoyancy térmica quedaba desactivada: era otro problema físico.

### Cambio fvSolution de molde en B3

Solo B3 tenía explícitamente:

```text
"(h|e)Final"
{
    solver          PCG;
    preconditioner  DIC;
    tolerance       1e-06;
    relTol          0;
}
```

mientras los otros cinco heredaban `$h; relTol 0;`.

Las plantillas CHT de Foundation v14 usan esta última forma. El bloque explícito B3 reproduce los mismos valores base con `relTol 0`; debe tratarse como reexpresión explícita, no como variable numérica significativa salvo demostración futura.

### Implicación

No crear el siguiente caso copiando ciegamente C5 actual.

Debe preservarse:

- B: `icoTabulated`, `beta=0`.
- C: `rhoConst=6820`, `beta=1.13e-4`.

y cambiar una variable numérica a la vez.

Un caso intencional sin buoyancy (`rhoConst + beta=0`) debe recibir nombre propio si se estudia.

**Estado:** ✅ divergencia identificada; definición siguiente pendiente.

---

## 2026-09-25 — AUD-053 — Definición V6/V7 y flujo foamLog
**[CONFIGURATION-RESTORE] [CONTROLLED-SERIES] [POST-PROCESSING]**

### Restauración histórica

Se eliminaron cambios temporales de la sesión del asesor:

- B3: `adjustTimeStep` restaurado a `no`; solver final del molde restaurado a `$h; relTol 0;`.
- C5: `adjustTimeStep` restaurado a `no`; `beta` restaurado a `1.13e-04 1/K`.

Los datos B3 adaptativos fueron sustituidos por outputs B3 fijos previos del historial. El set adaptativo `logs/` se eliminó.

Los logs `foamLog` históricos C5 se restauraron desde Git después de haberse eliminado accidentalmente durante sincronización.

### V6 controlado

Se crearon `B6_fvSolution` y `C6_fvSolution` desde V5 limpio.

Cambio controlado: solver final de energía del molde escrito explícitamente como el bloque PCG/DIC/tolerance/relTol mostrado arriba.

Todo lo demás permanecía V5.

### V7 controlado

Se crearon `B7_outer4` y `C7_outer4` desde V5 limpio.

Cambio:

`nOuterCorrectors 4;`

### foamLog estandarizado

Los casos controlados V3–V7 ejecutarían:

`foamLog log.foamMultiRun`

automáticamente desde `Allrun` tras terminar el solver.

Antes de parsear se eliminan `logs/` y `log.foamLog` anteriores para no mezclar diagnósticos.

`Allclean` elimina `logs/`.

**Estado:** ✅ restauración realizada; ✅ V6/V7 definidos inicialmente; ✅ foamLog estandarizado.

---

## 2026-09-25 — AUD-054 — Eliminación de outputs foamLog restaurados y obsoletos de C5
**[CORRECTION] [POST-PROCESSING] [TRACEABILITY]**

El directorio histórico `C5_outer3/logs/` restaurado en AUD-053 fue eliminado porque era inconsistente con el nuevo flujo, que requiere regenerar `logs/` desde el `log.foamMultiRun` rastreado.

El solver log fuente `C5_outer3/log.foamMultiRun` permaneció intacto.

Los nuevos `logs/` deben producirse con:

`foamLog log.foamMultiRun`

**Estado:** ✅ logs parseados obsoletos eliminados; solver log fuente conservado.

---

## 2026-09-25 — AUD-055 — Activación temporal de timestep adaptativo en V7
**[CONFIGURATION-CHANGE] [V7] [TIME-STEPPING]**

Por decisión del usuario, ambos V7 combinaron temporalmente:

- `nOuterCorrectors = 4`
- `adjustTimeStep = yes`

con:

- `deltaT = 0.001 s` inicial,
- `maxCo = 0.25`,
- `maxDeltaT = 0.1 s`.

Esto aplicaba a B7/C7 sin cambiar la física B/C.

Al modificar dos variables frente a V5, V7 dejaba de ser una prueba de una sola variable.

**Estado:** ✅ cambio transitorio documentado; posteriormente sustituido por AUD-056.

---

## 2026-09-25 — AUD-056 — Diseño final: V6 adaptive timestep y V7 outer correctors
**[CONFIGURATION-CHANGE] [CONTROLLED-SERIES] [SUPERSEDES-AUD-055]**

El diseño V6/V7 se revisó para conservar una variable numérica por comparación.

### V6 — timestep adaptativo

Los anteriores `B6_fvSolution` y `C6_fvSolution` se eliminaron antes de ejecución y se reemplazaron por:

- `B6_adaptiveDt`
- `C6_adaptiveDt`

copiados de V5 limpio y cambiando únicamente:

`adjustTimeStep yes;`

Conservan:

- `nOuterCorrectors = 3`
- `deltaT inicial = 0.001 s`
- `maxCo = 0.25`
- `maxDeltaT = 0.1 s`

La física B/C no cambia.

### V7 — sensibilidad a outer correctors

El ajuste temporal de AUD-055 se revirtió antes de ejecución.

Configuración final:

- `B7_outer4`
- `C7_outer4`
- `nOuterCorrectors = 4`
- `adjustTimeStep = no`
- `deltaT = 0.001 s` fijo

Así:

- V5 vs V6 aísla estrategia de timestep.
- V5 vs V7 aísla cantidad de outer correctors.

**Estado:** ✅ V6 adaptativo definido; ✅ V7 fijo con outerCorrectors=4; ✅ diseño de una variable a la vez restaurado.

---

## 2026-09-25 — Flujo documental paralelo: bitácora + manual práctico OpenFOAM

### Decisión

Desde esta fecha el proyecto mantiene dos capas paralelas:

1. **Bitácora de auditoría** — historia cronológica de cambios, pruebas, discrepancias, evidencia, resultados, impacto y estado.
2. **Manual práctico de comandos** — referencia tipo tutorial con bloques listos para copiar, explicación y recetas específicas.

### Razón

La bitácora responde **qué pasó y por qué**. El manual responde **cómo repetirlo rápidamente**.

Los comandos reutilizables deben incorporarse al manual cuando sean útiles más allá de una acción aislada.

### Incidente de rutas al encadenar casos 6/7

Se lanzó un bloque secuencial desde:

`~/OpenFOAM/QuickCup_Solidification/cases_controlled_buoyancy`

B6 completó su secuencia hasta `foamLog`, pero el siguiente subshell intentó:

`cd ../C6_adaptiveDt`

y falló:

`-bash: cd: ../C6_adaptiveDt: No such file or directory`

### Causa

Cada bloque entre paréntesis corre en un subshell. Al terminar:

`(cd B6_adaptiveDt && ./Allclean && ./Allrun)`

el shell padre sigue en `cases_controlled_buoyancy`.

Por tanto, el siguiente caso debe ser `C6_adaptiveDt`, no `../C6_adaptiveDt`.

### Patrón correcto

```bash
(cd B6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd C6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd B7_outer4 && ./Allclean && ./Allrun) && \
(cd C7_outer4 && ./Allclean && ./Allrun)
```

Si B6 ya terminó:

```bash
(cd C6_adaptiveDt && ./Allclean && ./Allrun) && \
(cd B7_outer4 && ./Allclean && ./Allrun) && \
(cd C7_outer4 && ./Allclean && ./Allrun)
```

### Impacto

La salida pegada no mostraba fallo de B6; su `Allrun` llegó a `foamLog`. La cadena se detuvo únicamente al intentar entrar a la ruta incorrecta de C6.

**Estado:** ✅ error explicado y documentado.

---

## 2026-09-25 — Manual bilingüe y recuperación histórica de comandos

### Cambio documental

El manual práctico se dividió en:

- `OPENFOAM_COMMAND_MANUAL.md` — selector.
- `OPENFOAM_COMMAND_MANUAL_ES.md` — español.
- `OPENFOAM_COMMAND_MANUAL_EN.md` — inglés.

Ambas versiones deben conservar el mismo conjunto de comandos y estructura.

### Recuperación histórica

Se incorporaron comandos usados antes del 2026-09-25, incluyendo:

- `paraFoam -builtin &` de B2/C2,
- `foamPostProcess -region metal -solver fluid -latestTime` relacionado con la solicitud del doctor de perfiles velocidad–temperatura (“plotline”),
- elementos `lineUniform`, `graphUniform`, `graphCell` y campos `U T phaseChangeSource:alpha1`,
- `find . -name "openfoam-solidification.agent.md"`,
- `git check-ignore -v cases_buoyancy/B2_test/10`,
- flujo Git pull/status/add/commit/push,
- `git add -f` para outputs seleccionados ignorados.

### Regla de atribución

Solo se etiqueta como “del doctor” o motivado por él aquello con evidencia histórica explícita. Los demás comandos se documentan como parte de la historia del proyecto sin inventar atribución.

**Estado:** ✅ selector bilingüe del manual activo; ✅ primera recuperación histórica completada.

---

## 2026-09-25 — Bitácora bilingüe

### Cambio documental

La bitácora se reorganizó con la misma lógica bilingüe del manual:

- `PROJECT_AUDIT_LOG.md` — selector de idioma.
- `PROJECT_AUDIT_LOG_ES.md` — versión completa en español.
- `PROJECT_AUDIT_LOG_EN.md` — versión completa en inglés.

Las dos versiones preservan:

- mismas fechas,
- mismos identificadores AUD,
- mismas etiquetas de evidencia,
- mismos comandos,
- mismos nombres de archivo,
- mismos valores numéricos,
- mismas decisiones y estados.

Solo cambia el idioma de la narrativa.

### Regla futura

Cada nueva entrada técnica deberá añadirse tanto a la versión española como a la inglesa para evitar que una se vuelva más actual que la otra.

**Estado:** ✅ estructura bilingüe establecida y traducción española creada.


---

## 2026-09-25 — Observación del asesor: sensibilidad del acoplamiento de `p_rgh` a `nOuterCorrectors`
**[ADVISOR-OBSERVATION] [USER-REPORTED] [OPEN]**

### Observación comunicada durante trabajo paralelo

El asesor está realizando sus propias corridas en paralelo a las simulaciones del usuario. Según lo reportado por el usuario, el asesor observó que al aumentar `nOuterCorrectors` disminuían de forma importante los residuals iniciales de `p_rgh`.

El usuario recuerda que el asesor pudo haber probado valores altos de `nOuterCorrectors`, posiblemente alrededor de **7**, pero el valor exacto no está confirmado y no debe tratarse como dato verificado hasta disponer del log, configuración o confirmación directa correspondiente.

### Evidencia propia relacionada

En los logs controlados ya preservados del proyecto, el primer timestep de varios casos muestra un `Initial residual` de `p_rgh` cercano a 1. Por ejemplo, en B5:

- `p_rgh_0 = 0.973321` a `t = 0.001 s`
- `p_rgh_1 = 0.00750951`
- `p_rgh_2 = 0.00516345`
- `p_rgh_3 = 2.51636e-05`
- `p_rgh_4 = 8.23277e-05`
- `p_rgh_5 = 7.45313e-07`

Por tanto, aunque la primera corrección de presión comienza con un residual de orden unidad, las correcciones PIMPLE reducen el residual varios órdenes de magnitud dentro del mismo timestep.

El mismo pico inicial ~0.973 aparece también en B3, B4, C3 y C4 en el primer timestep, por lo que no debe interpretarse automáticamente como una falla exclusiva de una formulación física.

### Hipótesis a reproducir

Probar de forma controlada la sensibilidad del acoplamiento presión–velocidad frente a:

`nOuterCorrectors = 2, 3, 4, 5, 6, 7`

manteniendo constantes las demás variables numéricas y físicas.

Las métricas deberán incluir:

- residual inicial máximo de `p_rgh`,
- residual de `p_rgh` después del último corrector,
- reducción total dentro del timestep,
- número de timesteps con spikes elevados,
- persistencia o desaparición de spikes después del arranque,
- continuidad,
- Courant,
- tiempo de CPU/reloj,
- efecto real sobre T y fracción líquida.

### Objetivo

Determinar el punto de **rendimientos decrecientes**: el menor número de outer correctors que logra un acoplamiento suficientemente robusto sin aumentar costo computacional de forma innecesaria.

### Implicación para OpenFOAM PostPlotter

Esta observación motiva un módulo de diagnóstico de acoplamiento que no solo grafique `p_rgh_0`, `p_rgh_1`, etc., sino que reconstruya automáticamente la reducción de residual dentro de cada timestep y entre outer correctors.

**Estado:** 🟡 observación del asesor documentada; valor máximo ensayado por el asesor no confirmado; prueba controlada propia pendiente.


---

## 2026-09-25 — Auditoría completa de Initial residuals: el comportamiento relevante está en `p_rgh`
**[RUN-VERIFIED] [GIT-VERIFIED] [COUPLING-DIAGNOSTIC]**

Se analizaron los archivos `foamLog` de Initial residual para los casos controlados disponibles B3/B4/B5 y C3/C4/C5. El análisis excluyó el primer transitorio de arranque al estudiar el comportamiento persistente (`t >= 0.1 s`).

### Familias de residual auditadas

Los `foamLog` disponibles contienen Initial residuals para:

- `p_rgh`
- `h`
- `e`
- `rho`

### `rho`

Todos los archivos `rho_*` de B3/B4/B5/C3/C4/C5 tienen el mismo blob SHA y contienen valores cero. No aportan una señal útil de convergencia en estos casos.

### `h` — entalpía del metal

El primer solve de `h` parte alrededor de 1.67–1.69e-3 a 0.1 s y disminuye de manera suave conforme avanza la simulación.

Los solves posteriores dentro del timestep reducen el residual a órdenes mucho menores. No se encontró una familia de spikes intermedios comparable con `p_rgh`.

Ejemplos:

- B3 `h_0`: máximo para t>=0.1 s = 1.67278e-3 a 0.1 s; mediana ≈ 1.029e-4.
- B5 `h_0`: 1.67354e-3 a 0.1 s; mediana ≈ 1.028e-4.
- C3/C5 `h_0`: 1.69063e-3 a 0.1 s; mediana ≈ 1.158e-4.

Los correctores adicionales llevan los `h` posteriores a aproximadamente 1e-7–1e-9 según configuración.

### `e` — energía del molde

`e_0` muestra una disminución suave desde aproximadamente 1.84e-3 a 0.1 s.

Los correctores posteriores están típicamente en órdenes 1e-8–1e-10. Tampoco se encontró una inestabilidad intermedia comparable con presión.

### `p_rgh` — residual no monótono y persistente

`p_rgh` es la familia que presenta el comportamiento de acoplamiento numéricamente interesante.

El pico de ~0.973 en t=0.001 s se considera un transitorio de inicialización y NO es la única evidencia relevante. Después de 0.1 s reaparecen residuals elevados durante la simulación.

#### Familia B

B3 (`nOuterCorrectors=2`), `p_rgh_0`:
- máximo post-arranque: **0.0343238 a 0.592 s**
- 2–4 s: máximo **0.0118509**
- 4–6 s: máximo **0.0153241 a 5.781 s**
- 6–8 s: máximo **0.012815 a 6.249 s**
- 8–10 s: máximo **0.00976308**

B5 (`nOuterCorrectors=3`), `p_rgh_0`:
- máximo post-arranque: **0.0317178 a 0.573 s**
- 2–4 s: máximo **0.0107382**
- 4–6 s: máximo **0.015842 a 5.791 s**
- 6–8 s: máximo **0.0128389 a 6.250 s**
- 8–10 s: máximo **0.0095283**

En B, por tanto, existen eventos importantes de residual alrededor de 5.3–6.25 s además del transitorio temprano.

#### Familia C

C3 `p_rgh_0`:
- 0.1–2 s: máximo **0.0112909**
- 2–4 s: máximo **0.0100891**
- 4–6 s: máximo **0.0121034**
- 6–8 s: máximo **0.0121384**
- 8–10 s: máximo **0.0173881 cerca de 9.985 s**

C5 `p_rgh_0`:
- 0.1–2 s: máximo **0.0105247**
- 2–4 s: máximo **0.0105513**
- 4–6 s: máximo **0.0120312**
- 6–8 s: máximo **0.0122043**
- 8–10 s: máximo **0.0178995 cerca de 9.981 s**

La rama C presenta un patrón diferente: el residual de presión vuelve a crecer hacia el final de la ventana 0–10 s.

### Persistencia de residuals altos

Para t>=0.1 s:

B3:
- `p_rgh_0 > 0.01` en 2100 de 9901 timesteps.
- `p_rgh_3 > 0.01` en 430 de 9901.

B5:
- `p_rgh_0 > 0.01` en 2036 de 9901.
- `p_rgh_5 > 0.01` en 428 de 9901.

C3:
- `p_rgh_0 > 0.01` en 1366 de 9901.
- `p_rgh_3 > 0.01` en 404 de 9901.

C5:
- `p_rgh_0 > 0.01` en 1427 de 9901.
- `p_rgh_5 > 0.01` en 245 de 9901.

### Efecto real de aumentar nOuterCorrectors 2 → 3

Se definió descriptivamente la razón:

`R = p_rgh_last / p_rgh_0`

dentro del mismo timestep, usando el último pressure solve disponible.

Para t>=0.1 s:

- B3 (2 outer): mediana R = **0.6054**
- B5 (3 outer): mediana R = **0.5975**
- C3 (2 outer): mediana R = **0.8127**
- C5 (3 outer): mediana R = **0.8010**

Por tanto, añadir un tercer outer corrector produce solo una mejora pequeña en la reducción típica del Initial residual de `p_rgh`.

Además, existen timesteps donde el residual del último pressure solve es mayor que el del primero:

- B3: ~2.62% de los timesteps auditados.
- B5: ~3.62%.
- C3: ~10.08%.
- C5: ~8.22%.

Ejemplos claros:

- B5 a 6.126 s: el residual aumenta de `p_rgh_0 = 0.00621936` a `p_rgh_5 = 0.00841035`, razón ≈ **1.35**.
- C5 alrededor de 8.0 s presenta eventos donde los outer correctors posteriores terminan con residuals aproximadamente **1.5–1.56×** el primer residual del timestep.

### Relación con pruebas numéricas previas

B4/C4 (`nEnergyCorrectors=2`) conserva esencialmente el mismo patrón de `p_rgh` que B3/C3. Aumentar correctores de energía no resuelve el comportamiento de acoplamiento de presión.

B5/C5 (`nOuterCorrectors=3`) ya había mostrado cambios térmicos/de fase despreciables frente a B3/C3 pero mayor costo computacional. Esta auditoría añade que el tercer outer corrector tampoco produce una mejora grande del residual típico de presión.

### Interpretación

El diagnóstico correcto no debe ser únicamente “el residual inicial es alto”. Debe distinguir:

1. transitorio de arranque,
2. spikes persistentes durante la corrida,
3. reducción entre outer correctors,
4. stagnation (`R≈1`),
5. deterioration (`R>1`),
6. comportamiento de cada formulación B/C.

El valor absoluto de un Initial residual aislado no debe etiquetarse automáticamente como error; se requiere observar su evolución dentro del timestep y en el tiempo.

### Siguiente prueba crítica

El caso V7 con `nOuterCorrectors=4` permitirá comprobar si aparece una reducción sustancial que no se observó al pasar de 2 a 3.

Si el asesor efectivamente observó mejoras claras con valores mayores, una serie posterior 4→5→6→7 deberá realizarse de forma controlada y con timestep fijo antes de concluir un valor óptimo.

### Implicación para OpenFOAM PostPlotter

La app debe evolucionar desde un visor de archivos `p_rgh_0`, `p_rgh_1`, etc. hacia un diagnóstico de acoplamiento que reconstruya automáticamente, por timestep:

- outer corrector,
- pressure corrector interno,
- `p_rgh_0 → ... → p_rgh_last`,
- razón `R = last/first`,
- reducción en órdenes de magnitud,
- eventos donde `R≈1`,
- eventos donde `R>1`,
- ranking de los peores timesteps,
- exclusión configurable del startup,
- comparación entre casos con diferente `nOuterCorrectors`.

**Estado:** ✅ Initial residuals B3–B5/C3–C5 auditados; ✅ `p_rgh` identificado como principal señal de acoplamiento; 🟡 B7/C7 pendientes para evaluar `nOuterCorrectors=4`.


---

## 2026-09-25 — Distinción entre convergencia del solver lineal y convergencia del acoplamiento PIMPLE
**[RUN-VERIFIED] [COUPLING-DIAGNOSTIC]**

Después de auditar los Initial residuals de `p_rgh`, se compararon también los `p_rghFinalRes_*` de B5 y C5 para distinguir dos fenómenos diferentes:

1. qué tan bien converge cada solve lineal de presión;
2. qué tan bien se cierra el acoplamiento entre outer iterations.

### B5

Para t>=0.1 s:

- `p_rghFinalRes_1`: mediana ≈ **6.68e-8**
- `p_rghFinalRes_3`: mediana ≈ **5.00e-8**
- `p_rghFinalRes_5`: mediana ≈ **3.91e-8**

Los segundos solves de presión de cada outer terminan consistentemente cerca del orden 1e-8–1e-7.

Sin embargo, los Initial residuals del siguiente outer pueden volver a valores de orden 1e-3–1e-2.

### C5

Para t>=0.1 s:

- `p_rghFinalRes_1`: mediana ≈ **6.76e-8**
- `p_rghFinalRes_3`: mediana ≈ **5.55e-8**
- `p_rghFinalRes_5`: mediana ≈ **5.09e-8**

De nuevo, cada solve lineal puede terminar con residual pequeño mientras el siguiente ciclo de acoplamiento comienza con un Initial residual mucho mayor.

### Interpretación

Esto indica que un residual inicial persistente de `p_rgh` no debe interpretarse automáticamente como incapacidad del solver lineal para resolver la ecuación de presión.

En los casos auditados, el solver lineal reduce correctamente su residual final, pero las actualizaciones acopladas de velocidad, presión, energía, densidad/fase y fuentes pueden hacer que la siguiente corrección de presión vuelva a comenzar con una discrepancia apreciable.

Por tanto, el diagnóstico debe separar explícitamente:

- **linear-solver convergence:** Initial residual → Final residual dentro de un único pressure solve;
- **PIMPLE/nonlinear coupling convergence:** Initial residual de un outer → Initial residual del siguiente outer.

### Implicación para la app

OpenFOAM PostPlotter debe mostrar estas dos métricas por separado. Un `Final residual` pequeño no debe ocultar un acoplamiento persistente, y un `Initial residual` alto no debe etiquetarse como fallo del solver lineal si ese solve converge correctamente.

**Estado:** ✅ solver lineal vs acoplamiento PIMPLE diferenciados con datos reales B5/C5.


---

## 2026-09-25 — Perfil vertical central añadido a la serie controlada
**[POST-PROCESSING] [CONFIG-VERIFIED] [GIT-VERIFIED]**

Se añadió un segundo function object de muestreo, `verticalProfiles`, a los diez casos controlados:

- B3_reference / C3_reference
- B4_energy2 / C4_energy2
- B5_outer3 / C5_outer3
- B6_adaptiveDt / C6_adaptiveDt
- B7_outer4 / C7_outer4

### Geometría

Nueva línea:

`line_x20mm`

con:

- x = **0.020 m**
- z = **0.005 m**
- y = **0.00025 → 0.03975 m**
- 80 puntos uniformes
- `axis y`

La línea atraviesa el centro geométrico del metal y la ubicación del probe central en x=20 mm, z=5 mm.

### Campos

Se conservan exactamente los mismos campos que en los perfiles horizontales:

- `U`
- `T`
- `phaseChangeSource:alpha1`

Por tanto, del vector `U` pueden analizarse Ux, Uy, Uz y |U|.

### Razón física

La gravedad del caso actúa en Y:

`g = (0, -9.81, 0)`

y el análisis espacial previo encontró que B y C presentan signos opuestos de `Uy` en el centro durante parte de la solidificación.

Las líneas horizontales existentes `line_y20mm` y `line_y30mm` cortan la circulación a alturas fijas. La nueva línea vertical permite observar la estructura completa de abajo hacia arriba y responder:

- dónde `Uy > 0`,
- dónde `Uy < 0`,
- dónde cambia de signo,
- cómo se relaciona con T(y),
- cómo se relaciona con alpha_l(y),
- si existe una celda de recirculación y cómo difiere entre B y C.

### Impacto

Es una modificación exclusivamente de postprocesamiento. No cambia:

- malla,
- propiedades,
- fronteras,
- modelo de cambio de fase,
- timestep,
- correctores,
- solución física.

### Nota de ejecución

Los casos B6/C6/B7/C7 ya habían comenzado a ejecutarse localmente antes de que esta configuración se añadiera al repositorio. Por tanto, esta modificación en Git no altera corridas locales que ya están en curso. Sus perfiles verticales pueden generarse posteriormente a partir de los tiempos guardados una vez sincronizada la configuración local.

**Estado:** ✅ configuración vertical añadida a B3–B7/C3–C7; 🟡 extracción/análisis de los nuevos perfiles pendiente.


---

## 2026-09-26 — Paquete completo de diagnósticos de solidificación añadido a V3–V7
**[POST-PROCESSING] [CONFIG-VERIFIED] [GIT-VERIFIED] [NOT-YET-RUN-VERIFIED]**

Se añadió a los diez casos controlados B3–B7/C3–C7 un paquete común de diagnósticos basado únicamente en function objects nativos de OpenFOAM Foundation v14.

Commit principal de implementación:

`bd77587a4bf8c813c40512cfdfc3a27ae4e0168f`

La modificación es exclusivamente de postprocesamiento. No cambia malla, propiedades, condiciones de frontera, modelo de solidificación, timestep, PIMPLE ni ecuaciones.

### Probe central ampliado

El probe en `(0.020 0.020 0.005) m` ahora registra en cada timestep:

- `U`
- `T`
- `p_rgh`
- `rho`
- `phaseChangeSource:alpha1`

Esto permite correlacionar directamente presión modificada, densidad, velocidad, temperatura y fracción líquida en el mismo punto.

### Gradiente térmico

Se añadieron:

- `gradT = grad(T)`
- `magGradT = |grad(T)|`

También se registra el máximo espacial de `magGradT` y su localización mediante `metalMaxThermalGradient`.

### Tasa térmica local

Se añadió el function object nativo `ddt`:

- `dTdt = dT/dt`
- `coolingRate = -dTdt`

Convención:

- `coolingRate > 0`: enfriamiento local
- `coolingRate < 0`: calentamiento local

Se añade además `metalMeanCoolingRate`.

### Gradiente de densidad

Se añadieron:

- `gradRho = grad(rho)`
- `magGradRho = |grad(rho)|`
- `metalMaxDensityGradient` con localización

Objetivo: comparar directamente las rutas de buoyancy B/C.

En B, la densidad depende de T y el gradiente de densidad participa en la buoyancy nativa de `p_rgh`.

En C, `rho` es constante, por lo que `gradRho` debería ser aproximadamente cero. Esto constituye además una comprobación interna útil de la formulación.

### Tasa de cambio de fase

Se añadieron:

- `dAlphaLdt = d(alpha_l)/dt`
- `solidificationRate = -dAlphaLdt`

Convención:

- `solidificationRate > 0`: solidificación local
- `solidificationRate < 0`: refusión local

Se verificó en el código fuente de OpenFOAM v14 que `solidificationMeltingSource` actualiza explícitamente `alpha1_.oldTime()`, por lo que el campo dispone del historial temporal requerido durante ejecución.

### Tasa de calor latente

Se verificó que los diez casos usan:

`L = 2.286e5 J/kg`

Se crea un campo uniforme nativo `latentHeat` con dimensiones físicas `J/kg`, y mediante `multiply` se calcula:

`latentHeatRateVol = rho * L * solidificationRate`

Dimensiones:

`W/m3`

Convención:

- valor positivo: liberación de calor latente por solidificación
- valor negativo: absorción de calor durante refusión

Se integra además sobre todo el metal:

`metalLatentHeatPower = integral(latentHeatRateVol dV)`

con resultado en W.

### Courant espacial

Se añadió el function object nativo:

`CoCell`

usando `phi` y `rho`. En v14, `CourantNo` detecta el flujo másico y divide por densidad internamente cuando corresponde.

También se registra:

`metalMaxCourant`

con valor y ubicación.

### Perfiles espaciales ampliados

Las dos líneas horizontales y la línea vertical central ahora muestrean:

- `U`
- `T`
- `p_rgh`
- `rho`
- `phaseChangeSource:alpha1`
- `vorticity`
- `flowType`
- `magSqrDevGradU`
- `gradT`
- `magGradT`
- `dTdt`
- `coolingRate`
- `gradRho`
- `magGradRho`
- `dAlphaLdt`
- `solidificationRate`
- `latentHeatRateVol`
- `CoCell`

Esto permite estudiar espacialmente, sobre exactamente las mismas líneas, flujo, presión, buoyancy, gradiente térmico, enfriamiento, avance/refusión de fase, liberación latente y carga numérica local.

### Diagnósticos energéticos ya presentes

Se conservan y quedan integrados con este paquete:

- `energyAdvectiveFlux`
- `heatFlux`
- `energyFlux`
- potencia en `metalTop`
- potencia en `metal_to_mold`
- potencia neta en ambas fronteras
- `metalSensibleEnthalpy`
- `metalMeanLiquidFraction`
- `vorticity`
- `flowType`

### Limitación importante de OpenFOAM v14

El propio código fuente de `functionObjects::ddt` indica que **`ddt` no está soportado por `foamPostProcess`**.

Por tanto, los campos:

- `dTdt`
- `coolingRate`
- `dAlphaLdt`
- `solidificationRate`
- `latentHeatRateVol`

deben generarse DURANTE una corrida del solver.

No pueden reconstruirse retrospectivamente con el `foamPostProcess` estándar de v14 a partir de una corrida ya terminada.

Para corridas antiguas, PostPlotter podrá estimar derivados temporales a partir de los datos almacenados; esas estimaciones deben distinguirse explícitamente de la evaluación nativa runtime `fvc::ddt`.

### Estado

- ✅ configuración añadida a B3–B7/C3–C7
- ✅ sintaxis y disponibilidad de `grad`, `mag`, `ddt`, `uniform`, `multiply` y `CourantNo` verificadas contra el código/caseDicts oficiales de OpenFOAM Foundation v14
- ✅ L verificado idéntico en los diez casos
- ✅ dependencias colocadas antes de `lineProfiles`
- 🟡 todavía no validado mediante una ejecución real del solver con este paquete completo
- 🟡 B6/C6/B7/C7 que ya estuvieran corriendo localmente antes de esta modificación no reciben estos nuevos function objects automáticamente



---

## 2026-09-26 — Validación real B3 del paquete de diagnósticos y corrección de nombre de `flowType`
**[RUN-VERIFIED] [BUG-FOUND] [FIXED]**

Se ejecutó `B3_reference` completo de 0 a 10 s con el paquete ampliado de diagnósticos.

La corrida terminó correctamente y `foamLog` se ejecutó al final.

### Campos verificados en `10/metal`

Se encontraron:

- `CoCell`
- `coolingRate`
- `dAlphaLdt`
- `dTdt`
- `gradRho`
- `gradT`
- `latentHeat`
- `latentHeatRateVol`
- `magGradRho`
- `magGradT`
- `magSqrDevGradU`
- `solidificationRate`
- `vorticity`

### Postprocesamiento verificado

Se generaron correctamente:

- `horizontalProfiles`
- `verticalProfiles`
- `metalBoundaryEnergyPower`
- `metalLatentHeatPower`
- `metalMaxCourant`
- `metalMaxDensityGradient`
- `metalMaxThermalGradient`
- `metalMeanCoolingRate`
- `metalMeanLiquidFraction`
- `metalMeanSolidificationRate`
- `metalMoldEnergyPower`
- `metalSensibleEnthalpy`
- `metalTopEnergyPower`
- `temperatureProbe`

### Hallazgo

No apareció un archivo llamado `flowType`.

La revisión del código fuente oficial de OpenFOAM Foundation v14 mostró que el function object `flowType` usa por defecto como nombre del campo de salida el **nombre del bloque function object**, salvo que se especifique explícitamente `result`.

La configuración usaba:

`flowTopology { type flowType; ... }`

por lo que el campo generado se denominaba `flowTopology`, mientras que los perfiles solicitaban `flowType`.

### Corrección

Se añadió a los diez casos:

`result flowType;`

dentro del bloque `flowTopology`.

Commit:

`c92c282ca7cb549b4efdd88b402191163c706066`

Con esto el nombre del campo queda canónico y consistente con `lineProfiles` y con el futuro parser de PostPlotter.

**Estado:** ✅ B3 validó el paquete de diagnósticos; ✅ inconsistencia de nombre identificada y corregida; 🟡 repetir B3 junto con la tanda final para producir un dataset completamente homogéneo.


---

## 2026-09-26 — Auditoría numérica final V3–V7 después del rerun completo
**[RUN-DATA-COMMITTED] [NUMERICAL-AUDIT] [COUPLING] [ADAPTIVE-DT]**

Los logs finales de los diez casos controlados fueron sincronizados al repositorio después de ejecutar la matriz V3–V7. Los commits de resultados incluyen `5d5ccb00f1b3` (logs finales) y `54182ef3cab9` (sincronización local restante).

El análisis siguiente usa los archivos `foamLog` versionados directamente en GitHub. Para las métricas de coupling de `p_rgh` se excluyó el startup y se usó `t >= 0.1 s`.

### Resumen

| Caso | Configuración | Pasos | Tiempo final parseado (s) | Exec. (s) | Co max | max `p_rgh_0` post-startup | Mediana R | P95 R | R>1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B3_reference | outer=2, dt fijo | 10000 | 10.000000 | 202.005 | 0.175912 | 0.0343238 @ 0.592 s | 0.605438 | 0.945131 | 2.62% |
| C3_reference | outer=2, dt fijo | 10000 | 10.000000 | 196.543 | 0.0700709 | 0.0173881 @ 9.985 s | 0.812747 | 1.059338 | 10.08% |
| B4_energy2 | outer=2, energy=2 | 10000 | 10.000000 | 250.984 | 0.176643 | 0.0307308 @ 0.591 s | 0.604283 | 0.943883 | 2.92% |
| C4_energy2 | outer=2, energy=2 | 10000 | 10.000000 | 220.093 | 0.0700709 | 0.0179951 @ 9.999 s | 0.813191 | 1.063103 | 10.62% |
| B5_outer3 | outer=3, dt fijo | 10000 | 10.000000 | 282.222 | 0.175874 | 0.0317178 @ 0.573 s | 0.597503 | 0.950764 | 3.62% |
| C5_outer3 | outer=3, dt fijo | 10000 | 10.000000 | 273.060 | 0.0700712 | 0.0178995 @ 9.981 s | 0.800997 | 1.041475 | 8.22% |
| B6_adaptiveDt | outer=3, dt adaptativo | 2810 | 9.999657 | 80.778 | 0.287759 | 0.0186405 @ 0.784957 s | 0.374538 | 0.764803 | 1.59% |
| C6_adaptiveDt | outer=3, dt adaptativo | 1584 | 10.003410 | 47.336 | 0.287049 | 0.0223995 @ 9.983344 s | 0.794831 | 1.034915 | 7.58% |
| B7_outer4 | outer=4, dt fijo | 10000 | 10.000000 | 381.367 | 0.175849 | 0.0362977 @ 0.731 s | 0.603163 | 0.950615 | 2.96% |
| C7_outer4 | outer=4, dt fijo | 10000 | 10.000000 | 365.418 | 0.0700710 | 0.0174552 @ 9.996 s | 0.808822 | 1.082497 | 10.65% |

donde:

`R = p_rgh(last outer Initial residual) / p_rgh(first outer Initial residual)`.

### Solver lineal vs coupling

En los diez casos, el `Final residual` del último solve de `p_rgh` permanece extremadamente bajo:

- mediana aproximadamente `3.9e-8 → 5.7e-8`;
- P99 aproximadamente `< 1e-7`;
- máximo observado aproximadamente `< 1e-7`.

Esto refuerza la separación ya establecida: el solver lineal de presión converge fuertemente dentro de cada solve, mientras que la evolución del **Initial residual entre outer corrections** describe el comportamiento del coupling no lineal. Un `R>1` no significa por sí mismo fallo del solver lineal.

### Outer-corrector sensitivity: diminishing returns

En las ramas de timestep fijo:

- B: mediana R = 0.6054 (outer2), 0.5975 (outer3), 0.6032 (outer4).
- C: mediana R = 0.8127 (outer2), 0.8010 (outer3), 0.8088 (outer4).

El cambio 2→3 es pequeño y 3→4 **no produce una mejora monotónica**; outer4 regresa hacia valores cercanos a outer2.

El costo sí crece con claridad en este rerun:

- B5 outer3 cuesta ~39.7% más que B3.
- B7 outer4 cuesta ~88.8% más que B3.
- C5 outer3 cuesta ~38.9% más que C3.
- C7 outer4 cuesta ~85.9% más que C3.

Por tanto, para estos casos y este intervalo de 0–10 s, outer4 añade costo sustancial sin evidencia de una mejora proporcional del coupling de `p_rgh`. Esto es evidencia de **diminishing returns**, no una regla universal para otros casos OpenFOAM.

### Energy-corrector sensitivity

B4/C4 mantienen métricas de coupling prácticamente iguales a B3/C3, mientras que en este rerun el tiempo de ejecución aumenta ~24.2% para B y ~12.0% para C.

Esto es consistente con la conclusión térmica previa: `nEnergyCorrectors=2` no modifica materialmente la solución monitoreada y tampoco muestra una mejora clara de coupling que justifique el costo adicional en esta matriz.

### Adaptive timestep V6

Respecto a V5, que comparte `nOuterCorrectors=3`:

- B6 reduce los pasos 10000→2810 y el tiempo 282.222→80.778 s: ~3.49× más rápido.
- C6 reduce los pasos 10000→1584 y el tiempo 273.060→47.336 s: ~5.77× más rápido.
- Mediana de `deltaT`: B6 ≈ 0.003954 s; C6 ≈ 0.005902 s.
- Máximo `deltaT` observado: B6 ≈ 0.005321 s; C6 ≈ 0.026623 s.
- Co máximo: B6 = 0.287759; C6 = 0.287049, por encima del `maxCo=0.25` configurado.

La revisión del fuente oficial de OpenFOAM Foundation v14, `src/finiteVolume/cfdTools/general/include/setDeltaT.H`, confirma que `adjustTimeStep` calcula el **siguiente** `deltaT` usando el Co observado y limita el crecimiento a 1.2× por ajuste. Por ello `maxCo` funciona como objetivo/controlador para la actualización del timestep y no como garantía matemática de que ningún Co reportado pueda sobrepasarlo transitoriamente.

El acumulado final de continuidad reportado también es mayor en V6:

- B6: 2.44980e-4 vs B5: 1.65205e-4.
- C6: 2.71897e-4 vs C5: 1.78172e-4.

Esto merece seguimiento; no debe interpretarse por sí solo como invalidez física. Antes de seleccionar V6 como configuración productiva hay que comparar sus historias térmicas, fase, perfiles y diagnósticos físicos contra V5.

### Diferencia B/C en coupling

Las ramas B de timestep fijo muestran una reducción relativa de Initial residual más fuerte (mediana R ~0.60) y menos eventos `R>1` (~2.6–3.6%) que las C (~0.80 y ~8.2–10.6%).

Al mismo tiempo, B puede presentar máximos de `p_rgh_0` mayores que C. Por tanto deben mantenerse separadas dos preguntas:

1. magnitud del mismatch al inicio del solve;
2. reducción relativa conseguida durante el coupling.

La diferencia puede estar relacionada con las formulaciones físicas B/C, pero no se etiqueta aquí como “estabilidad superior/inferior” sin más evidencia.

**Estado:** ✅ logs finales V3–V7 versionados; ✅ outer2/3/4 auditado; ✅ V6 adaptive auditado numéricamente; ✅ convergencia lineal separada de coupling; 🟡 comparación física completa de V6/V7 con los nuevos outputs de `researchDiagnostics` todavía pendiente.


---

## 2026-09-26 — Auditoría numérica final V3–V7 desde resultados sincronizados
**[RUN-VERIFIED] [GIT-VERIFIED] [NUMERICAL-AUDIT]**

Los resultados finales de los diez casos controlados V3–V7 fueron sincronizados desde la estación de trabajo local al repositorio y auditados directamente desde los `log.foamMultiRun` y `logs/` versionados.

Commits de resultados:
- `5d5ccb00f1b3...` — actualización de logs finales V3–V7.
- `54182ef3cab9...` — sincronización restante de datos locales.

### Comparación de costo y coupling de `p_rgh` (startup excluido: t < 0.1 s)

| Caso | Pasos | Max p0 | Mediana p0 | Mediana R | p95 R | R>1 | Co max | Exec. s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B3_reference | 10000 | 0.0343238 | 0.00835789 | 0.605438 | 0.945131 | 2.62% | 0.175912 | 202.005 |
| C3_reference | 10000 | 0.0173881 | 0.00748726 | 0.812747 | 1.05934 | 10.08% | 0.0700709 | 196.543 |
| B4_energy2 | 10000 | 0.0307308 | 0.00835290 | 0.604283 | 0.943883 | 2.92% | 0.176643 | 250.984 |
| C4_energy2 | 10000 | 0.0179951 | 0.00751839 | 0.813191 | 1.06310 | 10.62% | 0.0700709 | 220.093 |
| B5_outer3 | 10000 | 0.0317178 | 0.00825669 | 0.597503 | 0.950764 | 3.62% | 0.175874 | 282.222 |
| C5_outer3 | 10000 | 0.0178995 | 0.00775813 | 0.800997 | 1.04147 | 8.22% | 0.0700712 | 273.060 |
| B6_adaptiveDt | 2810 | 0.0186405 | 0.00236917 | 0.374538 | 0.764803 | 1.59% | 0.287759 | 80.778 |
| C6_adaptiveDt | 1584 | 0.0223995 | 0.00898528 | 0.794831 | 1.03491 | 7.58% | 0.287049 | 47.336 |
| B7_outer4 | 10000 | 0.0362977 | 0.00831734 | 0.603163 | 0.950615 | 2.96% | 0.175849 | 381.367 |
| C7_outer4 | 10000 | 0.0174552 | 0.00759476 | 0.808822 | 1.08250 | 10.65% | 0.0700710 | 365.418 |

Aquí `R = p_rgh,last(initial) / p_rgh,first(initial)` dentro del timestep. `R>1` significa que el Initial residual aumentó a través del coupling; no implica por sí solo fallo del solver lineal.

Los últimos solves lineales de presión siguen terminando con residual final típicamente de orden `10^-8` a `10^-7` en todos los casos, por lo que debe mantenerse separada la interpretación de convergencia lineal y convergencia del acoplamiento PIMPLE.

### Resultado de outer correctors

Comparando el baseline V3 con V5 y V7:

- B: mediana R = 0.6054 → 0.5975 → 0.6032 para outer 2 → 3 → 4.
- C: mediana R = 0.8127 → 0.8010 → 0.8088.
- El costo de B7 frente a B3 aumenta de 202.0 s a 381.4 s (~89%).
- El costo de C7 frente a C3 aumenta de 196.5 s a 365.4 s (~86%).

La cuarta outer correction no produce una mejora monotónica en la mediana de R respecto a outer3, mientras el costo aumenta fuertemente. Esto refuerza el resultado previo de diminishing returns para el rango probado. No se interpreta como una selección de modelo físico.

### Resultado de energy correctors

B4/C4 mantienen métricas de coupling muy próximas a B3/C3, mientras incrementan el costo. Esto es consistente con la sensibilidad térmica/central previamente observada como pequeña.

### Adaptive timestep V6

V6 reduce fuertemente el número de pasos y el tiempo de ejecución:

- B6: 2810 pasos, 80.78 s.
- C6: 1584 pasos, 47.34 s.

`deltaT` observado:
- B6: mediana 0.003954 s, máximo 0.005321 s.
- C6: mediana 0.005902 s, máximo 0.026623 s.

El Courant máximo registrado alcanza ~0.288 en ambos casos, por encima del `maxCo=0.25` configurado, mientras los valores finales quedan aproximadamente en 0.25. Esto se registra como un sobrepaso observado del target durante la adaptación y requiere interpretación en contexto del algoritmo de ajuste; no se etiqueta automáticamente como inestabilidad.

La continuidad acumulada final es mayor en V6:
- B6: 2.4498e-4.
- C6: 2.71897e-4.

Antes de aceptar V6 como sustituto del timestep fijo se requiere comparar los resultados físicos (T, fase, perfiles, gradientes y energía), no solo costo y residuals.

**Estado:** auditoría numérica final V3–V7 completada desde datos versionados. Siguiente etapa: comparación física de outputs de postProcessing.


---

## 2026-09-26 — Matriz de validación y auditoría de paridad con Quick-Cup experimental
**[VALIDATION-GATE] [SOURCE-AUDIT] [NO-PHYSICS-CHANGE]**

Se completó una auditoría de la configuración controlada V3–V7 contra el benchmark Quick-Cup hipereutéctico/hipoeutéctico descrito por Chiumenti et al.

Hallazgos principales:

- V3–V7 permanecen congelados como estudio de sensibilidad numérica y de formulación de buoyancy.
- El rebound térmico de C3/C4/C5 (+5.35 K) se reproduce con prácticamente la misma Tmin y recuperación de fracción líquida bajo los cambios numéricos probados, por lo que no es un artefacto de elegir B3/C3 frente a B4/C4/B5/C5. En el modelo actual coincide con remelting local y no se etiqueta como recalescencia por nucleación.
- El caso actual no es todavía un benchmark experimental alineado: 1500 K iniciales frente a 1573.15 K en el Quick-Cup del paper, HTC exterior 10 frente a 50 W/m2K y propiedades de molde distintas.
- La resistencia de la capa de interfaz actual, 0.2 mm con k=0.1 W/mK, equivale a aproximadamente 500 W/m2K y sí coincide con el HTC metal–molde del paper.
- La temperatura inicial actual (1226.85 °C) está ~33 °C por debajo del T_start_L=1260 °C utilizado por el modelo hipereutéctico/hipoeutéctico del paper.
- El `solidificationMelting` estándar usa una sola variable de fracción líquida ligada a una relación de equilibrio, mientras el modelo del paper usa transformaciones dendrítica y eutéctica con leyes cinéticas temporales y subenfriamiento.
- No se localizó en el repositorio ni en los archivos disponibles una serie temporal experimental raw/CSV; por tanto no se fabrican RMSE/MAE.

Se añadieron:
- `VALIDATION_MATRIX.md`
- `VALIDATION_MATRIX_ES.md`
- `VALIDATION_MATRIX_EN.md`

**Decisión:** antes de escribir un fvModel cinético, construir un caso de equilibrio alineado con las condiciones experimentales. La rama cinética se abre solo si ese caso demuestra una limitación estructural del modelo de equilibrio.


---

## 2026-09-26 — Diagnóstico directo de términos de momento de `solidificationMeltingSource`
**[POSTPROCESSING] [PHYSICS-DIAGNOSTICS] [NO-PHYSICS-CHANGE]**

Después de completar la auditoría numérica V3–V7, se añadió un diagnóstico específico para determinar si las diferencias observadas en velocidad y comportamiento de la zona pastosa provienen del acoplamiento presión–velocidad, de la flotación o del amortiguamiento Darcy del modelo `solidificationMeltingSource`.

El nuevo bloque `solidificationMeltingMomentumDiagnostics` fue añadido a:

- B3_reference
- B4_energy2
- B5_outer3
- B6_adaptiveDt
- B7_outer4
- C3_reference
- C4_energy2
- C5_outer3
- C6_adaptiveDt
- C7_outer4

El diagnóstico lee directamente de `constant/metal/fvModels` los parámetros `Cu`, `q`, `beta`, `rhoRef`, `Tsol`, `Tliq` y `alpha1e`; por lo tanto no duplica manualmente la parametrización entre casos.

Se reconstruye el coeficiente de amortiguamiento Darcy:

`D = Cu (1-alpha_l)^2 / (alpha_l^3 + q)`

y su contribución de aceleración:

`a_D = -D U`.

También se reconstruyen:

- `phaseChangeModelDeltaT`: diferencia térmica usada por el modelo de cambio de fase.
- `phaseChangeBuoyancyAcceleration`: escala de aceleración `g beta DeltaT`.
- `phaseChangeBuoyancySu`: fuente explícita de flotación `rhoRef g beta DeltaT`.
- `pRghAcceleration`: `-grad(p_rgh)/rho`.
- razones locales `phaseChangeDragToBuoyancy` y `phaseChangeDragToPressure`.

Campos escritos:

- `phaseChangeSolidFraction`
- `phaseChangeDarcyCoeff`
- `phaseChangeDarcySp`
- `phaseChangeDarcyAcceleration`
- `phaseChangeModelDeltaT`
- `phaseChangeBuoyancyAcceleration`
- `phaseChangeBuoyancySu`
- `pRghAcceleration`
- `magPhaseChangeDarcyAcceleration`
- `magPhaseChangeBuoyancyAcceleration`
- `magPRghAcceleration`
- `phaseChangeDragToBuoyancy`
- `phaseChangeDragToPressure`

### Relación con los resultados V6 y V7 ya documentados

Esta ampliación no modifica las conclusiones numéricas previas:

- V6 sigue siendo la rama de timestep adaptativo, con fuerte reducción de costo pero necesidad de comprobar equivalencia física.
- V7 sigue siendo la prueba de cuatro outer correctors, con costo mucho mayor y sin mejora monotónica clara del coupling respecto a V5.
- Los residuals lineales de presión siguen terminando típicamente en el orden de 10^-8–10^-7; el problema abierto no es un fallo simple del solver lineal.
- La siguiente comparación debe usar simultáneamente los resultados ya registrados de V3–V7 y los nuevos campos de fuerza/amortiguamiento.

### Estado de validación

El código de diagnóstico está versionado, pero sus nuevos campos todavía deben validarse mediante una corrida corta de B7 y C7 en OpenFOAM Foundation v14 antes de relanzar toda la matriz.

**Siguiente gate:** compilar/ejecutar B7 y C7, comprobar escritura de los campos nuevos y, si pasa, aplicar el diagnóstico a la comparación física V3–V7.


### Corrección de compatibilidad detectada en validación B7

La primera validación de B7 falló antes de ejecutar el solver por compilación del `coded` function object:

`fatal error: fvCFD.H: No such file or directory`

Se confirmó que el problema era exclusivamente de includes del código dinámico bajo OpenFOAM Foundation v14; no correspondía a un fallo físico ni numérico del caso.

Se sustituyó `fvCFD.H` por headers específicos compatibles (`fvMesh.H`, `volFields.H`, `uniformDimensionedFields.H`, `IOdictionary.H`, `zeroGradientFvPatchFields.H`, `fvcGrad.H`) en los diez casos V3–V7. La validación B7 debe repetirse antes de ejecutar C7 o la matriz completa.


### Segunda corrección de compatibilidad B7

La segunda validación de compilación del diagnóstico detectó dos diferencias adicionales de API en OpenFOAM Foundation v14:

- `Time::timeName()` requiere un argumento de tiempo en este contexto de código dinámico.
- `gMax(field)` devuelve directamente un `scalar`, por lo que no debe usarse `.value()`.

Correcciones aplicadas a los diez casos V3–V7:

- `m.time().timeName()` → `m.time().timeName(m.time().timeOutputValue())`
- `gMax(...).value()` → `gMax(...)`

El fallo sigue siendo exclusivamente de compilación del postproceso dinámico y no corresponde a inestabilidad del solver ni a un problema físico del modelo.


### Tercera corrección de compatibilidad B7

La tercera validación mostró que `Time::timeOutputValue()` no existe en la API de OpenFOAM Foundation v14 instalada. Se verificó contra la interfaz de `Time` de OpenFOAM 14 que `timeName` acepta un `scalar` explícito, por lo que el código se cambió a:

`m.time().timeName(m.time().value())`

Esta corrección fue aplicada a los diez casos controlados V3–V7. El fallo sigue siendo exclusivamente de compilación del postproceso dinámico.


### Validación runtime B7 del diagnóstico de momento

La corrida completa de `B7_outer4` compiló y ejecutó correctamente el bloque `solidificationMeltingMomentumDiagnostics` bajo OpenFOAM Foundation v14.

Valores observados al final de la corrida:

- `max(phaseChangeDarcyCoeff) = 1e8 1/s`.
- `max(|phaseChangeDarcyAcceleration|)` disminuyó aproximadamente de 546.7 a 332.0 m/s2 en las últimas escrituras mostradas.
- `max(|phaseChangeBuoyancyAcceleration|) = 0`, consistente con `beta = 0` en la familia B.
- `max(|pRghAcceleration|)` disminuyó aproximadamente de 1.897 a 1.723 m/s2.

El valor máximo de Darcy es consistente con la forma del modelo:
`D = Cu(1-alpha_l)^2/(alpha_l^3 + q)`.
Con `Cu=1e5 1/s`, `q=1e-3` y `alpha_l=0`, el límite sólido es `D=1e8 1/s`.

Advertencia de interpretación: los máximos globales de Darcy y presión pueden ocurrir en celdas distintas y no deben dividirse entre sí para inferir dominancia local. Para esa comparación deben usarse los campos celda-a-celda `phaseChangeDragToPressure` y `phaseChangeDragToBuoyancy`, junto con `alpha_l`, `U` y las magnitudes absolutas.

**Estado:** B7 diagnostic runtime validation PASSED. Siguiente caso de validación: C7.


### Validación runtime C7 del diagnóstico de momento

La corrida completa de `C7_outer4` compiló y ejecutó correctamente el bloque `solidificationMeltingMomentumDiagnostics` bajo OpenFOAM Foundation v14.

Valores observados al final de la corrida:

- `max(phaseChangeDarcyCoeff) = 1e8 1/s`.
- `max(|phaseChangeDarcyAcceleration|)` disminuyó aproximadamente de 422.25 a 418.58 m/s2 en las últimas escrituras mostradas.
- `max(|phaseChangeBuoyancyAcceleration|)` se mantuvo alrededor de 0.1070–0.1074 m/s2.
- `max(|pRghAcceleration|)` aumentó ligeramente de aproximadamente 0.08177 a 0.08247 m/s2.

A diferencia de la familia B, donde `beta=0` y la contribución de flotación del `solidificationMeltingSource` es nula, C7 presenta una contribución de flotación distinta de cero, consistente con `beta=1.13e-4 1/K`.

Advertencia: los máximos globales de Darcy, buoyancy y presión no necesariamente ocurren en la misma celda. Para evaluar dominancia local deben analizarse `phaseChangeDragToBuoyancy`, `phaseChangeDragToPressure`, `phaseChangeSource:alpha1` y `U` celda a celda.

**Estado:** C7 diagnostic runtime validation PASSED. El paquete de diagnóstico de momento queda validado para ambas formulaciones B y C.
