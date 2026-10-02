# Selección y Filtrado de Currículums para Recursos Humanos

Proyecto del **Laboratorio de Temas Selectos de Sistemas Inteligentes** (LBTSSI), FIME, UANL.
Semestre agosto - diciembre 2026. Docente: Raquel Martínez Martínez.

Sistema inteligente (agente basado en aprendizaje) que analiza currículums en PDF o DOCX, los
compara con los requisitos de una vacante y genera un puntaje de idoneidad y un ranking de
candidatos. Usa PLN (spaCy), TF-IDF, Naive Bayes y Regresión Logística, y aprende de la
retroalimentación de los reclutadores.

## Equipo

| Integrante | Rol |
|---|---|
| Ariel Osvaldo Main Acosta | Líder de proyecto y analista |
| Eduardo Damián Presas Méndez | Ingeniero de datos |
| Raúl Manzanera Medina | Desarrollador backend |
| Oziel Segura Delgadillo | Especialista en PLN e IA |
| Aldo Sebastián López Rivas | Desarrollador frontend y UX |

## Documentación

- [Requerimientos](docs/requisitos.md): requerimientos funcionales y no funcionales, criterios
  de evaluación de perfiles y alcance.
- [Arquitectura](docs/arquitectura.md): diagrama, módulos, flujo de datos y librerías elegidas.

## Instalación

Requisitos: Python 3.12 o superior (el repositorio fija 3.14 con [mise](https://mise.jdx.dev/),
opcional) y Git.

Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
```

Verificar la instalación:

```bash
pytest
ruff check .
```

## Estructura

```
docs/             requerimientos, arquitectura y decisiones
src/cv_screening/ código del sistema (paquete de Python)
tests/            pruebas automatizadas (pytest)
```

Las carpetas `data/` (fase 2), los módulos de parsing (fase 3) y el dashboard (fase 7) se
agregan en sus fases correspondientes.
