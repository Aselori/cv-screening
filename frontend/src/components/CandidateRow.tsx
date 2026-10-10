import { EDUCATION, FEATURE, FIT_LABEL, FIT_ORDER, years } from "../labels";
import type { Evaluation, FitLabel, Vacancy } from "../types";

interface Props {
  rank: number;
  evaluation: Evaluation;
  vacancy: Vacancy;
  onDecision: (decision: FitLabel | null) => void;
}

const percent = (value: number) => `${Math.round(value * 100)} %`;

// Solo lo que necesita atención: habilidades faltantes y requisitos no cumplidos.
function exceptions(e: Evaluation, vacancy: Vacancy): string[] {
  const notes = [];
  if (e.missing_skills.length) notes.push(`Le falta: ${e.missing_skills.join(", ")}`);
  if (e.features.experience_fit < 1) {
    const asked = vacancy.min_years_experience;
    const found = e.years_experience == null ? "Sin experiencia detectada" : years(e.years_experience);
    notes.push(asked ? `${found} (pide ${years(asked)})` : `${found}, menos de lo pedido`);
  }
  if (e.features.education_fit < 1) {
    const asked = vacancy.min_education_level;
    const found = e.education_level ? EDUCATION[e.education_level] : "Sin estudios detectados";
    notes.push(asked ? `${found} (pide ${EDUCATION[asked]})` : `${found}, menos de lo pedido`);
  }
  return notes;
}

export function CandidateRow({ rank, evaluation: e, vacancy, onDecision }: Props) {
  const notes = exceptions(e, vacancy);
  return (
    <li className="candidate">
      <span className="rank">{rank}</span>
      <div className="candidate-main">
        <div className="score-line">
          <div className="score-bar" aria-hidden="true">
            <span style={{ width: `${e.score}%` }} />
          </div>
          <span className="score">{e.score.toFixed(1)}</span>
          <span className={`fit fit-${e.predicted_class.split(" ")[0].toLowerCase()}`}>
            {FIT_LABEL[e.predicted_class]}
          </span>
          <span className="file">{e.file_name}</span>
        </div>
        {notes.length > 0 && <p className="exceptions">{notes.join(" · ")}</p>}
        <details>
          <summary>Detalle</summary>
          <dl>
            <dt>Habilidades que cumple</dt>
            <dd>{e.matched_skills.length ? e.matched_skills.join(", ") : "Ninguna de las requeridas"}</dd>
            <dt>Experiencia</dt>
            <dd>{e.years_experience == null ? "No detectada" : years(e.years_experience)}</dd>
            <dt>Educación</dt>
            <dd>{e.education_level ? EDUCATION[e.education_level] : "No detectada"}</dd>
            <dt>Probabilidades</dt>
            <dd>{FIT_ORDER.map((c) => `${FIT_LABEL[c]} ${percent(e.probabilities[c])}`).join(" · ")}</dd>
          </dl>
          <table className="features">
            <tbody>
              {Object.entries(e.features).map(([name, value]) =>
                value == null ? null : (
                  <tr key={name}>
                    <th scope="row">{FEATURE[name] ?? name}</th>
                    <td>{percent(value)}</td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
          <p className="hint">
            El puntaje combina las tres probabilidades (Apto + la mitad de Posible); la etiqueta es
            la clase más probable. Por eso un candidato «Posible» puede quedar arriba de uno «Apto».
          </p>
        </details>
      </div>
      <div className="decision" role="group" aria-label={`Decisión sobre ${e.file_name}`}>
        {FIT_ORDER.map((label) => {
          const pressed = e.recruiter_decision === label;
          return (
            <button
              key={label}
              type="button"
              aria-pressed={pressed}
              onClick={() => onDecision(pressed ? null : label)}
            >
              {FIT_LABEL[label]}
            </button>
          );
        })}
      </div>
    </li>
  );
}
