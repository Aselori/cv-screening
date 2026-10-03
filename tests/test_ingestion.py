import io
from pathlib import Path

import pytest
from PIL import Image

from cv_screening.ingestion import (
    PRIVATE_USE_RE,
    IngestionError,
    IngestionErrorKind,
    extract_text,
    ingest_batch,
)

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples" / "es"


def _sample(fmt: str, stem: str) -> tuple[str, bytes]:
    path = SAMPLES / fmt / f"{stem}.{fmt}"
    return path.name, path.read_bytes()


def _extract(fmt: str, stem: str):
    name, data = _sample(fmt, stem)
    return extract_text(data, name)


@pytest.mark.parametrize("fmt", ["pdf", "docx"])
def test_extracts_text_from_both_formats(fmt):
    document = _extract(fmt, "cv-01")
    assert document.text.startswith("Andrés Villarreal Treviño")
    assert "PostgreSQL" in document.text


@pytest.mark.parametrize("fmt", ["pdf", "docx"])
def test_header_table_puts_name_first(fmt):
    # cv-02 tiene el encabezado en una tabla de dos columnas.
    document = _extract(fmt, "cv-02")
    assert document.text.startswith("Sofía Elizondo Cantú")


def test_word_bullets_are_normalized_in_pdf():
    document = _extract("pdf", "cv-03")
    assert not PRIVATE_USE_RE.search(document.text)
    assert "• Componentes reutilizables" in document.text


def _error_kind(data: bytes, file_name: str) -> IngestionErrorKind:
    with pytest.raises(IngestionError) as info:
        extract_text(data, file_name)
    return info.value.kind


def test_unsupported_format():
    assert _error_kind(b"hola", "cv.txt") is IngestionErrorKind.UNSUPPORTED_FORMAT
    assert _error_kind(b"hola", "cv.doc") is IngestionErrorKind.UNSUPPORTED_FORMAT


def test_corrupt_files():
    assert _error_kind(b"no soy un pdf", "cv.pdf") is IngestionErrorKind.CORRUPT_FILE
    assert _error_kind(b"no soy un docx", "cv.docx") is IngestionErrorKind.CORRUPT_FILE
    assert _error_kind(b"%PDF-1.7 truncado", "cv.pdf") is IngestionErrorKind.CORRUPT_FILE


def test_scanned_pdf_has_no_text():
    buffer = io.BytesIO()
    Image.new("RGB", (600, 800), "white").save(buffer, format="PDF")
    assert _error_kind(buffer.getvalue(), "escaneado.pdf") is IngestionErrorKind.NO_TEXT


def test_too_large(monkeypatch):
    monkeypatch.setattr("cv_screening.ingestion.MAX_FILE_BYTES", 10)
    name, data = _sample("pdf", "cv-01")
    assert _error_kind(data, name) is IngestionErrorKind.TOO_LARGE


def test_batch_reports_errors_without_stopping():
    documents, errors = ingest_batch(
        [_sample("pdf", "cv-01"), ("roto.pdf", b"basura"), _sample("docx", "cv-02")]
    )
    assert [d.file_name for d in documents] == ["cv-01.pdf", "cv-02.docx"]
    assert [(e.file_name, e.kind) for e in errors] == [
        ("roto.pdf", IngestionErrorKind.CORRUPT_FILE)
    ]


def test_batch_size_limit():
    with pytest.raises(ValueError):
        ingest_batch([("a.pdf", b"")] * 51)
