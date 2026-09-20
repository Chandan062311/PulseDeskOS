// Typed client for backend/main.py. No mock data here: failures surface as
// ApiError with status + detail so the UI can render honest error states.

export type TriageResult = {
  route: string;
  route_confidence: number;
  spam_risk: number;
  urgency: number;
  frustration: number;
  needs_memory: number;
  refund_requested: number;
  pii_detected: number;
  action: "auto_route" | "human_review" | "quarantine_spam" | string;
  reason: string;
};

export type MemoryHit = {
  id: string;
  text: string;
  type: string;
  relevance: number;
  contradicts: number;
  has_injection: number;
  has_pii: number;
};

export type OrchestrateResult = {
  triage: TriageResult;
  memory_hits: MemoryHit[];
  handler: { handler: string; summary: string; next_step: string };
  draft_reply: string;
  verify: { supported: number; confidence: number; verdict: string };
  captured_id?: string;
  captured_memory_id?: string;
};

export type TicketInput = {
  subject: string;
  message: string;
  sender: string;
  plan: string;
  openOrders: string;
};

export type Sample = TicketInput & { id: string };

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(`HTTP ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const ENV = (import.meta as unknown as { env: Record<string, string> }).env ?? {};
export const API_BASE = ENV.VITE_API ?? "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  // Single-key model: only the server-side Jev key exists. No app auth header.
  const headers = new Headers(init?.headers);
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch (e) {
    throw new ApiError(0, e instanceof Error ? e.message : "network unreachable");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* non-JSON error body: keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

function ticketBody(t: TicketInput) {
  return {
    ticket: {
      subject: t.subject,
      message: t.message,
      sender: { display_name: t.sender, email: t.sender },
      links: [],
    },
    customer: {
      plan: t.plan.trim() || "enterprise",
      open_orders: t.openOrders.split(",").map((s) => s.trim()).filter(Boolean),
    },
  };
}

export function getHealth(): Promise<{ status: string }> {
  return req("/healthz");
}

export type BackendStatus = { status: string; jev: "live" | "offline" };

export function getStatus(): Promise<BackendStatus> {
  return req("/v1/status");
}

export function postTriage(t: TicketInput, live: boolean): Promise<TriageResult> {
  return req(`/v1/triage?live=${live ? "true" : "false"}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(ticketBody(t)),
  });
}

export function postOrchestrate(t: TicketInput, tenantId = "default"): Promise<OrchestrateResult> {
  return req("/v1/orchestrate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...ticketBody(t), tenant_id: tenantId, seed: true }),
  });
}

export const SAMPLES: Sample[] = [
  {
    id: "dup-charge",
    subject: "Duplicate charge",
    message: "I was charged twice for order A-104. Please refund the duplicate.",
    sender: "user@acme.com",
  },
  {
    id: "outage",
    subject: "API 500s on checkout",
    message: "Our integration returns 500 on every request and we cannot process orders. Outage.",
    sender: "ops@acme.com",
  },
  {
    id: "vpn",
    subject: "VPN access for new joiner",
    message: "New joiner needs VPN access starting Monday, please provision.",
    sender: "hr@acme.com",
  },
  {
    id: "phish",
    subject: "Urgent: claim your bonus",
    message: "You won a $1000 bonus. Reply with your password today to claim.",
    sender: "rewards@claim-bonus.example",
  },
  {
    id: "vague",
    subject: "Something seems off",
    message: "Hi, something seems off but I'm not sure what. Can someone look?",
    sender: "user@acme.com",
  },
];
