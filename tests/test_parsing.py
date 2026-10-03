import re
from pathlib import Path

import pytest

from cv_screening.parsing import normalize_heading, parse_cv, section_of
from cv_screening.pipeline import process_batch, process_document

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples" / "es"
SOURCES = sorted((SAMPLES / "cvs").glob("cv-*.md"))

# Sección esperada para cada encabezado usado en las fuentes de las muestras.
EXPECTED_SECTION = {
    "Resumen": "summary",
    "Perfil": "summary",
    "Perfil profesional": "summary",
    "Objetivo": "summary",
    "Experiencia": "experience",
    "Experiencia laboral": "experience",
    "Educación": "education",
    "Formación académica": "education",
    "Habilidades": "skills",
    "Habilidades técnicas": "skills",
    "Idiomas": "other",
    "Proyectos escolares": "other",
}


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _source_sections(source: str) -> list[tuple[str, str]]:
    """(encabezado, primeras palabras del contenido) de cada sección de la fuente."""
    result = []
    for block in re.split(r"^## ", source, flags=re.M)[1:]:
        heading, *body = block.splitlines()
        first = next(line for line in body if line.strip())
        first = re.sub(r"^(### |- )", "", first)
        result.append((heading, " ".join(first.split()[:4])))
    return result


def test_normalize_heading():
    assert normalize_heading("EDUCACIÓN:") == "educacion"
    assert normalize_heading("  Formación   Académica ") == "formacion academica"


def test_section_of():
    assert section_of("EXPERIENCIA LABORAL") == "experience"
    assert section_of("Work Experience:") == "experience"
    assert section_of("Habilidades técnicas") == "skills"
    assert section_of("Experiencia en ventas de mostrador") is None
    assert section_of("• Habilidades") == "skills"


def test_text_without_headings_goes_to_other():
    cv = parse_cv("Juan, desarrollador.\nSabe Python y SQL.")
    assert cv.sections.other == "Juan, desarrollador.\nSabe Python y SQL."
    assert cv.sections.experience == ""


@pytest.mark.parametrize("source", SOURCES, ids=lambda p: p.stem)
@pytest.mark.parametrize("fmt", ["docx", "pdf"])
def test_sample_sections_land_in_the_right_place(source: Path, fmt: str):
    path = SAMPLES / fmt / f"{source.stem}.{fmt}"
    # Sin anonimizar: aquí se prueba el parsing, no la anonimización.
    cv = process_document(path.read_bytes(), path.name, anonymized=False)
    for heading, start in _source_sections(source.read_text(encoding="utf-8")):
        field = EXPECTED_SECTION[heading]
        assert start in _flat(getattr(cv.sections, field)), (heading, field)


def test_pipeline_output_has_no_personal_data():
    path = SAMPLES / "pdf" / "cv-01.pdf"
    cv = process_document(path.read_bytes(), path.name)
    assert "Villarreal" not in cv.raw_text
    assert cv.sections.other.startswith("[NOMBRE]")


def test_batch_returns_cvs_and_errors():
    cvs, errors = process_batch(
        [("cv-05.docx", (SAMPLES / "docx" / "cv-05.docx").read_bytes()), ("x.txt", b"hola")]
    )
    assert [cv.file_name for cv in cvs] == ["cv-05.docx"]
    assert "Licenciatura en Ingeniería en Sistemas" in cvs[0].sections.education
    assert [e.file_name for e in errors] == ["x.txt"]
