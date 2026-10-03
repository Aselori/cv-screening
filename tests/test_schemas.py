import pytest
from pydantic import ValidationError

from cv_screening.schemas import (
    EducationLevel,
    Evaluation,
    Features,
    FitLabel,
    Vacancy,
)


def test_education_levels_are_ordered():
    assert EducationLevel.HIGH_SCHOOL.rank < EducationLevel.BACHELOR.rank
    assert EducationLevel.MASTER.rank < EducationLevel.DOCTORATE.rank


def test_features_reject_values_outside_zero_one():
    with pytest.raises(ValidationError):
        Features(text_similarity=1.2, skill_coverage=0, experience_fit=0, education_fit=0)


def test_vacancy_rejects_negative_experience():
    with pytest.raises(ValidationError):
        Vacancy(vacancy_id="v1", title="t", description="d", min_years_experience=-1)


def test_evaluation_matches_the_documented_contract():
    evaluation = Evaluation.model_validate(
        {
            "candidate_id": "c-0042",
            "vacancy_id": "v-0003",
            "file_name": "cv_0042.pdf",
            "score": 78.4,
            "predicted_class": "Good Fit",
            "probabilities": {"Good Fit": 0.64, "Potential Fit": 0.29, "No Fit": 0.07},
            "features": {
                "text_similarity": 0.41,
                "skill_coverage": 0.8,
                "experience_fit": 1.0,
                "education_fit": 1.0,
            },
            "matched_skills": ["python", "sql", "excel"],
            "missing_skills": ["tableau"],
            "years_experience": 4,
            "education_level": "bachelor",
            "recruiter_decision": None,
        }
    )
    assert evaluation.predicted_class is FitLabel.GOOD
    assert evaluation.education_level is EducationLevel.BACHELOR
