# Resultados de los modelos

Fases 5 y 8 del cronograma. Las métricas de los modelos salen de `models/metrics.json`,
generado con:

```bash
python -m cv_screening.models train
```

## 1. Qué se evaluó

| Modelo | Descripción |
|---|---|
| Regresión Logística | Modelo principal. Usa las 7 características, estandarizadas, con pesos de clase balanceados. |
| Naive Bayes gaussiano | Modelo de comparación con las mismas 7 características. |
| Línea base de similitud | Regresión Logística con una sola característica: la similitud de texto TF-IDF. |
| Siempre "No Fit" | Predice siempre la clase más frecuente; sirve de referencia mínima. |

Características (todas independientes del idioma; ver `docs/requisitos.md`, sección 5):
`text_similarity`, `skill_coverage`, `experience_fit`, `education_fit`, y tres relativas a los
demás candidatos de la misma vacante: `similarity_rank`, `coverage_rank` y `matched_skills`.

Conjuntos de evaluación:

| Conjunto | Pares | Descripción |
|---|---|---|
| Prueba en inglés | 1,759 | Partición de prueba del conjunto de Hugging Face; vacantes que no aparecen en entrenamiento. |
| Validación agrupada por CV | 6,228 | Validación cruzada de 5 particiones sobre entrenamiento, sin repetir un CV entre entrenamiento y validación. |
| Conjunto propio en español | 96 | 24 CVs ficticios contra 4 vacantes, con etiquetas borrador. |
| Español, mismo dominio | 24 | Solo los pares de un CV con la vacante de su área. |

La métrica principal es **F1 macro**: promedia el F1 de las tres clases por igual. La exactitud
(accuracy) engaña con clases desbalanceadas: predecir siempre "No Fit" tiene 48.7 % de
exactitud en la prueba en inglés, más que cualquier modelo, pero no sirve para nada.

## 2. Resultados

F1 macro (exactitud entre paréntesis):

| Modelo | Prueba en inglés | Agrupada por CV | Español (96) | Español, mismo dominio (24) |
|---|---|---|---|---|
| **Regresión Logística** | **0.415** (0.444) | **0.428** (0.469) | **0.676** (0.875) | **0.674** (0.667) |
| Naive Bayes gaussiano | 0.374 (0.459) | 0.414 (0.505) | 0.593 (0.885) | 0.543 (0.583) |
| Línea base de similitud | 0.322 (0.407) | 0.346 (0.440) | 0.568 (0.865) | 0.573 (0.625) |
| Siempre "No Fit" | 0.218 (0.487) | | | |

**La Regresión Logística supera a las dos líneas base en todos los conjuntos**, que era el
criterio de aceptación (docs/requisitos.md, sección 5). Las cifras en español son las de la
fase 8, después de normalizar los puestos en femenino (sección 5); en inglés no cambiaron.

Matriz de confusión de la Regresión Logística en la prueba en inglés (renglones: clase real;
columnas: clase predicha):

| | No Fit | Potential Fit | Good Fit |
|---|---|---|---|
| **No Fit** | 463 | 280 | 114 |
| **Potential Fit** | 180 | 181 | 83 |
| **Good Fit** | 210 | 111 | 137 |

Matriz de confusión en español, mismo dominio:

| | No Fit | Potential Fit | Good Fit |
|---|---|---|---|
| **No Fit** | 7 | 1 | 0 |
| **Potential Fit** | 0 | 4 | 4 |
| **Good Fit** | 0 | 3 | 5 |

## 3. Interpretación

- **El sistema separa bien a quien no encaja, y le cuesta distinguir "Good" de "Potential".**
  En español, de 77 pares `No Fit` acierta 73; los errores se concentran entre `Potential Fit`
  y `Good Fit`, que también es la frontera más subjetiva para un reclutador.
- **Qué pesa más en el modelo.** Con características estandarizadas, el número de habilidades
  coincidentes es lo que más empuja hacia `Good Fit` (coeficiente 0.273) y lo que más aleja de
  `No Fit` (-0.185). La similitud de texto sola aporta poco, lo que confirma que la base de
  conocimiento de habilidades es la parte que más contribuye.
- **No hay inflación por CVs repetidos.** La validación agrupada por CV da resultados
  parecidos o mejores que la prueba oficial (0.428 frente a 0.415), así que repetir CVs entre
  entrenamiento y prueba no infló las métricas.
- **Las características relativas ayudan.** En una prueba previa, agregar los percentiles
  dentro de la vacante y el número de habilidades coincidentes subió el F1 macro en inglés de
  0.384 a 0.418.

## 4. Limitaciones

- **Etiquetas ruidosas en inglés.** El origen de las etiquetas del conjunto de Hugging Face no
  está documentado, y en entrenamiento los pares `Potential Fit` tienen en promedio más
  cobertura de habilidades que los `Good Fit`. Ningún modelo puede aprender una frontera que las
  etiquetas no marcan con claridad; por eso el F1 macro en inglés es modesto (0.415).
- **El resultado en español es optimista.** Los CVs, las vacantes y las etiquetas borrador del
  conjunto propio los escribió la misma persona que diseñó las características, y los CVs son
  más limpios que los reales. Además son pocos pares (24 del mismo dominio). Se reporta como
  indicativo; una evaluación seria necesitaría CVs reales etiquetados por reclutadores.
- **Experiencia sobreestimada en inglés.** Los periodos que terminan en "Current" se cuentan
  hasta hoy (ver `data/README.md`, sección 4).
- **Las características relativas necesitan varios candidatos.** Con un solo CV, los
  percentiles valen 0.5 y no aportan información.

## 5. Revisión de sesgos (fase 8, RNF-02)

Prueba: se evalúan los 24 CVs en español contra las 4 vacantes, se cambia algo que no debería
importar y se mide cuánto cambia el puntaje de cada uno de los 96 pares
(`tests/test_fairness.py`).

| Cambio | Antes de corregir | Después |
|---|---|---|
| Nombre de la persona (por uno de otro género) | 0 puntos | 0 puntos |
| Puestos en femenino escritos en masculino ("Desarrolladora" por "Desarrollador") | hasta 5.0 puntos | hasta 0.1 puntos |

- **El nombre no influye**: la anonimización lo quita antes de evaluar.
- **El género gramatical sí influía.** El lematizador de spaCy conserva las formas femeninas
  ("desarrolladora", "ingeniera") y las vacantes suelen escribirse en masculino, así que una
  candidata tenía menos similitud de texto que un candidato con el mismo CV; por las
  características relativas, el cambio también movía a los demás candidatos de la vacante.
- **Corrección:** el preprocesamiento lleva 32 puestos y títulos en femenino a una sola forma
  (`GENDERED_FORMS` en `src/cv_screening/preprocessing.py`). Cubre los puestos comunes, no todos
  los posibles.

## 6. Tiempos (fase 8, RNF-03)

Medidos con la API y los 48 documentos de muestra en una computadora de escritorio (Ryzen 5
7600, 32 GB):

| Medición | Resultado | Meta |
|---|---|---|
| Un CV dentro de un lote | 0.05 s | 2 s o menos |
| Lote de 48 documentos (PDF y DOCX) | 2.3 s | menos de 2 minutos (50 CVs) |
| Primera carga después de iniciar (carga spaCy y el modelo) | 0.64 s | |
| Agregar 1 CV a una vacante con 48 (vuelve a evaluar a todos) | 0.75 s | |

## 7. Reentrenamiento con retroalimentación (fase 8, RF-12)

Desde el dashboard (detalle del modelo) o con `POST /model/retrain`, el sistema reentrena la
Regresión Logística con los datos base más las decisiones del reclutador, cada una con peso 5.
El modelo nuevo solo reemplaza al vigente si su F1 macro en la prueba en inglés no baja más de
0.01; si lo reemplaza, el anterior queda en `models/model.previous.joblib`. Cada intento se
registra en `models/retraining.json` y se necesitan al menos 3 decisiones.

En la prueba del dashboard, con 4 decisiones sobre la vacante de analista de datos, el modelo
se actualizó (F1 macro en inglés de 0.415 a 0.411, dentro de la tolerancia) y el ranking se
recalculó.
