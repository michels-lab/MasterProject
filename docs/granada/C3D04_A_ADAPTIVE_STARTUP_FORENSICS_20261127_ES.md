# C14-3DA — diagnóstico de arranque adaptativo, 27-11-2026

Estado: etapa 9/10; 8/10 = 80% de hitos operativos. Campaña adaptativa 6/8 publicada; A cap .025 falló .68 s y A sin tope .70 s. No nueva corrida ni validación. Caso B y FS-C08 intactos.

Se revisaron los diccionarios de la réplica fiel archivada: metal PIMPLE outer=1, correctors=2, nonOrthogonal=0, energyCorrectors=2 (no asumir que fluid lo consume); metal y molde difusión corrected, Euler temporal. Malla metal 276 y molde 232 caras >70 grados. El salto de dt y el acoplamiento térmico/no ortogonalidad son hipótesis, no causa demostrada. Verificar hashes de los diccionarios efectivamente usados. El error T0 negativo es un síntoma, no prueba de que el campo T guardado tenga ese valor.

Se añade tools/audit_case_a_adaptive_startup.py, lectura de logs existentes, registro de SHA de log y entradas disponibles, deltaT, Courant previo al paso, residuos/iteraciones por región cuando el log identifica región, primeras líneas fatales y contexto. No modifica casos ni lanza solver. Las regiones no identificables quedan unknown. No verifica extremos celulares ni identifica causalidad. Se incluyen tres regresiones de fuente; ejecución aún no verificada.

Desde WSL, obtener únicamente el archivo de la rama de diagnóstico con git fetch + git show (no checkout ni pull de un caso vivo). Ejecutar python3 -B ~/OpenFOAM/audit_case_a_adaptive_startup.py > ~/OpenFOAM/C14_A_STARTUP_FORENSICS_20261127.json. Autodescubre los logs bajo CAMPAIGN_200S_ADAPTIVE_MPI_01; si están en otra ubicación, usar --adaptive PATH repetido; --fixed PATH permite contraste con referencia fija real. Usar únicamente logs detenidos. No compartir transcripciones personales ni credenciales.

Siguiente hito: comparar en tiempo físico los intentos fallidos y fijo, localizar región/ecuación, revisar estados celulares disponibles alrededor del fallo, evaluar candidato numérico aislado solo con aprobación expresa. Mantener propiedades, malla, condiciones y resultados originales. No repetir los mismos intentos fallidos ni declarar corrección hasta evidencia nativa.

English summary: Read-only startup log forensics added; actual WSL logs and tests not yet observed. No new solver run or physical validation. Case A remains 8/10; all successful runs preserved.
