import { EDUCATION, years } from "../labels";
import type { Vacancy } from "../types";

interface Props {
  vacancy: Vacancy;
  // Habilidades tomadas de la descripción cuando la vacante no las lista.
  derivedSkills: string[];
}

export function VacancyHeader({ vacancy, derivedSkills }: Props) {
  const skills = vacancy.required_skills.length ? vacancy.required_skills : derivedSkills;
  const extra = [
    vacancy.min_years_experience != null && years(vacancy.min_years_experience),
    vacancy.min_education_level && EDUCATION[vacancy.min_education_level],
  ].filter(Boolean);
  return (
    <header className="vacancy-header">
      <h1>{vacancy.title}</h1>
      {(skills.length > 0 || extra.length > 0) && (
        <p className="requirements">
          <span className="requirements-label">Pide</span>
          {skills.map((s) => (
            <span key={s} className="chip">
              {s}
            </span>
          ))}
          {extra.length > 0 && <span className="requirements-extra">{extra.join(" · ")}</span>}
        </p>
      )}
    </header>
  );
}
