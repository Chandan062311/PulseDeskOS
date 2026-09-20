import { API_BASE } from "../api";
import { Section } from "./ui";

const ENDPOINTS: Array<[string, string]> = [
  ["GET /healthz", "Liveness probe"],
  ["POST /v1/triage?live=true", "8-question Jev triage + gates"],
  ["POST /v1/ingest", "Triage + registry dispatch"],
  ["POST /v1/orchestrate", "Full pipeline: triage → recall → dispatch → verify"],
  ["POST /v1/memory/store · /seed · /recall", "Tenant memory lifecycle"],
  ["POST /v1/verify", "Draft-vs-evidence verdict"],
];

export default function SystemPanel({ health }: { health: string }) {
  return (
    <div className="grid">
      <Section title="Backend" hint={`Base: ${API_BASE}. Key + DB come from the server environment.`}>
        <dl className="kv">
          <dt>Status</dt>
          <dd>
            <span className={`dot ${health === "ok" ? "" : "down"}`} aria-hidden="true" /> {health}
          </dd>
          <dt>Live Jev</dt>
          <dd>{health === "ok" ? "available when TYPESAFE_API_KEY is set server-side" : "backend unreachable"}</dd>
          <dt>Thresholds</dt>
          <dd>quarantine ≥ 0.60 · review band 0.40–0.60 · topic conf &lt; 0.75 · destructive &lt; 0.90</dd>
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
          Full docs: <code>/docs</code> on the backend. Open-source repo: <code>pulsedesk-os/</code>.
        </p>
      </Section>
    </div>
  );
}
