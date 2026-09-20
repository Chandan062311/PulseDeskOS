import { useState } from "react";
import { ApiError, SAMPLES, postTriage, type TicketInput, type TriageResult } from "../api";
import { Chip, EmptyState, ErrorBanner, LoadingRow, Meter, Section, actionTone } from "./ui";

export type ReviewItem = { sample: TicketInput & { id: string }; triage: TriageResult };

const BARS = [
  { key: "route_confidence", label: "Route confidence" },
  { key: "spam_risk", label: "Spam risk" },
  { key: "urgency", label: "Urgency" },
  { key: "frustration", label: "Frustration" },
  { key: "needs_memory", label: "Needs memory" },
  { key: "refund_requested", label: "Refund requested" },
  { key: "pii_detected", label: "PII detected" },
] as const;

export default function TriagePanel({
  ticket,
  setTicket,
  onReviewed,
}: {
  ticket: TicketInput;
  setTicket: (t: TicketInput) => void;
  onReviewed: (item: ReviewItem) => void;
}) {
  const [triage, setTriage] = useState<TriageResult | null>(null);
  const [mode, setMode] = useState<string>("idle");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(live: boolean) {
    setLoading(true);
    setError(null);
    try {
      const t = await postTriage(ticket, live);
      setTriage(t);
      setMode(live ? "live Jev" : "offline mock");
      if (t.action !== "auto_route") onReviewed({ sample: { ...ticket, id: "custom" }, triage: t });
    } catch (e) {
      if (live && e instanceof ApiError && e.status === 503) {
        // Live needs a key: degrade to the offline mock instead of failing.
        try {
          const t = await postTriage(ticket, false);
          setTriage(t);
          setMode("offline mock (live unavailable: key missing)");
          return;
        } catch {
          /* fall through to the error banner */
        }
      }
      setError(e instanceof Error ? e.message : "unknown error");
    } finally {
      setLoading(false);
    }
  }

  const valid = ticket.message.trim().length > 0 && ticket.sender.trim().length > 0;

  return (
    <div className="grid">
      <Section title="Compose ticket" hint="Required: message + sender. Subject optional.">
        <label htmlFor="subject">Subject</label>
        <input id="subject" value={ticket.subject} onChange={(e) => setTicket({ ...ticket, subject: e.target.value })} />
        <label htmlFor="message">Message</label>
        <textarea id="message" rows={4} value={ticket.message} onChange={(e) => setTicket({ ...ticket, message: e.target.value })} />
        <label htmlFor="sender">Sender email</label>
        <input id="sender" value={ticket.sender} onChange={(e) => setTicket({ ...ticket, sender: e.target.value })} />
        <div className="grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <div>
            <label htmlFor="plan">Customer plan</label>
            <input id="plan" value={ticket.plan} onChange={(e) => setTicket({ ...ticket, plan: e.target.value })} />
          </div>
          <div>
            <label htmlFor="orders">Open orders (comma-separated)</label>
            <input
              id="orders"
              value={ticket.openOrders}
              onChange={(e) => setTicket({ ...ticket, openOrders: e.target.value })}
              placeholder="A-104, INV-2041"
            />
          </div>
        </div>
        <div className="row actions">
          <button disabled={!valid || loading} onClick={() => void run(true)}>
            Triage live (Jev)
          </button>
          <button className="ghost" disabled={!valid || loading} onClick={() => void run(false)}>
            Triage offline
          </button>
          <span className="muted">mode: {mode}</span>
        </div>
        {!valid && <p className="muted">Enter a message and sender to enable triage.</p>}
        <h3>Samples</h3>
        <table>
          <thead>
            <tr>
              <th scope="col">ID</th>
              <th scope="col">Subject</th>
              <th scope="col">
                <span className="sr-only">Load</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {SAMPLES.map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td>
                <td>{s.subject}</td>
                <td>
                  <button className="ghost" onClick={() => setTicket({ subject: s.subject, message: s.message, sender: s.sender, plan: "enterprise", openOrders: "" })}>
                    Load
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Jev result" hint="Gates: quarantine ≥ 0.60 · review if spam 0.40–0.60 or confidence < 0.75.">
        {loading && <LoadingRow label="Asking Jev…" />}
        {error && <ErrorBanner message={error} onRetry={() => void run(true)} />}
        {!loading && !error && !triage && (
          <EmptyState title="No triage yet" body="Compose a ticket and run live triage to see route probabilities and gates." />
        )}
        {triage && !loading && !error && (
          <div aria-live="polite">
            <div className="row">
              <strong>{triage.route}</strong>
              <Chip tone={actionTone(triage.action)}>{triage.action}</Chip>
            </div>
            {BARS.map(({ key, label }) => (
              <Meter key={key} label={label} value={triage[key]} />
            ))}
            <p className="muted">{triage.reason}</p>
          </div>
        )}
      </Section>
    </div>
  );
}
