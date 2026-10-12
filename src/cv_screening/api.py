"""API REST del sistema (fase 6). Documentación interactiva en /docs.

Uso:
    uvicorn cv_screening.api:app --reload
"""

import json
from pathlib import Path
from typing import Annotated

import numpy as np
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from cv_screening.datasets import DATA_DIR
from cv_screening.features import FEATURE_NAMES
from cv_screening.ingestion import MAX_BATCH_FILES
from cv_screening.models import MODELS_DIR, retrain_with_feedback
from cv_screening.pipeline import process_batch
from cv_screening.schemas import EducationLevel, Evaluation, FitLabel, Language, Vacancy
from cv_screening.scoring import evaluate_candidates, load_model
from cv_screening.storage import Storage

DEFAULT_DB = DATA_DIR / "app.db"
# Dashboard compilado con `pnpm build` en frontend/ (fase 7).
FRONTEND_DIST = DATA_DIR.parent / "frontend" / "dist"


class VacancyCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    language: Language | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_years_experience: float | None = Field(default=None, ge=0)
    min_education_level: EducationLevel | None = None


class FileError(BaseModel):
    file_name: str
    error: str
    message: str


class UploadResult(BaseModel):
    processed: int
    errors: list[FileError]
    ranking: list[Evaluation]


class Decision(BaseModel):
    decision: FitLabel | None


class RetrainResult(BaseModel):
    date: str
    feedback_pairs: int
    macro_f1_before: float
    macro_f1_after: float
    accepted: bool


def create_app(
    db_path=DEFAULT_DB, frontend_dir=FRONTEND_DIST, models_dir: Path = MODELS_DIR
) -> FastAPI:
    app = FastAPI(
        title="Selección y filtrado de currículums",
        description="Evalúa CVs en PDF o DOCX contra una vacante y los ordena por idoneidad.",
    )
    store = Storage(db_path)
    model_file = models_dir / "model.joblib"

    def evaluate_vacancy(vacancy: Vacancy) -> None:
        candidates = store.list_candidates(vacancy.vacancy_id)
        store.save_evaluations(evaluate_candidates(vacancy, candidates, load_model(model_file)))

    def vacancy_or_404(vacancy_id: str) -> Vacancy:
        vacancy = store.get_vacancy(vacancy_id)
        if vacancy is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "La vacante no existe.")
        return vacancy

    @app.post("/vacancies", status_code=status.HTTP_201_CREATED)
    def create_vacancy(data: VacancyCreate) -> Vacancy:
        return store.add_vacancy(Vacancy(vacancy_id="", **data.model_dump()))

    @app.get("/vacancies")
    def list_vacancies() -> list[Vacancy]:
        return store.list_vacancies()

    @app.get("/vacancies/{vacancy_id}")
    def get_vacancy(vacancy_id: str) -> Vacancy:
        return vacancy_or_404(vacancy_id)

    @app.post("/vacancies/{vacancy_id}/resumes")
    def upload_resumes(vacancy_id: str, files: Annotated[list[UploadFile], File()]) -> UploadResult:
        """Carga CVs y vuelve a evaluar a todos los candidatos de la vacante, porque tres
        características comparan a cada candidato con los demás."""
        vacancy = vacancy_or_404(vacancy_id)
        if len(files) > MAX_BATCH_FILES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, f"Máximo {MAX_BATCH_FILES} archivos por lote."
            )
        cvs, errors = process_batch([(f.filename or "sin_nombre", f.file.read()) for f in files])
        store.add_candidates(vacancy_id, cvs)
        evaluate_vacancy(vacancy)
        return UploadResult(
            processed=len(cvs),
            errors=[FileError(file_name=e.file_name, error=e.kind, message=str(e)) for e in errors],
            ranking=store.get_evaluations(vacancy_id),
        )

    @app.get("/vacancies/{vacancy_id}/ranking")
    def ranking(
        vacancy_id: str,
        min_score: float = Query(0, ge=0, le=100),
        skill: str | None = Query(None, description="Habilidad que debe tener el candidato"),
        min_years: float | None = Query(None, ge=0),
    ) -> list[Evaluation]:
        vacancy_or_404(vacancy_id)
        results = [e for e in store.get_evaluations(vacancy_id) if e.score >= min_score]
        if skill:
            wanted = skill.lower()
            results = [e for e in results if wanted in (s.lower() for s in e.matched_skills)]
        if min_years is not None:
            results = [e for e in results if (e.years_experience or 0) >= min_years]
        return results

    @app.put("/vacancies/{vacancy_id}/candidates/{candidate_id}/decision")
    def set_decision(vacancy_id: str, candidate_id: str, body: Decision) -> Evaluation:
        vacancy_or_404(vacancy_id)
        if not store.set_decision(vacancy_id, candidate_id, body.decision):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El candidato no existe.")
        return next(e for e in store.get_evaluations(vacancy_id) if e.candidate_id == candidate_id)

    @app.post("/model/retrain")
    def retrain() -> RetrainResult:
        """Reentrena con las decisiones del reclutador (RF-12). Si el modelo nuevo es peor en la
        prueba en inglés, se conserva el anterior."""
        feedback = store.feedback()
        # Las características relativas pueden faltar en evaluaciones antiguas: valor neutro 0.5.
        X = np.array(
            [
                [0.5 if (value := getattr(e.features, f)) is None else value for f in FEATURE_NAMES]
                for e, _ in feedback
            ]
        )
        try:
            result = retrain_with_feedback(X, [d.value for _, d in feedback], models_dir)
        except ValueError as error:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
        except FileNotFoundError as error:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Faltan los datos de entrenamiento: ejecuta `python -m cv_screening.datasets "
                "download`, `prepare` y `preprocess`.",
            ) from error
        if result["accepted"]:
            load_model.cache_clear()
            for vacancy in store.list_vacancies():
                evaluate_vacancy(vacancy)
        return RetrainResult(**result)

    @app.get("/model/metrics")
    def model_metrics() -> dict:
        path = models_dir / "metrics.json"
        if not path.exists():
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El modelo no se ha entrenado.")
        return json.loads(path.read_text(encoding="utf-8"))

    # Se monta al final para que las rutas de la API tengan prioridad sobre los archivos.
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="dashboard")
    return app


app = create_app()
