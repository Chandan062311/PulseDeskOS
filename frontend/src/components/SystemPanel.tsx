import { useEffect, useState } from "react";
import { API_BASE, getStatus } from "../api";
import { Section } from "./ui";

const ENDPOINTS: Array<[string, string]> = [
  ["GET /healthz", "Liveness probe (open)"],
  ["GET /v1/status", "Setup status: Jev live or offline"],
  ["POST /v1/triage?live=true", "9-question Jev triage + gates"],
  ["POST /v1/ingest", "Triage + registry dispatch"],
  ["POST /v1/orchestrate", "Full pipeline: triage → recall → dispatch → verify"],
  ["POST /v1/memory/store · /seed · /recall", "Tenant memory lifecycle"],
  ["GET /v1/memory/list · /count", "Browse tenant memories"],
  ["POST /v1/verify", "Draft-vs-evidence verdict"],
];

export default function SystemPanel({ health }: { health: string }) {
  const [jev, setJev] = useState("checking…");

  useEffect(() => {
    getStatus()
      .then((s) => setJev(s.jev))
      .catch(() => setJev("unreachable"));
  }, []);

  return (
    <div className="grid">
      <Section title="Backend" hint={`Base: ${API_BASE}. One key only: TYPESAFE_API_KEY in the server's .env.`}>
        <dl className="kv">
          <dt>Status</dt>
          <dd>
            <span className={`dot ${health === "ok" ? "" : "down"}`} aria-hidden="true" /> {health}
          </dd>
          <dt>Live Jev</dt>
          <dd>
            <span className={`dot ${jev === "live" ? "" : "down"}`} aria-hidden="true" /> {jev}
            {jev === "offline" && (
              <span className="muted">
                {" "}— put your key in <code>.env</code> as
                <code>TYPESAFE_API_KEY=…</code> (from console.typesafe.ai/keys)
                and restart the API. Triage still works offline (mock mode).
              </span>
            )}
          </dd>
          <dt>Thresholds</dt>
          <dd>quarantine ≥ 0.60 · review band 0.40–0.60 (exclusive) · topic conf &lt; 0.75 · other always reviews</dd>
        </dl>
      </Section>
      <Section title="API reference" hint="Frozen Pydantic contracts in backend/schemas.py.">
        <table>
          <thead>
            <tr>
              <th scope="col">Endpoint</th>
              <th scope="col">Purpose</th>
            </tr>
          </thead>
          <tbody>
            {ENDPOINTS.map(([ep, desc]) => (
              <tr key={ep}>
                <td>
                  <code>{ep}</code>
                </td>
                <td>{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted">
          Full docs: <code>/docs</code> on the backend. Source: <code>backend/</code> in this repository.
        </p>
      </Section>
    </div>
  );
}
