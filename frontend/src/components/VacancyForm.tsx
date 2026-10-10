import { useState, type FormEvent } from "react";
import { EDUCATION } from "../labels";
import type { EducationLevel, VacancyCreate } from "../types";

interface Props {
  heading: string;
  onSubmit: (data: VacancyCreate) => Promise<void>;
  onCancel?: () => void;
}

const list = (text: string) =>
  text
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

export function VacancyForm({ heading, onSubmit, onCancel }: Props) {
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const years = String(form.get("years") ?? "");
    setSaving(true);
    try {
      await onSubmit({
        title: String(form.get("title")),
        description: String(form.get("description")),
        required_skills: list(String(form.get("required") ?? "")),
        preferred_skills: list(String(form.get("preferred") ?? "")),
        min_years_experience: years === "" ? null : Number(years),
        min_education_level: (form.get("education") || null) as EducationLevel | null,
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="vacancy-form" onSubmit={submit}>
      <h2>{heading}</h2>
      <label>
        Puesto
        <input name="title" required placeholder="Analista de datos" />
      </label>
      <label>
        Descripción
        <textarea name="description" required rows={5} placeholder="Responsabilidades y requisitos" />
      </label>
      <label>
        Habilidades requeridas <small>separadas por comas</small>
        <input name="required" placeholder="SQL, Excel, Power BI" />
      </label>
      <label>
        Habilidades deseables <small>separadas por comas</small>
        <input name="preferred" placeholder="Tableau" />
      </label>
      <div className="form-row">
        <label>
          Años mínimos
          <input name="years" type="number" min={0} step={0.5} />
        </label>
        <label>
          Nivel educativo mínimo
          <select name="education" defaultValue="">
            <option value="">Sin requisito</option>
            {Object.entries(EDUCATION).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="hint">Lo que no llenes se toma de la descripción.</p>
      <div className="form-actions">
        <button type="submit" disabled={saving}>
          {saving ? "Guardando…" : "Crear vacante"}
        </button>
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}
