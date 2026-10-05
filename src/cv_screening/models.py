"""Entrenamiento, evaluación y puntaje de los modelos (fase 5).

Uso:
    python -m cv_screening.models train

Requiere haber ejecutado antes `python -m cv_screening.datasets prepare` y `preprocess`.
Guarda el modelo en models/model.joblib y las métricas en models/metrics.json.
"""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cv_screening.datasets import DATA_DIR, PROCESSED_DIR
from cv_screening.features import FEATURE_NAMES, CandidateInput, VacancyInput, compute_features
from cv_screening.knowledge import extract_skills
from cv_screening.pipeline import process_document
from cv_screening.preprocessing import preprocess
from cv_screening.schemas import EducationLevel, FitLabel, Language

MODELS_DIR = DATA_DIR.parent / "models"
SAMPLES_DIR = DATA_DIR / "samples" / "es"
LABELS = [FitLabel.NO.value, FitLabel.POTENTIAL.value, FitLabel.GOOD.value]
SEED = 0


def build_models() -> dict:
    """Modelo principal, modelo de comparación y línea base (solo similitud de texto)."""
    return {
        "logistic_regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED),
        ),
        "naive_bayes": GaussianNB(),
        "baseline_similarity": LogisticRegression(class_weight="balanced", random_state=SEED),
    }


def _columns(name: str) -> list[int]:
    return [0] if name == "baseline_similarity" else list(range(len(FEATURE_NAMES)))


def score(probabilities: np.ndarray, classes: list[str]) -> np.ndarray:
    """Puntaje de 0 a 100: 100 × (P(Good Fit) + 0.5 × P(Potential Fit))."""
    good = probabilities[:, classes.index(FitLabel.GOOD.value)]
    potential = probabilities[:, classes.index(FitLabel.POTENTIAL.value)]
    return 100 * (good + 0.5 * potential)


def _skills(value) -> set[str]:
    return set(value.split("|")) if isinstance(value, str) and value else set()


def _level(value) -> EducationLevel | None:
    return EducationLevel(value) if isinstance(value, str) and value else None


def _number(value) -> float | None:
    return None if pd.isna(value) else float(value)


def english_features(split: str, processed_dir: Path = PROCESSED_DIR) -> tuple:
    """Características de los pares de entrenamiento o prueba, calculadas por vacante."""
    pairs = pd.read_csv(processed_dir / f"{split}.csv")
    cvs = pd.read_csv(processed_dir / "cvs_nlp.csv").set_index("cv_id")
    vacancies = pd.read_csv(processed_dir / "vacancies_nlp.csv").set_index("vacancy_id")
    X = np.zeros((len(pairs), len(FEATURE_NAMES)))
    for vacancy_id, rows in pairs.groupby("vacancy_id").indices.items():
        v = vacancies.loc[vacancy_id]
        vacancy = VacancyInput(
            lemmas=v.lemmas if isinstance(v.lemmas, str) else "",
            required_skills=_skills(v.skills),
            min_years=_number(v.min_years_experience),
            min_education=_level(v.min_education_level),
        )
        candidates = []
        for cv_id in pairs.cv_id.iloc[rows]:
            c = cvs.loc[cv_id]
            candidates.append(
                CandidateInput(
                    lemmas=c.lemmas if isinstance(c.lemmas, str) else "",
                    skills=_skills(c.skills),
                    years=_number(c.years_experience),
                    education=_level(c.education_level),
                )
            )
        X[rows] = compute_features(vacancy, candidates)
    return X, pairs.label.to_numpy(), pairs.cv_id.to_numpy()


def spanish_features(samples_dir: Path = SAMPLES_DIR) -> tuple:
    """Características del conjunto propio: los 24 PDF pasan por el flujo completo."""
    candidates = {}
    for path in sorted((samples_dir / "pdf").glob("cv-*.pdf")):
        cv = process_document(path.read_bytes(), path.name)
        candidates[path.stem] = CandidateInput(
            lemmas=" ".join(preprocess(cv.raw_text, cv.language)),
            skills=set(cv.profile.skills),
            years=cv.profile.years_experience,
            education=cv.profile.education_level,
        )
    with open(samples_dir / "labels.csv", encoding="utf-8") as f:
        labels = pd.DataFrame(csv.DictReader(f))
    vacancies = json.loads((samples_dir / "vacancies.json").read_text(encoding="utf-8"))
    X = np.zeros((len(labels), len(FEATURE_NAMES)))
    for v in vacancies:
        vacancy = VacancyInput(
            lemmas=" ".join(preprocess(f"{v['title']}. {v['description']}", Language.ES)),
            required_skills=extract_skills(", ".join(v["required_skills"])),
            preferred_skills=extract_skills(", ".join(v["preferred_skills"])),
            min_years=v["min_years_experience"],
            min_education=_level(v["min_education_level"]),
        )
        rows = np.flatnonzero(labels.vacancy_id == v["vacancy_id"])
        X[rows] = compute_features(vacancy, [candidates[c] for c in labels.cv_id.iloc[rows]])
    same_domain = (labels.pair_type == "mismo dominio").to_numpy()
    return X, labels.label.to_numpy(), same_domain


def metrics(y_true, y_pred) -> dict:
    return {
        "macro_f1": round(f1_score(y_true, y_pred, average="macro", labels=LABELS), 3),
        "accuracy": round(accuracy_score(y_true, y_pred), 3),
        "f1_by_class": dict(
            zip(
                LABELS,
                np.round(f1_score(y_true, y_pred, average=None, labels=LABELS), 3).tolist(),
                strict=True,
            )
        ),
        # Renglones: clase real; columnas: clase predicha (orden de LABELS).
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist(),
    }


def train(models_dir: Path = MODELS_DIR) -> dict:
    X_train, y_train, groups = english_features("train")
    X_test, y_test, _ = english_features("test")
    X_es, y_es, same_domain = spanish_features()

    results = {"labels_order": LABELS, "features": FEATURE_NAMES, "models": {}}
    trained = {}
    for name, model in build_models().items():
        cols = _columns(name)
        grouped = cross_val_predict(
            model, X_train[:, cols], y_train, groups=groups, cv=GroupKFold(5)
        )
        model.fit(X_train[:, cols], y_train)
        trained[name] = model
        es_pred = model.predict(X_es[:, cols])
        results["models"][name] = {
            "english_test": metrics(y_test, model.predict(X_test[:, cols])),
            "english_grouped_cv": metrics(y_train, grouped),
            "spanish_all": metrics(y_es, es_pred),
            "spanish_same_domain": metrics(y_es[same_domain], es_pred[same_domain]),
        }
    always_no_fit = np.full(len(y_test), FitLabel.NO.value)
    results["models"]["always_no_fit"] = {"english_test": metrics(y_test, always_no_fit)}

    main_model = trained["logistic_regression"]
    regression = main_model[-1]
    # Coeficientes sobre características estandarizadas: comparables entre sí.
    results["logistic_regression_coefficients"] = {
        label: dict(zip(FEATURE_NAMES, np.round(row, 3).tolist(), strict=True))
        for label, row in zip(regression.classes_, regression.coef_, strict=True)
    }
    results["trained_at"] = datetime.now().isoformat(timespec="seconds")

    models_dir.mkdir(exist_ok=True)
    joblib.dump(
        {"model": main_model, "features": FEATURE_NAMES, "trained_at": results["trained_at"]},
        models_dir / "model.joblib",
    )
    (models_dir / "metrics.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["train"])
    parser.parse_args()
    results = train()
    for name, result in results["models"].items():
        summary = {split: r["macro_f1"] for split, r in result.items()}
        print(f"{name}: macro F1 {summary}")


if __name__ == "__main__":
    main()
