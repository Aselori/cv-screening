"""Descarga y preparación del conjunto de datos de entrenamiento.

Uso:
    python -m cv_screening.datasets download
    python -m cv_screening.datasets prepare
"""

import argparse
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["download"])
    args = parser.parse_args()
    if args.command == "download":
        for path in download():
            print(path)


if __name__ == "__main__":
    main()
