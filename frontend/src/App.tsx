import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "./api";
import { CandidateRow } from "./components/CandidateRow";
import { ModelInfo } from "./components/ModelInfo";
import { Toolbar, type Filters } from "./components/Toolbar";
import { UploadSummary, type Summary } from "./components/UploadSummary";
import { VacancyForm } from "./components/VacancyForm";
import { VacancyHeader } from "./components/VacancyHeader";
import { VacancyList } from "./components/VacancyList";
import type { Evaluation, FitLabel, ModelMetrics, Vacancy, VacancyCreate } from "./types";

const NO_FILTERS: Filters = { skill: "", minYears: "", minScore: "" };

export function App() {
  const [vacancies, setVacancies] = useState<Vacancy[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [ranking, setRanking] = useState<Evaluation[]>([]);
  const [filters, setFilters] = useState<Filters>(NO_FILTERS);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [uploading, setUploading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fail = (e: unknown) => setError(e instanceof ApiError ? e.message : String(e));

  useEffect(() => {
    api
      .listVacancies()
      .then((list) => {
        setVacancies(list);
        setSelectedId(list[0]?.vacancy_id ?? null);
      })
      .catch(fail);
    // Sin métricas la línea del modelo simplemente no aparece.
    api.metrics().then(setMetrics).catch(() => undefined);
  }, []);

  useEffect(() => {
    setRanking([]);
    setSummary(null);
    setFilters(NO_FILTERS);
    if (selectedId) api.ranking(selectedId).then(setRanking).catch(fail);
  }, [selectedId]);

  const vacancy = vacancies?.find((v) => v.vacancy_id === selectedId) ?? null;
  // Las habilidades de la vacante son las encontradas más las faltantes de cualquier candidato.
  const skills = useMemo(() => {
    const first = ranking[0];
    return first ? [...first.matched_skills, ...first.missing_skills].sort() : [];
  }, [ranking]);
  const visible = ranking
    .map((evaluation, index) => ({ evaluation, rank: index + 1 }))
    .filter(({ evaluation: e }) => {
      if (filters.skill && !e.matched_skills.includes(filters.skill)) return false;
      if (filters.minYears && (e.years_experience ?? 0) < Number(filters.minYears)) return false;
      if (filters.minScore && e.score < Number(filters.minScore)) return false;
      return true;
    });

  async function createVacancy(data: VacancyCreate) {
    try {
      const created = await api.createVacancy(data);
      setVacancies((list) => [...(list ?? []), created]);
      setSelectedId(created.vacancy_id);
      setCreating(false);
    } catch (e) {
      fail(e);
    }
  }

  async function upload(files: File[]) {
    if (!selectedId) return;
    setUploading(true);
    setError(null);
    try {
      const result = await api.uploadResumes(selectedId, files);
      setRanking(result.ranking);
      setSummary({ processed: result.processed, errors: result.errors });
    } catch (e) {
      fail(e);
    } finally {
      setUploading(false);
    }
  }

  async function decide(candidateId: string, decision: FitLabel | null) {
    if (!selectedId) return;
    try {
      const updated = await api.setDecision(selectedId, candidateId, decision);
      setRanking((list) => list.map((e) => (e.candidate_id === candidateId ? updated : e)));
    } catch (e) {
      fail(e);
    }
  }

  if (vacancies === null) {
    return (
      <main className="centered">
        {error ? <p className="error" role="alert">{error}</p> : <p>Cargando…</p>}
      </main>
    );
  }

  if (vacancies.length === 0 || creating) {
    return (
      <main className="centered">
        {error && <p className="error" role="alert">{error}</p>}
        <VacancyForm
          heading={vacancies.length === 0 ? "Crea la primera vacante" : "Nueva vacante"}
          onSubmit={createVacancy}
          onCancel={vacancies.length ? () => setCreating(false) : undefined}
        />
      </main>
    );
  }

  return (
    <div className="layout">
      <VacancyList
        vacancies={vacancies}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onNew={() => setCreating(true)}
      />
      <main className="content">
        {error && (
          <p className="error" role="alert">
            {error}{" "}
            <button type="button" className="link" onClick={() => setError(null)}>
              Cerrar
            </button>
          </p>
        )}
        {vacancy && (
          <>
            <VacancyHeader vacancy={vacancy} derivedSkills={skills} />
            <Toolbar
              skills={skills}
              filters={filters}
              onFilters={setFilters}
              uploading={uploading}
              onUpload={upload}
              showFilters={ranking.length > 0}
            />
            {summary && <UploadSummary summary={summary} />}
            {ranking.length === 0 ? (
              <p className="empty">Aún no hay CVs. Carga archivos PDF o DOCX para evaluarlos.</p>
            ) : visible.length === 0 ? (
              <p className="empty">Ningún candidato cumple los filtros.</p>
            ) : (
              <ol className="ranking">
                {visible.map(({ evaluation, rank }) => (
                  <CandidateRow
                    key={evaluation.candidate_id}
                    rank={rank}
                    evaluation={evaluation}
                    vacancy={vacancy}
                    onDecision={(decision) => decide(evaluation.candidate_id, decision)}
                  />
                ))}
              </ol>
            )}
          </>
        )}
        {metrics && <ModelInfo metrics={metrics} />}
      </main>
    </div>
  );
}
