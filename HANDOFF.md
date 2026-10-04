# HANDOFF

Punto de recuperación del trabajo. Actualizado: 2026-10-02.

## Objetivo

Avanzar el proyecto fase por fase con revisión de Aldo entre fases, **con alcance mínimo**:
Aldo no tiene interés en llevar el proyecto más allá de lo que pide el curso.

- Fases 1 a 3 (requerimientos, datos, carga y parsing): **aprobadas, en `main`**.
- Fase 4 (preprocesamiento PLN): **terminada en `phase-4-preprocessing`, pendiente de revisión**.

## Decisiones de Aldo

- Repositorio de código separado del repositorio del curso; público en la cuenta Aselori.
- Stack: FastAPI + React/Vite (Next.js sigue como opción; se fija en la fase 7).
- Enfoque en español con inglés también soportado; entrenamiento con características
  independientes del idioma (D7).
- No descargar `es_core_news_md`; se usa `es_core_news_sm` (su NER no se usa, D8).
- Los roles de la actividad 1.3 son nominales; no se asignan responsables por módulo.
- Aldo no entrega los reportes del curso; el equipo ya entregó al menos la fase 1.
- Fase 4 aprobada (2026-10-04) con alcance reducido: base de conocimiento de unas 80
  habilidades y reportar la cobertura en lugar de perseguir una meta.

## Ramas

- `main` (en GitHub): fases 1 a 3 y la corrección de nombres de salida.
- `phase-4-preprocessing` (local, sin subir).

## Fase 4: hecho

- `language.py`: idioma por palabras vacías exclusivas; 950 de 950 textos correctos.
- `preprocessing.py`: limpieza y lematización con spaCy (conserva la ñ).
- `knowledge/skills.json` + `knowledge/__init__.py`: 81 habilidades, 293 alias, reglas
  `implies` (MySQL implica SQL, HubSpot implica CRM).
- `extraction.py`: años de experiencia (mención explícita o suma de periodos sin traslapes ni
  estudios), nivel educativo (en curso cuenta como el nivel anterior), requisitos de vacantes.
- `pipeline.py`: agrega idioma y `CVProfile`; rechaza otros idiomas (`unsupported_language`).
- `datasets.py preprocess`: `data/processed/cvs_nlp.csv` y `vacancies_nlp.csv` (unos 50 s).
- Docs: `data/README.md` sección 4 con cobertura y limitaciones; estructura en arquitectura.

## Verificado

- 175 pruebas pasan, `ruff` limpio.
- Extracción en los 24 CVs de muestra igual a los valores escritos a mano (años con
  tolerancia de 1); requisitos de las 4 vacantes iguales a sus campos estructurados.
- Cobertura en entrenamiento: años 80.9 %, educación 85.8 %, vacantes con 3 o más
  habilidades 76.6 %.

## No verificado

- Instalación en Windows y en Python 3.12 o 3.13.
- CVs reales de formatos complejos.
- Etiquetas del conjunto propio: borrador sin revisar por el equipo.
- Años de experiencia del conjunto de entrenamiento: sobreestimados por "Current".

## Pendiente de Aldo

- Revisar la fase 4 y autorizar push y merge de `phase-4-preprocessing`.
- Invitar al equipo y pedirles revisar `data/samples/es/labels.csv`.

## Siguientes pasos

1. Fase 5 (cronograma: 12 al 16 de octubre): características (TF-IDF coseno, cobertura de
   habilidades, experiencia y educación), Naive Bayes y Regresión Logística, métricas en el
   conjunto de prueba en inglés y en el conjunto propio en español, partición agrupada por CV.
   Planearla y pedir aprobación antes de implementar.
