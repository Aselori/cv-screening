"""Características de cada par CV-vacante (docs/requisitos.md, sección 5).

Se calculan por vacante, con todos sus candidatos a la vez: así se usa el sistema (el
reclutador carga los CVs de una vacante) y así se entrena. Ninguna característica depende del
idioma, por eso el modelo entrenado con pares en inglés puede evaluar pares en español (D7).
"""

from dataclasses import dataclass, field

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from cv_screening.schemas import EducationLevel

FEATURE_NAMES = [
    "text_similarity",
    "skill_coverage",
    "experience_fit",
    "education_fit",
    # Relativas a los demás candidatos de la misma vacante (agregadas en la fase 5).
    "similarity_rank",
    "coverage_rank",
    "matched_skills",
]
MAX_MATCHED_SKILLS = 10


@dataclass
class VacancyInput:
    lemmas: str
    required_skills: set[str] = field(default_factory=set)
    preferred_skills: set[str] = field(default_factory=set)
    min_years: float | None = None
    min_education: EducationLevel | None = None


@dataclass
class CandidateInput:
    lemmas: str
    skills: set[str] = field(default_factory=set)
    years: float | None = None
    education: EducationLevel | None = None


def text_similarity(vacancy_lemmas: str, candidate_lemmas: list[str]) -> np.ndarray:
    """Similitud coseno TF-IDF de cada candidato con la vacante.

    El TF-IDF se ajusta con la vacante y sus candidatos: no necesita un corpus por idioma y se
    comporta igual en entrenamiento y en uso real (decisión D9).
    """
    documents = [vacancy_lemmas or ""] + [c or "" for c in candidate_lemmas]
    try:
        matrix = TfidfVectorizer(sublinear_tf=True).fit_transform(documents)
    except ValueError:  # Ningún documento tiene palabras.
        return np.zeros(len(candidate_lemmas))
    return (matrix[1:] @ matrix[0].T).toarray().ravel()


def skill_coverage(vacancy: VacancyInput, skills: set[str]) -> float:
    """(requeridas encontradas + 0.5 × deseables encontradas) / (requeridas + 0.5 × deseables)."""
    total = len(vacancy.required_skills) + 0.5 * len(vacancy.preferred_skills)
    if total == 0:
        return 1.0
    found = len(vacancy.required_skills & skills) + 0.5 * len(vacancy.preferred_skills & skills)
    return found / total


def experience_fit(min_years: float | None, years: float | None) -> float:
    if not min_years:
        return 1.0
    if years is None:
        return 0.0
    return min(years / min_years, 1.0)


def education_fit(minimum: EducationLevel | None, level: EducationLevel | None) -> float:
    if minimum is None:
        return 1.0
    if level is None:
        return 0.0
    return 1.0 if level.rank >= minimum.rank else 0.5


def _rank(values: np.ndarray) -> np.ndarray:
    """Percentil de cada valor entre los candidatos, de 0 a 1; un solo candidato vale 0.5."""
    order = values.argsort().argsort()
    # Los empates reciben el promedio de sus posiciones.
    ranks = np.array([order[values == v].mean() for v in values], dtype=float)
    return (ranks + 0.5) / len(values)


def compute_features(vacancy: VacancyInput, candidates: list[CandidateInput]) -> np.ndarray:
    """Matriz de características (un renglón por candidato, columnas en FEATURE_NAMES)."""
    if not candidates:
        return np.zeros((0, len(FEATURE_NAMES)))
    similarity = text_similarity(vacancy.lemmas, [c.lemmas for c in candidates])
    coverage = np.array([skill_coverage(vacancy, c.skills) for c in candidates])
    matched = np.array(
        [min(len(vacancy.required_skills & c.skills), MAX_MATCHED_SKILLS) for c in candidates]
    )
    return np.column_stack(
        [
            similarity,
            coverage,
            [experience_fit(vacancy.min_years, c.years) for c in candidates],
            [education_fit(vacancy.min_education, c.education) for c in candidates],
            _rank(similarity),
            _rank(coverage),
            matched / MAX_MATCHED_SKILLS,
        ]
    )
