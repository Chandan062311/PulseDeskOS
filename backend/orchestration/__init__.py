"""Agent orchestration framework: supervisor loop over worker agents.

The product the ticket pipeline was always heading toward: code owns the
supervisor workflow (decompose -> route -> fan out -> verify -> compose)
while Jev supplies the routing and verification judgments and worker
agents (Claude subagents in this environment, any executor behind the
``Executor`` protocol elsewhere) do the scoped work.

Stages per subtask:
1. ``router`` — Jev Choice picks the worker kind, Nouls flag context/risk
   needs, Score rates difficulty. Pure compose, tested offline.
2. ``executor`` — runs the worker. In live sessions the supervisor fans out
   via parallel subagents; the protocol keeps the framework runtime-agnostic.
3. ``verifier`` — Jev checks the result against acceptance criteria.
   ``pass`` composes, ``retry`` re-runs once with feedback, ``escalate``
   goes to a human (or a reviewer worker).
4. ``trace`` — every decision is JSONL-logged with its probabilities.
"""

from __future__ import annotations
