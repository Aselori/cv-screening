# Selección y Filtrado de Currículums para Recursos Humanos

Proyecto del **Laboratorio de Temas Selectos de Sistemas Inteligentes** (LBTSSI), FIME, UANL.
Semestre agosto - diciembre 2026. Docente: Raquel Martínez Martínez.

Sistema inteligente (agente basado en aprendizaje) que recibe los currículums de una vacante en
PDF o DOCX, en español o inglés, y devuelve un ranking de candidatos con un puntaje de
idoneidad de 0 a 100 y la explicación de cada puntaje. El reclutador registra sus decisiones y
el sistema puede reentrenarse con ellas.

Cómo funciona, en cinco pasos:

1. **Lectura** del PDF o DOCX y **anonimización** (nombre, correo, teléfono, domicilio).
2. **Secciones y PLN**: idioma, lematización con spaCy y extracción de habilidades (base de
   conocimiento bilingüe de 81 habilidades), años de experiencia y nivel educativo.
3. **Características** de cada CV frente a la vacante: similitud TF-IDF, cobertura de
   habilidades, experiencia, educación y su posición frente a los demás candidatos.
4. **Modelo**: Regresión Logística (comparada con Naive Bayes y una línea base) que estima si
   el candidato es Apto, Posible o No apto.
5. **Dashboard**: ranking, habilidades faltantes, filtros y decisión del reclutador.

Resultado principal: la Regresión Logística supera a las líneas base en todos los conjuntos de
evaluación (F1 macro 0.415 en la prueba en inglés y 0.676 en el conjunto propio en español).
Detalle y limitaciones en [docs/resultados.md](docs/resultados.md).

## Equipo

- Ariel Osvaldo Main Acosta
- Eduardo Damián Presas Méndez
- Raúl Manzanera Medina
- Oziel Segura Delgadillo
- Aldo Sebastián López Rivas

## Correr la demostración

El modelo ya está entrenado (`models/model.joblib`), así que no hace falta descargar datos.
Requisitos: Python 3.12 o superior, Node.js 20.19 o 22.12 en adelante y [pnpm](https://pnpm.io/).

Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m spacy download es_core_news_sm
python -m spacy download en_core_web_sm
cd frontend && pnpm install && pnpm build && cd ..
uvicorn cv_screening.api:app
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m spacy download es_core_news_sm
python -m spacy download en_core_web_sm
cd frontend; pnpm install; pnpm build; cd ..
uvicorn cv_screening.api:app
```

Abrir http://127.0.0.1:8000. Si el puerto 8000 está ocupado, agregar `--port 8001` al comando
de `uvicorn`. Los datos de la demostración se guardan en `data/app.db` (SQLite, fuera de Git);
borrar ese archivo deja el sistema vacío.

## Usar el sistema

1. Crear una vacante: puesto, descripción y, si se quiere, habilidades, años y nivel educativo.
   Lo que no se llene se toma de la descripción.
2. **Cargar CVs** en PDF o DOCX (hasta 50 por lote). En `data/samples/es/pdf` hay 24 CVs
   ficticios para probar; en `data/samples/es/vacancies.json`, las 4 vacantes que les
   corresponden.
3. Revisar el ranking: la barra es el puntaje; debajo aparece solo lo que le falta a cada
   candidato. "Detalle" muestra la explicación completa.
4. Marcar la decisión de cada candidato (Apto, Posible, No apto).
5. En "Modelo" (al final de la página), **Reentrenar con mis decisiones** usa esas decisiones
   para ajustar el modelo; si el modelo nuevo es peor, se conserva el anterior.

El guion para grabar la demostración está en [docs/demo.md](docs/demo.md).

## Reproducir el entrenamiento

```bash
python -m cv_screening.datasets download     # conjunto de Hugging Face (68 MB)
python -m cv_screening.datasets prepare      # limpieza y anonimización
python -m cv_screening.datasets preprocess   # lematización y extracción (unos 50 s)
python -m cv_screening.models train          # modelos, métricas y models/model.joblib
```

Los datos se describen en [data/README.md](data/README.md).

## Otras herramientas

- Procesar CVs a JSON sin el dashboard:
  `python -m cv_screening.pipeline data/samples/es/pdf --out salida/`
- Documentación interactiva de la API: http://127.0.0.1:8000/docs
- Desarrollar la interfaz con recarga automática (con la API corriendo en otra terminal):
  `cd frontend && pnpm dev`, en http://localhost:5173. Si la API usa otro puerto, cambiarlo en
  `frontend/vite.config.ts`.

## Pruebas

```bash
pytest           # la prueba de reentrenamiento se omite si no se descargaron los datos
ruff check .
cd frontend && pnpm build   # incluye la revisión de tipos de TypeScript
```

## Documentación

- [Requerimientos](docs/requisitos.md): requerimientos funcionales y no funcionales, criterios
  de evaluación de perfiles y alcance.
- [Arquitectura](docs/arquitectura.md): diagrama, módulos, contratos de datos, API, librerías y
  decisiones.
- [Resultados](docs/resultados.md): métricas, sesgos, tiempos, reentrenamiento y limitaciones.
- [Datos](data/README.md): fuentes, preparación, conjunto propio en español y anonimización.
- [Guion de demostración](docs/demo.md): pasos para grabar el video del PIA.

## Estructura

```
data/              descripción de los datos y conjunto propio en español (samples/es)
docs/              requerimientos, arquitectura, resultados y guion de demostración
frontend/          dashboard (React, Vite y TypeScript)
models/            modelo entrenado y sus métricas
scripts/           utilidades de desarrollo (generar los CVs de muestra)
src/cv_screening/  código del sistema (paquete de Python)
tests/             pruebas automatizadas (pytest)
```
