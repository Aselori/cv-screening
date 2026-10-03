"""Descarga y preparación del conjunto de datos de entrenamiento.

Uso:
    python -m cv_screening.datasets download
    python -m cv_screening.datasets prepare
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

from cv_screening.anonymization import anonymize
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["download", "prepare"])
    args = parser.parse_args()
    if args.command == "download":
        for path in download():
            print(path)
    elif args.command == "prepare":
        print(json.dumps(prepare(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
