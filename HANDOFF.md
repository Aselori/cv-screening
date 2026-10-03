# HANDOFF

Punto de recuperación del trabajo. Actualizado: 2026-10-02.

## Objetivo

Arrancar el proyecto completando las fases 1 a 3 del cronograma, una fase a la vez con revisión
de Aldo entre fases:

1. Requerimientos, criterios de evaluación de perfiles y arquitectura. **Aprobada, en `main`.**
2. Conjunto de datos preparado. **Aprobada, en `main`.**
3. Módulo de carga y parsing de PDF y DOCX. **Terminada, pendiente de revisión.**

## Decisiones de Aldo (2026-10-02)

- Repositorio de código separado del repositorio del curso; público en la cuenta Aselori.
- Stack: FastAPI + React/Vite (Next.js sigue como opción; se fija en la fase 7).
- Enfoque en español con inglés también soportado. Entrenamiento con el conjunto en inglés
  usando solo características independientes del idioma (D7).
- No descargar `es_core_news_md`; se usa `es_core_news_sm` (su NER no se usa, D8).
- Se construyen aquí las fases 1 a 3, fase por fase.
- Los roles de la actividad 1.3 son nominales; no se asignan responsables por módulo.

## Ramas

- `main` (en GitHub): fases 1 y 2 integradas con merges `--no-ff`.
- `phase-3-parsing` (local, sin subir): sale de `main`.

## Fase 3: hecho

- `src/cv_screening/ingestion.py`: PDF (pdfplumber) y DOCX (párrafos y tablas en orden) a
  texto; valida extensión, tamaño (5 MB), firma del archivo y lotes de hasta 50; errores por
  archivo: `unsupported_format`, `too_large`, `corrupt_file`, `no_text`.
- `src/cv_screening/parsing.py`: encabezados en español e inglés por coincidencia exacta
  normalizada; lo que no tiene sección va a `other`.
- `src/cv_screening/pipeline.py`: lectura, anonimización y parsing (en ese orden), con CLI
  `python -m cv_screening.pipeline <carpeta> --out <salida>`.
- Docs: orden de los pasos en el diagrama y la tabla de módulos, `pipeline.py` en la
  estructura, nota sobre texto completo para las características, uso en el README.

## Verificado

- 135 pruebas pasan, `ruff check` y `ruff format --check` limpios.
- Las secciones de los 48 documentos de muestra quedan en el campo correcto.
- La CLI procesó 4 muestras y reportó un PDF dañado sin detener el lote.
- Un PDF escaneado (solo imagen) se reporta como `no_text`.
- En los CVs de entrenamiento el parser reconoce secciones solo en 1 de 642 (encabezados
  pegados al texto). Por eso las características se calculan sobre el texto completo.

## No verificado

- Instalación en Windows y en Python 3.12 o 3.13.
- CVs reales de formatos más complejos (dos columnas reales, imágenes, plantillas de Canva).
- Licencia y origen de las etiquetas del conjunto de Hugging Face (no declarados).
- Etiquetas del conjunto propio: borrador sin revisar por el equipo.

## Pendiente de Aldo

- Revisar la fase 3 y autorizar push y merge de `phase-3-parsing`.
- Decidir React + Vite o Next.js (puede esperar a la fase 7).
- Invitar al equipo y pedirles revisar `data/samples/es/labels.csv`.

## Siguientes pasos

1. Reporte 3.2 "Avance del Proyecto 1" con el avance contra el cronograma (fases 1 a 3).
2. Fase 4 (preprocesamiento PLN, cronograma: 5 al 9 de octubre): detección de idioma (RF-14),
   limpieza y lematización con spaCy en español e inglés, primera versión de la base de
   conocimiento de habilidades bilingüe.
