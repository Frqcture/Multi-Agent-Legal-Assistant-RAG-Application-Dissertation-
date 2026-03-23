# Deployment Guide

## Scope

This guide covers practical deployment patterns for the current project:

1. Local single-machine deployment (recommended baseline).
2. Single-clinic self-hosted deployment on one server.

The current architecture is local-first and optimized for low-cost operation rather than cloud-scale throughput.

---

## 1. Local Single-Machine Deployment

### Prerequisites

- Python 3.10+
- Node.js 18+
- Ollama installed and running
- Models pulled locally:
  - `ollama pull gemma3:4b`
  - `ollama pull embeddinggemma`

### Backend

```bash
cd Backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy pydantic python-multipart python-jose[cryptography] passlib[bcrypt] pypdf slowapi langchain-chroma langchain-core langchain-text-splitters langchain-community langchain-ollama ddgs
uvicorn BackendAPI:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd Frontend/RAGapp
npm install
npm run dev
```

Set frontend API target in `Frontend/RAGapp/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 2. Single-Clinic Self-Hosted Deployment

### Deployment Notes

- Run backend and frontend behind HTTPS.
- Set `COOKIE_SECURE=True` in production.
- Restrict CORS using `ALLOWED_ORIGINS`.
- Keep Ollama on the same private host as backend to preserve local-first privacy assumptions.

### Suggested Runtime Layout

- Backend API process (FastAPI/Uvicorn)
- Frontend static host (or Vite preview for internal use)
- Ollama daemon
- Persistent storage:
  - SQLite file (`users.db` by default)
  - Chroma directory (`Backend/chroma_db`)
  - Uploads (`Backend/DocsToIngest`)

---

## 3. Backup and Recovery

Back up these paths regularly:

- `Backend/users.db`
- `Backend/chroma_db/`
- `Backend/DocsToIngest/`

Recommended schedule:

1. Nightly incremental backup.
2. Weekly full snapshot.

Recovery sequence:

1. Restore `users.db`.
2. Restore `chroma_db` and `DocsToIngest`.
3. Restart backend and verify `/me` and `/files` endpoints.

---

## 4. Security Hardening Checklist

1. Use HTTPS and secure reverse proxy.
2. Set strong `SECRET_KEY`.
3. Set `COOKIE_SECURE=True`.
4. Restrict `ALLOWED_ORIGINS` to trusted frontend hostnames.
5. Limit host-level access to backend and Ollama ports.
6. Monitor rate-limit responses and failed auth attempts.

---

## 5. Current Deployment Limits

- SQLite and local vectorstore are suitable for low-concurrency clinic use.
- Multi-tenant, high-concurrency, or internet-facing scale may require:
  - external database,
  - stronger observability,
  - process supervision,
  - and infrastructure hardening beyond this dissertation scope.
