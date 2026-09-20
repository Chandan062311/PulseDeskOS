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

  const rows = useMemo(
    () => (filter === "all" ? items : items.filter((i) => i.triage.action === filter)),
    [items, filter]
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
      {/* Active Threshold Explainer Strip */}
      <div
        className="card"
        style={{
          background: "var(--primary-subtle)",
          borderColor: "var(--primary-border)",
          padding: "10px 14px",
        }}
      >
        <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <strong style={{ color: "var(--ink)", fontSize: "12px" }}>Active Review Gating Criteria:</strong>
            <span className="small muted" style={{ marginLeft: "8px" }}>
              Policy thresholds triggering operator review
            </span>
          </div>
          <div className="row" style={{ gap: "6px" }}>
            <span className="chip chip-info">Confidence &lt; 0.75</span>
            <span className="chip chip-warn">Spam Band 0.40 – 0.60</span>
            <span className="chip chip-info">Route: other (always)</span>
          </div>
        </div>
      </div>

      {resolvedStatus && (
        <div className="card" style={{ background: "var(--ok-bg)", borderColor: "var(--ok-border)", padding: "10px 14px" }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <span style={{ color: "var(--ok)", fontWeight: 600 }}>{resolvedStatus}</span>
            <button className="ghost" style={{ padding: "2px 8px", fontSize: "11px" }} onClick={() => setResolvedStatus(null)}>
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
          <div className="row actions" style={{ marginBottom: "10px", justifyContent: "space-between" }}>
            <div className="row" style={{ gap: "6px" }}>
              <label htmlFor="action-filter" className="sr-only">Filter by action</label>
              <select id="action-filter" value={filter} onChange={(e) => setFilter(e.target.value)} style={{ width: "auto" }}>
                <option value="all">All Exceptions ({items.length})</option>
                <option value="human_review">human_review</option>
                <option value="quarantine_spam">quarantine_spam</option>
                <option value="auto_route">auto_route</option>
              </select>
            </div>
            {items.length > 0 && (
              <button className="ghost" style={{ padding: "3px 8px", fontSize: "11px" }} onClick={onClear}>
                Clear Session
              </button>
            )}
          </div>

          {rows.length === 0 ? (
            <EmptyState
              title="Review queue is empty"
              body="No tickets currently require manual review. Tickets evaluated by the triage engine with action 'human_review' or 'quarantine_spam' will appear here."
            />
          ) : (
            <div className="table-container">
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
                          background: isSelected ? "var(--primary-subtle)" : undefined,
                          borderLeft: isSelected ? "3px solid var(--primary)" : "3px solid transparent",
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
                          <strong style={{ color: "var(--ink)" }}>{q.sample.subject || "(no subject)"}</strong>
                          <div className="muted small">{q.sample.sender}</div>
                        </td>
                        <td>
                          <Chip tone="info">{q.triage.route}</Chip>
                        </td>
                        <td className="mono">{q.triage.route_confidence.toFixed(2)}</td>
                        <td>
                          <Chip tone={q.triage.spam_risk >= 0.4 ? "warn" : "ok"}>
                            {q.triage.spam_risk.toFixed(2)}
                          </Chip>
                        </td>
                        <td className="small">
                          <Chip tone={actionTone(q.triage.action)}>{q.triage.action}</Chip>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        {/* Right Pane: Selected Ticket Detail & Resolution Controls */}
        <Section title="Ticket Resolution" hint="Operator audit & dispatch panel">
          {selectedItem ? (
            <div className="stack">
              <div>
                <strong style={{ color: "var(--ink)" }}>{selectedItem.sample.subject || "(no subject)"}</strong>
                <div className="muted small">Sender: {selectedItem.sample.sender}</div>
              </div>

              <div style={{ background: "var(--surface-secondary)", border: "1px solid var(--line)", borderRadius: "var(--radius)", padding: "10px" }}>
                <div className="muted small" style={{ fontWeight: 600, marginBottom: "4px" }}>Message Body:</div>
                <div style={{ fontSize: "12px", color: "var(--ink)" }}>{selectedItem.sample.message}</div>
              </div>

              <div style={{ background: "var(--primary-subtle)", border: "1px solid var(--primary-border)", borderRadius: "var(--radius)", padding: "8px 10px" }}>
                <div style={{ fontWeight: 600, fontSize: "11px", color: "var(--primary)" }}>Trigger Diagnostic:</div>
                <div className="small" style={{ marginTop: "2px", color: "var(--ink-secondary)" }}>{selectedItem.triage.reason}</div>
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
                <label htmlFor="audit-note">Operator Audit Note (immutable audit trail)</label>
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
                  style={{ color: "var(--bad)", borderColor: "var(--bad-border)" }}
                  onClick={() => handleResolve("Quarantine as Spam")}
                >
                  Quarantine as Spam
                </button>
              </div>
            </div>
          ) : (
            <EmptyState title="No ticket selected" body="When tickets enter the review queue, select a ticket to review its details and resolve." />
          )}
        </Section>
      </div>
    </div>
  );
}
