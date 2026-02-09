# RAGapp — Local Retrieval-Augmented Generation

A small RAG (Retrieval-Augmented Generation) demo that combines:
- **Backend**: FastAPI API with Chroma vector store for semantic search and retrieval
- **Ingestion**: Pipeline for processing PDFs and creating embeddings
- **Frontend**: React + Vite UI for querying documents

## Quick Start

### Backend
1. Create a Python venv and install dependencies (`pip install -r requirements.txt` or similar)
2. Set up [Backend/.env](Backend/.env) with your configuration and API keys
3. Ingest documents by placing PDFs in [Backend/DocsToIngest/](Backend/DocsToIngest/), then run `run_ingestion()` in [Backend/ingest.py](Backend/ingest.py)
4. Start the API:
   ```sh
   uvicorn Backend.BackendAPI:app --reload --port 8000
   ```

### Frontend
1. Navigate to `Frontend/RAGapp`
2. Install dependencies: `npm install`
3. Start dev server: `npx vite --host` (or `npm run dev`)
4. The frontend will connect to the backend API running on `localhost:8000`

## Requirements
- Python 3.10+
- Node 16+

## Architecture

### Backend Modules
- [Backend/BackendAPI.py](Backend/BackendAPI.py) — FastAPI endpoints and PDF validation (`is_pdf_safe`)
- [Backend/index.py](Backend/index.py) — `RAGEngine` class for querying Chroma and formatting results
- [Backend/ingest.py](Backend/ingest.py) — Document pipeline: PDF splitting, OCR fallback, embeddings
- [Backend/chroma_db/chroma.sqlite3](Backend/chroma_db/chroma.sqlite3) — Vector database (persisted)

### Frontend Components
- Entry point: [Frontend/RAGapp/src/main.tsx](Frontend/RAGapp/src/main.tsx)
- Root: [Frontend/RAGapp/src/App.tsx](Frontend/RAGapp/src/App.tsx)
- Pages:
  - [Frontend/RAGapp/src/Login/Login.tsx](Frontend/RAGapp/src/Login/Login.tsx)
  - [Frontend/RAGapp/src/Register/Register.tsx](Frontend/RAGapp/src/Register/Register.tsx)
  - [Frontend/RAGapp/src/Search/Search.tsx](Frontend/RAGapp/src/Search/Search.tsx)
- Auth helper: [Frontend/RAGapp/src/useAuth.ts](Frontend/RAGapp/src/useAuth.ts)

## Common Workflows

**Ingest new documents:**
- Place PDFs in [Backend/DocsToIngest/](Backend/DocsToIngest/)
- Call `run_ingestion()` from [Backend/ingest.py](Backend/ingest.py)
- Documents are split, embedded, and stored in Chroma

**Query documents:**
- Frontend calls API endpoints ([Backend/BackendAPI.py](Backend/BackendAPI.py))
- Backend retrieves context from Chroma via `RAGEngine.query()` ([Backend/index.py](Backend/index.py))
- Results are formatted and returned to frontend

## Configuration & Security

- **Secrets**: [Backend/.env](Backend/.env) contains API keys and config. **Do not commit.** Add `.env` to `.gitignore` immediately.
- **Embedding provider**: To change embeddings, update [Backend/ingest.py](Backend/ingest.py) and reinitialize the vector store
- **CORS**: Configure as needed in [Backend/BackendAPI.py](Backend/BackendAPI.py)
- **PDF safety**: The `is_pdf_safe()` function validates uploads (see [Backend/BackendAPI.py](Backend/BackendAPI.py))

## Multi-Agent Workflow (MCP)

This project includes a **Model Context Protocol (MCP)** based multi-agent system for complex queries.

### Architecture

```
User Query → Planner Agent → Retriever Agent → Responder Agent → Final Answer
                   ↓              ↓                  ↓
              [MCP Server] ← JSON-RPC (stdio) → [RAG Tools]
```

### Components

| File | Description |
|------|-------------|
| `Backend/mcp_server.py` | MCP server process exposing RAG tools |
| `Backend/mcp_tools.py` | Tool definitions (search, list, answer) |
| `Backend/agents.py` | Agent coordinator with planner/retriever/responder |

### Running the Multi-Agent System

The MCP server is **automatically spawned** by the agent coordinator when you trigger a workflow. You only need to run the FastAPI backend and frontend.

**Terminal 1 — FastAPI Backend:**
```bash
cd Backend
uvicorn BackendAPI:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd Frontend/RAGapp
npm run dev
```

**Optional — Test MCP Server:**
```bash
cd Backend
python3 mcp_server.py --test
```

### Using Multi-Agent Mode

1. Login to the app
2. Click **"Agent Mode"** button in the navbar (turns blue when active)
3. Type your question in the search box
4. Click **"Run Multi-Agent"** button
5. Watch the agent steps appear in real-time:
   - **Planner**: Analyzes query and creates plan
   - **Retriever**: Searches documents via MCP tools
   - **Responder**: Generates final cited answer

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workflow/start` | POST | Start async workflow, returns `workflow_id` |
| `/workflow/status/{id}` | GET | Poll for status and agent steps |
| `/workflow/list` | GET | List recent workflows for user |

See [Backend/BACKEND_DOCUMENTATION.md](Backend/BACKEND_DOCUMENTATION.md) for full API docs.

## Development Notes

- User-scoped operations (file listing, deletion) are handled by `RAGEngine` methods in [Backend/index.py](Backend/index.py)
- RAG result formatting is in `RAGEngine.format_chroma_docs()` ([Backend/index.py](Backend/index.py))
- Keep frontend (`localhost:3000`) and backend (`localhost:8000`) ports in sync

## Contributing

1. Add PDFs to [Backend/DocsToIngest/](Backend/DocsToIngest/) and run ingestion
2. If modifying the schema or embedding logic, update [Backend/ingest.py](Backend/ingest.py)
3. Rotate any exposed API keys immediately

## License

Project-level license not set — add a LICENSE file if needed.


