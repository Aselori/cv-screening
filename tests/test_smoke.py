import spacy

import cv_screening


def test_package_version():
    assert cv_screening.__version__ == "0.1.0"


def test_spacy_english_model_loads():
    nlp = spacy.load("en_core_web_sm")
    doc = nlp("Jane Doe worked at Google using advanced Excel.")
    assert any(ent.label_ == "PERSON" for ent in doc.ents)


def test_spacy_spanish_model_lemmatizes():
    nlp = spacy.load("es_core_news_sm")
    lemmas = [token.lemma_ for token in nlp("Trabajó cinco años como analista de datos.")]
    assert "trabajar" in lemmas
    assert "dato" in lemmas
