# Production image: stdlib + pip, no dev deps.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY config.yaml ./
COPY backend ./backend

RUN pip install --no-cache-dir fastapi uvicorn pydantic pyyaml typesafe-sdk fastmcp

ENV MEMORY_DB=/data/memory.db
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
