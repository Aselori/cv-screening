import { useState } from "react";
import { api, ApiError } from "../api";
import type { ModelMetrics, RetrainResult } from "../types";

const MODEL_NAMES: Record<string, string> = {
  logistic_regression: "Regresión Logística (en uso)",
  naive_bayes: "Naive Bayes",
  baseline_similarity: "Solo similitud de texto",
  always_no_fit: "Siempre «No apto»",
};
const SPLITS: Record<string, string> = {
  english_test: "Prueba en inglés",
  spanish_same_domain: "Español, mismo dominio",
};

function describe(r: RetrainResult): string {
  const change = `F1 macro ${r.macro_f1_before.toFixed(3)} → ${r.macro_f1_after.toFixed(3)}`;
  return r.accepted
    ? `Modelo actualizado con ${r.feedback_pairs} decisiones (${change}). El ranking se recalculó.`
    : `Se conservó el modelo anterior: con tus ${r.feedback_pairs} decisiones empeoraba (${change}).`;
}

interface Props {
  metrics: ModelMetrics;
  onRetrained: () => void;
}

// Una línea discreta; las métricas y el reentrenamiento quedan en el detalle.
export function ModelInfo({ metrics, onRetrained }: Props) {
  const main = metrics.models.logistic_regression;
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function retrain() {
    setBusy(true);
    setMessage(null);
    try {
      const result = await api.retrain();
      setMessage(describe(result));
      if (result.accepted) onRetrained();
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <footer className="model-info">
      <details>
        <summary>
          Modelo: F1 macro {main.english_test.macro_f1.toFixed(3)} en la prueba en inglés
        </summary>
        <table>
          <thead>
            <tr>
              <th scope="col">Modelo</th>
              {Object.values(SPLITS).map((s) => (
                <th key={s} scope="col">
                  {s}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.entries(metrics.models).map(([name, splits]) => (
              <tr key={name}>
                <th scope="row">{MODEL_NAMES[name] ?? name}</th>
                {Object.keys(SPLITS).map((split) => (
                  <td key={split}>{splits[split]?.macro_f1.toFixed(3) ?? "-"}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <p className="hint">
          F1 macro: promedio del F1 de las tres clases. Detalle en docs/resultados.md.
        </p>
        <div className="retrain">
          <button type="button" className="secondary" disabled={busy} onClick={retrain}>
            {busy ? "Reentrenando…" : "Reentrenar con mis decisiones"}
          </button>
          {message && <p role="status">{message}</p>}
        </div>
      </details>
    </footer>
  );
}
