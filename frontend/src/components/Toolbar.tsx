import { useRef } from "react";

export interface Filters {
  skill: string;
  minYears: string;
  minScore: string;
}

interface Props {
  skills: string[];
  filters: Filters;
  onFilters: (filters: Filters) => void;
  uploading: boolean;
  onUpload: (files: File[]) => void;
  showFilters: boolean;
}

export function Toolbar({ skills, filters, onFilters, uploading, onUpload, showFilters }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const set = (key: keyof Filters) => (value: string) => onFilters({ ...filters, [key]: value });
  return (
    <div className="toolbar">
      <button type="button" disabled={uploading} onClick={() => input.current?.click()}>
        {uploading ? "Evaluando…" : "Cargar CVs"}
      </button>
      <input
        ref={input}
        type="file"
        multiple
        accept=".pdf,.docx"
        hidden
        onChange={(e) => {
          const files = Array.from(e.target.files ?? []);
          e.target.value = "";
          if (files.length) onUpload(files);
        }}
      />
      {showFilters && (
        <div className="filters" role="group" aria-label="Filtros">
          <label>
            Habilidad
            <select value={filters.skill} onChange={(e) => set("skill")(e.target.value)}>
              <option value="">Todas</option>
              {skills.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Años ≥
            <input
              type="number"
              min={0}
              step={0.5}
              value={filters.minYears}
              onChange={(e) => set("minYears")(e.target.value)}
            />
          </label>
          <label>
            Puntaje ≥
            <input
              type="number"
              min={0}
              max={100}
              step={5}
              value={filters.minScore}
              onChange={(e) => set("minScore")(e.target.value)}
            />
          </label>
        </div>
      )}
    </div>
  );
}
