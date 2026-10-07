# HANDOFF

Punto de recuperación del trabajo. Actualizado: 2026-10-02.

## Objetivo

Avanzar el proyecto fase por fase con revisión de Aldo entre fases. **Alcance: lo que pide el
curso, sin crecer más.** No se trata de recortar lo planeado, sino de no agregar funciones ni
pulido más allá del proyecto de clase; Aldo no lo seguirá después de aprobar la materia.

- Fases 1 a 3 (requerimientos, datos, carga y parsing): **aprobadas, en `main`**.
- Fase 4 (preprocesamiento PLN): **aprobada, en `main`**.
- Fase 5 (características y modelos): **aprobada, en `main`**.
- Fase 6 (motor de puntuación y API): **terminada en `phase-6-scoring`, pendiente de revisión**.

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
- Fase 6 aprobada (2026-10-07), incluida la base SQLite en `data/app.db` y `httpx` en dev.

## Ramas

- `main` (en GitHub): fases 1 a 5.
- `phase-6-scoring` (local, sin subir).

## Fase 6: hecho

- `scoring.py`: `evaluate_candidates(vacancy, cvs)` devuelve `Evaluation` ordenadas, con
  habilidades encontradas y faltantes; completa la vacante con lo extraído de su descripción.
- `storage.py`: SQLite (`data/app.db`, fuera de Git) con tablas `vacancies` y `candidates`.
- `api.py`: vacantes, carga de CVs (re-evalúa a todos los candidatos), ranking con filtros,
  decisión del reclutador y métricas. Inicio: `uvicorn cv_screening.api:app --reload`.
- `Features` admite las 3 características relativas; `httpx` en dependencias de desarrollo.
- Docs: sección API de la arquitectura (rutas reales, re-evaluación, orden contra clase),
  ejemplo JSON con nombres de habilidades, README con el arranque de la API.

## Verificado

- 189 pruebas pasan, `ruff` limpio.
- En las 4 vacantes de muestra, los 2 CVs etiquetados `Good Fit` quedan en los 2 primeros
  lugares (prueba `test_good_fit_candidates_rank_first`).
- Servidor real con uvicorn y curl: vacante creada, 7 CVs (PDF y DOCX) evaluados, un `.txt`
  rechazado sin detener el lote, filtros por habilidad y puntaje correctos.

## No verificado

- Instalación en Windows y en Python 3.12 o 3.13.
- CVs reales de formatos complejos; vacante y CVs en idiomas distintos (similitud casi 0).
- Etiquetas del conjunto propio: borrador sin revisar; el resultado en español es optimista.
- Carga concurrente de varios lotes a la misma vacante (no se probó).

## Pendiente de Aldo

- Revisar la fase 6 y autorizar push y merge de `phase-6-scoring`.
- Decidir React + Vite o Next.js para el dashboard (fase 7).
- Invitar al equipo y pedirles revisar `data/samples/es/labels.csv`.

## Siguientes pasos

1. Fase 7 (cronograma: 26 al 30 de octubre): dashboard de ranking (vacantes, carga de CVs,
   ranking con filtros, explicación del puntaje, decisión del reclutador, métricas), en
   `frontend/`, servido por FastAPI. Requiere crear `package.json`: pedir permiso. Planearla y
   pedir aprobación antes de implementar; verificar con Playwright.
