import type { ModelMetrics } from "../types";

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

// Una línea discreta; las métricas completas quedan en el detalle.
export function ModelInfo({ metrics }: { metrics: ModelMetrics }) {
  const main = metrics.models.logistic_regression;
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
      </details>
    </footer>
  );
}
