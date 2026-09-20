# PulseDesk OS Frontend

Vite + React operations console for the PulseDesk API. It includes Triage, Pipeline,
Review, and System views and works against the offline triage path before a Jev key is
configured.

## Run it

From the repository root:

```bash
make setup
make api       # separate terminal, http://localhost:8000
make ui        # http://localhost:5173
```

Or run the frontend directly:

```bash
npm install
npm run dev
npm run build
```

Set `VITE_API=http://host:8000` when the backend is not running on localhost.

## What it includes

- `src/api.ts` — typed API client and sample tickets.
- `src/components/TriagePanel.tsx` — ticket composer, validation, and result view.
- `src/components/PipelinePanel.tsx` — orchestration stages, draft, and memory hits.
- `src/components/ReviewQueue.tsx` — session review queue with action filtering.
- `src/components/SystemPanel.tsx` — backend status, thresholds, and API reference.
- `src/App.tsx` — responsive application shell and navigation.

The production container uses nginx to serve the Vite build. See `Dockerfile` and
`vercel.json` for deployment settings.
