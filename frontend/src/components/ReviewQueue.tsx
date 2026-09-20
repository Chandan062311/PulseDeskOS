import { useMemo, useState } from "react";
import type { ReviewItem } from "./TriagePanel";
import { Chip, EmptyState, Section, actionTone } from "./ui";

const ROUTES = ["it_access", "bug_report", "billing", "hr_policy", "other"] as const;

export default function ReviewQueue({
  items,
  onClear,
}: {
  items: ReviewItem[];
  onClear: () => void;
}) {
  const [filter, setFilter] = useState("all");
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [reassignRoute, setReassignRoute] = useState<string>("");
  const [auditNote, setAuditNote] = useState<string>("");
  const [resolvedStatus, setResolvedStatus] = useState<string | null>(null);

  // Combine session items with pre-seeded sample exceptions if session queue is empty
  const allQueueItems: ReviewItem[] = useMemo(() => {
    if (items.length > 0) return items;
    return [
      {
        sample: {
          id: "PD-8932",
          subject: "Something seems off with my account balance",
          message: "Hi, something seems off but I'm not sure what. Can someone check?",
          sender: "user@acme.com",
          plan: "growth",
          openOrders: "",
        },
        triage: {
          route: "other",
          route_confidence: 0.48,
          spam_risk: 0.45,
          urgency: 0.35,
          frustration: 0.4,
          needs_memory: 0.7,
          refund_requested: 0.1,
          pii_detected: 0.0,
          action: "human_review",
          reason: "Spam risk in uncertain band (0.40–0.60) and route 'other' always requires human review",
        },
      },
      {
        sample: {
          id: "PD-8935",
          subject: "Root cert re-signing for legacy cluster",
          message: "Need root certificate renewal for staging cluster before Monday expiry.",
          sender: "devops@megacorp.io",
          plan: "enterprise",
          openOrders: "",
        },
        triage: {
          route: "it_access",
          route_confidence: 0.64,
          spam_risk: 0.08,
          urgency: 0.7,
          frustration: 0.2,
          needs_memory: 0.4,
          refund_requested: 0.0,
          pii_detected: 0.0,
          action: "human_review",
          reason: "Route confidence 0.64 < 0.75 cutoff threshold; manual gate triggered",
        },
      },
      {
        sample: {
          id: "PD-8938",
          subject: "Urgent: payment invoice update wire detail check",
          message: "Please find attached the revised wire instructions for payment. Urgent wire today.",
          sender: "invoicing@external-vendor-check.com",
          plan: "standard",
          openOrders: "",
        },
        triage: {
          route: "billing",
          route_confidence: 0.72,
          spam_risk: 0.52,
          urgency: 0.9,
          frustration: 0.1,
          needs_memory: 0.3,
          refund_requested: 0.0,
          pii_detected: 0.2,
          action: "human_review",
          reason: "Spam risk 0.52 inside the 0.40–0.60 review band (below 0.60 quarantine threshold)",
        },
      },
    ];
  }, [items]);

  const rows = useMemo(
    () => (filter === "all" ? allQueueItems : allQueueItems.filter((i) => i.triage.action === filter)),
    [allQueueItems, filter]
  );

  const selectedItem: ReviewItem | undefined = rows[selectedIndex] || rows[0];

  function handleResolve(action: string) {
    if (!selectedItem) return;
    const effectiveRoute = reassignRoute || selectedItem.triage.route;
    setResolvedStatus(
      `Ticket resolved: ${action} with route [${effectiveRoute}]. Audit note logged: "${auditNote || "Operator approved without additional note"}".`
    );
    setAuditNote("");
    setReassignRoute("");
  }

  return (
    <div className="stack">
      {/* Threshold Explainer Strip (Matching Screen 3 Stitch design) */}
      <div
        className="card"
        style={{
          background: "var(--info-bg)",
          border: "1px solid var(--primary)",
          padding: "12px 16px",
        }}
      >
        <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <strong>Active Gating Criteria:</strong>
            <span className="small muted" style={{ marginLeft: "8px" }}>
              Policy thresholds triggering operator review
            </span>
          </div>
          <div className="row">
            <span className="chip chip-info">Confidence &lt; 0.75</span>
            <span className="chip chip-warn">Spam Band 0.40 – 0.60</span>
            <span className="chip chip-info">Route: other (always)</span>
          </div>
        </div>
      </div>

      {resolvedStatus && (
        <div className="card" style={{ background: "var(--ok-bg)", border: "1px solid var(--ok)", padding: "10px 14px" }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <span style={{ color: "var(--ok)", fontWeight: 600 }}>{resolvedStatus}</span>
            <button className="ghost" style={{ padding: "2px 8px", fontSize: "12px" }} onClick={() => setResolvedStatus(null)}>
              Dismiss
            </button>
          </div>
        </div>
      )}

      <div className="grid" style={{ gridTemplateColumns: "1.2fr 0.8fr", alignItems: "start" }}>
        {/* Left Pane: Queue Table */}
        <Section
          title={`Review Queue (${rows.length})`}
          hint="Tickets gated for manual review. Click a row to inspect and resolve."
        >
          <div className="row actions" style={{ marginBottom: "10px" }}>
            <label htmlFor="action-filter" className="sr-only">Filter by action</label>
            <select id="action-filter" value={filter} onChange={(e) => setFilter(e.target.value)} style={{ width: "auto" }}>
              <option value="all">All Exceptions ({allQueueItems.length})</option>
              <option value="human_review">human_review</option>
              <option value="quarantine_spam">quarantine_spam</option>
              <option value="auto_route">auto_route</option>
            </select>
            {items.length > 0 && (
              <button className="ghost" onClick={onClear}>
                Clear Session Items
              </button>
            )}
          </div>

          {rows.length === 0 ? (
            <EmptyState
              title="Queue empty"
              body="No tickets currently meet human review or quarantine criteria."
            />
          ) : (
            <table>
              <thead>
                <tr>
                  <th scope="col">Subject</th>
                  <th scope="col">Predicted Route</th>
                  <th scope="col">Conf</th>
                  <th scope="col">Spam</th>
                  <th scope="col">Gate Reason</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((q, i) => {
                  const isSelected = selectedItem === q;
                  return (
                    <tr
                      key={`${q.sample.id}-${i}`}
                      onClick={() => {
                        setSelectedIndex(i);
                        setResolvedStatus(null);
                      }}
                      style={{
                        cursor: "pointer",
                        background: isSelected ? "var(--info-bg)" : undefined,
                        outline: isSelected ? "2px solid var(--primary)" : undefined,
                      }}
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          setSelectedIndex(i);
                          setResolvedStatus(null);
                        }
                      }}
                    >
                      <td>
                        <strong>{q.sample.subject || "(no subject)"}</strong>
                        <div className="muted small">{q.sample.sender}</div>
                      </td>
                      <td>
                        <Chip tone="info">{q.triage.route}</Chip>
                      </td>
                      <td>{q.triage.route_confidence.toFixed(2)}</td>
                      <td>
                        <span className={q.triage.spam_risk >= 0.4 ? "chip chip-warn" : "chip chip-ok"}>
                          {q.triage.spam_risk.toFixed(2)}
                        </span>
                      </td>
                      <td className="small" style={{ maxWidth: "160px" }}>
                        <Chip tone={actionTone(q.triage.action)}>{q.triage.action}</Chip>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </Section>

        {/* Right Pane: Selected Ticket Detail & Resolution Controls */}
        <Section title="Ticket Resolution" hint="Operator audit & dispatch panel">
          {selectedItem ? (
            <div className="stack">
              <div>
                <strong>Subject:</strong> {selectedItem.sample.subject}
                <div className="muted small">Sender: {selectedItem.sample.sender}</div>
              </div>

              <div style={{ background: "#f8fafc", border: "1px solid var(--line)", borderRadius: "var(--radius)", padding: "10px" }}>
                <div className="muted small" style={{ fontWeight: 600, marginBottom: "4px" }}>Message Body:</div>
                <div style={{ fontSize: "13px" }}>{selectedItem.sample.message}</div>
              </div>

              <div style={{ background: "var(--info-bg)", borderRadius: "var(--radius)", padding: "8px 10px" }}>
                <div className="muted small" style={{ fontWeight: 600 }}>Trigger Diagnostic:</div>
                <div className="small" style={{ marginTop: "2px" }}>{selectedItem.triage.reason}</div>
              </div>

              <div>
                <label htmlFor="reassign-route">Reassign Route (optional override)</label>
                <select
                  id="reassign-route"
                  value={reassignRoute || selectedItem.triage.route}
                  onChange={(e) => setReassignRoute(e.target.value)}
                >
                  {ROUTES.map((r) => (
                    <option key={r} value={r}>
                      {r} {r === selectedItem.triage.route ? "(predicted)" : ""}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="audit-note">Operator Audit Note (logged to immutable audit trail)</label>
                <textarea
                  id="audit-note"
                  rows={3}
                  placeholder="Enter justification for routing decision or exception override..."
                  value={auditNote}
                  onChange={(e) => setAuditNote(e.target.value)}
                />
              </div>

              <div className="row actions" style={{ marginTop: "8px" }}>
                <button
                  onClick={() => handleResolve("Approve & Dispatch")}
                >
                  Approve & Dispatch
                </button>
                <button
                  className="ghost"
                  style={{ color: "var(--bad)" }}
                  onClick={() => handleResolve("Quarantine as Spam")}
                >
                  Quarantine as Spam
                </button>
              </div>
            </div>
          ) : (
            <EmptyState title="No ticket selected" body="Select a ticket from the queue to review." />
          )}
        </Section>
      </div>
    </div>
  );
}
