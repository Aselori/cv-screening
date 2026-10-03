import pandas as pd

from cv_screening.datasets import prepare_split, text_id

CV_A = "Jane Roe\nData analyst, contact jane@example.com, 5 years of SQL."
CV_B = "Backend developer with Python and Django."
JOB = "Job Description\nData Analyst. Apply at hr@acme.example or 555-123-4567."


def test_prepare_split_cleans_anonymizes_and_reports():
    raw = pd.DataFrame(
        {
            "resume_text": [CV_A, CV_A, CV_B, CV_B],
            "job_description_text": [JOB, JOB, JOB, JOB],
            "label": ["Good Fit", "Good Fit", "No Fit", "Potential Fit"],
        }
    )
    out, report = prepare_split(raw, "train")

    # Un duplicado exacto se quita; el par de CV_B tiene etiquetas contradictorias y sale.
    assert report["exact_duplicates_removed"] == 1
    assert report["conflicting_label_rows_removed"] == 2
    assert len(out) == 1

    row = out.iloc[0]
    assert row.cv_id == text_id("cv", CV_A)
    assert row.label == "Good Fit"
    assert "Jane" not in row.cv_text and "jane@example.com" not in row.cv_text
    # La vacante conserva su encabezado y pierde el contacto.
    assert row.vacancy_text.startswith("Job Description")
    assert "hr@acme.example" not in row.vacancy_text
    assert "555-123-4567" not in row.vacancy_text
