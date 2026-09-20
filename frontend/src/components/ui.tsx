import type { ReactNode } from "react";

// Shared primitives: one visual language for chips, meters, sections,
// empty / loading / error states. Flat enterprise styling — no gradients.

export function Chip({ tone, children }: { tone: "ok" | "warn" | "bad" | "info"; children: ReactNode }) {
  return <span className={`chip chip-${tone}`}>{children}</span>;
}

export function actionTone(action: string): "ok" | "warn" | "bad" {
  if (action === "auto_route") return "ok";
  if (action === "quarantine_spam") return "bad";
  return "warn";
}

export function Meter({ label, value }: { label?: string; value: number }) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));

  if (!label) {
    return (
      <div className="meter-inline">
        <div
          className="bar"
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="score"
        >
          <div style={{ width: `${pct}%` }} />
        </div>
        <span className="meter-val">{value.toFixed(2)}</span>
      </div>
    );
  }

  return (
    <div className="meter">
      <div className="meter-head">
        <span>{label}</span>
        <strong className="mono">{value.toFixed(2)}</strong>
      </div>
      <div
        className="bar"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        <div style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function Section({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <section className="card" aria-label={title}>
      <div className="section-head">
        <h2>{title}</h2>
        {hint && <p className="muted">{hint}</p>}
      </div>
      {children}
    </section>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="empty" role="status">
      <strong style={{ color: "var(--ink)" }}>{title}</strong>
      <p className="muted">{body}</p>
    </div>
  );
}

export function LoadingRow({ label }: { label: string }) {
  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="error" role="alert">
      <div>
        <strong>Request failed.</strong> <span>{message}</span>
      </div>
      {onRetry && (
        <button className="ghost" onClick={onRetry} style={{ padding: "3px 8px", fontSize: "11px" }}>
          Retry
        </button>
      )}
    </div>
  );
}
