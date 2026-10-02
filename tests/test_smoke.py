import spacy

import cv_screening


def test_package_version():
    assert cv_screening.__version__ == "0.1.0"


def test_spacy_english_model_loads():
    nlp = spacy.load("en_core_web_sm")
    doc = nlp("Jane Doe worked at Google using advanced Excel.")
    assert any(ent.label_ == "PERSON" for ent in doc.ents)
