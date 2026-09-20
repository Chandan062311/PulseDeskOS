# PulseDesk OS — one-command runnable.
# Uses .venv/bin tools when present (after `make setup`); falls back to PATH tools otherwise.
#   make setup  — create venv, install backend (dev), install UI deps, seed .env
#   make api    — run FastAPI on :8000
#   make ui     — run Vite dev server on :5173
#   make test   — pytest + ruff + mypy
#   make smoke  — end-to-end smoke checks (needs api, ui optional)
#   make build-ui — production build of the frontend
#   make mcp    — run the MCP server (stdio) for local clients
#   make secrets — fail on live secret material in tracked files

PY := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
UVICORN := $(if $(wildcard .venv/bin/uvicorn),.venv/bin/uvicorn,uvicorn)
PYTEST := $(if $(wildcard .venv/bin/pytest),.venv/bin/pytest,pytest)
RUFF := $(if $(wildcard .venv/bin/ruff),.venv/bin/ruff,ruff)
MYPY := $(if $(wildcard .venv/bin/mypy),.venv/bin/mypy,mypy)

.PHONY: setup api ui test smoke build-ui mcp secrets

setup:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"
	cd frontend && npm install
	test -f .env || cp .env.example .env

api:
	$(UVICORN) backend.main:app --port 8000

ui:
	cd frontend && npm run dev

test:
	$(PYTEST)
	$(RUFF) check .
	$(MYPY) .

smoke:
	bash scripts/smoke.sh

build-ui:
	cd frontend && npm run build

mcp:
	$(PY) -m backend.mcp_server

secrets:
	bash scripts/check-secrets.sh .
