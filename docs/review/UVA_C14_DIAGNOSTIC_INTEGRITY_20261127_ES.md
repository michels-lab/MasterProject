# Uva + Granada — C14 archived mass, energy and three-model comparison integrity
Fecha: 2026-11-27. Caso B etapa 3/7, 2/7 hitos (29%); no nuevas puertas científicas.

- Energía: rutas de salida resueltas antes de escritura; validación de 101 tiempos ordenados 0..10 s, etiquetas únicas y correspondencia numérica. No se cambia cuadratura, modelo h/e ni se afirma cierre.
- Masa: comparte aislamiento canónico, rechaza tiempos repetidos/no finitos y masa/flujo no finitos; distingue cobertura completa 0.1..10 s (99 intervalos) de sufijo tardío que llega a 10 s. No se inventa rho/phi t0 ni se cambia modelo.
- Comparación 2D/A/B: cada perfil y diccionario debe coincidir en bytes con blob Git del árbol HEAD fijado; no basta rev-parse. Verifica digest después de lectura de perfiles y registra coordenadas físicas además de claves cuantizadas para detectar cambios temporales. No interpolación ni extrapolación nueva.
- Pruebas: seis regresiones sintéticas de masa/energía y una de procedencia Git; workflow dedicado. Comprobación local independiente del comportamiento de git ls-tree desde subdirectorio: correcta. No se ha verificado todavía la suite CI ni el comparador sobre 3838 perfiles reales.

Commits: 33b7c1e9409739d1bcdd84d9e422e98a8752dff6, 99a62158348d2bbdcb6f2ad2b307034faf86f9d2, 079fb35be93475eb3b3da28e25b85d096c8d216e, e528861ad32e789357ef1f524b0e993bf2bd56dc, 4ef4429af9c6b5bf6c056447248b05fca0193617, 3a2e5faced14a45ef4430c82f7c4daafc34011cb. Base ee998d86039669ac5782d110b698f302a8361ba2.

Limitaciones: no ejecutar CFD, no certificar cierre energético o de masa; los hashes no sustituyen validación experimental y no garantizan aislamiento contra cambios externos hostiles simultáneos. Se mantienen parciales los alcances científicos aún no verificados. El criterio de 99 intervalos es específico del archivo histórico C14 B de 10 s, no se aplica a campañas 200 s. Siguiente: exportadores FoamLens, comparadores temporales y auditoría de manifiestos por campaña.
