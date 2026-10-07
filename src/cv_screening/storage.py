"""Almacenamiento local en SQLite: vacantes, candidatos y evaluaciones (fase 6).

Cada candidato pertenece a una vacante y guarda su CV ya anonimizado, su última evaluación y
la decisión del reclutador. Los objetos se guardan como JSON con los contratos de schemas.py.
"""

import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from cv_screening.schemas import CV, Evaluation, FitLabel, Vacancy

SCHEMA = """
CREATE TABLE IF NOT EXISTS vacancies (
    vacancy_id TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS candidates (
    vacancy_id TEXT NOT NULL REFERENCES vacancies (vacancy_id),
    candidate_id TEXT NOT NULL,
    cv TEXT NOT NULL,
    evaluation TEXT,
    decision TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (vacancy_id, candidate_id)
);
"""


class Storage:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        # Una conexión por operación: la API atiende peticiones en varios hilos.
        db = sqlite3.connect(self.path)
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def add_vacancy(self, vacancy: Vacancy) -> Vacancy:
        if not vacancy.vacancy_id:
            vacancy = vacancy.model_copy(update={"vacancy_id": f"v-{uuid.uuid4().hex[:8]}"})
        with self._connect() as db:
            db.execute(
                "INSERT INTO vacancies (vacancy_id, data) VALUES (?, ?)",
                (vacancy.vacancy_id, vacancy.model_dump_json()),
            )
        return vacancy

    def list_vacancies(self) -> list[Vacancy]:
        with self._connect() as db:
            rows = db.execute("SELECT data FROM vacancies ORDER BY created_at, rowid").fetchall()
        return [Vacancy.model_validate_json(data) for (data,) in rows]

    def get_vacancy(self, vacancy_id: str) -> Vacancy | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT data FROM vacancies WHERE vacancy_id = ?", (vacancy_id,)
            ).fetchone()
        return Vacancy.model_validate_json(row[0]) if row else None

    def add_candidates(self, vacancy_id: str, cvs: list[CV]) -> None:
        """Agrega CVs a la vacante; un CV idéntico a uno ya cargado no se duplica."""
        with self._connect() as db:
            db.executemany(
                "INSERT OR IGNORE INTO candidates (vacancy_id, candidate_id, cv) VALUES (?, ?, ?)",
                [(vacancy_id, cv.candidate_id, cv.model_dump_json()) for cv in cvs],
            )

    def list_candidates(self, vacancy_id: str) -> list[CV]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT cv FROM candidates WHERE vacancy_id = ? ORDER BY created_at, rowid",
                (vacancy_id,),
            ).fetchall()
        return [CV.model_validate_json(cv) for (cv,) in rows]

    def save_evaluations(self, evaluations: list[Evaluation]) -> None:
        with self._connect() as db:
            db.executemany(
                "UPDATE candidates SET evaluation = ? WHERE vacancy_id = ? AND candidate_id = ?",
                [(e.model_dump_json(), e.vacancy_id, e.candidate_id) for e in evaluations],
            )

    def get_evaluations(self, vacancy_id: str) -> list[Evaluation]:
        """Evaluaciones de la vacante con la decisión del reclutador, del mejor puntaje al peor."""
        with self._connect() as db:
            rows = db.execute(
                "SELECT evaluation, decision FROM candidates "
                "WHERE vacancy_id = ? AND evaluation IS NOT NULL",
                (vacancy_id,),
            ).fetchall()
        evaluations = []
        for data, decision in rows:
            evaluation = Evaluation.model_validate_json(data)
            evaluation.recruiter_decision = FitLabel(decision) if decision else None
            evaluations.append(evaluation)
        return sorted(evaluations, key=lambda e: (-e.score, -e.features.skill_coverage))

    def set_decision(self, vacancy_id: str, candidate_id: str, decision: FitLabel | None) -> bool:
        """Guarda la decisión del reclutador; devuelve False si el candidato no existe."""
        with self._connect() as db:
            cursor = db.execute(
                "UPDATE candidates SET decision = ? WHERE vacancy_id = ? AND candidate_id = ?",
                (decision.value if decision else None, vacancy_id, candidate_id),
            )
        return cursor.rowcount > 0
