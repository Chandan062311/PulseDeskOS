import { useEffect, useState } from "react";
import { API_BASE, getHealth, type TicketInput, type TriageResult } from "./api";
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
  const [tenant, setTenant] = useState("default");
  const [ticket, setTicket] = useState<TicketInput>({
    subject: "",
    message: "",
    sender: "",
    plan: "enterprise",
    openOrders: "",
  });
  const [activeTriage, setActiveTriage] = useState<TriageResult | null>(null);
  const [queue, setQueue] = useState<ReviewItem[]>([]);

  useEffect(() => {
    getHealth()
      .then(() => setHealth("ok"))
      .catch(() => setHealth("unreachable"));
  }, []);

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
            <span className="brand-sub">Operations Console</span>
          </div>

          <div className="tenant-badge" style={{ marginLeft: "14px" }}>
            <span className="small muted">Tenant:</span>
            <select
              aria-label="Select tenant"
              value={tenant}
              onChange={(e) => setTenant(e.target.value)}
            >
              <option value="default">default</option>
              <option value="acme-corp">acme-corp</option>
              <option value="production">production</option>
            </select>
          </div>
        </div>

        <div className="top-center">
          <div className={`health-status ${health === "ok" ? "ok" : "down"}`}>
            <span className={`dot ${health === "ok" ? "" : "down"}`} aria-hidden="true" />
            <span>backend: {health}</span>
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
                  {t.id === "review" && queue.length > 0 && (
                    <span className="badge">{queue.length}</span>
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* Supported Handlers */}
          <div>
            <div className="sidebar-section-title">Registered Routes</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "2px", padding: "0 4px" }}>
              {["it_access", "bug_report", "billing", "hr_policy", "other"].map((name) => (
                <div
                  key={name}
                  style={{
                    fontSize: "11px",
                    color: "var(--muted)",
                    padding: "3px 4px",
                  }}
                >
                  <span className="mono">{name}</span>
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
