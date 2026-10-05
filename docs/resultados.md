# Resultados de los modelos

Fase 5 del cronograma. Los números salen de `models/metrics.json`, generado con:

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
| **Regresión Logística** | **0.415** (0.444) | **0.428** (0.469) | **0.652** (0.865) | **0.674** (0.667) |
| Naive Bayes gaussiano | 0.374 (0.459) | 0.414 (0.505) | 0.569 (0.875) | 0.514 (0.542) |
| Línea base de similitud | 0.322 (0.407) | 0.346 (0.440) | 0.568 (0.865) | 0.573 (0.625) |
| Siempre "No Fit" | 0.218 (0.487) | | | |

**La Regresión Logística supera a las dos líneas base en todos los conjuntos**, que era el
criterio de aceptación (docs/requisitos.md, sección 5).

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
