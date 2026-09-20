import { useMemo, useState } from "react";
import type { ReviewItem } from "./TriagePanel";
import { Chip, EmptyState, Section } from "./ui";

export default function ReviewQueue({ items, onClear }: { items: ReviewItem[]; onClear: () => void }) {
  const [filter, setFilter] = useState("all");
  const rows = useMemo(
    () => (filter === "all" ? items : items.filter((i) => i.triage.action === filter)),
    [items, filter],
  );

  return (
    <Section
      title="Review queue"
      hint="Non-auto-routed results from this session. Production source of truth is the backend audit log."
    >
      <div className="row actions">
        <label htmlFor="action-filter">Action</label>
        <select id="action-filter" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">all ({items.length})</option>
          <option value="human_review">human_review</option>
          <option value="quarantine_spam">quarantine_spam</option>
          <option value="auto_route">auto_route</option>
        </select>
        <button className="ghost" disabled={items.length === 0} onClick={onClear}>
          Clear
        </button>
      </div>
      {rows.length === 0 ? (
        <EmptyState
          title="Queue empty"
          body="Triage results with action human_review or quarantine_spam land here automatically."
        />
      ) : (
        <table>
          <thead>
            <tr>
              <th scope="col">Subject</th>
              <th scope="col">Route</th>
              <th scope="col">Conf</th>
              <th scope="col">Spam</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((q, i) => (
              <tr key={`${q.sample.id}-${i}`}>
                <td>{q.sample.subject || "(no subject)"}</td>
                <td>{q.triage.route}</td>
                <td>{q.triage.route_confidence.toFixed(2)}</td>
                <td>{q.triage.spam_risk.toFixed(2)}</td>
                <td>
                  <Chip tone={q.triage.action === "auto_route" ? "ok" : q.triage.action === "quarantine_spam" ? "bad" : "warn"}>
                    {q.triage.action}
                  </Chip>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Section>
  );
}
