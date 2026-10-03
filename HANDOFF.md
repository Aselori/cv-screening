# HANDOFF

Punto de recuperación del trabajo. Actualizado: 2026-10-02.

## Objetivo

Arrancar el proyecto completando las fases 1 a 3 del cronograma, una fase a la vez con revisión
de Aldo entre fases:

1. Requerimientos, criterios de evaluación de perfiles y arquitectura. **Aprobada.**
2. Conjunto de datos preparado. **Terminada, pendiente de revisión.**
3. Módulo de carga y parsing de PDF y DOCX.

## Decisiones de Aldo (2026-10-02)

- Repositorio de código separado del repositorio del curso; público en la cuenta Aselori.
- Stack: FastAPI + React/Vite (Next.js sigue como opción; se fija en la fase 7).
- Enfoque en español con inglés también soportado. Entrenamiento con el conjunto en inglés
  usando solo características independientes del idioma (D7).
- No descargar `es_core_news_md`; se usa `es_core_news_sm` (y su NER ya no se usa, D8).
- Se construyen aquí las fases 1 a 3, fase por fase.
- Los roles de la actividad 1.3 son nominales; no se asignan responsables por módulo.

## Ramas

- `main` (en GitHub): commit inicial.
- `phase-1-requirements` (en GitHub hasta d17d362; 2 commits locales sin subir: quitar
  responsables y quitar configuración local). Pendiente de merge a `main`.
- `phase-2-dataset` (local, sin subir): sale de `phase-1-requirements`.

## Fase 2: hecho

- `src/cv_screening/schemas.py`: `CV`, `Vacancy`, `Features`, `Evaluation`, `LabeledPair`.
- `src/cv_screening/datasets.py`: `download` (revisión fija) y `prepare` (duplicados,
  etiquetas contradictorias, anonimización, ids por CV y vacante, validación, reporte).
- `src/cv_screening/anonymization.py`: patrones + estructura del CV, sin NER.
- `data/samples/es/`: 4 vacantes, 24 CVs (Markdown, DOCX, PDF en 3 formatos), 96 pares con
  etiquetas borrador. `scripts/build_samples.py` los genera (LibreOffice).
- `data/README.md`: fuente, preparación, hallazgos, conjunto propio, anonimización y mediciones.
- Docs sincronizados: 96 pares en lugar de 60, decisión D8, estructura del repositorio,
  diagrama regenerado.

## Verificado

- 71 pruebas pasan (`pytest`), `ruff check` y `ruff format --check` limpios.
- `prepare` corre en unos 4 s: 6,228 pares de entrenamiento y 1,759 de prueba, todos válidos
  contra `LabeledPair`; 0 correos y 0 teléfonos residuales en el texto procesado.
- Anonimización: 48 de 48 documentos del conjunto propio sin nombre, nombre de pila, correo ni
  teléfono; 0 nombres falsos en los 642 CVs de entrenamiento.
- 476 de 477 CVs de prueba también están en entrenamiento (solo cambian las vacantes).

## No verificado

- Instalación en Windows y en Python 3.12 o 3.13.
- Licencia y origen de las etiquetas del conjunto de Hugging Face (no declarados).
- Etiquetas del conjunto propio: son un borrador; el equipo no las ha revisado.
- Nombres de terceros dentro del texto (referencias laborales) no se eliminan.
- Que las características en español se comporten como en inglés (fase 5).

## Pendiente de Aldo

- Revisar la fase 2.
- Autorizar push de `phase-1-requirements` y `phase-2-dataset`, y merge a `main`.
- Decidir React + Vite o Next.js (puede esperar a la fase 7).
- Invitar al equipo al repositorio y pedirles revisar `data/samples/es/labels.csv`.
- Opcional: cambiar el correo de Git al `noreply` de GitHub (el actual es público en commits).

## Siguientes pasos

1. Fase 3 en la rama `phase-3-parsing` (sale de `phase-2-dataset` si no hay merge):
   - `ingestion.py`: PDF (pdfplumber) y DOCX (python-docx, incluidas tablas) a texto; errores
     por archivo (formato no soportado, archivo dañado, PDF sin texto) sin detener el lote.
   - `parsing.py`: secciones (resumen, experiencia, educación, habilidades, otros) a `CV`,
     con encabezados en español e inglés; si no hay secciones, todo el texto en `other`.
   - CLI para procesar una carpeta; pruebas contra las fuentes Markdown de las muestras.
