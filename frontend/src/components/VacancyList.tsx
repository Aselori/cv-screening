import type { Vacancy } from "../types";

interface Props {
  vacancies: Vacancy[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}

// Lista lateral en pantallas grandes; en el teléfono, un selector arriba (ver styles.css).
export function VacancyList({ vacancies, selectedId, onSelect, onNew }: Props) {
  return (
    <nav className="vacancies" aria-label="Vacantes">
      <h2>Vacantes</h2>
      <ul className="vacancy-links">
        {vacancies.map((v) => (
          <li key={v.vacancy_id}>
            <button
              type="button"
              aria-current={v.vacancy_id === selectedId ? "page" : undefined}
              onClick={() => onSelect(v.vacancy_id)}
            >
              {v.title}
            </button>
          </li>
        ))}
      </ul>
      <label className="vacancy-select">
        <span className="visually-hidden">Vacante</span>
        <select value={selectedId ?? ""} onChange={(e) => onSelect(e.target.value)}>
          {vacancies.map((v) => (
            <option key={v.vacancy_id} value={v.vacancy_id}>
              {v.title}
            </option>
          ))}
        </select>
      </label>
      <button type="button" className="secondary" onClick={onNew}>
        + Nueva vacante
      </button>
    </nav>
  );
}
