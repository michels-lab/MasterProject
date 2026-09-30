# Guía maestra del caso Quick-Cup en OpenFOAM 14

## Objetivo de esta guía

Esta guía explica **cómo está organizado el caso real del proyecto Quick-Cup**, qué lee OpenFOAM en cada carpeta, qué está escrito actualmente, qué significa física y numéricamente, qué alternativas relevantes existen y cómo esas decisiones pueden modificar los resultados.

La referencia principal es **V11**, porque V12 y V13 descienden de ella y cambian únicamente la condición de frontera de `p_rgh` en `metalTop`.

Casos de referencia:

- `B11_topFixedFlux_airGapOF14`
- `C11_topFixedFlux_airGapOF14`
- `B12_topFixedValue_airGapOF14`
- `C12_topFixedValue_airGapOF14`
- `B13_prghPressure_airGapOF14`
- `C13_prghPressure_airGapOF14`

---

# 1. Mapa mental de un caso OpenFOAM

Un caso OpenFOAM se puede entender separando cuatro preguntas:

1. **¿Cómo y durante cuánto tiempo voy a resolver?** → `system/`
2. **¿Qué materiales y modelos físicos existen?** → `constant/`
3. **¿Cómo empieza el problema y qué ocurre en sus fronteras?** → `0/`
4. **¿Cómo se prepara, ejecuta y analiza?** → scripts como `Allrun`, `Allclean`, más `logs/` y `postProcessing/`.

En nuestro caso además existen **dos regiones**:

- `metal`: región fluida donde se resuelven flujo, presión, energía y solidificación;
- `mold`: región sólida donde se resuelve conducción térmica.

Por eso muchos archivos aparecen separados como:

```
system/metal/
system/mold/
constant/metal/
constant/mold/
0/metal/
0/mold/
```

El solver principal es `foamMultiRun`, que carga un solver de tipo `fluid` para `metal` y uno de tipo `solid` para `mold`.

---

# 2. Carpeta `system/`: cómo se resuelve el problema

La carpeta `system` contiene principalmente **decisiones numéricas, geometría/malla, tiempo de simulación, algoritmos de solución y herramientas de diagnóstico**.

No define por sí sola las propiedades del hierro o de la sílica; eso está en `constant/`.

## 2.1 `system/controlDict`

### Para qué sirve

`controlDict` es el archivo que gobierna la ejecución general:

- qué aplicación se ejecuta;
- qué regiones existen;
- desde qué tiempo inicia;
- cuándo termina;
- tamaño de paso temporal;
- frecuencia de escritura;
- si el paso de tiempo se adapta;
- límites numéricos globales.

### Lo que tenemos escrito

```
application     foamMultiRun;

regionSolvers
{
    metal       fluid;
    mold        solid;
}

startTime       0;
endTime         10;
deltaT          0.001;

writeControl    timeStep;
writeInterval   100;

adjustTimeStep  no;
maxCo           0.25;
maxDeltaT       0.1;
```

### Qué significa

**`foamMultiRun`** indica que no tenemos un único dominio homogéneo. OpenFOAM ejecuta módulos de solver distintos para cada región.

**`metal fluid`** hace que la región del metal resuelva las ecuaciones propias de un fluido térmico, incluyendo velocidad, presión y energía.

**`mold solid`** hace que el molde resuelva conducción térmica como sólido.

**`endTime 10`** significa que simulamos los primeros **10 s físicos**.

**`deltaT 0.001`** significa:

[
Delta t = 0.001;s
]

Con 10 s totales:

[
N=rac{10}{0.001}=10000
]

por lo que el caso usa nominalmente **10 000 pasos de tiempo**.

**`writeInterval 100`** escribe cada 100 pasos:

[
100(0.001)=0.1;s
]

por lo que guardamos resultados aproximadamente cada **0.1 s**.

### Punto muy importante: `maxCo` NO controla actualmente (Delta t)

Tenemos:

```
adjustTimeStep no;
maxCo          0.25;
```

Por tanto, el paso temporal permanece fijo en 0.001 s. `maxCo=0.25` no hace que OpenFOAM reduzca automáticamente el timestep si se rebasa ese Courant.

El Courant se monitorea mediante nuestros diagnósticos, pero **no gobierna el timestep**.

### Opciones relevantes

#### A. `adjustTimeStep no` — nuestra opción

Ventajas:

- comparación limpia entre versiones;
- mismo número de pasos;
- fácil relacionar índices de timestep con tiempo físico;
- evita que una versión use más pasos que otra por cambios en velocidad.

Desventajas:

- si las velocidades aumentan mucho, el Courant puede crecer sin que OpenFOAM reduzca automáticamente (Delta t).

#### B. `adjustTimeStep yes`

OpenFOAM podría ajustar (Delta t) para respetar restricciones como `maxCo`.

Ventaja: más robustez ante cambios fuertes de velocidad.

Desventaja: la comparación de costo y convergencia entre casos deja de tener exactamente la misma secuencia temporal.

### Qué podría cambiar en los resultados si modificamos (Delta t)

Un timestep más grande:

- reduce costo;
- puede empeorar estabilidad;
- puede alterar el acoplamiento presión–velocidad;
- puede introducir error temporal;
- puede afectar la actualización de fracción líquida.

Un timestep más pequeño:

- aumenta costo;
- generalmente mejora resolución temporal;
- no garantiza automáticamente mejor convergencia espacial o física.

---

## 2.2 `system/blockMeshDict`

### Para qué sirve

Define:

- geometría;
- dimensiones;
- regiones/cellZones;
- discretización de malla;
- nombres geométricos de las fronteras.

### Geometría activa

```
convertToMeters 0.001;
```

Las coordenadas están escritas en milímetros y OpenFOAM las convierte a metros.

Metal:

- ancho X = 40 mm;
- altura Y = 40 mm;
- espesor Z = 10 mm.

Molde:

- 7 mm a izquierda;
- 7 mm a derecha;
- 15 mm abajo.

La parte superior central queda como:

```
metalTop
```

es decir, la superficie superior expuesta del metal.

### Malla activa

La malla gruesa está comentada.

La malla activa del metal es:

```
metal (80 80 1)
```

Así:

[
Delta x approx rac{40;mm}{80}=0.5;mm
]

[
Delta y approx 0.5;mm
]

En Z solo existe **una celda**.

### ¿Por qué es esencial `frontAndBack type empty`?

El caso es esencialmente **2-D**.

```
defaultPatch
{
    name frontAndBack;
    type empty;
}
```

`empty` le dice a OpenFOAM que la dirección Z no se resuelve como una dimensión física independiente.

Por tanto, nuestras celdas de convección representan una sección 2-D del Quick-Cup, no una estructura 3-D completa.

### Opciones

#### Malla más fina

Ejemplo: 160 × 160.

Posible efecto:

- mejor resolución de gradientes;
- mejor localización del frente de solidificación;
- potencialmente mejor resolución de celdas convectivas;
- mucho mayor costo.

En 2-D, duplicar X e Y aproximadamente cuadruplica el número de celdas del metal.

#### Malla más gruesa

Reduce costo, pero puede:

- suavizar gradientes;
- desplazar el frente;
- reducir artificialmente máximos de velocidad;
- aumentar difusión numérica.

#### Modelo 3-D

Requeriría más de una celda en Z y eliminar `empty`.

Puede permitir:

- estructuras convectivas tridimensionales;
- asimetrías fuera del plano;
- mayor fidelidad geométrica.

Costo: enorme comparado con el 2-D actual.

---

## 2.3 `system/fvSolution` global

### Para qué sirve

Contiene parámetros del algoritmo de acoplamiento global, especialmente PIMPLE para el caso multi-región.

Tenemos:

```
PIMPLE
{
    nOuterCorrectors         3;
    nCorrectors              2;
    nNonOrthogonalCorrectors 1;
}
```

### Interpretación

El `foamMultiRun` oficial crea un `pimpleMultiRegionControl`. Por tanto este nivel gobierna el acoplamiento general entre regiones.

**`nOuterCorrectors 3`**: hasta tres iteraciones externas de acoplamiento por timestep.

**`nCorrectors 2`**: correctores PISO/PIMPLE.

**`nNonOrthogonalCorrectors 1`**: corrección adicional asociada a no ortogonalidad.

### Opciones y efectos

Más outer correctors:

- mejor acoplamiento metal–molde dentro del timestep;
- mayor costo.

Menos:

- más barato;
- posible mayor desfase entre regiones.

Todos nuestros `relaxationFactors` están en 1.0. Eso significa que en este nivel **no estamos aplicando under-relaxation adicional** a U, h, p_rgh, etc.

---

## 2.4 `system/metal/fvSolution`

Este archivo controla los solucionadores lineales y el acoplamiento interno de la región del metal.

### Presión reducida

```
p_rgh
{
    solver      GAMG;
    tolerance   1e-7;
    relTol      0.01;
}
```

Usamos GAMG para presión.

La solución normal puede detenerse al cumplir el criterio absoluto o relativo. Para la solución final:

```
p_rghFinal
{
    $p_rgh;
    relTol 0;
}
```

`relTol 0` obliga al solve final a perseguir la tolerancia absoluta.

### Velocidad

```
U
{
    solver          PBiCGStab;
    preconditioner  DILU;
    tolerance       1e-8;
    relTol          0.05;
}
```

### Energía

`h` usa PBiCGStab/DILU con:

[
tolerance=10^{-9}
]

y `relTol=0.05`.

### PIMPLE regional

```
PIMPLE
{
    momentumPredictor   no;
    nOuterCorrectors    1;
    nCorrectors         2;
    nNonOrthogonalCorrectors 0;

    pRefPoint (0.02025 0.03975 0.005);
    pRefValue 1e5;
}
```

### `momentumPredictor no`

No se realiza una predicción independiente completa de momentum antes del corrector de presión.

Alternativa: `yes`.

Cambiarlo puede modificar:

- costo;
- secuencia de acoplamiento U–p;
- convergencia por timestep.

No debería cambiar la física idealmente convergida, pero sí puede cambiar estabilidad y error de acoplamiento.

### `pRefPoint` y `pRefValue`

Estos valores sirven como **referencia numérica de presión cuando el campo la necesita**.

No deben confundirse con:

```
constant/metal/pRef
```

que entra directamente en la definición física de `p_rgh`.

En V11, con `fixedFluxPressure`, la presión necesita referencia interna.

En V12/V13 la BC superior fija el valor de presión, por lo que OpenFOAM ya no necesita la referencia interna de la misma manera.

---

## 2.5 `system/metal/fvSchemes`

### Para qué sirve

Define **cómo se discretizan matemáticamente** derivadas, convección, difusión y gradientes.

Aquí no cambias la propiedad del material; cambias cómo las ecuaciones continuas se convierten en ecuaciones algebraicas sobre la malla.

### Tiempo

```
ddtSchemes
{
    default Euler;
}
```

Usamos Euler de primer orden temporal.

Ventaja: robusto.

Desventaja: mayor difusión/error temporal que esquemas de orden superior.

### Gradientes

```
Gauss linear
```

### Convección de momentum

```
div(phi,U) Gauss linearUpwind grad(U);
```

`linearUpwind` ofrece mayor precisión que upwind puro, aunque puede ser menos robusto.

### Convección de entalpía

```
div(phi,h) Gauss upwind;
```

Ésta es una decisión importante.

Upwind es robusto pero **numéricamente difusivo**.

Puede suavizar:

- gradientes térmicos;
- frentes;
- estructuras convectivas.

Una alternativa limitada o de mayor orden puede reducir difusión, pero requiere demostrar estabilidad.

### Laplacianos

```
Gauss linear corrected
```

La corrección trata la no ortogonalidad de la malla.

---

## 2.6 `system/mold/fvSchemes` y `system/mold/fvSolution`

El molde no tiene ecuación de momentum.

Su problema principal es conducción térmica:

[
ho C_vrac{partial T}{partial t}
=

ablacdot(k
abla T)
]

En el archivo tenemos:

```
laplacian(kappa,T) Gauss linear corrected;
```

y solver PCG/DIC para energía.

El molde y el metal se comunican mediante la BC térmica acoplada en la interfaz.

---

## 2.7 `system/functions`

### Para qué sirve

OpenFOAM Foundation v14 puede leer los function objects desde el archivo independiente:

```
system/functions
```

No es necesario meterlos directamente dentro de `controlDict`.

### Probe central

Tenemos un probe en:

[
(x,y,z)=(0.02,0.02,0.005);m
]

Registra cada timestep:

- U;
- T;
- p_rgh;
- rho;
- alpha líquida.

Eso permite construir una curva temporal central sin depender de ParaView.

### Includes

```
#include "researchDiagnostics"
#include "lineProfiles"
```

---

## 2.8 `researchDiagnostics`

Este archivo **no modifica las ecuaciones**. Genera información para auditar el caso.

Calculamos, entre otras cosas:

- vorticidad;
- tipo de flujo;
- flujo advectivo de energía;
- flujo de calor;
- energía total de frontera;
- flujo `phi` en `metalTop`;
- entalpía sensible integrada;
- fracción líquida promedio;
- gradientes térmicos;
- gradientes de densidad;
- velocidad de enfriamiento;
- tasa de solidificación;
- potencia de calor latente;
- Courant local;
- términos de Darcy, buoyancy y presión.

Ésta es una regla importante:

> **Un campo de diagnóstico puede existir en el caso sin ser una variable que controle la física.**

---

## 2.9 `system/lineProfiles`

Tomamos perfiles en:

- horizontal y = 20 mm;
- horizontal y = 30 mm;
- vertical x = 20 mm.

Sirven para comparar entre versiones:

- U;
- T;
- p_rgh;
- rho;
- alpha líquida;
- vorticidad;
- gradientes;
- tasas de solidificación;
- Courant.

La línea y=30 mm es especialmente útil para estudiar qué ocurre 10 mm debajo de `metalTop`.

---

## 2.10 `momentumPostProcessing`

Después de una corrida, reduce campos volumétricos complejos a:

- promedios;
- máximos;
- perfiles.

Esto disminuye la cantidad de datos que necesitamos versionar en Git.

No altera la simulación.

---

## 2.11 `createZonesDict`: existe, pero actualmente NO se usa

Tenemos el archivo, pero en `Allrun`:

```
##runApplication createZones
```

está comentado.

Las zonas `metal` y `mold` ya se definen desde `blockMeshDict`.

Por tanto:

> No debemos decir que actualmente usamos `createZones` para generar las regiones.

El archivo existe como alternativa/herramienta histórica.

---

# 3. Carpeta `constant/`: qué física existe

`constant` contiene lo que permanece constante como configuración física durante la corrida:

- propiedades termofísicas;
- gravedad;
- referencia de presión;
- modelo de solidificación;
- modelo de transporte de momentum.

---

# 3.1 `constant/metal/physicalProperties`

El archivo contiene:

```
#include "materials/castIron"
```

Por tanto el material activo es:

```
constant/metal/materials/castIron
```

---

## Puente con JMatPro — estado metodológico

La baseline C11 usa actualmente propiedades constantes para `rho`, `Cp` y transporte. Esto **no elimina JMatPro**: antes de G1 debe cerrarse la puerta J0 definida en `JMATPRO_OPENFOAM_TRACEABILITY_ES.md`.

Reglas:
- no llamar “JMatPro-derived” a un valor sin conservar su exportación/fuente;
- usar `rho(T)` de JMatPro para justificar `rhoRef` y derivar `beta` en la formulación Boussinesq de volumen fijo;
- comparar `fL_JMatPro(T)` contra la relación de fase real de `solidificationMeltingSource`, especialmente porque `alpha1e=0.8`;
- evaluar `Cp(T)` y `k(T)` reales antes de crear el caso G1 definitivo;
- mantener C11 congelado como baseline y hacer los cambios físicos en un descendiente G1.

La herramienta reproducible para esta etapa es:

`analysis_tools/jmatpro_property_bridge.py`

y el esquema de datos está en:

`thermodynamics/jmatpro/JMATPRO_EXPORT_TEMPLATE.csv`.

---

# 3.2 Hierro — propiedades térmicas y de transporte

En B11 tenemos:

```
type            heRhoThermo;
transport       const;
thermo          hConst;
equationOfState icoTabulated;
energy          sensibleEnthalpy;
```

Esto significa:

- termodinámica basada en entalpía sensible;
- Cp constante;
- transporte constante;
- densidad dependiente de T mediante tabla.

Valores:

[
C_p=827;J/(kg,K)
]

[
mu=5.5	imes10^{-3};Pa,s
]

[
Pr=0.14
]

OpenFOAM, con `constTransport` y Pr especificado, calcula:

[
k=rac{C_pmu}{Pr}
]

donde:

- (k): conductividad térmica [W/(m K)];
- (C_p): calor específico [J/(kg K)];
- (mu): viscosidad dinámica [Pa s];
- (Pr): número de Prandtl [-].

Con nuestros valores:

[
k approx
rac{827(5.5	imes10^{-3})}{0.14}
approx 32.49;W/(mK)
]

Así que aunque no escribimos directamente `kappa 32.49`, **ésa es aproximadamente la conductividad térmica que resulta del modelo actual**.

### Opciones

Podemos especificar propiedades:

- constantes;
- dependientes de temperatura;
- tabuladas.

Hacer (C_p(T)), (k(T)) o (mu(T)) más realistas puede cambiar:

- difusión térmica;
- velocidad de convección;
- tiempo de solidificación;
- respuesta térmica durante recalescencia.

---

# 3.3 Diferencia fundamental B vs C

## Familia B

```
equationOfState icoTabulated;
```

y existe una tabla:

[
ho=ho(T)
]

Ejemplos:

- 1473.15 K → 6820 kg/m³;
- 1573.15 K → 6740 kg/m³;
- 1773.15 K → 6580 kg/m³.

Además en `fvModels`:

```
beta 0;
```

Así evitamos añadir una segunda fuerza de buoyancy mediante el término Boussinesq del modelo de solidificación.

La flotación de B proviene de la densidad variable utilizada por el solver.

## Familia C

Tenemos:

```
equationOfState rhoConst;
rho 6820;
```

La densidad termodinámica no cambia con T.

Entonces usamos en el modelo de solidificación:

```
beta   1.13e-04;
rhoRef 6820;
```

para generar buoyancy mediante una aproximación tipo Boussinesq.

### Qué estamos comparando realmente

B:

[
ho=ho(T)
]

C:

[
ho=ho_{ref}
]

pero la fuerza de flotación térmica se representa mediante:

[
mathbf{a}_b
=
mathbf{g}etaDelta T
]

en el modelo de solidificación.

Por eso no debemos activar simultáneamente una fuerte (ho(T)) y un (eta) adicional sin revisar si estamos duplicando la misma física.

---

# 3.4 `constant/metal/fvModels`: solidificación

Usamos:

```
type solidificationMeltingSource;
```

OpenFOAM Foundation describe este modelo como un método de malla fija tipo entalpía–porosidad.

No dibuja explícitamente una nueva geometría sólido/líquido.

En cambio:

- añade calor latente a la ecuación de energía;
- genera una fracción líquida;
- amortigua el momentum al solidificar.

## Parámetros actuales

```
Tsol    1423;
Tliq    1473;
L       2.286e5;
alpha1e 0.8;
relax   0.1;
Cu      1e5;
q       1e-3;
```

### Solidus y liquidus

[
T_{sol}=1423;K
]

[
T_{liq}=1473;K
]

El intervalo nominal es:

[
Delta T_{mushy}=50;K
]

Modificar este rango cambia dónde y durante cuánto intervalo térmico coexisten sólido y líquido.

### Calor latente

[
L=2.286	imes10^5;J/kg
]

Mayor (L):

- más energía debe extraerse para solidificar;
- mayor retraso térmico;
- mayor posibilidad de meseta/recalescencia aparente según condiciones.

Menor (L):

- solidificación térmicamente más rápida.

### `alpha1e = 0.8`

Éste es un parámetro importante y debe defenderse.

En la implementación OF14, mientras la fracción líquida (alpha_L) está por debajo de `alpha1e`, la temperatura de fase usada por el modelo queda limitada por (T_{sol}). La fracción restante entre 0.8 y 1 se distribuye en el intervalo entre solidus y liquidus.

Por tanto `alpha1e` cambia directamente la relación:

[
T leftrightarrow alpha_L
]

y puede afectar fuertemente:

- liberación de calor latente;
- velocidad de avance del frente;
- forma de la curva de enfriamiento.

No es un parámetro numérico inocuo.

### `relax = 0.1`

El valor por defecto documentado del modelo es 0.9.

Nosotros usamos 0.1.

El código actualiza aproximadamente la fracción líquida mediante una corrección proporcional a:

[
alpha_L^{new}
=
alpha_L^{old}
+
relax;
rac{C_pDelta T}{L}
]

limitándola entre 0 y 1.

Un `relax` menor:

- amortigua la actualización;
- puede ayudar a estabilidad;
- pero puede introducir retraso artificial en la respuesta de fase y sensibilidad al timestep.

Por tanto debe tratarse como parámetro numérico del modelo que requiere justificación/sensibilidad.

### `Cu = 1e5` y `q=1e-3`

El modelo usa un término de Darcy:

[
S=
-C_u
rac{(1-alpha_L)^2}
{alpha_L^3+q}
]

donde:

- (C_u): constante de zona pastosa [1/s];
- (alpha_L): fracción líquida [-];
- (q): regularización [-].

Cuando:

[
alpha_Lightarrow1
]

el amortiguamiento desaparece.

Cuando:

[
alpha_Lightarrow0
]

el término se vuelve muy grande y la velocidad es fuertemente amortiguada.

Mayor `Cu`:

- frena más rápidamente el movimiento en la zona mushy/sólida.

Menor `Cu`:

- permite más flujo dentro de regiones parcialmente solidificadas.

`q` evita una singularidad cuando (alpha_L	o0).

Estos parámetros pueden modificar la convección cerca del frente y, por tanto, también el transporte térmico.

---

# 3.5 `constant/metal/momentumTransport`

Tenemos:

```
simulationType laminar;
```

Ésta es una decisión física.

Aunque dentro del archivo aparece una sección RAS con `kOmegaSST`, tenemos:

```
turbulence off;
```

y `simulationType laminar`.

Por tanto **no estamos resolviendo turbulencia RANS**.

Los archivos `k`, `epsilon`, `omega`, `nut` y `alphat` que aparecen en `0/metal` no deben interpretarse como prueba de que el caso sea turbulento.

### Alternativas

- laminar;
- RANS;
- LES, dependiendo del solver/modelo.

Antes de activar turbulencia habría que justificarla con escalas de flujo, Reynolds, geometría y evidencia experimental/numerical.

---

# 3.6 Gravedad

```
value (0 -9.81 0);
```

Así:

[
mathbf g=(0,-9.81,0);m/s^2
]

Y es coherente con Y como dirección vertical.

Cambiar el signo invertiría físicamente la dirección de buoyancy.

---

# 3.7 `constant/metal/pRef`

Tenemos:

[
p_{Ref}=100000;Pa
]

En OF14:

[
p_{rgh}=p-ho gh-p_{Ref}
]

donde:

- (p_{rgh}): presión reducida [Pa];
- (p): presión estática [Pa];
- (ho): densidad [kg/m³];
- (gh): potencial gravitatorio específico [m²/s²];
- (p_{Ref}): offset de presión [Pa].

No tenemos archivo `hRef`, así que OF14 usa:

[
h_{Ref}=0
]

---

# 3.8 Propiedades del molde

`constant/mold/physicalProperties` contiene:

```
#include "materials/silica"
```

Por tanto el material ACTIVO del molde es sílica.

Propiedades:

[
ho=1500;kg/m^3
]

[
k=2;W/(mK)
]

[
C_v=700;J/(kgK)
]

### Importante

También existen:

- `steel4140`;
- `steel4140cons`.

Pero actualmente **no están incluidos por `physicalProperties`**.

Por tanto no participan en la simulación.

Que un archivo exista en la carpeta no significa que el solver lo esté utilizando.

---

# 4. Carpeta `0/`: cómo inicia el problema y qué pasa en las fronteras

La carpeta `0` contiene campos iniciales y condiciones de frontera.

En un caso multi-región:

```
0/metal/
0/mold/
```

---

# 4.1 `0/metal/U`: velocidad

Tenemos:

```
internalField uniform (0 0 0);
```

El metal inicia en reposo:

[
mathbf U_0=(0,0,0);m/s
]

### `metalTop`

```
type slip;
```

`slip` impide velocidad normal a la pared pero no impone esfuerzo tangencial de una pared no-slip.

Conceptualmente:

[
U_n=0
]

pero la componente tangencial puede existir.

### `metal_to_mold`

```
type noSlip;
```

Entonces:

[
mathbf U=0
]

en la interfaz metal–molde.

### Opciones relevantes para `metalTop`

#### `slip`

Apropiada si queremos:

- tapa geométricamente impermeable;
- sin fricción tangencial.

#### `noSlip`

Representaría una pared sólida rígida en contacto mecánico con el metal.

Suprimiría más fuertemente circulación cerca del top.

#### BC abierta de velocidad

Por ejemplo una condición compatible con entrada/salida.

Sería necesaria si `metalTop` se modelara realmente como frontera abierta atmosférica con flujo normal permitido.

Ésta es la razón por la que **poner presión atmosférica y mantener `U=slip` no convierte mágicamente el modelo en una superficie libre física**.

---

# 4.2 `0/metal/p_rgh`: la decisión V11–V13

`p_rgh` es la variable de presión reducida que resuelve el problema buoyant.

Dimensiones:

[
[kg,m^{-1},s^{-2}]
]

es decir Pa.

## V11

En `metalTop`:

```
type  fixedFluxPressure;
value $internalField;
```

### Qué hace

No fija una presión determinada.

Ajusta el gradiente de presión para que el flujo de frontera sea consistente con la BC de velocidad y las fuerzas de cuerpo.

Con:

```
U = slip
```

es una combinación muy natural para una **tapa rígida impermeable bajo gravedad**.

V11 ya lo verifica directamente: B11 alcanza max `|sum(phi)| = 1.694066e-21 kg/s` y energía advectiva integrada ≈ 0 J; C11 registra `sum(phi)=0` y energía advectiva integrada = 0 J. Por tanto la impermeabilidad ya no depende solo de la evidencia histórica V9.

## V12

```
type fixedValue;
value uniform 2667.739248;   // B
```

o:

```
2676.168;                    // C
```

### Qué hace

Impone directamente:

[
p_{rgh}=valor
]

Es una condición tipo Dirichlet.

Los valores fueron calculados para ser compatibles inicialmente con 1 atm en y=40 mm.

En B:

[
p_{rgh}=2667.739248;Pa
]

En C:

[
p_{rgh}=2676.168;Pa
]

### Consecuencia

En C, donde (ho) es constante, el valor sigue siendo compatible con la misma presión atmosférica.

En B, donde (ho(T)) cambia, congelar (p_{rgh}) significa que la presión estática reconstruida puede cambiar.

Por tanto V12 prueba:

> **presión reducida fija**

no necesariamente:

> presión atmosférica fija.

## V13

Usa:

```
type prghPressure;
p    uniform 0;
rho  rho;
```

Como:

[
p_{Ref}=100000;Pa
]

ese `p uniform 0` es el offset respecto al valor de referencia.

La presión física reconstruida es aproximadamente:

[
p=100000;Pa
]

en la frontera.

### Ventaja

Si cambia (ho), OpenFOAM ajusta (p_{rgh}) automáticamente.

Por eso V13 representa mejor:

> **presión estática atmosférica conocida**

que V12.

---

# 4.3 El `internalField` actual de `p_rgh`

V11 contiene:

```
internalField uniform 1e5;
```

Esto debe entenderse como **valor inicial numérico**, no como una descripción hidrostática físicamente consistente del campo completo.

Con:

[
p_{rgh}=p-ho gh-p_{Ref}
]

un campo hidrostático consistente no sería uniformemente (10^5) Pa en todo el metal bajo nuestras referencias actuales.

El pressure corrector reajusta el campo al comenzar.

Para comparaciones V11/V12/V13 mantenemos el mismo estado interno inicial para no introducir otra variable.

Para un futuro caso final podría evaluarse una inicialización hidrostática más consistente, pero eso sería otra modificación que debe validarse por separado.

---

# 4.4 `0/metal/p`

Tenemos:

```
type calculated;
```

`p` no es el campo independiente que estamos imponiendo en V11.

Se reconstruye a partir de:

[
p=p_{rgh}+ho gh+p_{Ref}
]

Por eso no debemos mirar `p` y `p_rgh` como si fueran la misma variable.

---

# 4.5 `0/metal/T`

Inicialmente:

[
T_{metal,0}=1500;K
]

### Top del metal

Tenemos:

```
type       externalWallHeatFluxTemperature;
h          uniform 10;
Ta         constant 300;
emissivity 0.3;
```

Estamos modelando pérdida de calor al ambiente mediante:

1. convección;
2. radiación.

Convección aproximadamente:

[
q''_{conv}=h(T_s-T_a)
]

donde:

- (h=10;W/(m^2K));
- (T_a=300;K).

A 1500 K:

[
q''_{conv}approx10(1500-300)
=12000;W/m^2
]

La radiación escala con:

[
q''_{rad}
=
epsilonsigma(T_s^4-T_a^4)
]

donde:

- (epsilon=0.3);
- (sigma): constante de Stefan–Boltzmann.

A 1500 K, el término radiativo inicial es del orden de **86 kW/m²**, considerablemente mayor que los ~12 kW/m² convectivos.

Por tanto la emisividad puede influir mucho en el enfriamiento del top.

### Opciones

- `fixedValue`: imponer T conocida;
- flujo de calor conocido;
- `zeroGradient`: aproximación adiabática;
- convección+radiación como ahora.

Elegir otra cambia directamente la extracción de energía y, por tanto:

- curva de enfriamiento;
- tiempo de solidificación;
- gradientes;
- convección.

---

# 4.6 Interfaz térmica metal–molde

Metal:

```
type coupledTemperature;

h
{
    type            wallLayersHeatTransferCoefficient;
    thicknessLayers (2e-4);
    kappaLayers     (1e-1);
}
```

La capa representa una resistencia térmica tipo air gap.

Tenemos:

[
delta=2	imes10^{-4};m
]

[
k_{gap}=0.1;W/(mK)
]

La resistencia superficial es:

[
R''=rac{delta}{k}
=
rac{2	imes10^{-4}}{0.1}
=
0.002;m^2K/W
]

y el coeficiente equivalente:

[
h_{gap}=rac{1}{R''}
=rac{k}{delta}
=500;W/(m^2K)
]

OpenFOAM 14 implementa esta capa mediante suma de resistencias y promedio armónico.

### Opciones

#### Sin air gap

Mayor transferencia metal–molde.

Probablemente:

- enfriamiento más rápido;
- frente más rápido;
- gradientes distintos.

#### Gap más resistivo

Reducir (k) o aumentar (delta):

- menor extracción;
- solidificación más lenta;
- mayor temperatura del metal.

#### Contact conductance experimental

Idealmente el contacto debería justificarse mediante medición/literatura o calibración independiente.

---

# 4.7 `0/mold/T`

Inicialmente:

[
T_{mold,0}=300;K
]

Las superficies exteriores usan:

```
h          10;
Ta         300;
emissivity 0.5;
```

Por tanto el molde también pierde/recibe calor por convección y radiación hacia ambiente.

En la interfaz:

```
type coupledTemperature;
```

recibe el flujo térmico del metal.

---

# 4.8 Fracción líquida inicial

`phaseChangeSource:alpha1`:

```
internalField uniform 1.0;
```

Así:

[
alpha_L(0)=1
]

El metal inicia totalmente líquido, consistente con:

[
T_0=1500;K > T_{liq}=1473;K
]

Éste es un chequeo de consistencia importante.

Si inicializáramos (alpha_L=0) con T=1500 K, estaríamos introduciendo un estado físicamente contradictorio.

---

# 4.9 Archivos de turbulencia presentes pero no activos como modelo turbulento

En `0/metal` aparecen:

- k;
- epsilon;
- omega;
- nut;
- alphat.

Pero:

```
simulationType laminar;
```

Por tanto el caso sigue siendo laminar.

No debemos deducir la física activa solo por la existencia de esos archivos.

---

# 4.10 Campos derivados en `0/metal`

También aparecen archivos como:

- vorticity;
- gradT;
- gradRho;
- CoCell;
- coolingRate;
- pRghAcceleration;
- phaseChangeDarcyAcceleration;
- latentHeatRateVol.

Muchos son campos generados por nuestros function objects o diagnósticos.

En general su propósito es **medir la solución**, no determinarla.

La excepción importante es `phaseChangeSource:alpha1`, que sí es leído por el modelo de solidificación mediante `READ_IF_PRESENT`.

---

# 5. Scripts del caso

## 5.1 `Allrun`

El orden actual es:

1. `blockMesh`
2. `splitMeshRegions -cellZones all`
3. `foamMultiRun`
4. postproceso de momentum si el solver terminó correctamente;
5. `foamLog`;
6. crea `buoyant.foam`.

### Qué significa

`blockMesh` crea la malla inicial.

`splitMeshRegions` separa las cellZones en regiones `metal` y `mold`.

`foamMultiRun` ejecuta los módulos fluido+sólido.

`foamPostProcess` reduce diagnósticos.

`foamLog` extrae residuos, Courant, continuidad, iteraciones y costo desde el log.

---

## 5.2 `Allclean`

Elimina resultados generados y devuelve el caso a una condición limpia para volver a correr.

Es importante usarlo al comparar versiones para evitar que resultados antiguos contaminen una ejecución nueva.

---

# 6. Carpetas generadas después de correr

## `postProcessing/`

Contiene:

- probes;
- perfiles;
- integrales;
- function objects;
- diagnósticos de energía;
- resultados reducidos.

No define la física.

## `logs/`

Es generado por `foamLog`.

Contiene series temporales de:

- residuos;
- Courant;
- continuidad;
- iteraciones;
- etc.

## Directorios de tiempo

Ejemplos:

```
0.1/
0.2/
...
10/
```

Contienen los campos escritos por el solver a esos tiempos.

---

# 7. Qué cambia realmente entre V11, V12 y V13

| Versión | U en metalTop | p_rgh en metalTop | Interpretación principal |
|---|---|---|---|
| V11 | slip | fixedFluxPressure | tapa impermeable; presión ajusta gradiente para respetar flujo |
| V12 | slip | fixedValue | presión reducida fijada directamente |
| V13 | slip | prghPressure | presión estática atmosférica fijada; p_rgh se adapta |

Todo lo demás debe permanecer igual para que la comparación sea controlada.

La variable experimental es:

> **tipo de condición de frontera de presión en metalTop**.

---

# 8. Cómo afectan las decisiones principales al resultado

| Decisión | Si aumenta/cambia | Resultado esperado |
|---|---|---|
| resolución de malla | más fina | más detalle, mayor costo, posibles máximos más altos |
| deltaT | mayor | menos costo, más error temporal/riesgo numérico |
| Tsol/Tliq | cambian | cambia intervalo de solidificación |
| L | aumenta | más energía latente, solidificación térmicamente más lenta |
| alpha1e | cambia | cambia relación T–fracción líquida |
| Cu | aumenta | mayor frenado de flujo en mushy |
| q | disminuye | mayor penalización cerca del sólido |
| relax alpha | disminuye | fase cambia más lentamente por timestep |
| viscosidad | aumenta | menor velocidad/convección |
| k del metal | aumenta | mayor difusión térmica |
| air-gap resistance | aumenta | menor flujo metal→molde |
| emissivity | aumenta | mayor pérdida radiativa |
| h externo | aumenta | mayor pérdida convectiva |
| fixedFluxPressure → fixedValue | fija p_rgh | cambia referencia/gradiente de presión y potencialmente flujo |
| fixedValue → prghPressure | fija p estática | p_rgh responde a rho y altura |
| rhoConst → rho(T) | densidad variable real | cambia continuidad, buoyancy y presión |
| laminar → turbulento | activa transporte turbulento | mayor mezcla/transporte, física distinta |

---

# 9. Cómo debes auditar cualquier cambio futuro

Antes de cambiar un parámetro, responde cinco preguntas:

### 1. ¿Dónde vive?

- `system` → numérica/ejecución;
- `constant` → física/modelo/material;
- `0` → condición inicial/frontera.

### 2. ¿Qué ecuación afecta?

Ejemplo:

`Cu` → momentum en zona mushy.

`L` → energía.

`fixedValue p_rgh` → presión/frontera y acoplamiento con U.

### 3. ¿Es propiedad física o parámetro numérico?

Ejemplos:

- (L): material/física;
- (mu): material/física;
- `relax 0.1`: numérico/modelo;
- `tolerance 1e-7`: numérico;
- `writeInterval`: salida de datos, no física.

### 4. ¿Qué resultado debería cambiar si la hipótesis es correcta?

Debemos poder predecir cualitativamente el efecto antes de correr.

### 5. ¿Qué diagnóstico demuestra que ocurrió?

Ejemplo V11–V13:

- `metalTopPhiSum`;
- energía advectiva;
- p_rgh;
- presión;
- U;
- continuidad.

---

# 10. Preguntas de defensa que debes poder contestar

## “¿Qué solver estás usando?”

No responder solamente “OpenFOAM”.

Respuesta técnica:

> Uso OpenFOAM Foundation v14 con `foamMultiRun`. La región `metal` usa el módulo `fluid` y la región `mold` el módulo `solid`, acoplados térmicamente.

## “¿Tu simulación es 2-D o 3-D?”

> Es un modelo 2-D representado por una malla de una celda en Z y patches `frontAndBack=empty`. La geometría tiene un espesor nominal de 10 mm, pero no permite variación física resuelta en Z.

## “¿Tu flujo es turbulento?”

> No. `momentumTransport` usa `simulationType laminar`. Existen archivos k/epsilon/omega históricos/de soporte, pero el modelo RANS está desactivado.

## “¿Qué solidification model usas?”

> `solidificationMeltingSource`, método de malla fija tipo entalpía–porosidad. La fase sólida se representa mediante fracción líquida y un sumidero Darcy de momentum; no mediante una interfaz geométrica móvil.

## “¿De dónde sale la conductividad del metal?”

> El modelo usa `constTransport` con (C_p=827), (mu=5.5	imes10^{-3}) y (Pr=0.14). OpenFOAM calcula (k=C_pmu/Pr), aproximadamente 32.49 W/(m K).

## “¿Qué representa tu air gap?”

> Una resistencia térmica de 0.2 mm con k=0.1 W/(m K), equivalente a una conductancia superficial de 500 W/(m² K).

## “¿Por qué fixedFluxPressure?”

> Porque si `metalTop` representa una tapa impermeable con `U=slip`, `fixedFluxPressure` ajusta el gradiente de presión para ser compatible con el flujo impuesto por la condición de velocidad y la gravedad.

## “¿Por qué fixedValue?”

> Para probar explícitamente la hipótesis de imponer un valor conocido de presión reducida. Es una condición Dirichlet y fija directamente (p_{rgh}).

## “¿Por qué prghPressure?”

> Porque si la interpretación es una superficie a presión estática atmosférica, `prghPressure` fija esa presión física y recalcula (p_{rgh}) considerando densidad y altura.

## “¿Cuál es la diferencia entre pRef de constant y pRefValue de fvSolution?”

> `constant/metal/pRef` entra en la definición física de (p_{rgh}). `pRefPoint/pRefValue` es un anclaje numérico usado cuando el campo de presión necesita una referencia interna.

## “¿maxCo=0.25 controla el timestep?”

> No en el caso actual, porque `adjustTimeStep=no`. El timestep permanece en 0.001 s; el Courant se monitorea.

---

# 11. Jerarquía para aprender el caso

Si necesitas estudiar el caso para defenderlo oralmente, sigue este orden:

1. `system/controlDict` — qué problema ejecutas y por cuánto tiempo.
2. `system/blockMeshDict` — qué geometría y malla resolvemos.
3. `system/fvSolution` y `system/<region>/fvSolution` — cómo se acoplan y resuelven las ecuaciones.
4. `system/<region>/fvSchemes` — cómo se discretizan.
5. `constant/metal/physicalProperties` — propiedades del hierro.
6. `constant/metal/fvModels` — solidificación/porosidad/buoyancy.
7. `constant/metal/g` y `pRef` — gravedad y presión.
8. `constant/mold/physicalProperties` — propiedades del molde.
9. `0/metal/U` — velocidad inicial y fronteras.
10. `0/metal/p_rgh` — presión y diferencia V11/V12/V13.
11. `0/metal/T` — condiciones térmicas del metal.
12. `0/mold/T` — condiciones térmicas del molde.
13. `phaseChangeSource:alpha1` — estado inicial líquido.
14. `system/functions` y diagnósticos — cómo demostramos que la solución tiene sentido.
15. `Allrun` — secuencia completa de ejecución.

---

# 12. Regla profesional

Nunca justifiques una configuración diciendo:

> “porque así estaba en el tutorial”  
> “porque fue la que corrió”  
> “porque ChatGPT me dijo”  
> “porque es la más común”.

La defensa correcta siempre debe tener esta estructura:

> **Esta opción impone matemáticamente X. La elegimos porque nuestro dominio representa físicamente Y. Frente a la alternativa Z, esperamos que cambie W. Lo comprobamos mediante el diagnóstico Q.**

Ese patrón sirve para condiciones de frontera, propiedades, solvers, esquemas, timestep y modelos físicos.

---

## Fuentes técnicas principales

Configuración real:
- `cases_controlled_buoyancy/B11_topFixedFlux_airGapOF14/`
- `cases_controlled_buoyancy/C11_topFixedFlux_airGapOF14/`
- V12/V13 correspondientes.

OpenFOAM Foundation v14:
- `applications/solvers/foamMultiRun/foamMultiRun.C`
- `src/fvModels/general/solidificationMelting/solidificationMelting.H/.C`
- `src/finiteVolume/cfdTools/general/buoyancy/buoyancy.H/.C`
- `src/finiteVolume/fields/fvPatchFields/derived/PrghPressure/`
- `src/finiteVolume/fields/fvPatchFields/derived/fixedFluxPressure/`
- `src/ThermophysicalTransportModels/coupledThermophysicalTransportModels/coupledTemperature/`
- `src/ThermophysicalTransportModels/coupledThermophysicalTransportModels/wallLayersHeatTransferCoefficient/`
- `src/thermophysicalModels/specie/transport/const/constTransportI.H`.


---

## 13. MAZAPÁN — cierre completo de una corrida OpenFOAM

**MAZAPÁN** es el protocolo completo de cierre científico y documental de una o varias corridas del proyecto Quick-Cup. **No termina en el `git push`.**

Cuando Michel diga **“MAZAPÁN”** o **“haz MAZAPÁN”**, se debe ejecutar este flujo completo:

1. **Confirmar la corrida local**
   - comprobar `latestTime`;
   - comprobar `End`;
   - buscar `FOAM FATAL`, segmentation fault, floating point exception o procesos killed;
   - registrar el código de retorno cuando exista un runner.

2. **Sincronizar las carpetas completas de los casos**
   - añadir cada carpeta completa con `git add cases_controlled_buoyancy/<CASO>`;
   - dejar que `.gitignore` filtre automáticamente tiempos calculados, mallas generadas, archivos ParaView, imágenes, ZIP y demás outputs no versionables;
   - no enumerar manualmente `logs/`, `postProcessing/`, etc.;
   - no usar `git add -f` salvo una excepción explícita.

3. **Preservar primero los resultados locales**
   - commit local de resultados;
   - `git pull --rebase origin main`;
   - `git push origin main`;
   - nunca usar `force push` para resolver un remoto adelantado con resultados locales válidos.

4. **Verificar lo que realmente quedó en GitHub**
   - confirmar el commit;
   - confirmar que `logs/`, `postProcessing/` y demás evidencia científica necesaria sí quedaron versionados;
   - comprobar que outputs pesados/temporales no quedaron trackeados accidentalmente.

5. **Limpiar tracking accidental**
   - recordar que `.gitignore` no deja de rastrear archivos que ya estaban versionados;
   - si un tiempo calculado u otro output ignorado sigue trackeado, retirarlo del árbol/índice de Git **sin confundirlo con borrar el resultado local**;
   - verificar después que la ruta ya no esté trackeada.

6. **Auditar científicamente los resultados**
   Como mínimo, cuando existan:
   - flujo de masa en fronteras relevantes, incluido `metalTopPhiSum`;
   - energía advectiva y heat/energy flux;
   - residuos iniciales/finales de `p_rgh`;
   - contracción entre outer correctors;
   - continuidad;
   - Courant;
   - T, U, rho y fracción líquida;
   - balances y magnitudes integradas;
   - comparación contra el caso padre/baseline y contra la familia equivalente;
   - cualquier diagnóstico específico de la hipótesis probada.

7. **Separar estados de evidencia**
   - `RUN-VERIFIED`: terminó limpiamente;
   - `ANALYSIS-VERIFIED`: los resultados fueron auditados;
   - una corrida que da PASS **no** se declara físicamente válida solo por haber terminado.

8. **Crear o actualizar el registro de análisis**
   - guardar resumen reproducible en `analysis_results/` cuando el análisis lo amerite;
   - guardar métricas/tablas derivadas que permitan reconstruir la conclusión.

9. **Actualizar la bitácora global**
   - `PROJECT_AUDIT_LOG_ES.md`;
   - registrar qué se corrió, resultados, interpretación, decisión y nueva pregunta técnica.

10. **Actualizar las notas de CADA caso afectado**
    - `CASE_NOTES.md`: estado actual, resultados medidos, interpretación, advertencias y decisión;
    - `CASE_VARIANT.md`: propósito de la variante y conclusión posterior a la corrida;
    - no dejar una nota en modo “qué pretendemos probar” después de que el caso ya fue ejecutado y analizado.

11. **Actualizar documentación de comparación**
    Según lo que cambie:
    - README de la familia/prueba;
    - `VALIDATION_MATRIX_ES.md`;
    - documentación de baseline/casos canónicos.

12. **Actualizar las guías de aprendizaje**
    Si el resultado cambia o fortalece cómo entendemos el modelo:
    - `CASE_GUIDE_ES.md`;
    - `CASE_GUIDE_INTERACTIVE_ES.html`;
    - incorporar qué opción se probó, qué ocurrió realmente, qué opción queda como baseline y cómo defender la decisión oralmente.

13. **Actualizar el manual de comandos cuando aparezca un procedimiento reutilizable**
    - `OPENFOAM_COMMAND_MANUAL_ES.md`;
    - documentar comandos nuevos o corregidos que deban repetirse en futuras corridas.

14. **Reevaluar explícitamente la baseline**
    - decidir si la evidencia mantiene, reemplaza o limita la baseline vigente;
    - si la baseline cambia o queda reafirmada, reflejarlo en las notas de la baseline y de las variantes comparadas.

15. **Cerrar con verificación de consistencia documental**
    - ninguna guía debe llamar “pendiente” a una corrida ya analizada;
    - ninguna nota debe llamar “baseline” a una variante descartada;
    - los números de las notas deben coincidir con `analysis_results/`;
    - Git debe quedar sin outputs generados accidentalmente trackeados.

### Flujo Git de MAZAPÁN

```bash
cd ~/OpenFOAM/QuickCup_Solidification

git add \
cases_controlled_buoyancy/<CASO_1> \
cases_controlled_buoyancy/<CASO_2>

git commit -m "results: add simulation outputs"
git pull --rebase origin main
git push origin main
```

### Regla corta

> **MAZAPÁN = sincronizar + auditar + decidir + documentar + limpiar + verificar consistencia.**

El `git push` es solo la mitad del flujo.

