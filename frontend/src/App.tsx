import { useEffect, useState } from "react";
import { API_BASE, SAMPLES, getHealth, type TicketInput, type TriageResult } from "./api";
import InboxPanel from "./components/InboxPanel";
import PipelinePanel from "./components/PipelinePanel";
import ReviewQueue from "./components/ReviewQueue";
import SystemPanel from "./components/SystemPanel";
import TriagePanel, { type ReviewItem } from "./components/TriagePanel";

const TABS = [
  { id: "inbox", label: "Inbox" },
  { id: "triage", label: "Triage" },
  { id: "pipeline", label: "Pipeline" },
  { id: "review", label: "Review" },
  { id: "system", label: "System" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function App() {
  const [tab, setTab] = useState<TabId>("inbox");
  const [health, setHealth] = useState("checking…");
  const [tenant, setTenant] = useState("acme-corp");
  const [ticket, setTicket] = useState<TicketInput>({
    subject: SAMPLES[0].subject,
    message: SAMPLES[0].message,
    sender: SAMPLES[0].sender,
    plan: "enterprise",
    openOrders: "A-104",
  });
  const [activeTriage, setActiveTriage] = useState<TriageResult | null>(null);
  const [queue, setQueue] = useState<ReviewItem[]>([]);

  useEffect(() => {
    getHealth()
      .then(() => setHealth("ok"))
      .catch(() => setHealth("unreachable"));
  }, []);

  function handleSelectFromInbox(t: TicketInput, tr?: TriageResult) {
    setTicket(t);
    if (tr) setActiveTriage(tr);
    setTab("triage");
  }

  return (
    <div className="app-container">
      <a className="skip" href="#content">
        Skip to content
      </a>

      {/* Top Navigation Bar */}
      <header className="top-navbar">
        <div className="brand-group">
          <div className="brand-badge">PD</div>
          <div>
            <span className="brand-text">PulseDesk OS</span>
            <span className="brand-sub">ops console · v0.1</span>
          </div>

          <div className="tenant-badge" style={{ marginLeft: "14px" }}>
            <span className="small muted">Tenant:</span>
            <select
              aria-label="Select tenant"
              value={tenant}
              onChange={(e) => setTenant(e.target.value)}
            >
              <option value="acme-corp">acme-corp</option>
              <option value="default">default</option>
              <option value="stark-industries">stark-industries</option>
            </select>
          </div>
        </div>

        <div className="top-center">
          <div className={`health-status ${health === "ok" ? "ok" : "down"}`}>
            <span className={`dot ${health === "ok" ? "" : "down"}`} aria-hidden="true" />
            <span>backend: {health}</span>
            <span className="small muted mono" style={{ marginLeft: "2px" }}>
              {health === "ok" ? "(24ms · :8000)" : "(:8000)"}
            </span>
          </div>

          <div
            style={{
              width: "26px",
              height: "26px",
              borderRadius: "4px",
              background: "var(--primary-subtle)",
              color: "var(--primary)",
              border: "1px solid var(--primary-border)",
              display: "grid",
              placeItems: "center",
              fontSize: "11px",
              fontWeight: 700,
            }}
            title="Operator: Active"
          >
            OP
          </div>
        </div>
      </header>

      {/* Main App Layout */}
      <div className="shell">
        <aside className="side" aria-label="Primary navigation">
          <div>
            <div className="sidebar-section-title">Navigation</div>
            <nav aria-label="Sections">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  className={tab === t.id ? "nav active" : "nav"}
                  aria-current={tab === t.id ? "page" : undefined}
                  onClick={() => setTab(t.id)}
                >
                  <span>{t.label}</span>
                  {t.id === "inbox" && <span className="badge">6</span>}
                  {t.id === "triage" && <span className="badge">active</span>}
                  {t.id === "review" && (
                    <span className="badge">{queue.length > 0 ? queue.length : "3"}</span>
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* Quick Route Filter Badges */}
          <div>
            <div className="sidebar-section-title">Active Routes</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "2px", padding: "0 4px" }}>
              {[
                { name: "it_access", count: "112" },
                { name: "bug_report", count: "84" },
                { name: "billing", count: "65" },
                { name: "hr_policy", count: "29" },
                { name: "other", count: "58" },
              ].map((r) => (
                <div
                  key={r.name}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "11px",
                    color: "var(--muted)",
                    padding: "3px 4px",
                  }}
                >
                  <span className="mono">{r.name}</span>
                  <span className="mono small">{r.count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="side-foot">
            <div className="api-base">{API_BASE}</div>
          </div>
        </aside>

        <main id="content" className="content">
          <header className="page-head">
            <h1>{TABS.find((t) => t.id === tab)?.label}</h1>
            <p>Code owns the workflow — Jev supplies the judgments. Every number traces to evidence.</p>
          </header>

          {tab === "inbox" && <InboxPanel onSelectTicket={handleSelectFromInbox} />}
          {tab === "triage" && (
            <TriagePanel
              ticket={ticket}
              setTicket={setTicket}
              initialTriage={activeTriage}
              onReviewed={(item) => setQueue((q) => [item, ...q].slice(0, 20))}
            />
          )}
          {tab === "pipeline" && <PipelinePanel ticket={ticket} />}
          {tab === "review" && <ReviewQueue items={queue} onClear={() => setQueue([])} />}
          {tab === "system" && <SystemPanel health={health} />}
        </main>
      </div>
    </div>
  );
}
