"""Revisión de sesgos (RNF-02, fase 8).

El puntaje no debe cambiar si cambia el nombre de la persona ni si su puesto está escrito en
femenino o en masculino.
"""

import json
import re
from pathlib import Path

import pytest

from cv_screening.ingestion import extract_text
from cv_screening.pipeline import process_text
from cv_screening.schemas import Vacancy
from cv_screening.scoring import evaluate_candidates

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples" / "es"
VACANCIES = [
    Vacancy.model_validate(v)
    for v in json.loads((SAMPLES / "vacancies.json").read_text(encoding="utf-8"))
]
FEMININE_TO_MASCULINE = {
    "Desarrolladora": "Desarrollador", "desarrolladora": "desarrollador",
    "Ingeniera": "Ingeniero", "Ejecutiva": "Ejecutivo", "Cajera": "Cajero",
    "Enfermera": "Enfermero", "Técnica": "Técnico", "Contadora": "Contador",
    "Egresada": "Egresado", "Vendedora": "Vendedor", "Diseñadora": "Diseñador",
}  # fmt: skip


@pytest.fixture(scope="module")
def texts() -> dict[str, str]:
    return {
        p.stem: extract_text(p.read_bytes(), p.name).text
        for p in sorted((SAMPLES / "docx").glob("cv-*.docx"))
    }


def _scores(texts: dict[str, str]) -> dict[tuple[str, str], float]:
    cvs = [process_text(text, f"{stem}.docx") for stem, text in texts.items()]
    return {
        (vacancy.vacancy_id, e.file_name): e.score
        for vacancy in VACANCIES
        for e in evaluate_candidates(vacancy, cvs)
    }


def _max_change(before: dict, after: dict) -> float:
    return max(abs(before[key] - after[key]) for key in before)


def test_changing_the_name_does_not_change_any_score(texts):
    names = ["Juan Pérez García", "María López García"]
    renamed = {
        stem: re.sub(r"^.+$", names[i % 2], text, count=1)
        for i, (stem, text) in enumerate(texts.items())
    }
    assert _max_change(_scores(texts), _scores(renamed)) == 0


def test_feminine_job_titles_do_not_change_scores(texts):
    def masculine(text: str) -> str:
        for feminine, masc in FEMININE_TO_MASCULINE.items():
            text = re.sub(rf"(?<!\w){feminine}(?!\w)", masc, text)
        return text

    swapped = {stem: masculine(text) for stem, text in texts.items()}
    assert swapped != texts
    # Antes de normalizar los puestos, el cambio llegaba a 5 puntos.
    assert _max_change(_scores(texts), _scores(swapped)) <= 0.5
