"""Motor de puntuación: evalúa los CVs de una vacante y los ordena (fase 6, RF-08 y RF-09)."""

from functools import cache
from pathlib import Path

import joblib

from cv_screening.extraction import min_education_required, min_years_required
from cv_screening.features import FEATURE_NAMES, CandidateInput, VacancyInput, compute_features
from cv_screening.knowledge import extract_skills, skill_name
from cv_screening.language import detect_language
from cv_screening.models import MODELS_DIR, score
from cv_screening.preprocessing import preprocess
from cv_screening.schemas import CV, Evaluation, Features, FitLabel, Language, Vacancy

MODEL_FILE = MODELS_DIR / "model.joblib"


@cache
def load_model(path: Path = MODEL_FILE):
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Entrena el modelo con: python -m cv_screening.models train"
        )
    return joblib.load(path)["model"]


def vacancy_input(vacancy: Vacancy) -> VacancyInput:
    """Datos de la vacante para las características. Lo que el reclutador no llenó se extrae
    de la descripción."""
    text = f"{vacancy.title}. {vacancy.description}"
    language = vacancy.language or detect_language(text) or Language.ES
    required = (
        extract_skills(", ".join(vacancy.required_skills))
        if vacancy.required_skills
        else extract_skills(vacancy.description)
    )
    min_years = vacancy.min_years_experience
    min_education = vacancy.min_education_level
    return VacancyInput(
        lemmas=" ".join(preprocess(text, language)),
        required_skills=required,
        preferred_skills=extract_skills(", ".join(vacancy.preferred_skills)) - required,
        min_years=min_years if min_years is not None else min_years_required(vacancy.description),
        min_education=min_education or min_education_required(vacancy.description),
    )


def candidate_input(cv: CV) -> CandidateInput:
    language = cv.language or detect_language(cv.raw_text) or Language.ES
    profile = cv.profile
    return CandidateInput(
        lemmas=" ".join(preprocess(cv.raw_text, language)),
        skills=set(profile.skills) if profile else extract_skills(cv.raw_text),
        years=profile.years_experience if profile else None,
        education=profile.education_level if profile else None,
    )


def evaluate_candidates(vacancy: Vacancy, cvs: list[CV], model=None) -> list[Evaluation]:
    """Evalúa todos los CVs de una vacante a la vez y los devuelve del mejor al peor puntaje.

    Se evalúan juntos porque tres características comparan a cada candidato con los demás.
    """
    if not cvs:
        return []
    model = model or load_model()
    vacancy_data = vacancy_input(vacancy)
    X = compute_features(vacancy_data, [candidate_input(cv) for cv in cvs])
    classes = list(model.classes_)
    probabilities = model.predict_proba(X)
    scores = score(probabilities, classes)

    evaluations = []
    for cv, row, probs, value in zip(cvs, X, probabilities, scores, strict=True):
        skills = set(cv.profile.skills) if cv.profile else set()
        evaluations.append(
            Evaluation(
                candidate_id=cv.candidate_id,
                vacancy_id=vacancy.vacancy_id,
                file_name=cv.file_name,
                score=round(float(value), 1),
                predicted_class=FitLabel(classes[probs.argmax()]),
                probabilities={
                    FitLabel(c): round(float(p), 3) for c, p in zip(classes, probs, strict=True)
                },
                features=Features(**dict(zip(FEATURE_NAMES, map(float, row), strict=True))),
                matched_skills=sorted(skill_name(s) for s in vacancy_data.required_skills & skills),
                missing_skills=sorted(skill_name(s) for s in vacancy_data.required_skills - skills),
                years_experience=cv.profile.years_experience if cv.profile else None,
                education_level=cv.profile.education_level if cv.profile else None,
            )
        )
    # Mayor puntaje primero; en empate, mayor cobertura de habilidades (requisitos.md, sección 5).
    return sorted(evaluations, key=lambda e: (-e.score, -e.features.skill_coverage))
