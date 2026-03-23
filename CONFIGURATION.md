# Configuration Reference

## Backend Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./users.db` | SQLAlchemy connection string for user auth database. |
| `SECRET_KEY` | none | JWT signing secret. Must be set for secure deployment. |
| `ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Session token expiry window in minutes. |
| `COOKIE_SECURE` | `True` | Marks auth/CSRF cookies as secure-only. Use `False` for local HTTP testing only. |
| `COOKIE_SAMESITE` | `lax` | Cookie SameSite policy (`lax`, `strict`, or `none`). |
| `ALLOWED_ORIGINS` | built-in localhost list | Comma-separated CORS allowlist for frontend origins. |

---

## Frontend Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | none | Base URL for backend API requests from frontend. |

Example:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## Runtime Dependencies

### Core

- FastAPI
- Uvicorn
- SQLAlchemy
- LangChain components
- ChromaDB integration
- Ollama integration

### Optional but Recommended

- `ddgs` for web-search fallback (`search_web` MCP tool).

Install example:

```bash
pip install ddgs
```

---

## Storage Locations

| Path | Purpose |
|---|---|
| `Backend/users.db` | User account database (SQLite). |
| `Backend/chroma_db/` | Persistent embedding/vector data. |
| `Backend/DocsToIngest/` | Uploaded source files organized per user ID. |

---

## Suggested Local .env (Backend)

```env
DATABASE_URL=sqlite:///./users.db
SECRET_KEY=replace_with_a_long_random_secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
COOKIE_SECURE=False
COOKIE_SAMESITE=Lax
ALLOWED_ORIGINS=http://localhost:5173
```
