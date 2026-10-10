// Contratos de la API (src/cv_screening/schemas.py y api.py).

export type FitLabel = "Good Fit" | "Potential Fit" | "No Fit";
export type EducationLevel = "high_school" | "technical" | "bachelor" | "master" | "doctorate";

export interface Vacancy {
  vacancy_id: string;
  title: string;
  description: string;
  language: "es" | "en" | null;
  required_skills: string[];
  preferred_skills: string[];
  min_years_experience: number | null;
  min_education_level: EducationLevel | null;
}

export type VacancyCreate = Omit<Vacancy, "vacancy_id" | "language">;

export interface Features {
  text_similarity: number;
  skill_coverage: number;
  experience_fit: number;
  education_fit: number;
  similarity_rank: number | null;
  coverage_rank: number | null;
  matched_skills: number | null;
}

export interface Evaluation {
  candidate_id: string;
  vacancy_id: string;
  file_name: string | null;
  score: number;
  predicted_class: FitLabel;
  probabilities: Record<FitLabel, number>;
  features: Features;
  matched_skills: string[];
  missing_skills: string[];
  years_experience: number | null;
  education_level: EducationLevel | null;
  recruiter_decision: FitLabel | null;
}

export interface FileError {
  file_name: string;
  error: string;
  message: string;
}

export interface UploadResult {
  processed: number;
  errors: FileError[];
  ranking: Evaluation[];
}

interface SplitMetrics {
  macro_f1: number;
  accuracy: number;
}

export interface ModelMetrics {
  models: Record<string, Record<string, SplitMetrics>>;
  trained_at: string;
}
