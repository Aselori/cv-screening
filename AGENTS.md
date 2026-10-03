# AGENTS.md

Instrucciones para asistentes de código (Codex, Claude Code y similares) en este repositorio.

## Proyecto

- Proyecto de equipo del Laboratorio de Temas Selectos de Sistemas Inteligentes (LBTSSI),
  FIME UANL, agosto - diciembre 2026. Docente: Raquel Martínez Martínez.
- Los reportes del curso y la rúbrica se manejan fuera de este repositorio. Aquí solo están el
  código y su documentación técnica.
- El cronograma de 9 fases está en la actividad 1.3 (Definición del proyecto). Los
  requerimientos y la arquitectura están en `docs/`.
- Los roles por integrante de la actividad 1.3 son nominales: no indican quién hace cada
  parte. No asignar responsables por módulo en la documentación.

## Decisiones vigentes

Ver `docs/arquitectura.md`, sección 8. En resumen:

- Enfoque en español: CVs, vacantes, interfaz, documentación, comentarios y mensajes de commit
  en español. Los CVs y vacantes en inglés también se aceptan. Los identificadores (variables,
  funciones, archivos, campos JSON, ramas) están en inglés.
- Clasificación de pares CV-vacante en `Good Fit`, `Potential Fit` y `No Fit`, con el conjunto
  de datos `cnamuangtoun/resume-job-description-fit` de Hugging Face.
- Los modelos usan solo las cuatro características que no dependen del idioma (D7):
  Regresión Logística como principal, Naive Bayes como comparación y similitud coseno como
  línea base. Se entrenan en inglés y se miden también con un conjunto propio en español.
- Backend Python + FastAPI, dashboard React + Vite + TypeScript, SQLite local.

## Entorno y comandos

- Python 3.12 o superior (probado con 3.14). Entorno virtual en `.venv/`.
- Instalación: `pip install -e ".[dev]"`, `python -m spacy download es_core_news_sm` y
  `python -m spacy download en_core_web_sm`.
- Antes de cada commit: `ruff check .`, `ruff format --check .` y `pytest`.

## Reglas

- No modificar archivos `.env` ni subir datos descargados o modelos entrenados (están en
  `.gitignore`).
- Los CVs de prueba usan solo datos ficticios.
- Una rama por fase o tarea; `git push` y merges solo con aprobación del responsable.
