import type { FormEvent } from "react";
import { useState } from "react";

import "./styles.css";

type Insurer = "aetna" | "cigna" | "unitedhealthcare" | "cms";

type MentalHealthBenefit = {
  service_type_code: "MH";
  status: "active" | "inactive" | "member_not_found" | "unknown";
  copay: string | null;
  coinsurance: string | null;
  deductible: string | null;
  in_network: boolean | null;
  payer_name: string | null;
  carve_out: boolean;
};

type EligibilityResult = {
  covered: boolean;
  copay: string | null;
  coinsurance: string | null;
  deductible: string | null;
  in_network: boolean | null;
  mental_health: MentalHealthBenefit;
};

type ApiError = {
  code: string;
  message: string;
};

type FormState = {
  memberId: string;
  dateOfBirth: string;
  insurer: Insurer;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const insurerOptions: Array<{ value: Insurer; label: string }> = [
  { value: "aetna", label: "Aetna" },
  { value: "cigna", label: "Cigna" },
  { value: "unitedhealthcare", label: "UnitedHealthcare" },
  { value: "cms", label: "CMS" },
];

function formatCurrency(value: string | null): string {
  if (value === null) {
    return "Not shown";
  }
  return `$${Number(value).toFixed(2)}`;
}

function formatPercent(value: string | null): string {
  if (value === null) {
    return "Not shown";
  }
  return `${Number(value) * 100}%`;
}

function formatNetwork(value: boolean | null): string {
  if (value === null) {
    return "Network status not shown";
  }
  return value ? "In network" : "Out of network";
}

function plainAnswer(result: EligibilityResult): string {
  if (!result.covered) {
    return "Not covered";
  }

  const copay = result.copay
    ? `${formatCurrency(result.copay)} per session`
    : "cost details pending";
  const network =
    result.in_network === true
      ? "in-network"
      : formatNetwork(result.in_network).toLowerCase();
  return `Covered - ${copay}, ${network}`;
}

function App() {
  const [form, setForm] = useState<FormState>({
    memberId: "",
    dateOfBirth: "",
    insurer: "unitedhealthcare",
  });
  const [result, setResult] = useState<EligibilityResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setResult(null);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/eligibility`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          member_id: form.memberId.trim(),
          date_of_birth: form.dateOfBirth,
          insurer: form.insurer,
        }),
      });
      const body = (await response.json()) as EligibilityResult | ApiError;

      if (!response.ok) {
        setError(
          "message" in body
            ? body.message
            : "The eligibility check could not be completed.",
        );
        return;
      }

      setResult(body as EligibilityResult);
    } catch {
      setError("The eligibility check could not be completed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace" aria-labelledby="page-title">
        <div className="page-heading">
          <p className="eyebrow">Eligibility checker</p>
          <h1 id="page-title">Mental health coverage lookup</h1>
        </div>

        <div className="layout-grid">
          <form className="lookup-form" onSubmit={handleSubmit}>
            <label>
              <span>Member ID</span>
              <input
                autoComplete="off"
                name="memberId"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    memberId: event.target.value,
                  }))
                }
                required
                value={form.memberId}
              />
            </label>

            <label>
              <span>Date of birth</span>
              <input
                name="dateOfBirth"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    dateOfBirth: event.target.value,
                  }))
                }
                required
                type="date"
                value={form.dateOfBirth}
              />
            </label>

            <label>
              <span>Insurer</span>
              <select
                name="insurer"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    insurer: event.target.value as Insurer,
                  }))
                }
                value={form.insurer}
              >
                {insurerOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <button disabled={isSubmitting} type="submit">
              {isSubmitting ? "Checking" : "Check coverage"}
            </button>
          </form>

          <section className="result-surface" aria-live="polite">
            {!result && !error ? (
              <div className="empty-state">
                <p className="surface-label">Result</p>
                <p>No coverage result yet.</p>
              </div>
            ) : null}

            {error ? (
              <div className="error-state">
                <p className="surface-label">Result</p>
                <h2>Could not verify coverage</h2>
                <p>{error}</p>
              </div>
            ) : null}

            {result ? (
              <div className="coverage-result">
                <p className="surface-label">Result</p>
                <h2>{plainAnswer(result)}</h2>
                <dl>
                  <div>
                    <dt>Copay</dt>
                    <dd>{formatCurrency(result.copay)}</dd>
                  </div>
                  <div>
                    <dt>Coinsurance</dt>
                    <dd>{formatPercent(result.coinsurance)}</dd>
                  </div>
                  <div>
                    <dt>Deductible</dt>
                    <dd>{formatCurrency(result.deductible)}</dd>
                  </div>
                  <div>
                    <dt>Network</dt>
                    <dd>{formatNetwork(result.in_network)}</dd>
                  </div>
                  <div>
                    <dt>Benefit</dt>
                    <dd>Mental health</dd>
                  </div>
                  <div>
                    <dt>Payer</dt>
                    <dd>{result.mental_health.payer_name ?? "Not shown"}</dd>
                  </div>
                </dl>
                {result.mental_health.carve_out ? (
                  <p className="notice">
                    Mental health benefits are handled by a separate payer.
                  </p>
                ) : null}
              </div>
            ) : null}
          </section>
        </div>
      </section>
    </main>
  );
}

export default App;
