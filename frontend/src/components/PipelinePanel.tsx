import { useState } from "react";
import { postOrchestrate, type OrchestrateResult, type TicketInput } from "../api";
import { Chip, EmptyState, ErrorBanner, LoadingRow, Section } from "./ui";

const STAGES = ["triage", "recall", "dispatch", "verify"] as const;

export default function PipelinePanel({ ticket }: { ticket: TicketInput }) {
  const [orch, setOrch] = useState<OrchestrateResult | null>(null);
  const [status, setStatus] = useState("idle");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const result = await postOrchestrate(ticket);
      setOrch(result);
      setStatus("live pipeline");
    } catch (e) {
      setError(e instanceof Error ? e.message : "unknown error");
      setStatus("failed");
    } finally {
      setLoading(false);
    }
  }

  const capturedId = orch?.captured_id || orch?.captured_memory_id;

  return (
    <div className="stack">
      <Section title="Full pipeline" hint="POST /v1/orchestrate: triage → conditional recall → dispatch → verify. Live Jev only.">
        <div className="row actions">
          <button disabled={loading || ticket.message.trim().length === 0} onClick={() => void run()}>
            Run orchestration
          </button>
          <span className="muted">status: {status}</span>
        </div>
        {loading && <LoadingRow label="Running triage → recall → dispatch → verify…" />}
        {error && <ErrorBanner message={error} onRetry={() => void run()} />}
        {!loading && !error && !orch && (
          <EmptyState title="Pipeline not run" body="Runs against the ticket composed in the Triage tab." />
        )}
      </Section>

      {orch && !loading && !error && (
        <>
          <Section title="Stage trace" hint="Each stage's Jev output feeds the next — code owns the handoffs.">
            <ol className="stages">
              <li>
                <strong>1 · Triage</strong>
                <span>
                  {orch.triage.route} <Chip tone={orch.triage.action === "auto_route" ? "ok" : orch.triage.action === "quarantine_spam" ? "bad" : "warn"}>{orch.triage.action}</Chip>
                </span>
                <span className="muted">
                  conf {orch.triage.route_confidence.toFixed(2)} · spam {orch.triage.spam_risk.toFixed(2)} · needs_memory {orch.triage.needs_memory.toFixed(2)}
                </span>
              </li>
              <li>
                <strong>2 · Recall</strong>
                <span>{orch.memory_hits.length} hit{orch.memory_hits.length === 1 ? "" : "s"}</span>
                <span className="muted">
                  {orch.memory_hits.length > 0 ? "needs_memory met threshold (0.60)" : "skipped — needs_memory below threshold"}
                </span>
              </li>
              <li>
                <strong>3 · Dispatch</strong>
                <span>handler: {orch.handler.handler}</span>
                <span className="muted">{orch.handler.summary}</span>
              </li>
              <li>
                <strong>4 · Verify</strong>
                <span>
                  <Chip tone={orch.verify.verdict === "supported" ? "ok" : orch.verify.verdict === "unsupported" ? "bad" : "warn"}>
                    {orch.verify.verdict} ({orch.verify.confidence.toFixed(2)})
                  </Chip>
                </span>
              </li>
            </ol>
            <p className="muted sr-note">Stages: {STAGES.join(" → ")}</p>

            {capturedId && (
              <div style={{ marginTop: "14px", padding: "10px 12px", background: "var(--primary-subtle)", border: "1px solid var(--primary-border)", borderRadius: "var(--radius)" }}>
                <strong style={{ color: "var(--primary)" }}>Captured Memory ID:</strong> <code style={{ marginLeft: "6px" }}>{capturedId}</code>
              </div>
            )}
          </Section>

          <div className="grid">
            <Section title="Draft reply" hint="Deterministic template — every claim traces to handler output or cited evidence.">
              <pre className="draft">{orch.draft_reply}</pre>
            </Section>
            <Section title={`Memory hits (${orch.memory_hits.length})`}>
              {orch.memory_hits.length === 0 ? (
                <EmptyState title="No evidence" body="needs_memory was below threshold, or the tenant store is empty." />
              ) : (
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th scope="col" style={{ width: "95px" }}>ID / Type</th>
                        <th scope="col">Evidence Text</th>
                        <th scope="col" style={{ width: "50px" }}>Rel</th>
                        <th scope="col" style={{ width: "110px" }}>Safety Flags</th>
                      </tr>
                    </thead>
                    <tbody>
                      {orch.memory_hits.map((h) => (
                        <tr key={h.id}>
                          <td>
                            <div style={{ marginBottom: "2px" }}><code>{h.id.slice(0, 8)}</code></div>
                            <Chip tone="info">{h.type || "doc"}</Chip>
                          </td>
                          <td style={{ fontSize: "12px", maxWidth: "260px" }}>{h.text}</td>
                          <td><strong className="mono">{h.relevance.toFixed(2)}</strong></td>
                          <td className="small" style={{ fontSize: "11px", color: "var(--muted)" }}>
                            <div>contra: {h.contradicts.toFixed(2)}</div>
                            <div>inj: {h.has_injection.toFixed(2)}</div>
                            <div>pii: {h.has_pii.toFixed(2)}</div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Section>
          </div>
        </>
      )}
    </div>
  );
}
