import type { EducationLevel, FitLabel } from "./types";

// Textos de la interfaz para los valores de la API.
export const FIT_LABEL: Record<FitLabel, string> = {
  "Good Fit": "Apto",
  "Potential Fit": "Posible",
  "No Fit": "No apto",
};

export const FIT_ORDER: FitLabel[] = ["Good Fit", "Potential Fit", "No Fit"];

export const EDUCATION: Record<EducationLevel, string> = {
  high_school: "Preparatoria",
  technical: "Técnico",
  bachelor: "Licenciatura",
  master: "Maestría",
  doctorate: "Doctorado",
};

export const FEATURE: Record<string, string> = {
  text_similarity: "Similitud del texto con la vacante",
  skill_coverage: "Cobertura de habilidades",
  experience_fit: "Ajuste de experiencia",
  education_fit: "Ajuste de educación",
  similarity_rank: "Similitud frente a los demás candidatos",
  coverage_rank: "Cobertura frente a los demás candidatos",
  matched_skills: "Habilidades coincidentes",
};

export function years(value: number): string {
  const rounded = Math.round(value * 10) / 10;
  return `${rounded} ${rounded === 1 ? "año" : "años"}`;
}
