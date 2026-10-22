# Multi-Agent Legal Assistant RAG Application

Welcome to the Multi-Agent Legal Assistant Repository! This project explores advanced Retrieval-Augmented Generation (RAG) capabilities via a multi-agent orchestrated backend communicating over the Model Context Protocol (MCP), married to a beautiful, proactive React frontend.

The system is purposely designed to securely ingest, vectorize, and search case files to provide highly contextualized legal intelligence to the end user.

---

## 📖 Key Features

- **Multi-Agent RAG Orchestration**: Instead of standard linear RAG prompts, the backend splits reasoning into specialized `Planner`, `Retriever`, and `Responder` agents that self-coordinate solutions to complex queries.
- **Model Context Protocol (MCP) Interoperability**: The vector search and retrieval functionalities operate securely via separate standard IO subprocesses mimicking industry-standard MCP capabilities.
- **Proactive Insights Dashboard**: An automated six-section panel that analyzes uploaded case material and surfaces `Next Actions`, `Related Statutes`, `Checklists`, `Information Gaps`, `Deadlines`, and `Conflicts`.
- **Tenant-isolated Vector Datastores**: End-to-end data isolation matching document embeddings uniquely against authenticated user IDs (preventing contextual contamination inside ChromaDB).
- **Robust Security Constructs**: Token generation with JWTs, dual-layered CSRF token validation, HTTP-Only strict cookies, API rate limiting via `slowapi`, and file structural safety evaluations.
- **Privacy-aware Web Fallback**: If document retrieval is weak, the system can query DuckDuckGo using only the user query text (never uploaded document content), and the UI marks when this fallback was used.

---

## 📂 Project Structure

- **`Backend/`** Python/FastAPI code facilitating the main REST server, SQLite setup, ChromaDB vectorization interfaces, indexing logistics, and MCP Agent subprocesses. 
- **`Frontend/`** A React 19 + TypeScript SPA spun up with Vite addressing sophisticated UI state loops, session guarding, and CSS modular design layouts.

> Note: For incredibly low-level breakdowns of module functionality, please view:
> - [BACKEND_DOCUMENTATION.md](./BACKEND_DOCUMENTATION.md)
> - [FRONTEND_DOCUMENTATION.md](./FRONTEND_DOCUMENTATION.md)
> - [CONFIGURATION.md](./CONFIGURATION.md)
> - [DEPLOYMENT.md](./DEPLOYMENT.md)
> - [FAQ.md](./FAQ.md)

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ (with npm)
- Ollama (installed locally)
- Two downloaded Ollama Models: `gemma3:4b` and `embeddinggemma`

*(To download Ollama models, run: `ollama pull gemma3:4b` & `ollama pull embeddinggemma` in your terminal)*

### 1. Setting up the Backend

1. **Navigate to the Backend layer**:
   ```bash
   cd Backend
   ```
2. **Create a Virtual Environment** and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. **Install dependencies** (assuming `requirements.txt` is present, or manually using pip based on imports):
   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic python-multipart python-jose[cryptography] passlib[bcrypt] pypdf slowapi langchain-chroma langchain-core langchain-text-splitters langchain-community langchain-ollama ddgs
   ```
4. **Environment File**:
   Create a `.env` in the `Backend/` folder config (optional, it defaults safely):
   ```env
   DATABASE_URL=sqlite:///./users.db
   SECRET_KEY=your_super_secret_key_here
   COOKIE_SECURE=False  # Set to True if testing under HTTPS
   COOKIE_SAMESITE=Lax
   ALLOWED_ORIGINS=http://localhost:5173
   ```
5. **Boot the Backend Server**:
   ```bash
   uvicorn BackendAPI:app --host 127.0.0.1 --port 8000 --reload
   ```

### 2. Setting up the Frontend

1. **Navigate to the Frontend layer**:
   ```bash
   cd Frontend/RAGapp
   ```
2. **Install Node packages**:
   ```bash
   npm install
   ```
3. **Setup environment variables**:
   Create a `.env` in the `Frontend/RAGapp/` folder pointing to your fastapi:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```
4. **Boot the Application**:
   ```bash
   npm run dev
   ```
5. **Access the platform**: Direct your web browser to `http://localhost:5173`. Create a user account to get started!

---

## 🛠 Usage Flow

1. **Register & Log In**: Access the client interface. The secure JWT cookie bindings start immediately upon valid credentials.
2. **Upload Documents**: Open the Library tab or use the 'Book' icon at the Chat footer to upload local documents (`.pdf`, `.docx`, `.pptx`, `.txt`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`). PDF uploads also receive magic-byte and structural safety checks before ingestion.
3. **Wait for Vectorization**: LangChain reads, splits, and pipes your text chunks into ChromaDB's local filesystem structure.
4. **Ask Complex Queries**: Ask substantive questions about the files. Ensure the "Steps Visible" icon in the navigation bar is enabled to observe how the *Planner* maps out the objective, the *Retriever* hits the MCP tool interface, and the *Responder* compiles your verified citation.
5. **Review Proactive Tools**: See automated extraction alerts analyzing how tight your legal posture currently rests based on context logs. 

---

## 🌐 Web Search Fallback Behavior

- The retriever first searches uploaded documents.
- If the best document match is below relevance expectations, the workflow may call a web-search fallback.
- The fallback sends only the user query text to DuckDuckGo. Uploaded document content is not transmitted.
- The frontend explicitly indicates when web fallback was used in the response.

---

## 📌 Scope Notes (Current vs Deferred)

- **Implemented now**: local-first RAG search and drafting, citation-oriented responses, and six-section proactive insights.
- **Deferred (future work)**: simplified "explain like I'm five" legal summaries and collaborative multi-user case workspaces.

---

## 🛡 License & Content Policy

Adheres standardly to academic constraints / general open source protections. Always verify any legal output produced by the LLM (Large Language Model) against documented and cited page returns natively enclosed in the Application framework.

This repository contains software developed as part of an academic dissertation. It is a research prototype and is not a substitute for professional legal advice. Outputs may be incomplete, inaccurate, or out of date and must be independently verified. The application should not be used with confidential, personal, or legally privileged information.

All legal documents in `Backend/TestDocuments/` are fictional, synthetic test data created for this project. No real client documents or confidential case files are included.