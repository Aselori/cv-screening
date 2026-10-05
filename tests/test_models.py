import numpy as np
import pytest

from cv_screening.features import (
    FEATURE_NAMES,
    CandidateInput,
    VacancyInput,
    _rank,
    compute_features,
    education_fit,
    experience_fit,
    skill_coverage,
)
from cv_screening.models import LABELS, build_models, score
from cv_screening.schemas import EducationLevel


def test_skill_coverage_weights_preferred_skills_by_half():
    vacancy = VacancyInput(
        lemmas="", required_skills={"sql", "excel"}, preferred_skills={"tableau"}
    )
    # (1 requerida + 0.5 × 1 deseable) / (2 + 0.5 × 1)
    assert skill_coverage(vacancy, {"sql", "tableau"}) == pytest.approx(1.5 / 2.5)
    assert skill_coverage(VacancyInput(lemmas=""), {"sql"}) == 1.0


def test_experience_and_education_fit():
    assert experience_fit(None, None) == 1.0
    assert experience_fit(2, None) == 0.0
    assert experience_fit(4, 1) == 0.25
    assert experience_fit(2, 5) == 1.0
    bachelor, technical = EducationLevel.BACHELOR, EducationLevel.TECHNICAL
    assert education_fit(None, None) == 1.0
    assert education_fit(bachelor, None) == 0.0
    assert education_fit(bachelor, technical) == 0.5
    assert education_fit(technical, bachelor) == 1.0


def test_rank_is_a_percentile_with_neutral_single_value():
    assert _rank(np.array([0.7])).tolist() == [0.5]
    assert _rank(np.array([0.1, 0.9, 0.5])).tolist() == pytest.approx([1 / 6, 5 / 6, 3 / 6])
    assert _rank(np.array([0.3, 0.3])).tolist() == [0.5, 0.5]


def test_similar_candidate_scores_higher_text_similarity():
    vacancy = VacancyInput(lemmas="analista dato sql python power bi")
    candidates = [
        CandidateInput(lemmas="analista dato sql python tablero"),
        CandidateInput(lemmas="cocinero parrilla cocina inventario"),
    ]
    features = compute_features(vacancy, candidates)
    assert features.shape == (2, len(FEATURE_NAMES))
    assert features[0, 0] > features[1, 0]
    assert features[1, 0] == 0.0


def test_score_formula():
    probabilities = np.array([[0.1, 0.3, 0.6], [1.0, 0.0, 0.0]])  # columnas en orden LABELS
    assert score(probabilities, LABELS).tolist() == pytest.approx([75.0, 0.0])


def test_models_train_and_predict_on_small_data():
    rng = np.random.default_rng(0)
    X = rng.random((60, len(FEATURE_NAMES)))
    y = np.array(LABELS * 20)
    for name, model in build_models().items():
        cols = [0] if name == "baseline_similarity" else slice(None)
        model.fit(X[:, cols], y)
        assert set(model.predict(X[:, cols])) <= set(LABELS)
