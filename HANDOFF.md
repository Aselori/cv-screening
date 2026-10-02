# HANDOFF

Punto de recuperación del trabajo. Actualizado: 2026-10-02.

## Objetivo

Arrancar el proyecto completando las fases 1 a 3 del cronograma, una fase a la vez con revisión
de Aldo entre fases:

1. Requerimientos, criterios de evaluación de perfiles y arquitectura.
2. Conjunto de datos preparado (descarga, anonimización, esquemas de datos, CVs de muestra).
3. Módulo de carga y parsing de PDF y DOCX.

## Decisiones de Aldo (2026-10-02)

- Repositorio de código en `~/Work/projects/cv-screening`, separado del repo del curso.
- Stack: FastAPI + React/Vite.
- CVs analizados en inglés; interfaz y documentación en español.
- Se construyen aquí las fases 1 a 3, fase por fase.

## Estado

- Rama `main`: commit inicial con la estructura (pyproject, mise, pytest, ruff, prueba básica).
- Rama `phase-1-requirements`: fase 1 terminada, pendiente de revisión.
  - `docs/requisitos.md`: RF-01 a RF-13, RNF-01 a RNF-08, criterios de evaluación (4
    características y fórmula del puntaje), datos, métricas, alcance, riesgos.
  - `docs/arquitectura.md`: diagrama Mermaid, componentes del agente, módulos y responsables,
    contratos de datos, API propuesta, librerías con versiones, estructura objetivo,
    decisiones D1 a D6.
  - `docs/arquitectura.png`: diagrama exportado (renderizado con Mermaid 11 y Playwright).
  - `AGENTS.md`, este archivo.

## Verificado

- Las dependencias se instalan y funcionan en Python 3.14.7 (spaCy 3.8.16 con
  `en_core_web_sm` 3.8.0, scikit-learn 1.9.1, pdfplumber 0.11.10, python-docx 1.2.0,
  FastAPI 0.142.2, Pydantic 2.13.5, pandas 3.0.6).
- `ruff check`, `ruff format --check` y `pytest` (2 pruebas) pasan.
- El conjunto de datos tiene 6,241 + 1,759 pares y la distribución de etiquetas indicada en
  requisitos.md (consultado en la API de Hugging Face). En una muestra de 40 vacantes, 33
  mencionan años de experiencia y 26 un grado académico.

## No verificado

- Instalación en Windows y en Python 3.12 o 3.13.
- Licencia y origen de las etiquetas del conjunto de datos (no están declarados).
- Que el equipo y la profesora acepten CVs en inglés.
- No hay repositorio remoto en GitHub todavía; nada se ha subido.

## Pendiente de Aldo

- Revisar la fase 1 y aprobar o pedir cambios.
- Decidir si se crea el repositorio en GitHub (cuenta propia u organización) y a quién se
  invita.
- Confirmar con el equipo el estado real de las fases 2 y 3 y que aceptan el plan.

## Siguientes pasos

1. Tras la aprobación: merge de `phase-1-requirements` a `main` (con autorización de Aldo).
2. Fase 2 en la rama `phase-2-dataset`: `schemas.py` (Pydantic: `CV`, `Vacancy`,
   `Evaluation`), script de descarga a `data/raw/`, anonimización a `data/processed/`,
   `data/README.md` con fuente y limitaciones, CVs de muestra ficticios en `data/samples/`,
   pruebas.
3. Fase 3 en la rama `phase-3-parsing`: `ingestion.py` y `parsing.py`, CLI, pruebas con
   las muestras.
