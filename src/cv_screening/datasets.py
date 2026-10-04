"""Descarga y preparación del conjunto de datos de entrenamiento.

Uso:
    python -m cv_screening.datasets download
    python -m cv_screening.datasets prepare
    python -m cv_screening.datasets preprocess
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

from cv_screening.anonymization import anonymize
from cv_screening.extraction import (
    education_level,
    min_education_required,
    min_years_required,
    years_of_experience,
)
from cv_screening.knowledge import extract_skills
from cv_screening.preprocessing import preprocess_many
from cv_screening.schemas import LabeledPair, Language

REPO_ID = "cnamuangtoun/resume-job-description-fit"
# Versión fija del conjunto de datos para que la descarga sea reproducible (RNF-04).
REVISION = "08978e21714984bb417547d2c0f9b477f5298163"
SPLITS = ("train", "test")

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


def download(raw_dir: Path = RAW_DIR) -> list[Path]:
    """Descarga los CSV de entrenamiento y prueba a data/raw/."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    return [
        Path(
            hf_hub_download(
                repo_id=REPO_ID,
                filename=f"{split}.csv",
                repo_type="dataset",
                revision=REVISION,
                local_dir=raw_dir,
            )
        )
        for split in SPLITS
    ]


def load_raw(split: str, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    return pd.read_csv(raw_dir / f"{split}.csv")


def text_id(prefix: str, text: str) -> str:
    """Identificador estable de un texto, para agrupar los pares por CV o por vacante."""
    return f"{prefix}-{hashlib.sha1(text.encode()).hexdigest()[:10]}"


def _anonymize_unique(texts: pd.Series, remove_names: bool) -> tuple[dict[str, str], Counter]:
    """Anonimiza cada texto distinto una sola vez (los CVs se repiten en muchos pares)."""
    clean, counts = {}, Counter()
    for text in texts.unique():
        result = anonymize(text, remove_names=remove_names)
        clean[text] = result.text
        counts += result.replacements
    return clean, counts


def prepare_split(raw: pd.DataFrame, split: str) -> tuple[pd.DataFrame, dict]:
    """Quita duplicados y pares con etiquetas contradictorias, anonimiza y valida."""
    pair_cols = ["resume_text", "job_description_text"]
    df = raw.drop_duplicates()
    conflicting = int(df.duplicated(pair_cols, keep=False).sum())
    df = df.drop_duplicates(pair_cols, keep=False).reset_index(drop=True)

    cv_clean, cv_counts = _anonymize_unique(df.resume_text, remove_names=True)
    vacancy_clean, vacancy_counts = _anonymize_unique(df.job_description_text, remove_names=False)
    out = pd.DataFrame(
        {
            "pair_id": [f"{split}-{i:05d}" for i in range(len(df))],
            "cv_id": df.resume_text.map(lambda t: text_id("cv", t)),
            "vacancy_id": df.job_description_text.map(lambda t: text_id("vac", t)),
            "cv_text": df.resume_text.map(cv_clean),
            "vacancy_text": df.job_description_text.map(vacancy_clean),
            "label": df.label,
            "language": Language.EN.value,
            "source": f"{REPO_ID}@{REVISION[:7]}/{split}",
        }
    )
    for row in out.to_dict("records"):
        LabeledPair.model_validate(row)

    report = {
        "raw_rows": len(raw),
        "exact_duplicates_removed": len(raw) - len(raw.drop_duplicates()),
        "conflicting_label_rows_removed": conflicting,
        "rows": len(out),
        "labels": out.label.value_counts().to_dict(),
        "unique_cvs": out.cv_id.nunique(),
        "unique_vacancies": out.vacancy_id.nunique(),
        "replacements": {"cv": dict(cv_counts), "vacancy": dict(vacancy_counts)},
    }
    return out, report


def prepare(raw_dir: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR) -> dict:
    """Limpia y anonimiza los pares, y los guarda en data/processed/ con un reporte."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    report = {"source": REPO_ID, "revision": REVISION, "splits": {}}
    frames = {}
    for split in SPLITS:
        frames[split], report["splits"][split] = prepare_split(load_raw(split, raw_dir), split)
        frames[split].to_csv(processed_dir / f"{split}.csv", index=False)
    train, test = frames["train"], frames["test"]
    report["overlap_train_test"] = {
        "cvs": len(set(train.cv_id) & set(test.cv_id)),
        "vacancies": len(set(train.vacancy_id) & set(test.vacancy_id)),
    }
    (processed_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def preprocess_texts(processed_dir: Path = PROCESSED_DIR) -> dict:
    """Lematiza y extrae entidades de cada CV y vacante distintos, una sola vez.

    Guarda data/processed/cvs_nlp.csv y vacancies_nlp.csv para la fase 5 y devuelve la
    cobertura de la extracción.
    """
    pairs = pd.concat(pd.read_csv(processed_dir / f"{split}.csv") for split in SPLITS)
    cvs = pairs.drop_duplicates("cv_id")[["cv_id", "cv_text"]]
    vacancies = pairs.drop_duplicates("vacancy_id")[["vacancy_id", "vacancy_text"]]

    cv_skills = [extract_skills(t) for t in cvs.cv_text]
    cv_table = pd.DataFrame(
        {
            "cv_id": cvs.cv_id,
            "lemmas": [" ".join(x) for x in preprocess_many(cvs.cv_text, Language.EN)],
            "skills": ["|".join(sorted(x)) for x in cv_skills],
            "years_experience": [years_of_experience(t) for t in cvs.cv_text],
            "education_level": [education_level(t) for t in cvs.cv_text],
        }
    )
    vacancy_skills = [extract_skills(t) for t in vacancies.vacancy_text]
    vacancy_table = pd.DataFrame(
        {
            "vacancy_id": vacancies.vacancy_id,
            "lemmas": [" ".join(x) for x in preprocess_many(vacancies.vacancy_text, Language.EN)],
            "skills": ["|".join(sorted(x)) for x in vacancy_skills],
            "min_years_experience": [min_years_required(t) for t in vacancies.vacancy_text],
            "min_education_level": [min_education_required(t) for t in vacancies.vacancy_text],
        }
    )
    cv_table.to_csv(processed_dir / "cvs_nlp.csv", index=False)
    vacancy_table.to_csv(processed_dir / "vacancies_nlp.csv", index=False)

    def share(series) -> float:
        return round(float(series.mean()), 3)

    return {
        "cvs": len(cv_table),
        "vacancies": len(vacancy_table),
        "cv_with_years": share(cv_table.years_experience.notna()),
        "cv_with_education": share(cv_table.education_level.notna()),
        "cv_median_skills": float(pd.Series(map(len, cv_skills)).median()),
        "vacancy_with_3_skills": share(pd.Series(map(len, vacancy_skills)) >= 3),
        "vacancy_median_skills": float(pd.Series(map(len, vacancy_skills)).median()),
        "vacancy_with_min_years": share(vacancy_table.min_years_experience.notna()),
        "vacancy_with_min_education": share(vacancy_table.min_education_level.notna()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["download", "prepare", "preprocess"])
    args = parser.parse_args()
    if args.command == "download":
        for path in download():
            print(path)
    elif args.command == "prepare":
        print(json.dumps(prepare(), indent=2, ensure_ascii=False))
    elif args.command == "preprocess":
        print(json.dumps(preprocess_texts(), indent=2))


if __name__ == "__main__":
    main()
