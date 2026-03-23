# FAQ and Troubleshooting

## Setup

### Q1: Backend starts but queries fail immediately.

Check all runtime dependencies are installed in the active environment, including `ddgs` for optional web fallback.

### Q2: Frontend cannot call backend.

Verify:

1. Backend is running on the URL set in `VITE_API_BASE_URL`.
2. `ALLOWED_ORIGINS` includes the frontend origin.
3. Browser requests include credentials (cookies).

### Q3: I get authentication errors after login.

Check cookie settings:

- For local HTTP testing, use `COOKIE_SECURE=False`.
- For HTTPS deployments, use `COOKIE_SECURE=True`.

Also ensure browser has not blocked cookies for the site.

---

## Upload and Ingestion

### Q4: Upload succeeds but content is not retrievable.

Possible causes:

1. Ingestion failed for one or more files.
2. OCR extraction returned low text quality.
3. The query does not match indexed language strongly enough.

Try re-uploading and then refreshing knowledge base state.

### Q5: PDF upload is rejected.

PDFs are validated beyond extension checks:

- magic-byte header validation,
- structural parse safety checks,
- encrypted or malformed PDFs are rejected.

---

## Query Behavior

### Q6: Why did my answer use web sources?

Web fallback may trigger when document retrieval confidence is too weak. In that path:

- only the query string is sent externally,
- uploaded document content is not transmitted,
- UI indicates that web search was used.

### Q7: Why is a drafted answer missing details?

Possible reasons:

1. Limited source detail in uploaded documents.
2. Retrieval did not surface all relevant chunks.
3. Local model size and context trade-offs.

---

## Data and Recovery

### Q8: What should I back up?

Back up:

- `Backend/users.db`
- `Backend/chroma_db/`
- `Backend/DocsToIngest/`

### Q9: Can I delete all project data quickly?

Yes, by stopping services and removing the paths above. This removes accounts, vectors, and uploaded files.

---

## Known Scope Limits

1. Collaborative multi-user case workspace features are not implemented in this version.
2. Simplified "explain like I'm five" client-language summarization is deferred to future work.
