"""Pruebas del motor de puntuación y de la API (fase 6)."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cv_screening.api import create_app
from cv_screening.pipeline import process_document
from cv_screening.schemas import Vacancy
from cv_screening.scoring import evaluate_candidates

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples" / "es"
VACANCIES = json.loads((SAMPLES / "vacancies.json").read_text(encoding="utf-8"))
WEB_VACANCY = VACANCIES[0]


def _pdf(stem: str) -> tuple[str, bytes]:
    path = SAMPLES / "pdf" / f"{stem}.pdf"
    return path.name, path.read_bytes()


@pytest.fixture(scope="module")
def sample_cvs():
    paths = sorted((SAMPLES / "pdf").glob("cv-*.pdf"))
    return [process_document(path.read_bytes(), path.name) for path in paths]


@pytest.mark.parametrize("vacancy", VACANCIES, ids=lambda v: v["vacancy_id"])
def test_good_fit_candidates_rank_first(vacancy, sample_cvs):
    """En cada vacante, los dos CVs etiquetados como Good Fit quedan en los dos primeros lugares."""
    with open(SAMPLES / "labels.csv", encoding="utf-8") as f:
        good = {
            line.split(",")[1]
            for line in f
            if f",{vacancy['vacancy_id']}," in line and ",Good Fit," in line
        }
    ranking = evaluate_candidates(Vacancy.model_validate(vacancy), sample_cvs)
    assert {Path(e.file_name).stem for e in ranking[:2]} == good
    assert [e.score for e in ranking] == sorted((e.score for e in ranking), reverse=True)


def test_evaluation_explains_missing_skills(sample_cvs):
    ranking = evaluate_candidates(Vacancy.model_validate(WEB_VACANCY), sample_cvs)
    frontend = next(e for e in ranking if e.file_name == "cv-03.pdf")
    # cv-03 sabe React y JavaScript, pero no Node.js ni SQL.
    assert {"React", "JavaScript", "Git"} <= set(frontend.matched_skills)
    assert {"Node.js", "SQL"} <= set(frontend.missing_skills)


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "test.db"))


def test_full_flow(client):
    vacancy_data = {k: v for k, v in WEB_VACANCY.items() if k != "vacancy_id"}
    created = client.post("/vacancies", json=vacancy_data)
    assert created.status_code == 201
    vacancy_id = created.json()["vacancy_id"]
    assert [v["vacancy_id"] for v in client.get("/vacancies").json()] == [vacancy_id]

    files = [("files", _pdf(stem)) for stem in ("cv-01", "cv-03", "cv-17")]
    files.append(("files", ("roto.pdf", b"basura")))
    upload = client.post(f"/vacancies/{vacancy_id}/resumes", files=files).json()
    assert upload["processed"] == 3
    assert [e["error"] for e in upload["errors"]] == ["corrupt_file"]
    assert [e["file_name"] for e in upload["ranking"]][0] == "cv-01.pdf"
    assert "Villarreal" not in json.dumps(upload)

    # Volver a cargar el mismo CV no lo duplica.
    again = client.post(f"/vacancies/{vacancy_id}/resumes", files=[("files", _pdf("cv-01"))])
    assert len(again.json()["ranking"]) == 3

    filtered = client.get(f"/vacancies/{vacancy_id}/ranking", params={"skill": "node.js"}).json()
    assert [e["file_name"] for e in filtered] == ["cv-01.pdf"]

    candidate = upload["ranking"][0]["candidate_id"]
    url = f"/vacancies/{vacancy_id}/candidates/{candidate}/decision"
    decided = client.put(url, json={"decision": "Good Fit"})
    assert decided.json()["recruiter_decision"] == "Good Fit"
    ranking = client.get(f"/vacancies/{vacancy_id}/ranking").json()
    assert ranking[0]["recruiter_decision"] == "Good Fit"


def test_not_found_errors(client):
    assert client.get("/vacancies/v-nada").status_code == 404
    assert client.get("/vacancies/v-nada/ranking").status_code == 404
    vacancy_id = client.post("/vacancies", json={"title": "t", "description": "d"}).json()[
        "vacancy_id"
    ]
    url = f"/vacancies/{vacancy_id}/candidates/c-nada/decision"
    assert client.put(url, json={"decision": None}).status_code == 404


def test_model_metrics(client):
    metrics = client.get("/model/metrics").json()
    assert metrics["models"]["logistic_regression"]["english_test"]["macro_f1"] > 0
