"""Contratos de datos del sistema (ver docs/arquitectura.md, sección 4)."""

from enum import StrEnum

from pydantic import BaseModel, Field


class Language(StrEnum):
    ES = "es"
    EN = "en"


class FitLabel(StrEnum):
    """Clases de idoneidad de un par CV-vacante. En la interfaz: Apto, Posible, No apto."""

    GOOD = "Good Fit"
    POTENTIAL = "Potential Fit"
    NO = "No Fit"


class EducationLevel(StrEnum):
    """Niveles educativos ordenados de menor a mayor."""

    HIGH_SCHOOL = "high_school"
    TECHNICAL = "technical"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"

    @property
    def rank(self) -> int:
        return list(EducationLevel).index(self)


class CVSections(BaseModel):
    summary: str = ""
    experience: str = ""
    education: str = ""
    skills: str = ""
    other: str = ""


class CV(BaseModel):
    """Salida del parsing de un currículum."""

    candidate_id: str
    file_name: str | None = None
    language: Language | None = None
    raw_text: str
    sections: CVSections = Field(default_factory=CVSections)


class Vacancy(BaseModel):
    vacancy_id: str
    title: str
    description: str
    language: Language | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_years_experience: float | None = Field(default=None, ge=0)
    min_education_level: EducationLevel | None = None


class Features(BaseModel):
    """Características independientes del idioma (docs/requisitos.md, sección 5)."""

    text_similarity: float = Field(ge=0, le=1)
    skill_coverage: float = Field(ge=0, le=1)
    experience_fit: float = Field(ge=0, le=1)
    education_fit: float = Field(ge=0, le=1)


class Evaluation(BaseModel):
    """Resultado de evaluar un CV contra una vacante; es lo que recibe el dashboard."""

    candidate_id: str
    vacancy_id: str
    file_name: str | None = None
    score: float = Field(ge=0, le=100)
    predicted_class: FitLabel
    probabilities: dict[FitLabel, float]
    features: Features
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    years_experience: float | None = None
    education_level: EducationLevel | None = None
    recruiter_decision: FitLabel | None = None


class LabeledPair(BaseModel):
    """Par CV-vacante etiquetado, para entrenar o evaluar los modelos."""

    pair_id: str
    cv_text: str
    vacancy_text: str
    label: FitLabel
    language: Language
    source: str
