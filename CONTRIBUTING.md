# Contributing to PulseDesk OS

Principles first — every PR must hold these:

1. **Code owns the workflow, Jev owns the judgments.** No LLM prose parsing in
   core logic; new decisions are `Choice`/`Noul`/`Score` questions + code gates.
2. **Frozen contracts.** Shapes change in `backend/schemas.py` (domain) or the
   request/response models in `backend/main.py` — never ad-hoc dicts. Bump `/v1`.
3. **Open/Closed.** New route = new file under `backend/handlers/` + `register()`.
   New store = implement `MemoryBackend`. Never branch core on route names.
4. **Config, not code.** Thresholds go in `config.yaml` with code fallbacks.
5. **No secrets in the repo.** Keys live in `.env` (gitignored). Run
   `./scripts/check-secrets.sh` before pushing.

## Setup

```bash
make setup   # venv + deps + frontend install + .env from template
```

## Gates (must all pass)

```bash
make test    # pytest + ruff check + mypy (backend strict)
(cd frontend && npm run build)
claude plugin validate .
./scripts/smoke.sh   # needs API on :8000 (make api)
```

## Adding things

| Add | How | Test |
|---|---|---|
| Route/handler | new file `backend/handlers/<name>.py` + `register()` | dispatch test in `tests/test_triage.py` |
| Memory backend | implement `MemoryBackend` protocol | CRUD test like `test_memory_crud_endpoints` |
| Jev question | extend builder + `compose_*` default | offline compose test, golden rerun (`evals/`) |
| Skill | `skills/<name>/SKILL.md` with `description` frontmatter | extend `tests/test_plugin.py` |
| Threshold | `config.yaml` + code fallback | default-mirrors-config test |

## PR checklist

- [ ] Gates green (paste output)
- [ ] No behavior change to gates/thresholds unless intended + evals re-run
- [ ] Docs updated if routes/contracts/thresholds changed (README, ARCHITECTURE, skills)
- [ ] `./scripts/check-secrets.sh` passes
