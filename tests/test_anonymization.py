from cv_screening.anonymization import anonymize, header_name, looks_like_name

SPANISH_CV = """María Fernanda López Garza
Analista de datos
Correo: maria.lopez@example.com | Tel. +52 81 1234 5678 | linkedin.com/in/mflopez
Calle Hidalgo 123, Col. Centro, Monterrey, N.L. C.P. 64000

Experiencia
Cemex, Analista de datos (2019 - 2023). Manejo avanzado de hojas de cálculo.
María Fernanda López Garza coordinó reportes semanales.

Educación
Licenciatura en Ingeniería en Sistemas, UANL (2014 - 2018).
"""

ENGLISH_CV = (
    "Jessica Claire\nPhone: (555) 432-1000 resumesample@example.com Atlanta, GA 30043\n"
    "Summary: Data analyst with 5 years of experience in advanced Excel and SQL.\n"
    "Experience 2016 - 2021 Company Name, Data Analyst."
)


def test_looks_like_name():
    assert looks_like_name("María Fernanda López Garza")
    assert looks_like_name("José de la Garza")
    assert not looks_like_name("Experiencia Profesional")
    assert not looks_like_name("Analista de datos")
    assert not looks_like_name("Ingeniero 2019")
    assert not looks_like_name("Software Engineer")
    assert not looks_like_name("Job Description")


def test_header_name_is_first_name_like_line():
    assert header_name(SPANISH_CV) == "María Fernanda López Garza"


def test_spanish_cv_removes_personal_data_and_keeps_content():
    result = anonymize(SPANISH_CV)
    text = result.text
    for personal in ("María", "López", "maria.lopez", "1234 5678", "mflopez", "Hidalgo", "64000"):
        assert personal not in text
    for content in ("Cemex", "Licenciatura", "hojas de cálculo", "UANL", "2019 - 2023"):
        assert content in text
    assert result.replacements["name"] == 2


def test_english_cv_removes_placeholder_contact_data():
    result = anonymize(ENGLISH_CV)
    text = result.text
    for personal in ("Jessica Claire", "432-1000", "resumesample", "GA 30043"):
        assert personal not in text
    for content in ("Excel", "SQL", "2016 - 2021", "5 years"):
        assert content in text


def test_years_are_not_phones():
    text = "Periodo 2018-2021 y 2021 - 2024, folio 12345. Scholarship 2011-20153.9 GPA"
    assert anonymize(text).text == text


def test_labeled_name_is_removed_everywhere():
    text = "CURRÍCULUM VITAE\nNombre: Juan Pérez Treviño\nJuan Pérez Treviño lideró el equipo."
    result = anonymize(text)
    assert "Juan" not in result.text
    assert result.replacements["name"] == 2


def test_job_title_header_is_kept():
    text = "Software Engineer\nBuilt REST APIs with Python."
    assert anonymize(text).text == text


def test_vacancy_keeps_headings_but_removes_contact_data():
    vacancy = "Job Description\nSend your CV to jobs@acme.example or call 555-123-4567."
    text = anonymize(vacancy, remove_names=False).text
    assert text.startswith("Job Description")
    assert "[CORREO]" in text and "[TELEFONO]" in text


def test_us_city_pattern_does_not_swallow_preceding_words():
    text = anonymize("Summary Senior Data Analyst Lawrenceville, GA 30043 SQL").text
    assert text.startswith("Summary Senior Data Analyst ")
    assert "30043" not in text
