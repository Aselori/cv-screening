import type { FileError } from "../types";

export interface Summary {
  processed: number;
  errors: FileError[];
}

// Lo normal (CVs evaluados) en una línea discreta; los archivos con error se listan.
export function UploadSummary({ summary }: { summary: Summary }) {
  const { processed, errors } = summary;
  return (
    <div className="upload-summary" role="status">
      <p>
        {processed} {processed === 1 ? "CV evaluado" : "CVs evaluados"}
        {errors.length > 0 &&
          ` · ${errors.length} ${errors.length === 1 ? "archivo no se pudo leer" : "archivos no se pudieron leer"}`}
      </p>
      {errors.length > 0 && (
        <ul className="upload-errors">
          {errors.map((e) => (
            <li key={e.file_name}>
              <strong>{e.file_name}</strong>: {e.message.replace(`${e.file_name}: `, "")}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
