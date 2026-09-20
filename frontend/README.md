# PulseDesk OS — Frontend

Demo console (Stitch-independent fallback). Same tokens as Stitch screens:
LIGHT, Inter/Inter, 8px radius, `#2563EB` tonal-spot.

## Design system spec

Apply this system to every Stitch screen for consistency:

- Color mode: `LIGHT`
- Headline font: `Inter`
- Body font: `Inter`
- Roundness: `ROUND_EIGHT`
- Seed color: `#2563EB`
- Color variant: `TONAL_SPOT`

## Run it

```bash
cd pulsedesk-os/frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # verified: vite build succeeds -> dist/
```

Backend first (separate terminal):
```bash
cd pulsedesk-os
export $(grep TYPESAFE_API_KEY .env | xargs)
/tmp/opencode/pdvenv/bin/python -m uvicorn backend.main:app --port 8000
```

Point the UI elsewhere with `VITE_API=http://host:8000 npm run dev`.

## What it does

Ops console with sidebar nav (Triage / Pipeline / Review / System):

- `src/api.ts` — typed backend client (`ApiError` with status+detail, `SAMPLES`).
- `src/components/ui.tsx` — chips, meters, section/empty/loading/error states.
- `src/components/TriagePanel.tsx` — composer (validated) + Jev result + samples.
- `src/components/PipelinePanel.tsx` — stage trace (triage→recall→dispatch→verify),
  draft reply, memory hits table.
- `src/components/ReviewQueue.tsx` — session queue with action filter.
- `src/components/SystemPanel.tsx` — backend status, thresholds, API reference.
- `src/App.tsx` — shell: dark sidebar (badge on Review), tabs, skip link.

## Stitch workflow (production screens)

1. Stitch MCP key lives in `/home/asus/Typesafe/.mcp.json` (server `stitch`).
2. Verify connectivity with `ListProjects` before generating anything.
3. Generate with `GenerateScreenFromText`, `deviceType: DESKTOP`, and the
   design system above.
4. Full copy-paste prompts: see `stitch-prompts.md` (Screen 1 Inbox dashboard,
   Screen 2 Triage detail, Screen 3 Review queue).

## Stitch vs fallback

- Stitch (blocked on OAuth from this session — run in your connected client):
  prompts in `stitch-prompts.md` (Inbox, Triage detail, Review queue).
- This console: unblocked now, mirrors the same three views (composer ≈
  detail, samples table ≈ inbox, session queue ≈ review queue).
