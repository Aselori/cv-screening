"""Flujo de procesamiento de CVs: lectura, anonimización, secciones, idioma y entidades.

La anonimización va antes del parsing porque necesita el encabezado completo para encontrar
el nombre, y así el `CV` resultante ya no contiene datos personales.

Uso:
    python -m cv_screening.pipeline data/samples/es/pdf --out salida/
"""

import argparse
import json
from pathlib import Path

from cv_screening.anonymization import anonymize
from cv_screening.extraction import education_level, years_of_experience
from cv_screening.ingestion import (
    IngestedDocument,
    IngestionError,
    IngestionErrorKind,
    extract_text,
    ingest_batch,
)
from cv_screening.knowledge import extract_skills
from cv_screening.language import detect_language
from cv_screening.parsing import parse_cv
from cv_screening.schemas import CV, CVProfile


def _to_cv(document: IngestedDocument, anonymized: bool) -> CV:
    language = detect_language(document.text)
    if language is None:
        raise IngestionError(IngestionErrorKind.UNSUPPORTED_LANGUAGE, document.file_name)
    text = anonymize(document.text).text if anonymized else document.text
    cv = parse_cv(text, document.file_name)
    cv.language = language
    # Las entidades se extraen del texto completo, igual que en los datos de entrenamiento.
    cv.profile = CVProfile(
        skills=sorted(extract_skills(text)),
        years_experience=years_of_experience(text),
        education_level=education_level(text),
    )
    return cv


def process_document(data: bytes, file_name: str, *, anonymized: bool = True) -> CV:
    """Convierte un PDF o DOCX en un `CV`. Lanza IngestionError si no se puede procesar."""
    return _to_cv(extract_text(data, file_name), anonymized)


def process_batch(
    files: list[tuple[str, bytes]], *, anonymized: bool = True
) -> tuple[list[CV], list[IngestionError]]:
    documents, errors = ingest_batch(files)
    cvs = []
    for document in documents:
        try:
            cvs.append(_to_cv(document, anonymized))
        except IngestionError as error:
            errors.append(error)
    return cvs, errors


def _collect(paths: list[Path]) -> list[Path]:
    files = []
    for path in paths:
        files.extend(sorted(p for p in path.iterdir() if p.is_file()) if path.is_dir() else [path])
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description="Procesa CVs en PDF o DOCX a JSON.")
    parser.add_argument("paths", nargs="+", type=Path, help="archivos o carpetas")
    parser.add_argument("--out", type=Path, required=True, help="carpeta de salida")
    parser.add_argument("--no-anonymize", action="store_true", help="conservar datos personales")
    args = parser.parse_args()

    files = [(p.name, p.read_bytes()) for p in _collect(args.paths)]
    cvs, errors = process_batch(files, anonymized=not args.no_anonymize)
    args.out.mkdir(parents=True, exist_ok=True)
    for cv in cvs:
        # Nombre completo con extensión: cv.pdf y cv.docx no deben sobrescribirse entre sí.
        out_file = args.out / f"{cv.file_name}.json"
        out_file.write_text(cv.model_dump_json(indent=2), encoding="utf-8")
    report = [{"file_name": e.file_name, "error": e.kind.value, "message": str(e)} for e in errors]
    (args.out / "errors.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"{len(cvs)} CVs procesados, {len(errors)} con error. Salida en {args.out}")


if __name__ == "__main__":
    main()
