"""Built-in route handlers (Agent A).

One trivial handler per route. Each checks ownership via ``triage.route``
and returns a deterministic :class:`HandlerResult`. Registered by side effect
on import so :mod:`backend.main` only needs to import this module.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ..jev_client import load_config
from ..registry import register
from ..schemas import HandlerResult, Route, Ticket, TriageResult


@lru_cache(maxsize=1)
def _handler_config() -> dict[str, Any]:
    """Cached handler thresholds. Missing config falls back to defaults."""
    cfg = load_config()
    section = cfg.get("handlers", {})
    return section if isinstance(section, dict) else {}


def _hthreshold(key: str, default: float) -> float:
    """Read a handler threshold with a fallback default."""
    raw = _handler_config().get(key, default)
    return float(raw) if isinstance(raw, (int, float)) else default


class ITAccessHandler:
    """Handle IT access tickets (resets, SSO/VPN, provisioning)."""

    name: str = "it_access"

    def can_handle(self, triage: TriageResult) -> bool:
        """Return True when triage routed to IT access.

        Args:
            triage: Composed triage result.

        Returns:
            True iff ``triage.route`` is ``IT_ACCESS``.
        """
        return triage.route is Route.IT_ACCESS

    def run(self, ticket: Ticket, triage: TriageResult) -> HandlerResult:
        """Return the deterministic IT access next step.

        Args:
            ticket: Incoming support ticket.
            triage: Composed triage result.

        Returns:
            HandlerResult with identity-verification next step.
        """
        _ = triage
        return HandlerResult(
            handler=self.name,
            ticket_subject=ticket.subject,
            summary="Access request triaged; verify identity before provisioning.",
            next_step="Verify identity, then reset credentials or grant access in the IdP.",
        )


class BugReportHandler:
    """Handle bug report tickets (crashes, 500s, broken features)."""

    name: str = "bug_report"

    def can_handle(self, triage: TriageResult) -> bool:
        """Return True when triage routed to bug report.

        Args:
            triage: Composed triage result.

        Returns:
            True iff ``triage.route`` is ``BUG_REPORT``.
        """
        return triage.route is Route.BUG_REPORT

    def run(self, ticket: Ticket, triage: TriageResult) -> HandlerResult:
        """File the bug with severity derived from urgency.

        Args:
            ticket: Incoming support ticket.
            triage: Composed triage result.

        Returns:
            HandlerResult with file-and-reproduce next step.
        """
        severity = "SEV-1" if triage.urgency >= _hthreshold("sev1_urgency", 0.75) else "SEV-3"
        return HandlerResult(
            handler=self.name,
            ticket_subject=ticket.subject,
            summary=f"Bug filed at {severity}; attach repro and logs.",
            next_step="Open an incident ticket with repro steps and escalate on SEV-1.",
        )


class BillingHandler:
    """Handle billing tickets (charges, invoices, refunds)."""

    name: str = "billing"

    def can_handle(self, triage: TriageResult) -> bool:
        """Return True when triage routed to billing.

        Args:
            triage: Composed triage result.

        Returns:
            True iff ``triage.route`` is ``BILLING``.
        """
        return triage.route is Route.BILLING

    def run(self, ticket: Ticket, triage: TriageResult) -> HandlerResult:
        """Return the deterministic billing next step.

        Args:
            ticket: Incoming support ticket.
            triage: Composed triage result.

        Returns:
            HandlerResult noting refund review when a refund was requested.
        """
        refund_note = (
            " Refund requested: review charge history before approving."
            if triage.refund_requested >= _hthreshold("refund_note", 0.5)
            else ""
        )
        return HandlerResult(
            handler=self.name,
            ticket_subject=ticket.subject,
            summary=f"Billing case opened.{refund_note}",
            next_step="Pull invoices and charge history, then resolve or escalate to finance.",
        )


class HRPolicyHandler:
    """Handle HR policy tickets (leave, benefits, payroll)."""

    name: str = "hr_policy"

    def can_handle(self, triage: TriageResult) -> bool:
        """Return True when triage routed to HR policy.

        Args:
            triage: Composed triage result.

        Returns:
            True iff ``triage.route`` is ``HR_POLICY``.
        """
        return triage.route is Route.HR_POLICY

    def run(self, ticket: Ticket, triage: TriageResult) -> HandlerResult:
        """Return the deterministic HR policy next step.

        Args:
            ticket: Incoming support ticket.
            triage: Composed triage result.

        Returns:
            HandlerResult pointing at the policy lookup step.
        """
        _ = triage
        return HandlerResult(
            handler=self.name,
            ticket_subject=ticket.subject,
            summary="HR policy question triaged; look up the current handbook entry.",
            next_step="Answer from the handbook or route to People Ops for confirmation.",
        )


class OtherHandler:
    """Catch-all handler for vague, mixed, or suspicious tickets."""

    name: str = "other"

    def can_handle(self, triage: TriageResult) -> bool:
        """Return True when triage routed to other.

        Args:
            triage: Composed triage result.

        Returns:
            True iff ``triage.route`` is ``OTHER``.
        """
        return triage.route is Route.OTHER

    def run(self, ticket: Ticket, triage: TriageResult) -> HandlerResult:
        """Return the deterministic catch-all next step.

        Args:
            ticket: Incoming support ticket.
            triage: Composed triage result.

        Returns:
            HandlerResult queueing the ticket for human triage.
        """
        _ = triage
        return HandlerResult(
            handler=self.name,
            ticket_subject=ticket.subject,
            summary="Unclassified ticket; needs human clarification.",
            next_step="Ask a clarifying question or move to the human review queue.",
        )


register(ITAccessHandler())
register(BugReportHandler())
register(BillingHandler())
register(HRPolicyHandler())
register(OtherHandler())
