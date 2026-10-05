# HANDOFF

Punto de recuperación del trabajo. Actualizado: 2026-10-02.

## Objetivo

Avanzar el proyecto fase por fase con revisión de Aldo entre fases. **Alcance: lo que pide el
curso, sin crecer más.** No se trata de recortar lo planeado, sino de no agregar funciones ni
pulido más allá del proyecto de clase; Aldo no lo seguirá después de aprobar la materia.

- Fases 1 a 3 (requerimientos, datos, carga y parsing): **aprobadas, en `main`**.
- Fase 4 (preprocesamiento PLN): **aprobada, en `main`**.
- Fase 5 (características y modelos): **aprobada, en `main`**.

## Decisiones de Aldo

- Repositorio de código separado del repositorio del curso; público en la cuenta Aselori.
- Stack: FastAPI + React/Vite (Next.js sigue como opción; se fija en la fase 7).
- Enfoque en español con inglés también soportado; entrenamiento con características
  independientes del idioma (D7).
- No descargar `es_core_news_md`; se usa `es_core_news_sm` (su NER no se usa, D8).
- Los roles de la actividad 1.3 son nominales; no se asignan responsables por módulo.
- Aldo no entrega los reportes del curso; el equipo ya entregó al menos la fase 1.
- Fase 4 aprobada (2026-10-04): base de conocimiento de unas 80 habilidades y reportar la
  cobertura en lugar de perseguir una meta.
- Fase 5 aprobada (2026-10-05) con las 3 características relativas; sin ajustar métricas más
  allá de superar las líneas base.

## Ramas

- `main` (en GitHub): fases 1 a 5.

## Fase 5: hecho

- `features.py`: 7 características por vacante (4 documentadas + percentil de similitud,
  percentil de cobertura y habilidades coincidentes). TF-IDF ajustado por vacante (D9).
- `models.py`: Regresión Logística (principal), Naive Bayes gaussiano y línea base de
  similitud; evaluación en prueba en inglés, validación agrupada por CV y conjunto en español;
  guarda `models/model.joblib` (fuera de Git) y `models/metrics.json`.
- `docs/resultados.md`: tablas, matrices de confusión, interpretación y limitaciones.
- Docs: requisitos (7 características), arquitectura (D9, módulos), README, AGENTS.

## Verificado

- 181 pruebas pasan, `ruff` limpio. `models train` tarda unos 8 s.
- F1 macro de la Regresión Logística: prueba en inglés 0.415, agrupada por CV 0.428, español
  0.652 (96 pares) y 0.674 (24 del mismo dominio). Supera a Naive Bayes (0.374) y a la línea
  base de similitud (0.322) en todos los conjuntos.

## No verificado

- Instalación en Windows y en Python 3.12 o 3.13.
- CVs reales de formatos complejos.
- Etiquetas del conjunto propio: borrador sin revisar; el resultado en español es optimista.
- Años de experiencia del conjunto de entrenamiento: sobreestimados por "Current".

## Pendiente de Aldo

- Invitar al equipo y pedirles revisar `data/samples/es/labels.csv`.

## Siguientes pasos

1. Fase 6 (cronograma: 19 al 23 de octubre): motor de puntuación integrado. Función que recibe
   una vacante y sus CVs y devuelve `Evaluation` (puntaje, clase, probabilidades, habilidades
   encontradas y faltantes) ordenados; API REST con FastAPI (vacantes, carga de CVs, ranking)
   y SQLite. Planearla y pedir aprobación antes de implementar.
