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


def _lemmas(doc) -> list[str]:
    return [
        strip_accents(token.lemma_.lower())
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
