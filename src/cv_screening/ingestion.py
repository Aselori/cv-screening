"""Lectura de currículums en PDF y DOCX (RF-02, RF-04).

Cada archivo se procesa por separado: un error en uno no detiene el resto del lote.
"""

import io
import re
import zipfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import docx
import pdfplumber
from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_BATCH_FILES = 50
# Un PDF con menos texto que esto se considera escaneado (sin capa de texto).
MIN_TEXT_CHARS = 30

# Las viñetas de Word salen en el PDF como caracteres de uso privado (fuente Symbol).
PRIVATE_USE_RE = re.compile(r"[-]")


class IngestionErrorKind(StrEnum):
    UNSUPPORTED_FORMAT = "unsupported_format"
    TOO_LARGE = "too_large"
    CORRUPT_FILE = "corrupt_file"
    NO_TEXT = "no_text"
    UNSUPPORTED_LANGUAGE = "unsupported_language"


ERROR_MESSAGES = {
    IngestionErrorKind.UNSUPPORTED_FORMAT: "Formato no soportado: solo se aceptan PDF y DOCX.",
    IngestionErrorKind.TOO_LARGE: "El archivo supera el tamaño máximo de 5 MB.",
    IngestionErrorKind.CORRUPT_FILE: "El archivo está dañado o no se puede abrir.",
    IngestionErrorKind.NO_TEXT: "El PDF no tiene texto extraíble (posiblemente es escaneado).",
    IngestionErrorKind.UNSUPPORTED_LANGUAGE: "No se reconoce el idioma: solo español o inglés.",
}


class IngestionError(Exception):
    def __init__(self, kind: IngestionErrorKind, file_name: str):
        self.kind = kind
        self.file_name = file_name
        super().__init__(f"{file_name}: {ERROR_MESSAGES[kind]}")


@dataclass
class IngestedDocument:
    file_name: str
    text: str


def _clean(text: str) -> str:
    text = PRIVATE_USE_RE.sub("•", text)
    lines = (line.strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def _pdf_text(data: bytes) -> str:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _docx_blocks(document: DocxDocument):
    """Párrafos y tablas en el orden en que aparecen en el documento."""
    for child in document.element.body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, document)
        elif child.tag.endswith("}tbl"):
            yield Table(child, document)


def _docx_text(data: bytes) -> str:
    document = docx.Document(io.BytesIO(data))
    lines = []
    for block in _docx_blocks(document):
        if isinstance(block, Paragraph):
            lines.append(block.text)
            continue
        for row in block.rows:
            seen = set()
            for cell in row.cells:
                # Las celdas combinadas se repiten en python-docx; se leen una sola vez.
                if id(cell._tc) in seen:
                    continue
                seen.add(id(cell._tc))
                lines.extend(p.text for p in cell.paragraphs)
    return "\n".join(lines)


def extract_text(data: bytes, file_name: str) -> IngestedDocument:
    """Extrae el texto de un PDF o DOCX. Lanza IngestionError si no se puede."""
    suffix = Path(file_name).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise IngestionError(IngestionErrorKind.UNSUPPORTED_FORMAT, file_name)
    if len(data) > MAX_FILE_BYTES:
        raise IngestionError(IngestionErrorKind.TOO_LARGE, file_name)

    is_pdf = suffix == ".pdf"
    # Se revisa el contenido, no solo la extensión: un .docx es un ZIP y un PDF empieza con %PDF.
    valid_signature = data.startswith(b"%PDF") if is_pdf else zipfile.is_zipfile(io.BytesIO(data))
    if not valid_signature:
        raise IngestionError(IngestionErrorKind.CORRUPT_FILE, file_name)
    try:
        text = _pdf_text(data) if is_pdf else _docx_text(data)
    except Exception as error:  # Cada librería lanza sus propias excepciones al fallar.
        raise IngestionError(IngestionErrorKind.CORRUPT_FILE, file_name) from error

    text = _clean(text)
    if len(text) < MIN_TEXT_CHARS:
        raise IngestionError(IngestionErrorKind.NO_TEXT, file_name)
    return IngestedDocument(file_name=file_name, text=text)


def ingest_batch(
    files: list[tuple[str, bytes]],
) -> tuple[list[IngestedDocument], list[IngestionError]]:
    """Procesa un lote de (nombre, contenido); devuelve los documentos y los errores por archivo."""
    if len(files) > MAX_BATCH_FILES:
        raise ValueError(f"Un lote admite como máximo {MAX_BATCH_FILES} archivos.")
    documents, errors = [], []
    for file_name, data in files:
        try:
            documents.append(extract_text(data, file_name))
        except IngestionError as error:
            errors.append(error)
    return documents, errors
