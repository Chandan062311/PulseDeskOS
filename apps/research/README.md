# Research App — Evidence-Backed Briefs

Second reference app proving the PulseDesk agent framework is generic:
given a topic, produce an evidence-backed brief on `<topic>` via
scout → verify → compose.

## Goal shape

- Input: a topic string, e.g. `evidence-backed brief on <topic>`.
- Output: one Markdown brief in `apps/research/work/` named
  `<slug>-brief.md`, with:
  - Summary (5 bullets max, every number cited).
  - Findings by angle (one section per scout angle).
  - Conflict table (where scouts disagree).
  - Source list (named sources with URLs).
  - What remains unknown.

## The 3 scout angles template

Fan out one read-only scout worker per angle over the same `$TOPIC`:

1. `landscape` — What is the current state of `$TOPIC`? Key players,
   definitions, recent developments.
2. `numbers` — What quantitative evidence exists for `$TOPIC`?
   Sizes, rates, trends. Every number needs a named source URL.
3. `risks-and-gaps` — What is contested, uncertain, or missing about
   `$TOPIC`? Conflicting claims, weak evidence, open questions.

Each scout reads `apps/research/prompts/scout.md`, substitutes
`$TOPIC` / `$ANGLE` / `$OUTPUT`, and writes only its own findings file
under `apps/research/work/` (e.g. `angle-landscape.md`).

## Acceptance criteria

Every brief passes only if:

1. **Named sources with URLs** — every factual claim that matters links
   to a named source with a URL in the source list. No bare links.
2. **No unsourced numbers** — every number, date, percentage, or
   quantity carries an inline citation to a named source URL.
   A finding with a number and no source fails verification.
3. **Uncertainty marked** — contested claims, single-source claims, and
   gaps are explicitly marked (`contested:`, `single-source:`,
   `unknown:`). No hedging-by-omission.

## How a supervisor runs it

1. **Route** via `backend/orchestration/router.py` — each angle is a
   read-only subtask, so the router should return worker `scout`
   (safe default for research/measurement). Escalate to a reviewer
   when `risky` is high or routing confidence is low.
2. **Fan out workers** — launch one `scout` worker per angle with the
   rendered `scout.md` prompt (`$TOPIC`, `$ANGLE`, `$OUTPUT` filled in).
   Scouts are read-only: web research + findings file only, no code edits.
3. **Verify** via `backend/orchestration/verifier.py`
   (`verifier.py`) — check each scout findings file against the
   acceptance criteria above (sources present, numbers cited,
   uncertainty marked). Retry or escalate failures.
4. **Compose** — render `apps/research/prompts/composer.md` with the
   verified findings files and run one `scribe` worker to merge them
   into the final brief (dedupe, conflict table, source list,
   what-remains-unknown).

## Where outputs go

- Scout findings: `apps/research/work/angle-<angle>.md` (intermediate).
- Final brief: `apps/research/work/<slug>-brief.md` (the deliverable).
- `apps/research/work/.gitkeep` keeps the directory in git before the
  first run; real runs add findings + brief files alongside it.
