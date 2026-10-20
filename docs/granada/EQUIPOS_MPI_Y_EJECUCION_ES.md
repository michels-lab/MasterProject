# C3D-01 — Inventario de cómputo y plan MPI (sin ejecutar simulaciones)

**Operación Granada | 2026-10-19 | Estado: planificación, no pruebas de rendimiento.**

## Evidencia proporcionada por el investigador

| Computadora | Entorno | RAM total reportada por \`free -h\` | Swap | Procesador |
|---|---|---:|---:|---|
| \`Michel-DuarteHP\` | Ubuntu/WSL, de acuerdo con la sesión | 7.5 GiB | 2.0 GiB | **No medido en esta sesión** |
| \`DESKTOP-I00527M\` | Ubuntu bajo WSL (\`systemd-detect-virt = wsl\`) | 7.7 GiB | 2.0 GiB | AMD Ryzen 5 5600X, 6 núcleos físicos / 12 procesadores lógicos |

La RAM **física instalada en Windows** no se comprobó en el segundo equipo; \`free -h\` solo muestra la memoria que WSL hace visible. Aumentar asignación con \`%USERPROFILE%\\.wslconfig\` depende de memoria física, reserva de Windows y versión de WSL. No asumir que asignar 24 GiB es posible, no modificar \`.wslconfig\` sin inspección ni configurar el mismo tamaño para ambos equipos.

## División de trabajo propuesta (no restricción rígida)

- Laptop: experimentos B de superficie libre metal–aire en 2D, análisis de resultados y FoamLENS; también puede usarse para pequeñas pruebas estáticas y pruebas de malla.
- Segundo equipo: candidata para \`C3D-01\` metal/molde, después de verificar RAM física, almacenamiento, WSL y rendimiento real.
- Mantener el solver en el equipo del investigador, nunca ejecutar CFD ni instalar OpenFOAM en GitHub Actions.
- No afirmar viabilidad de >1 millón de celdas por disponer de 12 hilos: la RAM disponible, coste de solvers, regiones, campos, tamaño de malla, comunicación y disco también limitan.

## Comprobación no destructiva antes de cualquier cambio de WSL

En **Ubuntu del segundo equipo**:

\`\`\`bash
free -h
systemd-detect-virt
lscpu | grep -E 'Model name|CPU\(s\)|Core\(s\) per socket|Thread\(s\) per core'
df -h ~
command -v blockMesh
command -v mpirun
\`\`\`

En **Windows del segundo equipo**, revisar Administrador de tareas → Rendimiento → Memoria (GB físicos). Después inspeccionar configuración WSL existente antes de editarla. No reiniciar/apagar WSL mientras haya una corrida sin finalizar.

## MPI: distinción entre mesh, descomposición y solver

El diccionario \`system/decomposeParDict\` incluye, por ejemplo, \`numberOfSubdomains 6;\` y \`method scotch;\` para un ensayo con 6 procesos. **Es un ejemplo educativo, no un archivo creado ni una decisión de producción**. En ejecución multi-región puede ser necesario adaptar parámetros por región a la versión específica de OpenFOAM y verificar la descomposición.

- \`blockMesh\`: crea la caja de fondo, normalmente en serie.
- \`decomposePar\` / descomposición de regiones: prepara archivos \`processor*\` según la malla física y estructura del caso; opciones como \`-allRegions\` requieren validación de arquitectura.
- \`mpirun -np N snappyHexMesh -parallel\`: procedimiento posible para mallar en paralelo **solo cuando exista su diccionario correcto y esté prevista esa estrategia**.
- \`mpirun -np N foamMultiRun -parallel\`: ejecución conceptual del caso final multirregión de Foundation v14. No sustituir ciegamente por \`foamRun\`; este último aplica a otra arquitectura de solver.
- \`reconstructPar\` y opciones de regiones dependen de la configuración y del tipo de salida; diseñar después de comprobar resultados por subdominio.

**No ejecutar estos comandos todavía** en C3D-01, ya que solo cuenta con diccionarios de caja de fondo, sin mallas finales, regiones ni propiedades físicas 3D validadas. No se ha creado \`decomposeParDict\` en C3D-01 ni hay benchmarks de velocidad documentados. En el Ryzen 5 5600X podrían evaluarse 4 y 6 procesos MPI frente a ejecución serial cuando el caso esté listo. Los 12 procesadores lógicos no equivalen a 12 núcleos reales.

## Cuadro de aceptación de hardware

1. Medir RAM física total en Windows y límite WSL2; apuntar estado antes/después si se ajusta.
2. Preparar caso piloto científicamente **ya validado en serie**; medir pico de RSS, tiempo de malla, disco libre, estabilidad y errores por OOM.
3. Medir 1, 4 y 6 procesos (si hardware lo permite), misma física/malla/campos, resultados físicos y desbalance entre procesos.
4. Aceptar una configuración por memoria, tiempo y reproducibilidad, no por disponibilidad nominal de hilos.
5. Registrar en bitácora y evidencia local resultados de las ejecuciones reales antes de etiquetarlas como verificadas.

### Estado

**RAM de Windows y ajustes WSL pendientes; ningún ajuste realizado; ningún ensayo MPI ejecutado.**
