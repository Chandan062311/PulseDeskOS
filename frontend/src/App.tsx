import { useEffect, useState } from "react";
import { API_BASE, SAMPLES, getHealth, type TicketInput } from "./api";
import PipelinePanel from "./components/PipelinePanel";
import ReviewQueue from "./components/ReviewQueue";
import SystemPanel from "./components/SystemPanel";
import TriagePanel, { type ReviewItem } from "./components/TriagePanel";

const TABS = [
  { id: "triage", label: "Triage" },
  { id: "pipeline", label: "Pipeline" },
  { id: "review", label: "Review" },
  { id: "system", label: "System" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function App() {
  const [tab, setTab] = useState<TabId>("triage");
  const [health, setHealth] = useState("checking…");
  const [ticket, setTicket] = useState<TicketInput>({
    subject: SAMPLES[0].subject,
    message: SAMPLES[0].message,
    sender: SAMPLES[0].sender,
    plan: "enterprise",
    openOrders: "A-104",
  });
  const [queue, setQueue] = useState<ReviewItem[]>([]);

  useEffect(() => {
    getHealth()
      .then(() => setHealth("ok"))
      .catch(() => setHealth("unreachable"));
  }, []);

  return (
    <div className="shell">
      <a className="skip" href="#content">
        Skip to content
      </a>
      <aside className="side" aria-label="Primary">
        <div className="brand">
          <span className="mark" aria-hidden="true">
            P
          </span>
          <div>
            <strong>PulseDesk OS</strong>
            <div className="muted small">ops console · v0.1</div>
          </div>
        </div>
        <nav aria-label="Sections">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={tab === t.id ? "nav active" : "nav"}
              aria-current={tab === t.id ? "page" : undefined}
              onClick={() => setTab(t.id)}
            >
              {t.label}
              {t.id === "review" && queue.length > 0 && <span className="badge">{queue.length}</span>}
            </button>
          ))}
        </nav>
        <div className="side-foot muted small">
          <span className={`dot ${health === "ok" ? "" : "down"}`} aria-hidden="true" /> backend: {health}
          <div className="api-base">{API_BASE}</div>
        </div>
      </aside>

      <main id="content" className="content">
        <header className="page-head">
          <h1>{TABS.find((t) => t.id === tab)?.label}</h1>
          <p className="muted">Code owns the workflow — Jev supplies the judgments. Every number traces to evidence.</p>
        </header>
        {tab === "triage" && (
          <TriagePanel ticket={ticket} setTicket={setTicket} onReviewed={(item) => setQueue((q) => [item, ...q].slice(0, 20))} />
        )}
        {tab === "pipeline" && <PipelinePanel ticket={ticket} />}
        {tab === "review" && <ReviewQueue items={queue} onClear={() => setQueue([])} />}
        {tab === "system" && <SystemPanel health={health} />}
      </main>
    </div>
  );
}
