import type { Evaluation, FitLabel, ModelMetrics, UploadResult, Vacancy, VacancyCreate } from "./types";

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, init);
  } catch {
    throw new ApiError("No se pudo conectar con el servidor. ¿Está corriendo la API?");
  }
  if (!response.ok) {
    // FastAPI devuelve {"detail": "..."} o, en errores de validación, una lista.
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : `Error ${response.status}`;
    throw new ApiError(detail);
  }
  return response.json() as Promise<T>;
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  listVacancies: () => request<Vacancy[]>("/vacancies"),
  createVacancy: (data: VacancyCreate) => request<Vacancy>("/vacancies", json("POST", data)),
  ranking: (vacancyId: string) => request<Evaluation[]>(`/vacancies/${vacancyId}/ranking`),
  uploadResumes: (vacancyId: string, files: File[]) => {
    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    return request<UploadResult>(`/vacancies/${vacancyId}/resumes`, { method: "POST", body: form });
  },
  setDecision: (vacancyId: string, candidateId: string, decision: FitLabel | null) =>
    request<Evaluation>(
      `/vacancies/${vacancyId}/candidates/${candidateId}/decision`,
      json("PUT", { decision }),
    ),
  metrics: () => request<ModelMetrics>("/model/metrics"),
};
