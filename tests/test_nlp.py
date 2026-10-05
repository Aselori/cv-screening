"""Pruebas de la fase 4: idioma, preprocesamiento, habilidades y extracción de entidades."""

import json
from datetime import date
from pathlib import Path

import pytest

from cv_screening.extraction import (
    education_level,
    min_education_required,
    min_years_required,
    years_of_experience,
)
from cv_screening.ingestion import IngestionError, IngestionErrorKind
from cv_screening.knowledge import extract_skills
from cv_screening.language import detect_language
from cv_screening.pipeline import process_batch, process_document
from cv_screening.preprocessing import preprocess
from cv_screening.schemas import EducationLevel, Language

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples" / "es"
SOURCES = {p.stem: p.read_text(encoding="utf-8") for p in sorted((SAMPLES / "cvs").glob("*.md"))}
VACANCIES = json.loads((SAMPLES / "vacancies.json").read_text(encoding="utf-8"))
# Las muestras se escribieron como si hoy fuera mediados de 2024 ("2021 - Actualidad").
SAMPLES_TODAY = date(2024, 6, 30)

B, T, H, M = (
    EducationLevel.BACHELOR,
    EducationLevel.TECHNICAL,
    EducationLevel.HIGH_SCHOOL,
    EducationLevel.MASTER,
)
# (años de experiencia, nivel educativo) esperados, leídos a mano de cada CV.
EXPECTED = {
    "cv-01": (4, B), "cv-02": (3, B), "cv-03": (1, B), "cv-04": (5, B), "cv-05": (None, H),
    "cv-06": (3, T), "cv-07": (3, B), "cv-08": (2, M), "cv-09": (0.5, B), "cv-10": (4, B),
    "cv-11": (3, B), "cv-12": (2, H), "cv-13": (5, B), "cv-14": (3, B), "cv-15": (2, H),
    "cv-16": (1, B), "cv-17": (6, T), "cv-18": (4, None), "cv-19": (3, B), "cv-20": (2, T),
    "cv-21": (0.5, H), "cv-22": (2, T), "cv-23": (5, B), "cv-24": (3, B),
}  # fmt: skip


def test_language_of_samples_and_short_texts():
    assert {detect_language(t) for t in SOURCES.values()} == {Language.ES}
    assert {detect_language(v["description"]) for v in VACANCIES} == {Language.ES}
    assert detect_language("Data analyst with 5 years of experience in SQL and the cloud.") is (
        Language.EN
    )
    assert detect_language("Python, SQL, Excel") is None


def test_preprocess_lemmatizes_and_drops_noise():
    lemmas = preprocess("[NOMBRE] trabajó 3 años • analista de datos", Language.ES)
    assert lemmas == ["trabajar", "año", "analista", "dato"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Manejo avanzado de hojas de cálculo", {"excel"}),
        ("ReactJS y NodeJS", {"react", "nodejs", "javascript"}),
        ("MySQL y GitHub", {"mysql", "sql", "github", "git"}),
        ("Búsqueda de clientes y seguimiento en HubSpot", {"prospecting", "hubspot", "crm"}),
        ("Facturación electrónica y servicio al cliente", {"cfdi", "customer_service"}),
        ("Experienced in C++ and C#", {"cpp", "csharp"}),
        ("Contenido para redes sociales", set()),
    ],
)
def test_skill_synonyms(text, expected):
    assert extract_skills(text) == expected


@pytest.mark.parametrize("stem", EXPECTED)
def test_cv_entities(stem):
    years, level = EXPECTED[stem]
    found = years_of_experience(SOURCES[stem], SAMPLES_TODAY)
    if years is None:
        assert found is None
    else:
        assert found == pytest.approx(years, abs=1)
    assert education_level(SOURCES[stem]) is level


@pytest.mark.parametrize("vacancy", VACANCIES, ids=lambda v: v["vacancy_id"])
def test_vacancy_requirements_match_structured_fields(vacancy):
    description = vacancy["description"]
    assert min_years_required(description) == vacancy["min_years_experience"]
    assert min_education_required(description) == vacancy["min_education_level"]
    listed = extract_skills(", ".join(vacancy["required_skills"] + vacancy["preferred_skills"]))
    assert listed <= extract_skills(description)


def test_pipeline_adds_language_and_profile():
    path = SAMPLES / "pdf" / "cv-08.pdf"
    cv = process_document(path.read_bytes(), path.name)
    assert cv.language is Language.ES
    assert {"excel", "power_bi", "python", "sql"} <= set(cv.profile.skills)
    assert cv.profile.education_level is M


def test_pipeline_rejects_unknown_language(monkeypatch):
    monkeypatch.setattr("cv_screening.pipeline.detect_language", lambda text: None)
    path = SAMPLES / "pdf" / "cv-01.pdf"
    with pytest.raises(IngestionError) as info:
        process_document(path.read_bytes(), path.name)
    assert info.value.kind is IngestionErrorKind.UNSUPPORTED_LANGUAGE
    cvs, errors = process_batch([(path.name, path.read_bytes())])
    assert not cvs and errors[0].kind is IngestionErrorKind.UNSUPPORTED_LANGUAGE
