"""Preprocesamiento de texto con PLN (RF-06): limpieza, normalización y lematización.

El resultado es la lista de lemas que usa TF-IDF en la fase 5.
"""

import re
import unicodedata
from collections.abc import Iterable
from functools import cache

import spacy

from cv_screening.schemas import Language

SPACY_MODELS = {Language.ES: "es_core_news_sm", Language.EN: "en_core_web_sm"}
# Etiquetas que deja la anonimización; no aportan contenido.
PLACEHOLDER_RE = re.compile(r"\[(?:NOMBRE|CORREO|TELEFONO|URL|DOMICILIO)\]")

# Formas femeninas de puestos y títulos, llevadas a una sola forma (RNF-02). El lematizador de
# spaCy las conserva ("desarrolladora"), y como las vacantes suelen escribirse en masculino, una
# candidata recibía menos similitud de texto que un candidato con el mismo CV (fase 8).
GENDERED_FORMS = {
    "desarrolladora": "desarrollador", "programadora": "programador",
    "administradora": "administrador", "coordinadora": "coordinador", "operadora": "operador",
    "trabajadora": "trabajador", "investigadora": "investigador", "vendedora": "vendedor",
    "contadora": "contador", "directora": "director", "asesora": "asesor",
    "consultora": "consultor", "supervisora": "supervisor", "profesora": "profesor",
    "doctora": "doctor", "diseñadora": "diseñador", "ingeniera": "ingeniero", "cajera": "cajero",
    "enfermera": "enfermero", "cocinera": "cocinero", "empleada": "empleado",
    "egresada": "egresado", "licenciada": "licenciado", "titulada": "titulado",
    "encargada": "encargado", "abogada": "abogado", "tecnica": "tecnico", "medica": "medico",
    "ejecutiva": "ejecutivo", "actuaria": "actuario", "maestra": "maestro", "jefa": "jefe",
}  # fmt: skip


@cache
def _nlp(language: Language):
    return spacy.load(SPACY_MODELS[language], disable=["parser", "ner"])


def strip_accents(text: str) -> str:
    """Quita acentos pero conserva la ñ ("año" no debe volverse "ano")."""
    text = text.replace("ñ", "\0").replace("Ñ", "\1")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return text.replace("\0", "ñ").replace("\1", "Ñ")


def clean(text: str) -> str:
    """Quita etiquetas de anonimización y separa palabras pegadas por viñetas o barras."""
    text = PLACEHOLDER_RE.sub(" ", text)
    return re.sub(r"[•|·]", " ", text)


def _lemma(token) -> str:
    # La palabra escrita se revisa antes que su lema: con mayúscula inicial, spaCy lematiza
    # "Desarrolladora" como "desarrolladoro".
    word = strip_accents(token.text.lower())
    if word in GENDERED_FORMS:
        return GENDERED_FORMS[word]
    lemma = strip_accents(token.lemma_.lower())
    return GENDERED_FORMS.get(lemma, lemma)


def _lemmas(doc) -> list[str]:
    return [
        _lemma(token)
        for token in doc
        if not (token.is_stop or token.is_punct or token.is_space or token.like_num)
        and any(c.isalpha() for c in token.text)
    ]


def preprocess(text: str, language: Language) -> list[str]:
    """Lemas en minúsculas y sin acentos, sin palabras vacías, puntuación ni números."""
    return _lemmas(_nlp(language)(clean(text)))


def preprocess_many(texts: Iterable[str], language: Language) -> list[list[str]]:
    """Versión por lotes de `preprocess`, mucho más rápida para el conjunto de datos."""
    docs = _nlp(language).pipe((clean(t) for t in texts), batch_size=32)
    return [_lemmas(doc) for doc in docs]
