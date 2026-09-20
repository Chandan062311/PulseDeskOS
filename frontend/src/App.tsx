import { useEffect, useState } from "react";
import { API_BASE, SAMPLES, getHealth, getApiKey, setApiKey, type TicketInput, type TriageResult } from "./api";
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
  const [keyInput, setKeyInput] = useState(getApiKey());
  const [showKey, setShowKey] = useState(false);
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

  function handleKeyChange(val: string) {
    setKeyInput(val);
    setApiKey(val);
  }

  function handleSelectFromInbox(t: TicketInput, tr?: TriageResult) {
    setTicket(t);
    if (tr) setActiveTriage(tr);
    setTab("triage");
  }

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

        {/* Tenant Switcher */}
        <div>
          <label htmlFor="tenant-select" className="small muted" style={{ display: "block", marginBottom: "4px" }}>
            Tenant
          </label>
          <select
            id="tenant-select"
            value={tenant}
            onChange={(e) => setTenant(e.target.value)}
            style={{ fontSize: "12px", padding: "4px 8px" }}
          >
            <option value="acme-corp">acme-corp (active)</option>
            <option value="default">default</option>
            <option value="stark-industries">stark-industries</option>
          </select>
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

        {/* Operator Dev Key Input */}
        <div style={{ marginTop: "auto", borderTop: "1px solid #334155", paddingTop: "12px" }}>
          <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
            <label htmlFor="dev-api-key" className="small muted" style={{ margin: 0 }}>
              Operator API Key
            </label>
            <button
              type="button"
              className="ghost"
              style={{ fontSize: "10px", padding: "1px 5px", height: "auto" }}
              onClick={() => setShowKey(!showKey)}
            >
              {showKey ? "hide" : "show"}
            </button>
          </div>
          <input
            id="dev-api-key"
            type={showKey ? "text" : "password"}
            placeholder="dev key (optional)"
            value={keyInput}
            onChange={(e) => handleKeyChange(e.target.value)}
            style={{ fontSize: "11px", padding: "4px 6px", marginTop: "4px" }}
          />
        </div>

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
  );
}
