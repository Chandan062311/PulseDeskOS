import { useState, useEffect } from "react";
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
  initialTriage = null,
}: {
  ticket: TicketInput;
  setTicket: (t: TicketInput) => void;
  onReviewed: (item: ReviewItem) => void;
  initialTriage?: TriageResult | null;
}) {
  const [triage, setTriage] = useState<TriageResult | null>(initialTriage);
  const [mode, setMode] = useState<string>(initialTriage ? "inspected ticket" : "idle");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialTriage) {
      setTriage(initialTriage);
      setMode("inspected ticket");
    }
  }, [initialTriage]);

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
  const isOfflineMock = mode.toLowerCase().includes("offline mock");

  return (
    <div className="grid">
      <Section title="Compose ticket" hint="Required: message + sender. Subject optional.">
        <label htmlFor="subject">Subject</label>
        <input
          id="subject"
          placeholder="e.g. Cannot connect to VPN"
          value={ticket.subject}
          onChange={(e) => setTicket({ ...ticket, subject: e.target.value })}
        />
        <label htmlFor="message">Message</label>
        <textarea
          id="message"
          rows={4}
          placeholder="Enter ticket body text..."
          value={ticket.message}
          onChange={(e) => setTicket({ ...ticket, message: e.target.value })}
        />
        <label htmlFor="sender">Sender email</label>
        <input
          id="sender"
          placeholder="e.g. user@example.com"
          value={ticket.sender}
          onChange={(e) => setTicket({ ...ticket, sender: e.target.value })}
        />
        <div className="grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <div>
            <label htmlFor="plan">Customer plan</label>
            <input
              id="plan"
              placeholder="enterprise / growth / free"
              value={ticket.plan}
              onChange={(e) => setTicket({ ...ticket, plan: e.target.value })}
            />
          </div>
          <div>
            <label htmlFor="orders">Open orders (comma-separated)</label>
            <input
              id="orders"
              value={ticket.openOrders}
              onChange={(e) => setTicket({ ...ticket, openOrders: e.target.value })}
              placeholder="e.g. A-104, INV-2041"
            />
          </div>
        </div>
        <div className="row actions" style={{ marginTop: "12px" }}>
          <button disabled={!valid || loading} onClick={() => void run(true)}>
            Triage live (Jev)
          </button>
          <button className="ghost" disabled={!valid || loading} onClick={() => void run(false)}>
            Triage offline
          </button>
          <span className="muted">mode: {mode}</span>
        </div>
        {!valid && <p className="muted small" style={{ marginTop: "6px" }}>Enter a message and sender to enable triage.</p>}

        {/* Optional quick scenario loader */}
        <div style={{ marginTop: "16px", paddingTop: "10px", borderTop: "1px solid var(--line)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span className="small muted">Load test scenario:</span>
          <select
            aria-label="Load test scenario"
            style={{ width: "auto", fontSize: "11px", padding: "3px 8px" }}
            value=""
            onChange={(e) => {
              const s = SAMPLES.find((item) => item.id === e.target.value);
              if (s) {
                setTicket({
                  subject: s.subject,
                  message: s.message,
                  sender: s.sender,
                  plan: "enterprise",
                  openOrders: s.id === "dup-charge" ? "A-104" : "",
                });
              }
            }}
          >
            <option value="" disabled>Select a scenario…</option>
            {SAMPLES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.subject} ({s.id})
              </option>
            ))}
          </select>
        </div>
      </Section>

      <Section title="Jev result" hint="Gates: quarantine ≥ 0.60 · review if spam 0.40–0.60 or confidence < 0.75.">
        {loading && <LoadingRow label="Asking Jev…" />}
        {error && <ErrorBanner message={error} onRetry={() => void run(true)} />}
        {!loading && !error && !triage && (
          <EmptyState title="No triage yet" body="Compose a ticket and run live triage to see route probabilities and gates." />
        )}
        {triage && !loading && !error && (
          <div aria-live="polite">
            <div className="row" style={{ marginBottom: "12px", alignItems: "center" }}>
              <strong style={{ fontSize: "1.1rem", color: "var(--ink)" }}>{triage.route}</strong>
              <Chip tone={actionTone(triage.action)}>{triage.action}</Chip>
              {isOfflineMock && (
                <span className="chip chip-warn" title="Result produced by offline mock heuristic">
                  offline mock
                </span>
              )}
            </div>
            {BARS.map(({ key, label }) => (
              <Meter key={key} label={label} value={triage[key]} />
            ))}
            <div style={{ marginTop: "14px", padding: "10px 12px", background: "var(--primary-subtle)", border: "1px solid var(--primary-border)", borderRadius: "var(--radius)" }}>
              <div style={{ fontWeight: 600, fontSize: "11px", color: "var(--primary)", marginBottom: "2px" }}>Triage Reason:</div>
              <p style={{ margin: 0, fontSize: "12px", color: "var(--ink-secondary)" }}>{triage.reason}</p>
            </div>
          </div>
        )}
      </Section>
    </div>
  );
}
