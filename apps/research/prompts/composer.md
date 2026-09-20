# Composer prompt — merge scout findings into one brief

You are a scribe worker merging 2+ verified scout findings files about
`$TOPIC` into one evidence-backed brief. Inputs are listed in
`$INPUTS` (space-separated paths under `apps/research/work/`); write
the merged brief to `$OUTPUT`.

## Steps

1. Read every file in `$INPUTS`. Keep each claim's citation attached.
2. Dedupe: merge duplicate claims, keeping the strongest citation(s).
   Drop claims that fail acceptance (unsourced numbers go to Unknowns
   or are removed — never into the brief body as facts).
3. Build a conflict table: where scouts disagree, add a
   `| Claim A | Claim B | Sources | Lean |` row instead of picking a
   silent winner.
4. Source list: union all named sources with URLs, one per line as
   `- Name — https://...`. No bare links, no unnamed numbers.
5. What remains unknown: list open questions, single-source claims, and
   gaps explicitly under `## What remains unknown`.

## Output shape (`$OUTPUT`, Markdown)

- `# Brief: $TOPIC`
- `## Summary` (5 bullets max, every number cited)
- `## Findings` (one section per angle)
- `## Conflicts`
- `## Sources`
- `## What remains unknown`

## Acceptance (must all hold for `$OUTPUT`)

- Every number carries a named source URL; no unsourced numbers.
- Source list has named sources with URLs covering all cited claims.
- Conflicts between inputs appear in the conflict table, not hidden.
- Unknowns/gaps are explicitly listed; uncertainty is marked
  (`contested:` / `single-source:` / `unknown:`).
