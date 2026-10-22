# Project Inspection Cheat Sheet

## 1. Brief Project Description

This project is a privacy-focused, multi-agent legal document assistant built as a full-stack Retrieval-Augmented Generation system. The core problem it solves is fast, reliable searching and summarising of large document sets for legal-clinic style work, where users need citations, bulk upload support, and strong guarantees that sensitive data is handled locally and securely.

The backend is built with FastAPI and coordinates a multi-agent workflow using a planner, retriever, responder, and drafter model. Document retrieval is handled through local embeddings and ChromaDB, with per-user isolation so one user’s case materials never leak into another user’s results. The frontend is a React and TypeScript single-page app that provides login, upload, chat, and proactive insight panels.

The main design choices were driven by the user interview: the system must support mass upload, scanned documents, citations for every factual claim, and privacy by default. For that reason, the project uses local Ollama models rather than cloud APIs, stores data in local infrastructure, and applies authentication, CSRF protection, rate limiting, and user-scoped retrieval filters.

## 2. Demo Script

### Goal

Show a complete user journey from login to evidence-backed answers, while highlighting the AI pipeline, OCR support, and security posture.

### Suggested Flow

1. Login and show that the app only exposes the main workflow after authentication.
2. Upload a batch of mixed documents, ideally including at least one scanned or blurry file.
3. Wait for ingestion and point out that the system supports local processing and per-user storage.
4. Ask a question that can be answered directly from the uploaded documents and show the citations in the response.
5. Open the agent step view and explain the planner, retriever, and responder roles.
6. Ask a question that is only partially covered by the documents and show how the system falls back to web search, if available, while making that fallback explicit.
7. Show the proactive dashboard and explain that it extracts useful case signals such as actions, gaps, and deadlines.
8. Mention the privacy controls: local inference, no cloud upload for the LLM, authentication, and document isolation.

### Recording Tip

Because generation can be slow on modest hardware, record the demo in segments and speed up the waiting periods only. Keep the query and result moments at normal speed so the citations and reasoning remain readable.

## 3. Inspector Cheat Sheet

### AI and RAG Questions

Q: Why did you use a multi-agent workflow instead of a single RAG prompt?

- It separates responsibilities: planning, retrieval, and answer generation.
- The planner can simplify the query before retrieval.
- The responder can stay tightly constrained to retrieved evidence.
- This is easier to explain, debug, and extend than a single monolithic prompt.

Q: How do you reduce hallucinations?

- The answer prompt forces citation-based responses.
- Retrieved chunks are the only evidence source for the final answer.
- If the context is insufficient, the system should say it does not know rather than inventing an answer.
- The UI can expose the reasoning steps so the answer process is inspectable.

Q: How do citations work?

- Each chunk keeps metadata such as document name and page number.
- Retrieval formats the context with visible source headers.
- The prompt instructs the model to cite every factual claim.
- This makes the answer traceable back to the original document pages.

Q: Why use local Ollama models?

- The project was designed around privacy-sensitive legal data.
- Local inference avoids sending documents to a third-party API.
- It also makes the project easier to justify against the interview requirement that data must not be used for training.
- The tradeoff is slower generation, which is acceptable for the dissertation scope.

Q: Why is the retriever user-specific?

- Retrieval is filtered by user ID in the vector store.
- That prevents cross-case contamination.
- It also matches the legal use case where client matters must remain isolated.

Q: What is the role of the planner, retriever, responder, and drafter?

- Planner: breaks the request into a strategy.
- Retriever: finds the most relevant evidence.
- Responder: writes a citation-backed answer.
- Drafter: handles drafting or summarisation style outputs when needed.

### OCR and Ingestion Questions

Q: How does the system handle scanned or blurry documents?

- The ingestion pipeline supports OCR for image-based and scanned content.
- PDF loading can include OCR parsing so text can be recovered from page images.
- The document support is broader than plain text PDF parsing.

Q: How do you support mass uploads?

- The upload endpoint accepts multiple files.
- The ingestion layer processes them into a local store and vector index.
- The architecture is designed for case files with many supporting documents.

Q: How do you prevent bad files from breaking the system?

- PDFs are checked for structure and encryption issues.
- Upload size is limited.
- The ingestion path includes timeout handling so one bad file does not block everything.

Q: Why is OCR important in this domain?

- Legal evidence often includes scanned letters, forms, and photocopies.
- If OCR fails, useful evidence is lost.
- Robust OCR is therefore a core requirement, not an optional feature.

### Security and Privacy Questions

Q: How is user data protected?

- Authentication uses JWT cookies.
- CSRF protection is enforced for mutating requests.
- Cookies can be configured to be secure and same-site aware.
- Uploaded data is stored locally rather than sent to a cloud service.

Q: How do you stop one user seeing another user’s documents?

- Uploaded files are stored in user-specific directories.
- Vector retrieval is filtered by user ID.
- The system is designed around tenant isolation rather than shared retrieval.

Q: Is any uploaded data used to train a model?

- No cloud model training is part of the workflow.
- The inference stack is local.
- That directly addresses the user concern about confidentiality and training use.

Q: Where is the data stored?

- User files are stored locally in the backend project structure.
- Vectors are stored in a local ChromaDB directory.
- Authentication state is handled with browser cookies and the backend database.

### Backend Architecture Questions

Q: Why FastAPI?

- It fits a typed API design well.
- It supports the async-style request handling needed for the workflow.
- It is straightforward to combine with authentication, file upload, and background processing.

Q: Why use MCP-style subprocess communication?

- It cleanly separates the agent coordinator from the tool server.
- It keeps the tool boundary explicit.
- It makes the orchestration feel closer to a real tool-using agent architecture.

Q: How do you make the system robust?

- Rate limiting reduces abuse.
- File checks reduce ingestion failures.
- Timeouts prevent a single file from hanging the pipeline.
- Error handling is explicit in the API responses.

Q: What are the main backend modules?

- BackendAPI handles endpoints and request flow.
- ingest manages document ingestion and OCR.
- index manages retrieval and answer generation.
- agents manages the multi-agent orchestration.
- mcp_tools and mcp_server define the tool layer.

### Frontend Questions

Q: What is the purpose of the proactive dashboard?

- It surfaces useful case-level signals automatically.
- It is meant to help the user find deadlines, gaps, and next actions quickly.
- It is a usability feature layered on top of the RAG workflow.

Q: How is the app structured on the frontend?

- It is a React single-page application written in TypeScript.
- The Search view is the main workspace.
- Login and Register are separated into their own components.
- The dashboard is integrated with the search and document workflow.

Q: How do you handle state in the UI?

- Auth state is centralised through a custom hook.
- Chat messages and uploaded documents are managed in component state.
- The dashboard can persist lightweight UI state locally where needed.

### Evaluation and Limitations Questions

Q: What is the strongest part of the project?

- The combination of privacy-aware design and citation-backed answers.
- The agent workflow shows a deeper implementation than a basic chat wrapper.
- The project is grounded in a real user interview rather than a purely theoretical idea.

Q: What are the current limitations?

- Generation is slower than a cloud-hosted system.
- OCR quality depends on the input document quality.
- Full collaboration features are not the main focus of the current implementation.

Q: What would you improve next?

- More rigorous evaluation of citation accuracy.
- Better collaboration and shared case management.
- Stronger scalability for larger user bases.
- More refined OCR and document layout handling.

## 4. Short Closing Line

If asked to summarise the project in one sentence, use this:

This is a privacy-first, citation-driven legal document assistant that combines local RAG, OCR, and a multi-agent workflow to help users query large evidence sets reliably.

## 5. Extra Likely Questions (from the writeup)

Below are additional questions the inspector may raise, paired with concise, evidence-backed answers drawing from the project write-up. These cover evaluation, failure modes, governance, and measurable results.

Q: What empirical evaluation did you run and what were the results?

- The project used a bespoke evaluation dataset: 5 synthetic case files and 20 test queries (10 fact-retrieval, 10 drafting). Key metrics recorded were planner routing accuracy, top-5 retrieval success, and citation precision.
- Baseline figures from the write-up: planner routing reached 100% accuracy; top-5 retrieval success was reported at ~70–85% depending on the split; citation precision in manual review was ~70% for fact-retrieval tests. Use these numbers honestly and explain they reflect an early iteration.

Q: How do you demonstrate citation correctness during the inspection?

- Run a small controlled query set live (or from recordings): pick a few fact-queries from `EVALUATION_TEST_PLAN.md` where the ground-truth pages are known, then show the inline citation `[document_name, page_number]` and open the source PDF page to verify the quoted text.
- Explain the manual review protocol used to compute the citation-precision metric.

Q: What are the main failure modes and mitigations?

- Failure mode: cross-page or cross-chunk hallucinations caused by rigid chunking. Mitigation: upgraded to sentence-aware `NLTKTextSplitter` and adjusted chunk overlaps.
- Failure mode: poor OCR on low-quality scans. Mitigation: three-tier ingestion (RapidOCR → native text → rasterise + Tesseract with OpenCV preprocessing) and timeouts to avoid blocking ingestion.
- Failure mode: insufficient retrieval relevance. Mitigation: relevance threshold logic (fallback to web-search surfaced to user) and re-indexing with improved split parameters.

Q: How do you measure and reduce hallucination risk quantitatively?

- Use citation-precision: manual spot checks and an aggregated precision percentage (reported ~70% baseline). Increase sample size, refine chunking, and re-run evaluation to measure improvements.
- Use top-K retrieval diagnostics (top-1/top-5 success rates) to tune embedding and splitter settings.

Q: What are the operational tradeoffs (privacy vs. quality vs. latency)?

- Privacy: local Ollama inference keeps data on-device and avoids third-party training, satisfying the core user requirement.
- Quality: smaller local models underperform GPT-4-class systems; to compensate, we enforce citation constraints and use multi-agent routing rather than relying on parametric knowledge.
- Latency: per-query MCP subprocess lifecycle introduces cold-start overhead; explain why per-query subprocesses were chosen (isolation, explicit tool boundaries) and note this is an area for optimization (pooling, long-lived worker processes) in future work.

Q: Data governance—how to prove data never left the machine?

- Implementation detail: inference is performed by local Ollama models. The only non-local operation is the optional web-search fallback which sends only the plain query string to DuckDuckGo; this is flagged in the UI whenever used.
- For inspection, demonstrate the network tab (no external LLM API calls), show local model process invocation logs, and note there is no telemetry or training pipeline attached to uploaded documents in the codebase.

Q: What about deletion, backups, and encryption-at-rest?

- Current implementation stores files under `DocsToIngest/<user_id>` and vectors in `chroma_db/`. The write-up documents local storage but does not implement encrypted-at-rest or automated backups by default—be prepared to state that these are recommended production additions (encrypted disks, secure backups, and retention policies).

Q: How robust is the ingestion pipeline and what happens on timeouts or malformed files?

- The ingestion pipeline enforces file magic-byte checks, `PdfReader` validation, per-file size limits, and a threaded timeout (`loadPdfWithTimeout`) so problematic files don't block other ingestion jobs. Show that these checks are implemented in `Backend/BackendAPI.py` and `Backend/ingest.py`.

Q: Is the tool providing legal advice or decision-making?

- Position the system as a decision-support and drafting aid: it surfaces evidence and drafts but is not a substitute for professional legal judgment. The write-up frames the tool as returning time to practitioners, not replacing them—use that wording.

Q: What next steps improve trust and deployability?

- More extensive evaluation (larger, real-world datasets), continuous citation-precision measurement, stronger OCR preprocessing, audited deletion workflows, encrypted storage, and scalable vector-db/backing store (Postgres/Redis/Pinecone) plus a Redis-backed workflow store for multi-instance robustness.

Q: How would you scale beyond a single machine?

- Replace SQLite with PostgreSQL, move Chroma to a remotely-managed vector DB or scale with Faiss/Weaviate, migrate the workflow store to Redis, and replace per-query subprocess cold-starts with a pooled MCP server or microservice architecture.

---

Progress: drafted these extra likely questions using the write-up's evaluation, ingestion, architecture, and security sections. Next I will finish the todo entry and validate the file in-place.