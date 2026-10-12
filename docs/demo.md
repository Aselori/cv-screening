# Guion de demostración

Guion para el video del PIA (unos 6 minutos). Usa la vacante de analista de datos y los CVs
ficticios de `data/samples/es/pdf`, cuyas etiquetas y motivos están en
`data/samples/es/labels.csv`.

## Preparación

1. Borrar `data/app.db` si existe, para empezar con el sistema vacío.
2. Levantar el servidor (`uvicorn cv_screening.api:app`) y abrir http://127.0.0.1:8000.
3. Tener a la mano:
   - Los datos de la vacante `v-es-02` de `data/samples/es/vacancies.json`.
   - Los archivos `cv-07.pdf` a `cv-12.pdf` y `cv-17.pdf`.
   - Un archivo que no sea CV (por ejemplo, un `.txt`) para mostrar el manejo de errores.
4. Tener abierto `docs/resultados.md` para la parte de métricas.

## Escenas

| # | Duración | Qué se hace | Qué se explica |
|---|---|---|---|
| 1 | 30 s | Pantalla vacía ("Crea la primera vacante"). | El problema: muchos CVs por vacante; el sistema prioriza, la decisión es del reclutador. |
| 2 | 45 s | Crear la vacante: "Analista de datos", su descripción, habilidades `SQL, Excel, Power BI, Python`, deseables `Estadística, Tableau`, 1 año, Licenciatura. | El perfil del puesto es lo que el agente percibe de la vacante; lo que no se llena se extrae de la descripción. |
| 3 | 45 s | **Cargar CVs** con los 7 PDF y el `.txt`. | Lectura de PDF y DOCX, anonimización (no se ven nombres ni correos) y que un archivo inválido no detiene el lote. |
| 4 | 60 s | Leer el ranking de arriba hacia abajo. | La barra es el puntaje; debajo solo aparece lo que falta. cv-07 y cv-08 arriba: cv-08 dice "hojas de cálculo" y "tableros en Power BI" y aun así cuenta como Excel y Power BI, gracias a la base de conocimiento de habilidades. |
| 5 | 45 s | Abrir "Detalle" de cv-09 o cv-10. | Probabilidades de cada clase, las 7 características y por qué el orden puede no coincidir con la etiqueta. |
| 6 | 30 s | Filtro "Habilidad: Python" y "Años ≥ 1". | Filtrar por requisitos indispensables sin perder la posición en el ranking. |
| 7 | 45 s | Marcar decisiones (Apto a cv-07 y cv-08, No apto a cv-11 y cv-12) y, en "Modelo", **Reentrenar con mis decisiones**. | Aprendizaje con retroalimentación: el modelo nuevo solo se queda si no empeora en la prueba en inglés. |
| 8 | 60 s | Mostrar `docs/resultados.md`: tabla de F1 macro, sesgos y tiempos. | La Regresión Logística supera a Naive Bayes y a la línea base; el nombre no cambia el puntaje y los puestos en femenino tampoco (después de la corrección); 0.05 s por CV. |
| 9 | 30 s | Volver al ranking. | Limitaciones: etiquetas del conjunto en inglés ruidosas, conjunto en español pequeño y escrito por el equipo, CVs reales más variados. |

## Si algo falla

- **"No se pudo conectar con el servidor"**: el servidor no está corriendo o usa otro puerto.
- **"address already in use" al iniciar**: agregar `--port 8001` y abrir esa dirección.
- **El ranking cambia al cargar más CVs**: es lo esperado; tres características comparan a cada
  candidato con los demás de la vacante.
