# Development Journal

A chronological log of changes made to this codebase, derived from git commit history and code diffs.

---

## 2025-10-25

- **First commit** — Basic file structure established and the beginning of the MVP committed. Included an initial ChromaDB vector store pre-populated with data.
- **Base code added** — Core backend files committed: a LangChain-based RAG pipeline (`index.py`) wiring together a ChromaDB vector store, OllamaEmbeddings, and a ChatOllama LLM into a retrieval chain.
- **User input branch** — Multiple commits to make user query input functional end-to-end.
- **Merged `userInput` into `main`.**
- **Merged `ingest` into `main`.**

---

## 2025-10-28

- **Re-organised** the project structure in preparation for a basic frontend for user interviews.
- **Started creating a basic frontend** — Very first page setup.

---

## 2025-10-30

- **Updated VectorDB** to include all data for ML Week 4.
- **Created a Next.js application** as the initial frontend scaffold.
- **Tested rich text input** in the prototype frontend.
- **Started further basic frontend additions.**
- **Deleted `.env`** file from version control.

---

## 2025-10-31

- **Edited `.gitignore`** to improve ignored file coverage.
- **Fixed git issues** that had arisen.

---

## 2025-12-16

- **Test commit** to verify repository–remote connectivity (against `git.cs.bham.ac.uk`).
- **Set up `.gitignore`** for the project.

---

## 2025-12-21

- **Framework switched from Next.js to Vite + React** — A fresh React/TypeScript application was created with Vite as the build tool.
- **Basic FastAPI API scaffolded** — Created `BackendAPI.py` with initial endpoints, wired up to the existing LangChain RAG pipeline, prior to any testing.
- **Final corrections** made before testing.
- **API tested and confirmed working** — Also added a `/refresh` endpoint to reload the vector store when new documents are added.
- **Final touches to the API** for this phase of development.

---

## 2025-12-22

- **Very basic frontend built** — Foundation of the React application laid (search input, basic layout). More work noted as needed.
- **Removed non-essential files** from the repository.
- **Fixed visual problems** — Corrected width restrictions in `index.css`.
- **Frontend-to-backend communication working** — Confirmed queries flow from the React frontend to the FastAPI backend when both dev servers are running.

---

## 2025-12-27

- **Message-style chat UI added** — The search page now renders conversation history, displaying both the user's input and the model's response in a chat bubble layout, and showing recent message history.
- **Final frontend tweaks** before planning user interviews.

---

## 2025-12-30

- **Document upload feature implemented** — A `/upload` endpoint added to `BackendAPI.py` to accept a PDF, save it to disk, and trigger ingestion into the ChromaDB vector store. The frontend gained an upload control wired to this endpoint.
- **Document upload confirmed working** — Testing complete with a real PDF.

---

## 2025-12-31

- **Per-user system and login screen added** — A `database.py` module introduced using SQLAlchemy with a SQLite `users.db`. A `models.py` User model defined. The `/login` endpoint updated to issue a JWT access token. A login page added to the React frontend. Mostly functioning; new-user registration page still outstanding.
- **Database fully integrated** — Separate per-user login system complete except for the registration page. Per-user data isolation hooked into the ChromaDB queries (filtering by `user_id` metadata).

---

## 2026-01-03

- **User registration page added** — A new React `Register` component created with a form, routed via React Router, with a link from the login screen.
- **Merged `perUserSetup` into `main`.**

---

## 2026-01-14

- **Fixed a small upload issue.**
- **Basic `/upload` endpoint security implemented** — File type validation (PDF-only), file size cap, and path traversal checks (`os.path.basename` / path prefix assertion) added.
- **Upload security hardened further** — Additional input sanitisation added.
- **PDF content safety check added** — A check that validates the PDF magic bytes (`%PDF-` header) to guard against disguised malicious files.

---

## 2026-01-23

- **All LLM and embedding models migrated to run locally via Ollama and LangChain** — Replaced `OpenAIEmbeddings` (model `text-embedding-3-small`) with `OllamaEmbeddings` (model `embeddinggemma`), and replaced `ChatOpenAI` (GPT) with `ChatOllama` (model `gemma3:4b`). This removed the dependency on external paid inference APIs.

---

## 2026-01-24

- **Rate limiting added with SlowAPI** — `slowapi.Limiter` integrated and applied to all key endpoints: `/login` (5/min), `/register` (5/min), `/ask` (20/min), `/refresh` (5/min), `/upload` (5/min). A `RateLimitExceeded` exception handler registered with the app.
- **Merged `RateLimiting` into `main`.**
- **Document referencing fixed** — In `ingest.py`, page number metadata (`page_number`) is now attached to each document chunk *before* splitting, so it propagates correctly to every chunk. The RAG chain now accurately cites document name and page number in responses.
- **Merged `FixingReferencing` into `main`.**
- **List and Delete Files feature started** — Initial backend endpoints and frontend UI work begun to let users view and remove their uploaded documents.
- **List and Delete Files feature completed** — Fully tested and working; users can see their uploaded files and delete them (removing from disk and ChromaDB).
- **Merged `ViewAndDeleteFiles` into `main`.**

---

## 2026-01-27

- **Auth tokens migrated from `localStorage` to HTTP-only cookies** — The `/login` endpoint now calls `response.set_cookie(key="access_token", httponly=True, samesite="lax")` instead of returning the token in the JSON body. The frontend's `Login.tsx` no longer stores the token in `localStorage`; all subsequent API calls use `credentials: 'include'` instead of an `Authorization` header. A new `useAuth` hook introduced in `useAuth.ts` to check authentication state by calling a new `/me` endpoint on mount. CORS `allow_origins` narrowed from `"*"` to `["http://localhost:5173"]`.

---

## 2026-01-30

- **Cookie-based auth confirmed working** — System functional end-to-end; logout method noted as still needing updating.
- **Logout updated** — Logout method corrected to clear the `access_token` cookie rather than clearing `localStorage`.
- **Merged `authTokenInCookies` into `main`.**

---

## 2026-02-02

- **Residual cookie-auth bugs fixed** — Cleaned up loose ends left over from the `localStorage` → cookie migration (e.g. stale token header references in fetch calls).

---

## 2026-02-03

- **Login and registration page styling updated** — Visual alignment improved so the login and register pages share a coherent style with the search page.
- **Merged `stylingUpdate` into `main`.**
- **Multi-PDF upload supported** — The `/upload` endpoint signature changed from `file: UploadFile` to `files: List[UploadFile]`. The frontend's upload handler renamed from `uploadPDF` to `uploadPDFs` and updated to send a `FileList`. The backend loops over all uploaded files, validates and saves each, then triggers a single ingestion pass for the whole batch.

---

## 2026-02-04

- **OCR pipeline work started** — `ingest.py` extended with optional imports for `python-docx`, `python-pptx`, `Pillow`/`cv2`, `pytesseract`, and `pdf2image`, each guarded by a try/except so the app degrades gracefully if a library is absent.
- **OCR fully working** — A `load_pdf_with_timeout` helper introduced that runs `PyPDFLoader` with `RapidOCRBlobParser` in a background thread with a configurable timeout (default 30 s), preventing hangs on scanned or malformed PDFs. Support for `.docx`, `.pptx`, images, and scanned PDFs confirmed working across a range of test files.
- **Merged `ocrImplementation` into `main`.**
- **Refactoring completed** and merged.
- **Backend documentation written** (`BACKEND_DOCUMENTATION.md`) covering all API endpoints, the RAG pipeline, and the ingestion flow.
- **Documentation improved** with additional detail and examples.

---

## 2026-02-09

- **First multi-agent pipeline implemented** — `agents.py` created from scratch. Introduced `WorkflowStatus`, `AgentRole`, `AgentStep`, and `WorkflowState` dataclasses. A `Coordinator` class orchestrates three agents in sequence: **Planner** (lists available docs), **Retriever** (calls ChromaDB via the MCP server subprocess), **Responder** (calls `ChatOllama` to synthesise an answer from retrieved chunks). `mcp_server.py` and `mcp_tools.py` added to expose retrieval as MCP-compatible tools. Three new endpoints added to `BackendAPI.py`: `POST /workflow/start` (returns a `workflow_id`), `GET /workflow/status/{id}` (polls step-by-step progress), `GET /workflow/list`. The `Search.tsx` frontend updated to display the agent step log.
- **Issues fixed** — Multiple follow-up commits to resolve bugs discovered during testing of the agent pipeline.

---

## 2026-02-10

- **Deleted `.env`** accidentally committed file removed.
- **Convenience updates** — `.gitignore` updated; a `.env` file added for the Vite frontend to configure the backend URL.

---

## 2026-02-11

- **Demo changes** — Minor tweaks made ahead of a live demonstration.
- **Merged `multiAgentTest` into `main`** (after resolving `.env` conflict).
- **Proactive Insights Dashboard introduced** — A new `POST /proactive-insights` endpoint added to `BackendAPI.py`. It samples six document chunks from the user's ChromaDB collection, feeds them into a single `ChatOllama` (`gemma3:4b`) call with a structured prompt, and returns four insight panels as JSON: `next_actions`, `related_statutes`, `checklist`, and `info_gaps`. Results are cached for 1 hour (reduced to 2 min during debugging, later restored). Rate limited to 10 req/min. A new `ProactiveDashboard.tsx` React component renders the four panels on the search page when no conversation is active. `ProactiveDashboard.module.css` added for styling.
- **Documentation updated** to document the Proactive Insights architecture and API contract.
- **Merged `proactivity` into `main`.**
- **Security substantially hardened** — Added CSRF protection: a `csrf_token` cookie set on every response, with a `_require_csrf` dependency that validates the `x-csrf-token` request header against the cookie on all state-changing methods (POST/PUT/PATCH/DELETE). `ALLOWED_ORIGINS` made configurable via an `ALLOWED_ORIGINS` environment variable instead of hardcoded. `COOKIE_SECURE` and `COOKIE_SAMESITE` made environment-configurable. A `_get_user_upload_dir` helper introduced that isolates each user's uploads to a per-user subdirectory and re-validates the resolved path to prevent directory traversal. File upload rewritten to stream content in 1 MB chunks with a hard `max_bytes` cap (`_save_upload_file`). Added `_looks_like_pdf` magic-byte check. The `secrets` module used to generate CSRF tokens. `ALLOWED_ORIGINS` narrowed to localhost only unless overridden by env.
- **Merged `securityCheckingUpdating` into `main`.**
- **Styling updated** — `ProactiveDashboard.module.css`, `Search.module.css`, `Search.tsx`, and `index.css` updated to align visuals with the new proactive dashboard and agent step display.

---

## 2026-02-26

- **General updates** — Python `__pycache__` files and ChromaDB binary updated; stale `node_modules` lock file removed.
- **`.gitignore` extended** — Additional patterns added (e.g. to exclude `node_modules` subtrees that had slipped in).
- **Merged `stylingUpdate` into `main`.**

---

## 2026-03-02

- **Cleanup: outdated files deleted** — Removed old copies of `README.md`, `UML_UPDATES.md`, `structure.uml`, a legacy `README - old.md`, the Vite app's own `README.md`, and the entire `BACKEND_DOCUMENTATION.md` from inside the `Backend/` folder (content was being reorganised at root level). `agents 2.py` and `mcp_tools 2.py` (duplicate working copies) also deleted.
- **`/ask` endpoint overhauled** — The endpoint previously called `ragApp.query(...)` directly. It now instantiates the multi-agent `Coordinator` and calls `coordinator.run_query(query, user_id)`, returning `answer`, `steps`, and `status`. The old polling workflow endpoints (`/workflow/start`, `/workflow/status/{id}`, `/workflow/list`) removed. The `Coordinator` gained a synchronous `run_query` method that runs the full Planner → Retriever → Responder pipeline in one awaited call. The `Search.tsx` frontend updated to handle the new response shape (including the `steps` array) and a new `Search.module.css` written to style the step log.
- **Documentation rewritten** — `BACKEND_DOCUMENTATION.md`, `FRONTEND_DOCUMENTATION.md`, and `README.md` fully regenerated at the repo root to reflect the current architecture (multi-agent pipeline, CSRF, cookie auth, OCR, proactive insights).
- **Merged `cleanup` into `main`.**
- **UML diagrams added** — `structure.uml`, `simpleStructure.uml`, and `completeStructure.uml` committed at repo root, providing class/component diagrams of the full system.

---

## 2026-03-03

- **Web search fallback implemented** — `agents.py` extended with a `_run_web_search_fallback` method on the `Coordinator`. After the Retriever step runs ChromaDB retrieval, a relevance threshold (`RELEVANCE_THRESHOLD = 1.0`) is applied to the best cosine/L2 score. If no sufficiently relevant chunks are found, the agent falls back to a DuckDuckGo web search (via the `ddgs` library, run in a thread executor to avoid blocking the asyncio event loop), fetching up to 5 results. Results are attached to `WorkflowState` as `web_sources` and a `used_web_search` flag. The `/ask` endpoint response now includes `web_searched` and `web_sources` fields. `BackendAPI.py` and `Search.tsx` updated accordingly. The `ProactiveDashboard` and `Search` components gained coloured background styling per insight card.  `mcp_tools.py` updated with a `search_web` tool registration. Duplicate `BACKEND_DOCUMENTATION 2.md`, `FRONTEND_DOCUMENTATION 2.md`, `README 2.md`, and `Workflow 2.tsx` / `Workflow.module 2.css` files committed (working copies).
- **Web search sensitivity tuned** — A single-line change in `agents.py` adjusted the relevance threshold to improve the agent's judgement about when local documents are sufficient vs. when to fall back to the web.
- **Merged `addFeatures` into `main`.**
- **New user-value features added** (`featuresForUserValue` branch) — The proactive insights prompt expanded from 4 to **6 insight sections**, adding `deadlines` (statutory/filing deadlines extracted from documents) and `conflicts` (cross-referencing party names across documents to flag potential conflicts of interest). A `section_relevance` scoring system introduced: the LLM rates each section 0–1; scores are boosted if the section has content, and the **top 4 sections by relevance** are selected as `visible_sections` for display. A `jurisdiction` field added (detected from court names, statute references, and legal terminology in the documents). A **Drafter agent** added: the `Planner` now uses an LLM call to classify the intent as either `"draft"` (generate a legal document) or `"query"` (answer a question); if `"draft"`, the new `_run_drafter` method runs instead of `_run_responder`, using `ChatOllama` at `temperature=0.3` and `num_predict=2048`. `asyncio.wait_for` timeouts applied to the insights LLM (120 s) and the query-classifier LLM (15 s), with graceful fallbacks on timeout. `num_predict` for insight generation increased from 1024 to 2048.
- **Features fixed and finalised** — Timeout handling polished; minor bugs resolved.
- **Merged `featuresForUserValue` into `main`.**

---

## Research References

The following trusted academic and standards sources support the architectural and design decisions documented above. Each entry is mapped to the relevant decision(s) in the journal.

---

### 1. RAG Architecture

**Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." *Advances in Neural Information Processing Systems (NeurIPS 2020)*.** arXiv:2005.11401. https://arxiv.org/abs/2005.11401

> Establishes the foundational RAG approach: a parametric seq2seq model combined with a non-parametric dense vector index. Directly justifies use of ChromaDB + Ollama embeddings to ground LLM responses in user-uploaded legal documents rather than relying on model weights alone.

---

### 2. Vector Database & Dense Retrieval (ChromaDB / HNSW)

**Malkov, Yu. A., & Yashunin, D. A. (2016/2018). "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs." *IEEE Transactions on Pattern Analysis and Machine Intelligence (TPAMI)*.** arXiv:1603.09320. https://arxiv.org/abs/1603.09320

> Describes the HNSW graph-based approximate nearest-neighbour algorithm that underpins ChromaDB's similarity search. Justifies the choice of a vector store for semantic retrieval of legal document chunks at scale, with logarithmic complexity scaling.

**Karpukhin, V., Oğuz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., & Yih, W-t. (2020). "Dense Passage Retrieval for Open-Domain Question Answering." *EMNLP 2020*.** arXiv:2004.04906. https://arxiv.org/abs/2004.04906

> Demonstrates that dense embedding-based retrieval substantially outperforms sparse BM25 retrieval for knowledge-intensive NLP tasks. Supports the decision to use `OllamaEmbeddings` + ChromaDB rather than keyword search for retrieving relevant legal document passages.

---

### 3. Multi-Agent Pipeline (Planner → Retriever → Responder / Drafter)

**Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2022). "ReAct: Synergizing Reasoning and Acting in Language Models." *ICLR 2023*.** arXiv:2210.03629. https://arxiv.org/abs/2210.03629

> Introduces the ReAct pattern of interleaving reasoning traces with concrete actions (tool calls). Directly justifies the multi-agent `Coordinator` design in `agents.py`: the Planner reasons about which documents are available, the Retriever acts by querying ChromaDB/MCP tools, and the Responder/Drafter synthesises a grounded answer. ReAct-style architectures are also shown to reduce hallucination by anchoring LLM outputs to retrieved evidence.

**Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., Chen, Z., Tang, J., Chen, X., Lin, Y., Zhao, W. X., Wei, Z., & Wen, J-R. (2023). "A Survey on Large Language Model based Autonomous Agents." *Frontiers of Computer Science, 18(6)*.** arXiv:2308.11432. https://arxiv.org/abs/2308.11432

> Comprehensive survey of LLM-based autonomous agent architectures covering planning, memory, and tool use. Provides broader academic grounding for the Planner/Retriever/Responder/Drafter architecture used in `agents.py`, including the use of asyncio timeouts for fault-tolerant agent orchestration.

---

### 4. Web Search Fallback / Hybrid RAG

**Izacard, G., Lewis, P., Lomeli, M., Hosseini, L., Petroni, F., Schick, T., Dwivedi-Yu, J., Joulin, A., Riedel, S., & Grave, E. (2022). "Atlas: Few-shot Learning with Retrieval Augmented Language Models."** arXiv:2208.03299. https://arxiv.org/abs/2208.03299

> Demonstrates that retrieval-augmented LMs dramatically outperform pure parametric models on knowledge-intensive tasks, and that the quality of the retrieval index determines answer faithfulness. Supports the decision to implement a web-search fallback (DuckDuckGo via `ddgs`) when the local ChromaDB index is insufficient — ensuring the model always has access to grounding evidence rather than hallucinating.

---

### 5. Hallucination Mitigation (Source + Page Citation)

**Maynez, J., Narayan, S., Bohnet, B., & McDonald, R. (2020). "On Faithfulness and Factuality in Abstractive Summarization." *ACL 2020*.** arXiv:2005.00661. https://arxiv.org/abs/2005.00661

> Quantifies that neural abstractive models hallucinate substantially — producing content unfaithful to source documents — and that grounding generation in retrieved source text is the most effective mitigation strategy. Directly justifies the design decision to attach `document_name` and `page_number` metadata to every ChromaDB chunk and to include explicit citations in all LLM responses, which is especially critical in the legal domain where citations are professionally and ethically required.

---

### 6. LLMs in the Legal Domain

**Bommarito II, M., & Katz, D. M. (2022). "GPT Takes the Bar Exam."** arXiv:2212.14402. https://arxiv.org/abs/2212.14402

> Documents the performance of GPT-3.5 on the US Bar Exam, showing that large language models are approaching professional legal competence. Provides the research context motivating this project — LLMs have demonstrated genuine legal reasoning capability, making RAG-based legal assistants a practically meaningful application. Also highlights the importance of accuracy and grounding, as errors in legal contexts carry professional consequences.

**Susskind, R. (2017). *Tomorrow's Lawyers: An Introduction to Your Future* (2nd ed.). Oxford University Press.**

> The leading academic reference for the transformation of the legal profession through technology. Establishes both the commercial and ethical imperative for AI-assisted legal tools: increasing access to justice, reducing cost of routine legal tasks, and supporting lawyers in information-intensive workflows — the exact use case this system addresses.

---

### 7. Local / On-Premise LLMs for Legal Data Privacy

**UK Data Protection Act 2018 (implementing UK GDPR post-Brexit). ICO (Information Commissioner's Office). https://ico.org.uk/for-organisations/dp-at-the-end-of-the-transition-period/data-protection-and-the-eu-in-detail/the-uk-gdpr/**

> Mandates that personal data (including legally privileged client information) must be processed lawfully, with appropriate technical and organisational measures. Sending client-sensitive legal documents to third-party cloud APIs would constitute data transfer outside the controller's processing environment, raising compliance concerns. Justifies the architectural decision (2026-01-23) to migrate from OpenAI's cloud APIs (`ChatOpenAI`, `OpenAIEmbeddings`) to local Ollama models (`gemma3:4b`, `embeddinggemma`) running entirely on-premise.

**Solicitors Regulation Authority (SRA). (2019). *SRA Code of Conduct for Firms 2019*. https://www.sra.org.uk/solicitors/standards-regulations/code-conduct-firms/**

> Under Principle 6 (behaving in a way that maintains the trust the public places in solicitors) and Standard 2.1 (keeping clients' affairs confidential), solicitors have a professional duty of confidentiality over client data. Transmitting client documents to external APIs without explicit client consent would breach this duty. Supports the local-LLM decision and the per-user data isolation architecture.

---

### 8. Per-User Data Isolation

The per-user architecture (separate upload directories, ChromaDB metadata filtering by `user_id`) is supported by:

- **SRA Code of Conduct for Firms 2019** (see §7 above) — confidentiality obligations require strict separation of client data between different users/clients on the same system.
- **UK GDPR / Data Protection Act 2018** — principle of data minimisation: each user should only be able to access their own personal/client data, not other users'.

---

### 9. JWT Authentication

**Jones, M., Bradley, J., & Sakimura, N. (2015). *JSON Web Token (JWT)*. Internet Engineering Task Force (IETF), RFC 7519.** https://datatracker.ietf.org/doc/html/rfc7519

> Defines the JWT standard used to implement stateless session tokens in this application. JWTs allow the FastAPI backend to authenticate users without server-side session storage, issuing a signed token at login that encodes `user_id` and is verified on each subsequent request.

---

### 10. HTTP-Only Cookies vs. localStorage (XSS Prevention)

**OWASP. *Session Management Cheat Sheet*. OWASP Cheat Sheet Series.** https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html

> Specifies that the `HttpOnly` cookie attribute "instructs web browsers not to allow scripts (e.g. JavaScript) an ability to access the cookies via the DOM document.cookie object. This session ID protection is mandatory to prevent session ID stealing through XSS attacks." Directly justifies the 2026-01-27 migration from `localStorage` (accessible to JavaScript, vulnerable to XSS token theft) to HTTP-only cookies in `BackendAPI.py`.

---

### 11. CSRF Double-Submit Cookie Pattern

**OWASP. *Cross-Site Request Forgery Prevention Cheat Sheet*. OWASP Cheat Sheet Series.** https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html

> Documents the double-submit cookie pattern implemented in the 2026-02-11 security hardening: a `csrf_token` cookie (generated with `secrets.token_hex`) is set in every response, and the `x-csrf-token` request header must match the cookie value on all state-changing methods (POST/PUT/PATCH/DELETE). OWASP confirms this pattern is appropriate for stateless APIs where server-side token storage is impractical. The `secrets` module usage aligns with OWASP's requirement for cryptographically unpredictable token values.

---

### 12. API Rate Limiting (SlowAPI)

**OWASP. *OWASP API Security Top 10 2023*. API4:2023 — Unrestricted Resource Consumption.** https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/

> "Satisfying API requests requires resources such as network bandwidth, CPU, memory, and storage. Successful attacks can lead to Denial of Service or an increase of operational costs." Directly justifies the SlowAPI rate limits applied from 2026-01-24: `/login` and `/register` (5 req/min) to prevent credential-stuffing, `/ask` (20 req/min) and `/proactive-insights` (10 req/min) to prevent LLM resource exhaustion, and `/upload` (5 req/min) to prevent storage abuse.

---

### 13. File Upload Security (Magic Bytes, Path Traversal, Size Cap)

**OWASP. *File Upload Cheat Sheet*. OWASP Cheat Sheet Series.** https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html

> Specifies a defence-in-depth approach for file uploads: (a) validate the file's MIME type and do not rely on the `Content-Type` header alone ("don't trust the Content-Type header as it can be spoofed"), (b) validate file signatures/magic bytes, (c) restrict filenames to safe characters and prevent path traversal, (d) set file size limits. Directly justifies the `_looks_like_pdf()` magic-byte check (`%PDF-` header validation), `os.path.basename()` + path prefix assertion to prevent directory traversal, and the `max_bytes` streaming cap in `_save_upload_file()` implemented from 2026-01-14 and hardened on 2026-02-11.

---

### 14. OCR for Multi-Format Legal Document Ingestion

**Smith, R. (2007). "An Overview of the Tesseract OCR Engine." *Proceedings of the 9th International Conference on Document Analysis and Recognition (ICDAR 2007)*, pp. 629–633. IEEE.**

> Describes the Tesseract OCR engine, which is the basis for the `pytesseract` library used in `ingest.py`. Establishes OCR as a mature and reliable technology for extracting text from scanned documents — directly relevant to the legal domain where many historical documents exist only as scanned images. Justifies the 2026-02-04 decision to introduce the `load_pdf_with_timeout` helper with RapidOCR/pytesseract for scanned PDF handling, enabling ingestion of document types common in legal practice.

---

### 15. Proactive AI Assistance in Legal Practice

**Susskind, R. (2017). *Tomorrow's Lawyers: An Introduction to Your Future* (2nd ed.). Oxford University Press.**

> See §6 above. Susskind argues that "latent legal market" demand significantly exceeds what the traditional legal profession can service through billable-hour models, and that proactive, AI-driven legal guidance systems are the pathway to broader access to justice. The Proactive Insights Dashboard (6 panels: `next_actions`, `related_statutes`, `checklist`, `info_gaps`, `deadlines`, `conflicts`) embodies this vision by surfacing actionable intelligence from uploaded legal documents before the user even asks a question.

---

### 16. Conflict of Interest Detection

The `conflicts` panel in the Proactive Insights Dashboard cross-references party names across documents to flag potential conflicts of interest. This aligns with:

- **SRA Code of Conduct for Firms 2019, Standard 6.1**: "You do not act if there is an own interest conflict or a significant risk of such a conflict." Automated conflict detection provides a first-pass screening tool to assist solicitors in meeting this professional obligation.

---

### 17. Deadline Extraction from Legal Documents

The `deadlines` panel extracts statutory and filing deadlines from uploaded documents. This is grounded in:

- **SRA Code of Conduct for Solicitors, REL, and RFLs 2019, Standard 3.3**: Solicitors must ensure that clients receive a proper service, which includes being informed of critical deadlines. Deadline extraction supports this by making deadline information immediately visible rather than requiring manual document review.

---

### 18. LLM for Legal Document Drafting (Drafter Agent)

**Bommarito II, M., & Katz, D. M. (2022). "GPT Takes the Bar Exam."** arXiv:2212.14402. (See §6 above.)

> Demonstrates LLMs' legal drafting capability. The Drafter agent (`_run_drafter`, `temperature=0.3`, `num_predict=2048`) uses a lower temperature than the Responder to produce more controlled, less creative output appropriate for legal document generation, balancing fluency with predictability.

---

### 19. FastAPI Framework

**Ramírez, S. (2018–present). *FastAPI*. https://fastapi.tiangolo.com/**

> FastAPI's combination of Python type hints, automatic OpenAPI documentation, async/await support, and Pydantic validation makes it well-suited for building a performant AI-backend REST API. The async nature is critical for the multi-agent pipeline — `asyncio.wait_for` timeouts and thread-executor-based blocking operations (DuckDuckGo search, OCR) require an async event loop.

---

### 20. React / TypeScript Frontend

**Meta Open Source. *React*. https://react.dev/**
**Microsoft. *TypeScript*. https://www.typescriptlang.org/**

> React's component model enables the modular UI architecture used here (`Search.tsx`, `ProactiveDashboard.tsx`, `Login.tsx`, `Register.tsx`). TypeScript's static typing reduces runtime errors in the frontend — important when handling complex API response shapes such as the `steps` array from the multi-agent pipeline and the 6-panel proactive insights object. The `useAuth` hook pattern leverages React's composability for authentication state management.

---

### Summary Table

| Decision | Primary Reference(s) |
|---|---|
| RAG architecture | Lewis et al. 2020 (arXiv:2005.11401) |
| ChromaDB / HNSW vector search | Malkov & Yashunin 2018 (arXiv:1603.09320) |
| Dense embedding retrieval | Karpukhin et al. 2020 (arXiv:2004.04906) |
| Multi-agent pipeline (Planner/Retriever/Responder) | Yao et al. 2022 ReAct (arXiv:2210.03629) |
| Autonomous LLM agent design | Wang et al. 2023 (arXiv:2308.11432) |
| Web search fallback / hybrid RAG | Izacard et al. 2022 Atlas (arXiv:2208.03299) |
| Hallucination mitigation via source citation | Maynez et al. 2020 (arXiv:2005.00661) |
| LLMs in legal domain | Bommarito & Katz 2022 (arXiv:2212.14402) |
| Proactive legal AI / tomorrow's lawyers | Susskind 2017 |
| Local LLMs for data privacy | UK Data Protection Act 2018 / UK GDPR; SRA Code 2019 |
| Per-user data isolation | SRA Code of Conduct for Firms 2019; UK GDPR |
| JWT authentication | RFC 7519 (IETF 2015) |
| HTTP-only cookies (XSS prevention) | OWASP Session Management Cheat Sheet |
| CSRF double-submit cookie | OWASP CSRF Prevention Cheat Sheet |
| Rate limiting (SlowAPI) | OWASP API Security Top 10 2023, API4:2023 |
| File upload security (magic bytes, path traversal, size cap) | OWASP File Upload Cheat Sheet |
| OCR ingestion pipeline | Smith 2007, Tesseract OCR Engine (ICDAR 2007) |
| Conflict of interest detection | SRA Code of Conduct for Firms 2019, Standard 6.1 |
| Deadline extraction | SRA Code of Conduct for Solicitors 2019, Standard 3.3 |
| Legal document drafting (Drafter agent) | Bommarito & Katz 2022; Susskind 2017 |
