# Selección y Filtrado de Currículums para Recursos Humanos

Proyecto del **Laboratorio de Temas Selectos de Sistemas Inteligentes** (LBTSSI), FIME, UANL.
Semestre agosto - diciembre 2026. Docente: Raquel Martínez Martínez.

Sistema inteligente (agente basado en aprendizaje) que analiza currículums en PDF o DOCX, en
español o inglés, los compara con los requisitos de una vacante y genera un puntaje de
idoneidad y un ranking de candidatos. Usa PLN (spaCy), TF-IDF, Naive Bayes y Regresión
Logística, y aprende de la retroalimentación de los reclutadores.

## Equipo

- Ariel Osvaldo Main Acosta
- Eduardo Damián Presas Méndez
- Raúl Manzanera Medina
- Oziel Segura Delgadillo
- Aldo Sebastián López Rivas

## Documentación

- [Requerimientos](docs/requisitos.md): requerimientos funcionales y no funcionales, criterios
  de evaluación de perfiles y alcance.
- [Arquitectura](docs/arquitectura.md): diagrama, módulos, flujo de datos y librerías elegidas.

## Instalación

Requisitos: Python 3.12 o superior y Git.

Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m spacy download es_core_news_sm
python -m spacy download en_core_web_sm
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m spacy download es_core_news_sm
python -m spacy download en_core_web_sm
```

Verificar la instalación:

```bash
pytest
ruff check .
```

## Uso

Procesar CVs (PDF o DOCX) a JSON, anonimizados y divididos en secciones:

```bash
python -m cv_screening.pipeline data/samples/es/pdf --out salida/
```

Se genera un JSON por CV y `errors.json` con los archivos que no se pudieron leer. Los datos de
entrenamiento se describen en [data/README.md](data/README.md).

## Estructura

```
data/             descripción de los datos y conjunto propio en español (samples/es)
docs/             requerimientos, arquitectura y decisiones
scripts/          utilidades de desarrollo (generar los CVs de muestra)
src/cv_screening/ código del sistema (paquete de Python)
tests/            pruebas automatizadas (pytest)
```

El resto de los módulos (PLN, modelos, API y dashboard) se agrega en sus fases; la estructura
objetivo está en [docs/arquitectura.md](docs/arquitectura.md), sección 7.
