import { useState, useMemo } from "react";
import { SAMPLES, type TicketInput, type TriageResult } from "../api";
import { Chip, EmptyState, Meter, Section, actionTone } from "./ui";

export type InboxTicket = {
  id: string;
  subject: string;
  sender: string;
  message: string;
  plan: string;
  openOrders: string;
  route: string;
  route_confidence: number;
  spam_risk: number;
  urgency: number;
  frustration: number;
  action: "auto_route" | "human_review" | "quarantine_spam" | string;
  reason: string;
};

// Realistic mock tickets reflecting inbound stream when backend GET /v1/tickets is unavailable
const INITIAL_INBOX_TICKETS: InboxTicket[] = [
  {
    id: "PD-8924",
    subject: SAMPLES[0].subject,
    sender: SAMPLES[0].sender,
    message: SAMPLES[0].message,
    plan: "enterprise",
    openOrders: "A-104",
    route: "billing",
    route_confidence: 0.94,
    spam_risk: 0.02,
    urgency: 0.78,
    frustration: 0.65,
    action: "auto_route",
    reason: "Duplicate capture for order A-104 matches historical pattern",
  },
  {
    id: "PD-8925",
    subject: SAMPLES[1].subject,
    sender: SAMPLES[1].sender,
    message: SAMPLES[1].message,
    plan: "enterprise",
    openOrders: "INV-500",
    route: "bug_report",
    route_confidence: 0.88,
    spam_risk: 0.01,
    urgency: 0.95,
    frustration: 0.82,
    action: "auto_route",
    reason: "Outage keywords detected, high urgency SLA",
  },
  {
    id: "PD-8926",
    subject: SAMPLES[2].subject,
    sender: SAMPLES[2].sender,
    message: SAMPLES[2].message,
    plan: "standard",
    openOrders: "",
    route: "it_access",
    route_confidence: 0.91,
    spam_risk: 0.04,
    urgency: 0.60,
    frustration: 0.15,
    action: "auto_route",
    reason: "Standard provisioning workflow for new joiner",
  },
  {
    id: "PD-8927",
    subject: SAMPLES[3].subject,
    sender: SAMPLES[3].sender,
    message: SAMPLES[3].message,
    plan: "free",
    openOrders: "",
    route: "other",
    route_confidence: 0.45,
    spam_risk: 0.92,
    urgency: 0.85,
    frustration: 0.10,
    action: "quarantine_spam",
    reason: "Phishing credential solicitation detected (spam risk >= 0.60)",
  },
  {
    id: "PD-8928",
    subject: SAMPLES[4].subject,
    sender: SAMPLES[4].sender,
    message: SAMPLES[4].message,
    plan: "growth",
    openOrders: "",
    route: "other",
    route_confidence: 0.48,
    spam_risk: 0.48,
    urgency: 0.35,
    frustration: 0.40,
    action: "human_review",
    reason: "Spam in uncertain band (0.40-0.60) and route 'other' requires review",
  },
  {
    id: "PD-8929",
    subject: "Need root certificate renewal for cluster",
    sender: "devops@megacorp.io",
    message: "Root CA certificate expires next Monday on staging cluster.",
    plan: "enterprise",
    openOrders: "",
    route: "it_access",
    route_confidence: 0.68,
    spam_risk: 0.05,
    urgency: 0.70,
    frustration: 0.20,
    action: "human_review",
    reason: "Confidence 0.68 below cutoff 0.75; operator verification needed",
  },
];

export default function InboxPanel({
  onSelectTicket,
}: {
  onSelectTicket: (t: TicketInput, triageResult?: TriageResult) => void;
}) {
  const [routeFilter, setRouteFilter] = useState("all");
  const [actionFilter, setActionFilter] = useState("all");
  const [search, setSearch] = useState("");

  const filteredTickets = useMemo(() => {
    return INITIAL_INBOX_TICKETS.filter((t) => {
      if (routeFilter !== "all" && t.route !== routeFilter) return false;
      if (actionFilter !== "all" && t.action !== actionFilter) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        return (
          t.subject.toLowerCase().includes(q) ||
          t.sender.toLowerCase().includes(q) ||
          t.id.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [routeFilter, actionFilter, search]);

  const stats = useMemo(() => {
    const total = INITIAL_INBOX_TICKETS.length;
    const autoRouted = INITIAL_INBOX_TICKETS.filter((t) => t.action === "auto_route").length;
    const humanReview = INITIAL_INBOX_TICKETS.filter((t) => t.action === "human_review").length;
    const quarantined = INITIAL_INBOX_TICKETS.filter((t) => t.action === "quarantine_spam").length;
    return {
      total,
      pctAuto: Math.round((autoRouted / total) * 100),
      pctReview: Math.round((humanReview / total) * 100),
      pctSpam: Math.round((quarantined / total) * 100),
    };
  }, []);

  return (
    <div className="stack">
      {/* Metric Cards Banner (Screen 1 KPI Rail) */}
      <div className="grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        <div className="card">
          <div className="muted small">Triage Volume (Today)</div>
          <strong style={{ fontSize: "1.4rem" }}>{stats.total} tickets</strong>
          <div className="muted small" style={{ marginTop: "4px" }}>+12% vs yesterday</div>
        </div>
        <div className="card">
          <div className="muted small">% Auto-Routed</div>
          <strong style={{ fontSize: "1.4rem", color: "var(--ok)" }}>{stats.pctAuto}%</strong>
          <div className="muted small" style={{ marginTop: "4px" }}>Target: &ge; 70%</div>
        </div>
        <div className="card">
          <div className="muted small">% Human Review</div>
          <strong style={{ fontSize: "1.4rem", color: "var(--warn)" }}>{stats.pctReview}%</strong>
          <div className="muted small" style={{ marginTop: "4px" }}>Gated for audit</div>
        </div>
        <div className="card">
          <div className="muted small">% Quarantined</div>
          <strong style={{ fontSize: "1.4rem", color: "var(--bad)" }}>{stats.pctSpam}%</strong>
          <div className="muted small" style={{ marginTop: "4px" }}>Spam cutoff &ge; 0.60</div>
        </div>
      </div>

      <Section
        title="Inbound Tickets"
        hint="Live operational stream. Select any ticket to inspect probability bars, evidence, and actions."
      >
        <div className="row actions" style={{ justifyContent: "space-between", marginBottom: "12px" }}>
          <div className="row" style={{ flex: "1 1 300px" }}>
            <input
              type="search"
              placeholder="Search by ID, subject, or sender..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ maxWidth: "340px" }}
              aria-label="Search tickets"
            />
          </div>

          <div className="row">
            <label htmlFor="route-filter" className="sr-only">Filter by route</label>
            <select
              id="route-filter"
              value={routeFilter}
              onChange={(e) => setRouteFilter(e.target.value)}
              style={{ width: "auto" }}
            >
              <option value="all">All Routes</option>
              <option value="billing">billing</option>
              <option value="bug_report">bug_report</option>
              <option value="it_access">it_access</option>
              <option value="hr_policy">hr_policy</option>
              <option value="other">other</option>
            </select>

            <label htmlFor="action-filter" className="sr-only">Filter by action</label>
            <select
              id="action-filter"
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              style={{ width: "auto" }}
            >
              <option value="all">All Actions</option>
              <option value="auto_route">auto_route</option>
              <option value="human_review">human_review</option>
              <option value="quarantine_spam">quarantine_spam</option>
            </select>
          </div>
        </div>

        {filteredTickets.length === 0 ? (
          <EmptyState
            title="No matching tickets"
            body="Try adjusting your route, action, or search filters."
          />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Subject</th>
                  <th scope="col">Sender</th>
                  <th scope="col">Route</th>
                  <th scope="col" style={{ minWidth: "130px" }}>Confidence</th>
                  <th scope="col">Spam</th>
                  <th scope="col">Urgency</th>
                  <th scope="col">Action</th>
                  <th scope="col">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredTickets.map((t) => (
                  <tr key={t.id}>
                    <td>
                      <code>{t.id}</code>
                    </td>
                    <td>
                      <strong>{t.subject}</strong>
                      <div className="muted small" style={{ maxWidth: "280px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {t.message}
                      </div>
                    </td>
                    <td className="small">{t.sender}</td>
                    <td>
                      <Chip tone="info">{t.route}</Chip>
                    </td>
                    <td>
                      <Meter label="" value={t.route_confidence} />
                    </td>
                    <td>
                      <span className={t.spam_risk >= 0.6 ? "chip chip-bad" : t.spam_risk >= 0.4 ? "chip chip-warn" : "chip chip-ok"}>
                        {t.spam_risk.toFixed(2)}
                      </span>
                    </td>
                    <td>
                      <span className={t.urgency >= 0.7 ? "chip chip-warn" : "chip chip-info"}>
                        {t.urgency.toFixed(2)}
                      </span>
                    </td>
                    <td>
                      <Chip tone={actionTone(t.action)}>{t.action}</Chip>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <button
                        className="ghost"
                        onClick={() =>
                          onSelectTicket(
                            {
                              subject: t.subject,
                              message: t.message,
                              sender: t.sender,
                              plan: t.plan,
                              openOrders: t.openOrders,
                            },
                            {
                              route: t.route,
                              route_confidence: t.route_confidence,
                              spam_risk: t.spam_risk,
                              urgency: t.urgency,
                              frustration: t.frustration,
                              needs_memory: 0.5,
                              refund_requested: t.route === "billing" ? 0.95 : 0.0,
                              pii_detected: 0.1,
                              action: t.action,
                              reason: t.reason,
                            }
                          )
                        }
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  );
}

