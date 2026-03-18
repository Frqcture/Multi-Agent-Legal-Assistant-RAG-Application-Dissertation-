# Backend API Documentation

## Overview

This document provides detailed explanations of all functions and endpoints in the FastAPI backend. The backend handles authentication, document ingestion, vector storage, and RAG (Retrieval-Augmented Generation) queries.

---

## Table of Contents

1. [Authentication Functions](#authentication-functions)
2. [API Endpoints](#api-endpoints)
3. [Helper Functions](#helper-functions)
4. [Module Imports & Configuration](#module-imports--configuration)
5. [Document Ingestion System (`ingest.py`)](#document-ingestion-system-ingestpy)
6. [RAG Engine & Query Processing (`index.py`)](#rag-engine--query-processing-indexpy)
7. [OCR Processing (`ocr_processor.py`)](#ocr-processing-ocr_processorpy)
8. [Database Structure & Management](#database-structure--management)
9. [Data Flow Architecture](#data-flow-architecture)
10. [Performance Considerations](#performance-considerations)
11. [Multi-Agent Workflow (MCP)](#multi-agent-workflow-mcp)

---

## Authentication Functions

### `getCurrentUser(request: Request, db: Session) → User`

**File:** `BackendAPI.py`  
**Type:** Dependency Injection Function  
**Purpose:** Extracts and validates JWT token from cookies, returns authenticated user.

**Parameters:**
- `request: Request` - FastAPI request object containing cookies
- `db: Session` - SQLAlchemy database session (dependency injection)

**Returns:** `User` object if token is valid, raises HTTP 401 otherwise

**Logic Flow:**
1. Extract `access_token` from request cookies
2. If no token found, raise 401 "Not authenticated"
3. Decode JWT token using SECRET_KEY and HS256 algorithm
4. Extract username from token payload
5. Query database for user with that username
6. Return user object if found, raise 401 if not
7. Catch JWTError and raise 401 "Invalid credentials"

**Used By:** All protected endpoints (`/me`, `/ask`, `/upload`, `/files`, `/files/{filename}`)

---

## API Endpoints

### `GET /me`

**Purpose:** Returns authenticated user's information. Used by frontend to validate login status on page load.

**Rate Limit:** 6 requests per minute

**Dependencies:** `getCurrentUser` (requires valid auth token)

**Returns:**
```json
{
  "id": 1,
  "username": "joe_moore",
  "message": "Authenticated"
}
```

**Status Codes:**
- `200 OK` - User authenticated
- `401 Unauthorized` - No valid token in cookies

---

### `POST /login`

**Purpose:** Authenticates user by username/password and sets JWT cookie.

**Rate Limit:** 5 requests per minute

**Request Format:** `application/x-www-form-urlencoded`
```
username=joe_moore&password=mypassword
```

**Response (200 OK):**
```json
{
  "message": "Login Successful"
}
```

**Response Headers:** Includes `Set-Cookie` with JWT token

**Cookie Details:**
- `key`: "access_token"
- `httponly`: True (cannot be accessed via JavaScript)
- `samesite`: Configurable via `COOKIE_SAMESITE` env variable (default: "lax")
- `secure`: Configurable via `COOKIE_SECURE` env variable (default: True)
- `max_age`: Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60 minutes)
- `path`: "/" (valid for entire domain)

**Additional Security:**
- CSRF token automatically set as separate cookie on `/me` and `/login` endpoints
- CSRF token required in `x-csrf-token` header for state-changing operations (POST, PUT, PATCH, DELETE)
- CSRF cookie is httponly=false to allow JavaScript access for header transmission

**Logic Flow:**
1. Extract username and password from form data
2. Query database for user with matching username
3. Verify password using bcrypt
4. If authentication fails, raise 400 "Incorrect credentials"
5. Create JWT access token with username as subject
6. Create JSON response with success message
7. Set `access_token` cookie on response
8. Return response (FastAPI automatically includes Set-Cookie header)

**Status Codes:**
- `200 OK` - Login successful, cookie set
- `400 Bad Request` - Invalid username or password

---

### `POST /logout`

**Purpose:** Clears authentication cookie, logs user out.

**Rate Limit:** 5 requests per minute

**Dependencies:** None (no auth required)

**Response (200 OK):**
```json
{
  "message": "Logout Successful"
}
```

**Response Headers:** Includes `Set-Cookie` with empty/expired token

**Logic Flow:**
1. Validate CSRF token (required)
2. Create JSON response with logout message
3. Delete `access_token` cookie
4. Delete `csrf_token` cookie
5. Return response

**Status Codes:**
- `200 OK` - Logout successful
- `403 Forbidden` - Missing or invalid CSRF token

---

### `POST /register`

**Purpose:** Creates new user account with username and password.

**Rate Limit:** 5 requests per minute

**Request Format:** `application/x-www-form-urlencoded`
```
username=newuser&password=mypassword
```

**Response (200 OK):**
```json
{
  "message": "User created successfully"
}
```

**Logic Flow:**
1. Extract username and password from form data
2. Query database to check if username already exists
3. If exists, raise 400 "Username already exists"
4. Hash password using bcrypt
5. Create new User object with username and hashed_password
6. Add user to database session
7. Commit transaction
8. Refresh user object from database
9. Return success message

**Status Codes:**
- `200 OK` - User created successfully
- `400 Bad Request` - Username already exists

---

### `POST /ask`

**Purpose:** Queries the RAG engine using a multi-agent workflow that coordinates planner, retriever, and responder (or drafter) agents via MCP server.

**Rate Limit:** 20 requests per minute

**Dependencies:** `getCurrentUser` (requires valid auth token), `_require_csrf` (CSRF validation)

**Request Body:**
```json
{
  "question": "What is the capital of France?"
}
```

**Response (200 OK):**
```json
{
  "answer": "The capital of France is Paris. [document_name, page_number]",
  "steps": [
    {
      "agent": "planner",
      "message": "Plan: Search documents for capital information",
      "timestamp": "2026-03-02T10:30:00",
      "tool_calls": [{"tool": "list_user_docs", "args": {"user_id": "1"}}],
      "tool_results": [{"success": true, "data": {"files": ["geography.pdf"]}}]
    },
    {
      "agent": "retriever",
      "message": "Found 3 relevant chunks from: geography.pdf (p.5)",
      "timestamp": "2026-03-02T10:30:05",
      "tool_calls": [{"tool": "search_docs", "args": {"query": "What is the capital of France?", "top_k": 5}}],
      "tool_results": [{"success": true, "data": {"num_results": 3}}]
    },
    {
      "agent": "responder",
      "message": "Response generated with citations.",
      "timestamp": "2026-03-02T10:30:10",
      "tool_calls": [{"tool": "answer_question", "args": {"question": "What is the capital of France?"}}],
      "tool_results": [{"success": true}]
    }
  ],
  "status": "completed",
  "web_searched": false,
  "web_sources": []
}
```

**Logic Flow:**
1. Validate CSRF token (required for all POST requests)
2. Validate authentication via `getCurrentUser` dependency
3. Extract question from request body (QueryRequest model)
4. Get agent coordinator singleton instance
5. Run multi-agent workflow **synchronously** (blocking call):
   - **Planner Agent**: Lists user docs via MCP, analyzes query with LLM, creates execution plan
  - **Retriever Agent**: Searches documents via MCP `search_docs` tool; if matches are weak, it falls back to MCP `search_web`
  - **Responder/Drafter Agent**: Generates either a cited answer or a draft document depending on planner classification
6. MCP server automatically spawned as subprocess for tool execution
7. Return complete workflow result including answer, agent steps, status, and web-search metadata

**Status Codes:**
- `200 OK` - Query successful
- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Missing or invalid CSRF token
- `500 Internal Server Error` - Workflow execution failed

**Security:** User isolation via user_id metadata filtering in all MCP tool calls

---

### `POST /refresh`

**Purpose:** Reloads RAG engine after document ingestion. Called after file upload to make new documents searchable.

**Rate Limit:** 5 requests per minute

**Dependencies:** `getCurrentUser` (requires valid auth token), `_require_csrf` (CSRF validation)

**Response (200 OK):**
```json
{
  "message": "Knowledge base updated"
}
```

**Logic Flow:**
1. Validate CSRF token (required)
2. Validate authentication via `getCurrentUser` dependency
3. Create new RAGEngine instance
4. Assign it to global `ragApp` variable
5. New instance loads latest ChromaDB vectorstore
6. Return success message

**Status Codes:**
- `200 OK` - Engine reloaded
- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Missing or invalid CSRF token

---

### `POST /upload`

**Purpose:** Uploads multiple PDF files, validates them, and triggers ingestion into vectorstore.

**Rate Limit:** 5 requests per minute

**Dependencies:** `getCurrentUser` (requires valid auth token), `_require_csrf` (CSRF validation)

**Request Format:** `multipart/form-data` with file list

**Response (200 OK):**
```json
{
  "message": "2 files uploaded",
  "ingestionStatus": "Successfully ingested 2 files.",
  "files": [
    {"filename": "document1.pdf", "status": "Safe"},
    {"filename": "document2.pdf", "status": "Safe"}
  ]
}
```

**Logic Flow:**
1. Validate CSRF token (required)
2. Validate authentication via `getCurrentUser`
3. Create/get user-specific upload directory: `DocsToIngest/{user_id}/`
4. For each uploaded file:
   - Check filename ends with `.pdf`
   - Verify PDF magic bytes (`%PDF-`) using `_looks_like_pdf()`
   - Check file size ≤ 15MB (streaming validation)
   - Sanitize filename using `os.path.basename()`
   - Validate file path doesn't escape user upload directory
   - Check if file already exists (prevent overwriting)
   - Stream-save file to user directory using `_save_upload_file()`
   - Run `isPdfSafe()` validation (checks encryption, malformation)
   - If unsafe, delete file and raise error
5. After all files saved, call `runIngestion(userId)` from ingest.py
6. Reload RAG engine with new `RAGEngine()` instance
7. Return detailed status with per-file results

**Status Codes:**
- `200 OK` - Files uploaded and ingested
- `400 Bad Request` - Invalid file, filename, or PDF validation failed
- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Missing or invalid CSRF token
- `409 Conflict` - File already exists
- `413 Payload Too Large` - File exceeds 15MB
- `500 Internal Server Error` - Save or ingestion failed

**Security:**
- **Per-user directory isolation**: Files stored in `DocsToIngest/{user_id}/`
- **Magic byte validation**: Checks PDF header signature before processing
- **Path traversal prevention**: Double validation via resolve() and startswith()
- **File type validation**: PDF only (extension + magic bytes)
- **Streaming size validation**: Checks size incrementally during upload
- **Duplicate prevention**: Returns 409 if file already exists
- **Content validation**: `isPdfSafe()` checks for encryption and corruption
- **User isolation**: userId metadata attached during ingestion

---

### `GET /files`

**Purpose:** Returns list of filenames uploaded by authenticated user.

**Rate Limit:** No explicit limit

**Dependencies:** `getCurrentUser` (requires valid auth token)

**Response (200 OK):**
```json
{
  "files": [
    "document1.pdf",
    "document2.pdf",
    "research_paper.pdf"
  ]
}
```

**Logic Flow:**
1. Validate authentication via `getCurrentUser`
2. Call `ragApp.listUserFiles(userId=current_user.id)`
3. RAG engine queries ChromaDB metadata for all unique filenames with matching user_id
4. Return list of filenames

**Status Codes:**
- `200 OK` - Files list returned
- `401 Unauthorized` - Invalid token
- `500 Internal Server Error` - Query failed

**Security:** User isolation via user_id metadata filtering

---

### `DELETE /files/{filename}`

**Purpose:** Deletes a specific file from vectorstore, ingestion log, and local storage.

**Rate Limit:** No explicit limit

**Dependencies:** `getCurrentUser` (requires valid auth token), `_require_csrf` (CSRF validation)

**Path Parameters:**
- `filename` - Name of file to delete (URL-encoded)

**Response (200 OK):**
```json
{
  "message": "Deleted document.pdf"
}
```

**Logic Flow:**
1. Validate CSRF token (required)
2. Validate authentication via `getCurrentUser`
3. Call `ragApp.deleteFile(userId=current_user.id, filename=filename)`
   - RAG engine queries ChromaDB for chunks matching user_id AND filename
   - Deletes all matching chunks from ChromaDB
4. If no chunks found, raise 404 "File not found"
5. Remove filename from user's ingestion log `DocsToIngest/{user_id}/IngestedFiles.log`
6. Delete actual PDF file from user directory `DocsToIngest/{user_id}/` if it exists
7. Return success message

**Status Codes:**
- `200 OK` - File deleted
- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Missing or invalid CSRF token
- `500 Internal Server Error` - Deletion failed

**Implementation Note:** Current implementation wraps broad exceptions in the route handler, so a not-found condition may surface as `500` instead of `404`.

**Security:**
- User isolation via user_id metadata filtering
- Only deletes files associated with authenticated user
- Per-user directory structure prevents cross-user file access

---

### `POST /proactive-insights`

**Purpose:** Generates proactive legal-clinic case insights using LLM analysis of user's documents. Returns six insight sections (actions, statutes, checklist, info gaps, deadlines, conflicts), relevance scoring, and jurisdiction metadata. Results are cached per-user for 1 hour.

**Rate Limit:** 10 requests per minute

**Dependencies:** `getCurrentUser` (requires valid auth token), `_require_csrf` (CSRF validation)

**Request Body:**
```json
{
  "query": "custody case with domestic violence allegations"
}
```

*Note: `query` field is optional. Provides additional context for insights generation.*

**Response (200 OK):**
```json
{
  "next_actions": [
    {
      "action": "File protective order request",
      "priority": "high",
      "reason": "Client safety and evidence preservation"
    },
    {
      "action": "Schedule client intake interview",
      "priority": "medium",
      "reason": "Need complete timeline of events"
    }
  ],
  "related_statutes": [
    {
      "statute": "Family Code § 3044",
      "relevance": "Rebuttable presumption against custody to abuser",
      "jurisdiction": "California"
    },
    {
      "statute": "Family Code § 6211",
      "relevance": "Definition of domestic violence for protective orders",
      "jurisdiction": "California"
    }
  ],
  "checklist": [
    {
      "item": "Obtain police reports",
      "completed": false,
      "category": "Evidence"
    },
    {
      "item": "Complete intake forms",
      "completed": false,
      "category": "Intake"
    },
    {
      "item": "File petition",
      "completed": false,
      "category": "Filing"
    }
  ],
  "info_gaps": [
    {
      "field": "Client statement of events",
      "severity": "high",
      "suggestion": "Schedule detailed intake interview to document timeline"
    },
    {
      "field": "Medical records",
      "severity": "medium",
      "suggestion": "Request authorization for medical history records"
    }
  ],
  "deadlines": [
    {
      "title": "File response",
      "date": "2026-04-01",
      "source": "case_file.pdf",
      "urgency": "high",
      "description": "Court filing deadline"
    }
  ],
  "conflicts": [
    {
      "party_name": "ABC Ltd",
      "documents": ["retainer.pdf", "opposition_bundle.pdf"],
      "conflict_type": "shared_party",
      "severity": "medium",
      "description": "Same organisation appears in multiple opposing contexts"
    }
  ],
  "section_relevance": {
    "next_actions": 0.95,
    "related_statutes": 0.72,
    "checklist": 0.81,
    "info_gaps": 0.69,
    "deadlines": 0.88,
    "conflicts": 0.55
  },
  "visible_sections": ["next_actions", "deadlines", "checklist", "related_statutes"],
  "jurisdiction": {
    "name": "England and Wales",
    "confidence": "medium",
    "detected_from": "Court references in uploaded filings"
  }
}
```

**Logic Flow:**
1. Validate CSRF token (required)
2. Validate authentication via `getCurrentUser`
3. Check cache for user_id; if fresh (<1 hour), return cached result
4. Extract representative document chunks (limit: 6) from user's vectorstore
5. Format document context with source headers
6. Send single LLM request with combined prompt for all six insight sections:
   - System prompt: "You are a legal-clinic case advisor. Respond ONLY with valid JSON."
   - User prompt includes document context and optional query context
7. Parse LLM JSON response into structured insight sections
8. Compute `section_relevance`, choose `visible_sections` (top sections), and apply defaults for missing sections
9. Cache result with timestamp
10. Return complete insights object

**Empty State Response:**
If user has no documents uploaded, returns:
```json
{
  "next_actions": [{
    "action": "Upload case documents to get started",
    "priority": "high",
    "reason": "No documents found"
  }],
  "related_statutes": [],
  "checklist": [{
    "item": "Upload case documents",
    "completed": false,
    "category": "Setup"
  }],
  "info_gaps": [{
    "field": "Client documents",
    "severity": "high",
    "suggestion": "Upload relevant case files to begin analysis."
  }],
  "deadlines": [],
  "conflicts": [],
  "section_relevance": {
    "next_actions": 0.8,
    "related_statutes": 0.2,
    "checklist": 0.7,
    "info_gaps": 0.6,
    "deadlines": 0.1,
    "conflicts": 0.1
  },
  "visible_sections": ["next_actions", "checklist", "info_gaps", "related_statutes"],
  "jurisdiction": {
    "name": "Unknown",
    "confidence": "low",
    "detected_from": "No documents uploaded"
  }
}
```

**Status Codes:**
- `200 OK` - Insights generated or retrieved from cache
- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Missing or invalid CSRF token
- `500 Internal Server Error` - LLM error or processing failure

**Performance:**
- **Cache TTL**: 1 hour per user
- **LLM Model**: gemma3:4b with temperature 0.2
- **Sample Limit**: 6 document chunks maximum
- **Single LLM Call**: All six insight sections generated in one request
- **Response Size**: ~1024 tokens maximum (constrained via `num_predict`)

**Use Case:**
This endpoint powers the **Proactive Dashboard** feature in the frontend, providing legal clinic staff with:
- Prioritized action recommendations based on case documents
- Relevant statutes and legal authorities
- Case progress checklist items
- Identified information gaps requiring attention
- Timeline-sensitive deadline extraction
- Cross-document conflict signals

---

## Helper Functions

### `isPdfSafe(filePath: str) → tuple`

**Purpose:** Validates PDF structure and safety before ingestion.

**Parameters:**
- `filePath: str` - Path to PDF file to validate

**Returns:** Tuple of (bool, str)
- `(True, "Safe")` - PDF is valid
- `(False, "Encrypted PDFs not supported")` - PDF is encrypted
- `(False, "Malformed or corrupted PDF")` - PDF is invalid

**Logic Flow:**
1. Try to read PDF using PyPDFReader
2. Access page count to trigger parsing
3. Check if PDF is encrypted
4. Return success if valid, failure if any exception occurs

**Used By:** `/upload` endpoint

---

### `_get_user_upload_dir(user_id: int) → Path`

**Purpose:** Create and return user-specific upload directory with security validation.

**Parameters:**
- `user_id: int` - User ID for directory isolation

**Returns:** Resolved Path object for user's upload directory

**Logic Flow:**
1. Resolve base `UPLOAD_DIR` to absolute path
2. Create subdirectory: `{UPLOAD_DIR}/{user_id}/`
3. Create directory if it doesn't exist (with parents)
4. Validate resolved user_dir starts with base_dir (prevent directory traversal)
5. If validation fails, raise HTTP 400
6. Return validated Path object

**Security:** Prevents malicious user_id values from escaping upload directory

**Used By:** `/upload`, `/files/{filename}` (DELETE)

---

### `_ensure_csrf_cookie(response: Response, existing_token: str | None) → str`

**Purpose:** Generate CSRF token and set cookie if not already present.

**Parameters:**
- `response: Response` - FastAPI response object to set cookie on
- `existing_token: str | None` - Existing CSRF token from request cookies

**Returns:** CSRF token (existing or newly generated)

**Logic Flow:**
1. If existing token provided, return it (no-op)
2. Generate new token using `secrets.token_urlsafe(32)`
3. Set `csrf_token` cookie on response:
   - httponly=False (allows JavaScript access for header transmission)
   - max_age=86400 (24 hours)
   - samesite and secure values from environment
4. Return token

**Used By:** `/me`, `/login` endpoints

---

### `_require_csrf(request: Request)`

**Purpose:** Validate CSRF token for state-changing requests.

**Parameters:**
- `request: Request` - FastAPI request object

**Logic Flow:**
1. If request method is GET or other safe method, return immediately (no validation)
2. For POST/PUT/PATCH/DELETE:
   - Extract token from `csrf_token` cookie
   - Extract token from `x-csrf-token` header
   - Compare tokens
   - If missing or mismatched, raise HTTP 403
3. Return (validation passed)

**Used By:** All state-changing endpoints (POST, PUT, PATCH, DELETE)

---

### `_looks_like_pdf(upload: UploadFile) → bool`

**Purpose:** Verify file is PDF by checking magic bytes signature.

**Parameters:**
- `upload: UploadFile` - FastAPI file upload object

**Returns:** True if PDF signature present, False otherwise

**Logic Flow:**
1. Read first 5 bytes from file
2. Reset file pointer to beginning (seek(0))
3. Check if bytes equal `b"%PDF-"` (PDF header signature)
4. Return result, False on any exception

**Security:** Prevents non-PDF files with `.pdf` extension from being processed

**Used By:** `/upload` endpoint

---

### `_save_upload_file(upload: UploadFile, destination: Path, max_bytes: int) → int`

**Purpose:** Stream-save uploaded file with incremental size validation.

**Parameters:**
- `upload: UploadFile` - File to save
- `destination: Path` - Target file path
- `max_bytes: int` - Maximum allowed file size

**Returns:** Total bytes written

**Logic Flow:**
1. Open destination file for binary writing
2. Read file in 1MB chunks
3. For each chunk:
   - Add chunk size to total
   - If total exceeds max_bytes, raise HTTP 413
   - Write chunk to disk
4. Return total bytes written

**Security:** Prevents memory exhaustion from large file uploads by streaming and validating size incrementally

**Used By:** `/upload` endpoint

---

### `_env_bool(name: str, default: bool = False) → bool`

**Purpose:** Parse boolean environment variable with flexible value recognition.

**Parameters:**
- `name: str` - Environment variable name
- `default: bool` - Default value if not set

**Returns:** Boolean value

**Logic Flow:**
1. Get environment variable value
2. If None/unset, return default
3. Strip whitespace, convert to lowercase
4. Return True if value in {"1", "true", "yes", "on"}
5. Return False otherwise

**Used By:** Cookie configuration (`COOKIE_SECURE`)

---

### `_normalize_samesite(value: str) → str`

**Purpose:** Validate and normalize SameSite cookie attribute.

**Parameters:**
- `value: str` - SameSite value from environment

**Returns:** Normalized value ("lax", "strict", or "none")

**Logic Flow:**
1. Strip whitespace, convert to lowercase
2. If value in {"lax", "strict", "none"}, return it
3. Otherwise return "lax" (safe default)

**Used By:** Cookie configuration (`COOKIE_SAMESITE`)

---

## Module Imports & Configuration

### Key Dependencies

**FastAPI & HTTP:**
- `FastAPI` - Web framework
- `HTTPException` - Standard exception for HTTP errors
- `JSONResponse` - Direct control over response JSON
- `CORSMiddleware` - Cross-Origin Resource Sharing
- `OAuth2PasswordBearer` - OAuth2 token scheme
- `OAuth2PasswordRequestForm` - Standard username/password form

**Database:**
- `SQLAlchemy` - ORM for database operations
- `Session` - Database session for queries

**Authentication:**
- `jose` (JWT library) - JWT encoding/decoding
- Custom `auth_utils` - Password hashing and token creation

**Rate Limiting:**
- `slowapi` - Rate limiting middleware

**Document Processing:**
- `ingest.py` - Document ingestion and vectorization
- `index.py` - RAG engine and query logic

---

### Global Configuration

**Constants:**
- `MAX_FILE_SIZE`: 15 * 1024 * 1024 (15 MB)
- `UPLOAD_DIR`: "DocsToIngest" (base directory, per-user subdirectories created)
- `ACCESS_COOKIE_NAME`: "access_token"
- `CSRF_COOKIE_NAME`: "csrf_token"
- `ALLOWED_ORIGINS`: List of frontend origins for CORS (from `ALLOWED_ORIGINS` env variable)

**Environment-Based Configuration:**
- `COOKIE_SECURE`: Boolean (default: True) - Use secure cookies (HTTPS only)
- `COOKIE_SAMESITE`: String (default: "lax") - SameSite cookie attribute
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Integer (default: 60) - JWT token expiration
- `SECRET_KEY`: String (required) - JWT signing secret
- `ALGORITHM`: String (default: "HS256") - JWT algorithm
- `DATABASE_URL`: String (default: "sqlite:///./users.db") - Database connection URL

**Instances:**
- `limiter`: Slowapi limiter for rate limiting
- `app`: FastAPI application instance
- `ragApp`: RAGEngine instance (global, reloaded on file upload and refresh)
- `_insights_llm`: ChatOllama instance (gemma3:4b) for proactive insights
- `_insights_cache`: Dictionary for caching proactive insights (in-memory, 1 hour TTL)

**Middleware:**
- **CORS**: Enabled with credentials support, configurable allowed origins
- **Rate limiting**: Applied to all endpoints via slowapi
- **SQLAlchemy session**: Automatic session management via dependency injection
- **CSRF protection**: Token validation on state-changing operations

---

## Data Models

### User (SQLAlchemy Model)

**Fields:**
- `id: int` - Primary key
- `username: str` - Unique username
- `hashedPassword: str` - Bcrypt-hashed password

**Database Column Mapping:**
- `hashedPassword` ORM attribute maps to `hashed_password` column

---

### QueryRequest (Pydantic Model)

**Fields:**
- `question: str` - User's question for RAG query

---

### InsightsRequest (Pydantic Model)

**Fields:**
- `query: str` - Optional context query for proactive insights generation (default: "")

---

## Security Considerations

### Authentication
- All protected endpoints require valid JWT token in cookies
- Tokens expire after configurable duration (default: 60 minutes, set via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Token expiration enforced in JWT payload
- Passwords are hashed with bcrypt before storage
- JWT signing uses configurable secret key and algorithm

### CSRF Protection
- **Token Generation**: CSRF token generated on `/me` and `/login` (32-byte URL-safe random)
- **Cookie Storage**: Token stored in httponly=false cookie to allow JavaScript access
- **Header Transmission**: Frontend must send token in `x-csrf-token` header
- **Validation**: All POST/PUT/PATCH/DELETE requests validate token match
- **Error Response**: Returns 403 if token missing or mismatched
- **Token Lifetime**: 24 hours (same as auth token for simplicity)

### Authorization
- User isolation via `user_id` metadata in vectorstore
- Users can only see/delete their own documents
- Users can only query documents they uploaded
- Per-user upload directories prevent file system cross-contamination

### Input Validation
- **File path traversal prevention**: Double validation via `resolve()` and `startswith()` checks
- **File type validation**: PDF extension checking + magic byte verification (`%PDF-` signature)
- **File size limits**: 15MB maximum, validated incrementally during streaming upload
- **Duplicate prevention**: Checks for existing files before saving (409 Conflict)
- **Form data validation**: Pydantic models for request bodies
- **Per-user directory isolation**: User ID embedded in file path, validated before access
- **Filename sanitization**: `os.path.basename()` prevents directory traversal in filenames

### CORS
- Only allows requests from whitelisted frontend origins (configurable via `ALLOWED_ORIGINS` env variable)
- Credentials required to access protected endpoints
- Supports all HTTP methods for allowed origins

---

## Error Handling

All endpoints follow standard HTTP status code conventions:

- `200 OK` - Success
- `400 Bad Request` - Invalid input (malformed file, bad filename, validation failure)
- `401 Unauthorized` - Authentication failed or missing token
- `403 Forbidden` - CSRF validation failed
- `404 Not Found` - Resource not found
- `409 Conflict` - File already exists (prevents overwriting)
- `413 Payload Too Large` - File exceeds 15MB
- `500 Internal Server Error` - Server error (ingestion failure, RAG error, LLM error)

---

## Workflow Examples

### Typical User Journey

1. **Registration** → `POST /register`
2. **Login** → `POST /login` (sets auth cookie)
3. **Upload Documents** → `POST /upload`
4. **Ask Questions** → `POST /ask` (multiple times)
5. **View Files** → `GET /files`
6. **Delete File** → `DELETE /files/{filename}`
7. **Logout** → `POST /logout` (clears auth cookie)

### Authentication Flow

1. User submits login form with username/password
2. Backend verifies credentials against database
3. Backend generates JWT token with username as subject
4. JWT token set as httponly cookie in response
5. Browser automatically includes cookie in subsequent requests
6. Protected endpoints extract and validate token from cookies
7. User_id attached to all vectorstore operations for isolation

---

## Document Ingestion System (`ingest.py`)

### Overview

The ingestion system handles loading documents of multiple formats, extracting text, converting to embeddings, and storing in ChromaDB. It supports PDFs (with OCR), DOCX, PPTX, TXT, and image files.

### Configuration Constants

- `SOURCE_DIRECTORY`: "DocsToIngest" - Base directory where uploaded files are stored
  - **Per-User Structure**: Files stored in `DocsToIngest/{user_id}/`
  - **Per-User Logs**: Each user has own `IngestedFiles.log` in their directory
- `PERSIST_DIRECTORY`: "chroma_db" - Directory where ChromaDB vectorstore is persisted (shared, filtered by user_id metadata)
- `LOG_FILE`: "IngestedFiles.log" - Filename for tracking already-processed documents (per-user)

### Multi-Format Support Flags

Optional dependencies are checked at import time:
- `DOCX_AVAILABLE`: python-docx library available
- `PPTX_AVAILABLE`: python-pptx library available
- `IMAGE_PROCESSING_AVAILABLE`: PIL, cv2, numpy available
- `TESSERACT_AVAILABLE`: pytesseract available
- `PDF_TO_IMAGE_AVAILABLE`: pdf2image available

---

### Helper Functions

#### `get_user_source_directory(user_id: str) → str`

**Purpose:** Return and create per-user upload directory with security validation.

**Parameters:**
- `user_id: str` - User ID for directory isolation

**Returns:** Absolute path to user's upload directory

**Logic Flow:**
1. Resolve base `SOURCE_DIRECTORY` to absolute path
2. Create user subdirectory path: `{base_dir}/{user_id}/`
3. Resolve user directory to absolute path
4. Create directory if it doesn't exist (with parents)
5. Validate user_dir starts with base_dir (prevent directory traversal)
6. If validation fails, raise ValueError
7. Return validated directory path as string

**Security:** Prevents malicious user_id from escaping base directory

**Used By:** `runIngestion()`, `getProcessedFiles()`, `updateProcessedFiles()`

---

#### `get_user_log_file(user_id: str) → str`

**Purpose:** Return path to user's ingestion log file.

**Parameters:**
- `user_id: str` - User ID

**Returns:** Absolute path to user's log file

**Logic Flow:**
1. Get user's source directory via `get_user_source_directory()`
2. Append `LOG_FILE` filename to user directory
3. Resolve to absolute path
4. Return path as string

**Used By:** `getProcessedFiles()`, `updateProcessedFiles()`, `/files/{filename}` (DELETE endpoint)

---

#### `loadPdfWithTimeout(filePath: str, useOcr: bool = True, timeoutSeconds: int = 30) → Optional[List[Document]]`

**Purpose:** Load PDF with threading-based timeout to prevent hanging on problematic files.

**Parameters:**
- `filePath: str` - Path to PDF file
- `useOcr: bool` - Whether to use RapidOCR for image parsing (default: True)
- `timeoutSeconds: int` - Timeout in seconds (default: 30)

**Returns:** List of Document objects or None if timeout/error

**Logic Flow:**
1. Create thread-safe result and error containers
2. Define inner `loadPdf()` function that loads PDF into result container
3. Start daemon thread executing `loadPdf()`
4. Wait for thread with timeout
5. If thread still alive after timeout, log warning and return None
6. If error occurred, log and return None
7. Otherwise return loaded documents

**Why This Matters:** Some PDFs have malformed headers that cause PyPDFLoader to hang indefinitely. Threading with timeout prevents the entire ingestion pipeline from blocking.

---

#### `getProcessedFiles(log_file: str) → Set[str]`

**Purpose:** Load list of already-processed filenames from user's log file to prevent duplicate ingestion.

**Parameters:**
- `log_file: str` - Path to user's ingestion log file

**Returns:** Set of filenames that have been processed

**Logic Flow:**
1. Try to open log file at specified path
2. Read each line, strip whitespace, add to set
3. If file doesn't exist, return empty set
4. Return set of processed filenames

**Why Set:** O(1) lookup time when checking if file already processed

---

#### `updateProcessedFiles(log_file: str, filename: str) → None`

**Purpose:** Append filename to user's processed log after successful ingestion.

**Parameters:**
- `log_file: str` - Path to user's ingestion log file
- `filename: str` - Filename to add to log

**Logic Flow:**
1. Open log file in append mode
2. Write filename with newline
3. Close file

---

#### `extractDocx(filePath: str) → str`

**Purpose:** Extract all text from DOCX files.

**Parameters:**
- `filePath: str` - Path to DOCX file

**Returns:** Extracted text or empty string on error

**Logic Flow:**
1. Check if python-docx is available
2. Load DOCX document
3. Join all paragraph text with newlines
4. Log extraction statistics
5. Return text

---

#### `extractPptx(filePath: str) → str`

**Purpose:** Extract text from all slides in PPTX files.

**Parameters:**
- `filePath: str` - Path to PPTX file

**Returns:** Extracted text with slide headers

**Logic Flow:**
1. Check if python-pptx is available
2. Load presentation
3. For each slide, add slide number header
4. Extract text from all shapes in slide
5. Join all text with newlines
6. Log extraction statistics
7. Return text

---

#### `preprocessImageForOcr(imagePath: str) → Optional[np.ndarray]`

**Purpose:** Enhance image quality for better OCR accuracy using computer vision techniques.

**Parameters:**
- `imagePath: str` - Path to image file

**Returns:** Preprocessed image as numpy array or None

**Image Processing Steps:**
1. Read image with OpenCV
2. Convert BGR to grayscale
3. **CLAHE** - Contrast Limited Adaptive Histogram Equalization
   - Improves contrast in localized regions
   - Prevents over-amplification
4. **Denoise** - FastNLMeansDenoising
   - Removes noise while preserving edges
   - H=10 controls strength
5. **Binary Threshold** - Otsu's method
   - Converts to pure black/white
   - Improves OCR character recognition
6. Return binary image

**Why This Works:** Scanned documents often have poor contrast, noise, and grayscale values. Preprocessing converts them to high-contrast binary, which OCR engines handle much better.

---

#### `extractImage(filePath: str) → str`

**Purpose:** Extract text from image files using RapidOCR.

**Parameters:**
- `filePath: str` - Path to image file (PNG, JPG, etc.)

**Returns:** Extracted text or empty string

**Logic Flow:**
1. Load image with UnstructuredImageLoader (RapidOCR backend)
2. Extract text from loaded documents
3. Join document contents
4. Log extraction statistics
5. Return text

---

#### `extractTxt(filePath: str) → str`

**Purpose:** Extract text from plain text files.

**Parameters:**
- `filePath: str` - Path to TXT file

**Returns:** File contents or empty string

**Logic Flow:**
1. Open file with UTF-8 encoding
2. Read entire contents
3. Log extraction statistics
4. Return text

---

#### `ocrWithTesseract(image) → str`

**Purpose:** Extract text from PIL Image using Tesseract OCR engine.

**Parameters:**
- `image` - PIL Image object

**Returns:** Extracted text or empty string

**Logic Flow:**
1. Check if Tesseract is available
2. Call `pytesseract.image_to_string()`
3. Return extracted text or error string

---

#### `extractPdfWithOcr(filePath: str, useHighDpi: bool = True) → str`

**Purpose:** Extract text from PDF by converting pages to images and applying OCR chain.

**Parameters:**
- `filePath: str` - Path to PDF file
- `useHighDpi: bool` - Use 300 DPI (True) or 150 DPI (False)

**Returns:** Combined text from all pages or empty string

**DPI Selection:**
- 300 DPI (default) - High quality, slower, uses more memory
- 150 DPI (fallback) - Lower quality, faster, less memory

**Three-Tier OCR Chain for Each Page:**

**Tier 1 - Image Preprocessing:**
1. Convert PDF page to PIL Image
2. Save to temporary PNG file
3. Call `preprocessImageForOcr()`
4. Reload preprocessed image

**Tier 2 - Tesseract OCR:**
1. If Tesseract available, call `ocrWithTesseract(image)`
2. If text extracted, add to results and continue to next page
3. If no text, fall through to Tier 3

**Tier 3 - RapidOCR Fallback:**
1. Save image to temporary file
2. Load with UnstructuredImageLoader (RapidOCR)
3. Extract text from loaded documents
4. If successful, add to results

**Final Output:**
1. Combine all page texts with page headers
2. Join with double newlines
3. Log total character count
4. Return combined text

---

#### `processPdf(filePath: str, filename: str) → Optional[List[Document]]`

**Purpose:** Process PDF with intelligent 3-tier fallback strategy.

**Parameters:**
- `filePath: str` - Path to PDF file
- `filename: str` - Original filename for logging

**Returns:** List of Document objects or None

**Three-Tier Processing Strategy:**

**Tier 1 - RapidOCR via PyPDFLoader** (Fast)
- Load PDF with RapidOCRBlobParser
- Extract images embedded in PDF
- Validate: >100 characters required to proceed
- If fails, continue to Tier 2

**Tier 2 - Basic Text Extraction** (Fastest)
- Load PDF without OCR
- Extract text layer
- Validate: >100 characters required to proceed
- If fails, continue to Tier 3

**Tier 3 - Image-Based OCR** (Most Robust)
- Convert entire PDF to 300 DPI images
- Apply preprocessing to each page
- Try Tesseract first, then RapidOCR
- Validate: >50 characters required
- If all fail, return None

**Why This Works:**
- Text PDFs: Tier 1 or 2 handle instantly
- PDFs with embedded images: Tier 1 extracts both
- Scanned PDFs: Tier 3's preprocessing + dual OCR handles
- Problematic PDFs: 30-second timeout per tier prevents hangs

---

### Main Ingestion Function

#### `runIngestion(userId: str) → str`

**Purpose:** Main entry point for document ingestion. Processes all new files from user's directory and stores in vectorstore.

**Parameters:**
- `userId: str` - User ID for metadata isolation and directory selection

**Returns:** Status message with ingestion summary

**Supported File Extensions:**
- `.pdf` - PDF documents (with 3-tier OCR fallback)
- `.docx` - Microsoft Word documents
- `.pptx` - Microsoft PowerPoint presentations
- `.txt` - Plain text files
- `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp` - Image files

**Processing Steps:**

**1. Initialization**
- Initialize OllamaEmbeddings model ("embeddinggemma")
- Get user-specific source directory via `get_user_source_directory(userId)`
- Get user-specific log file via `get_user_log_file(userId)`
- Connect to ChromaDB vectorstore (shared, filtered by user_id metadata)

**2. File Discovery**
- Get set of already-processed files from user's log file
- List all supported file types in user's directory: `DocsToIngest/{userId}/`
- Filter to only new, unprocessed files

**3. Per-File Processing**
For each new file:
- Sanitize filename using `os.path.basename()`
- Build file path in user's directory
- Extract file extension
- Route to appropriate extraction function based on type:
  - PDF: `processPdf()` with 3-tier fallback
  - DOCX: `extractDocx()`
  - PPTX: `extractPptx()`
  - TXT: `extractTxt()`
  - Images: `extractImage()`
- Validate extracted text is not empty
- Filter out empty documents
- Attach metadata to each document:
  - `user_id` - For data isolation (as string matching userId parameter)
  - `document_name` - Original filename
  - `file_type` - Extension (e.g., ".pdf")
  - `page_number` - Page/position in document

**4. Chunking**
- Use a two-pass NLTK sentence-aware strategy:
  - Parent chunks (larger context blocks)
  - Child chunks (smaller retrieval units with overlap)
- Attach parent/child chunk metadata (`chunk_level`, `chunk_id`, `parent_chunk_id`)
- Filter empty chunks after splitting

**5. Embedding & Storage**
- Generate embeddings for each chunk using OllamaEmbeddings
- Store chunks in shared ChromaDB vectorstore with user_id metadata
- Update user's processed files log via `updateProcessedFiles(log_file, filename)`

**6. Error Handling**
- Per-file errors logged but don't stop pipeline
- Failed files tracked with error reason
- Return comprehensive status message listing successes and failures

**Return Message Examples:**
```
Successfully ingested 3 files.
```
```
Ingested 2 files. Failed: corrupted.pdf (Malformed PDF); empty.txt (No extractable text)
```

**User Isolation:**
- Files read from per-user directory: `DocsToIngest/{userId}/`
- Log maintained per-user: `DocsToIngest/{userId}/IngestedFiles.log`
- All chunks stored with `user_id` metadata for query filtering
- Users can only access their own documents via metadata filters

---

## RAG Engine & Query Processing (`index.py`)

### Overview

The RAG (Retrieval-Augmented Generation) engine handles semantic search over ingested documents and generates contextual answers using a local LLM.

### RAGEngine Class

#### `__init__(persistDirectory: str = "chroma_db", pdfPath: str = "testPDFinput.pdf")`

**Purpose:** Initialize RAG engine with vectorstore and LLM models.

**Parameters:**
- `persistDirectory: str` - Path to ChromaDB storage
- `pdfPath: str` - Fallback PDF for initial setup

**Initialization Steps:**
1. Load environment variables
2. Initialize OllamaEmbeddings ("embeddinggemma" model)
   - Local embedding model, no API calls
   - ~384-dimensional embeddings
3. Initialize ChatOllama LLM ("gemma3:4b" model)
   - Local LLM, temperature=0 for consistent answers
   - 4-billion parameter model
4. Load or create vectorstore via `_setupVectorstore()`

---

#### `_setupVectorstore() → Chroma`

**Purpose:** Load existing vectorstore or create new one.

**Logic Flow:**
1. Check if `persistDirectory` exists
2. If exists, connect to existing ChromaDB
3. If not exists:
   - Load fallback PDF
   - Split into chunks
   - Create new ChromaDB from documents
   - Persist to disk

**Why Split Logic:** On first run, system bootstraps with a test PDF. On subsequent runs, uses actual user data.

---

#### `formatChromaDocs(docs) → str`

**Purpose:** Format retrieved documents for LLM with source headers.

**Parameters:**
- `docs` - List of Document objects from ChromaDB

**Returns:** Formatted string with headers and content

**Output Format:**
```
--- SOURCE: [document_name, Page 12] ---
Document content here...

--- SOURCE: [another_doc.pdf, Page 5] ---
More document content...
```

**Why Format:** LLM needs clear source attribution for cited answers. Headers make it obvious where information comes from.

---

#### `query(question: str, userId: str) → str`

**Purpose:** Answer user question using RAG with document context.

**Parameters:**
- `question: str` - User's question
- `userId: str` - User ID for document filtering

**Returns:** Answer with citations

**Processing Pipeline:**

**1. User-Filtered Retrieval**
- Create retriever with metadata filter: `{"user_id": userId}`
- Only retrieves this user's documents
- Prevents data leakage between users

**2. Semantic Search**
- Embed user's question using same embedding model as documents
- Search ChromaDB for most similar chunks
- Default returns top 4 results (configurable)

**3. Context Formatting**
- Format retrieved chunks with source headers
- Pass to `formatChromaDocs()`

**4. LLM Prompt**
System prompt enforces:
- Every claim must include `[document_name, page_number]` citation
- If context doesn't answer, say "I don't know"
- Cite sources explicitly

**5. Answer Generation**
- ChatOllama processes:
  - Formatted context
  - User question
  - System prompt
- Returns cited answer

**Example Flow:**
```
User: "What is the battery life?"
↓
Embed question, search ChromaDB
↓
Retrieved: "Battery lasts 10 hours" [Manual.pdf, pg 12]
↓
LLM Response: "The battery lasts for 10 hours. [Manual.pdf, 12]"
```

---

#### `listUserFiles(userId: str) → List[str]`

**Purpose:** Get all filenames uploaded by user.

**Parameters:**
- `userId: str` - User ID

**Returns:** List of unique filenames

**Logic Flow:**
1. Query ChromaDB for all metadata with matching user_id
2. Extract unique "document_name" values
3. Return as list

---

#### `deleteFile(userId: str, filename: str) → bool`

**Purpose:** Delete all chunks for a specific user's file.

**Parameters:**
- `userId: str` - User ID (for authorization)
- `filename: str` - Filename to delete

**Returns:** True if deleted, False if not found

**Logic Flow:**
1. Query ChromaDB for chunks matching:
   - `user_id == userId` AND
   - `document_name == filename`
2. If results found:
   - Delete all matching chunk IDs
   - Return True
3. Else:
   - Return False (not found)

**Why Both Filters:** Ensures user can only delete their own files, not another user's document with same name.

---

## OCR Processing (`ocr_processor.py`)

### Overview

Standalone OCR processor module for extracting text from scanned PDFs using Tesseract. Used as fallback in main ingestion pipeline.

### Main Function

#### `extractTextFromScannedPdf(pdfPath: str) → str`

**Purpose:** Extract text from scanned PDF documents using Tesseract OCR.

**Parameters:**
- `pdfPath: str` - Path to PDF file

**Returns:** Combined text from all pages or raises exception

**Processing Steps:**

**1. PDF to Images Conversion**
- Convert PDF to PIL Images at 300 DPI
- Higher DPI = better OCR quality
- Log number of converted pages

**2. Per-Page OCR**
For each page:
- Log processing status
- Run Tesseract `image_to_string()`
- Add page header: `"--- Page {number} ---"`
- Log characters extracted
- Handle errors gracefully with error messages

**3. Text Aggregation**
- Join all page texts with double newlines
- Preserve page boundaries
- Log total character count

**Error Handling:**
- Page-level errors logged but don't stop processing
- Error message included in output for that page
- Function raises exception if PDF to image conversion fails

**When Used:**
- Explicitly called from `extractPdfWithOcr()` as Tier 3 fallback
- Used when PyPDFLoader fails on problematic PDFs
- Part of multi-tier OCR strategy

---

## Database Structure & Management

### Overview

SQLite-based user authentication database. Stores user credentials for login/registration.

### Database Configuration

**File:** `database.py`

#### Database URL

```python
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
```

**Default:** `sqlite:///./users.db` (SQLite file in project root)

**Environment Variable:** Can override via `DATABASE_URL` in `.env`

**Example Alternatives:**
```
postgresql://user:password@localhost/dbname  # PostgreSQL
mysql://user:password@localhost/dbname       # MySQL
```

---

#### Engine Configuration

```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
```

**`check_same_thread: False`:**
- SQLite safety feature (default True)
- Prevents same connection used across threads
- Disabled because FastAPI uses thread pool
- Each request gets its own session

---

#### Session Factory

```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

**Settings:**
- `autocommit=False` - Manual commit control
- `autoflush=False` - Manual flush control
- Allows explicit transaction management

---

#### Base Class

```python
Base = declarative_base()
```

Declarative base for all ORM models. All model classes inherit from `Base`.

---

#### Dependency Injection Function

#### `getDb() → Generator[Session]`

**Purpose:** FastAPI dependency for database session management.

**Returns:** Generator yielding database session

**Usage in Endpoints:**
```python
async def loginRoute(db: Session = Depends(getDb)):
    # db is automatically provided
    user = db.query(User).filter(...).first()
```

**Session Lifecycle:**
1. Create new SQLAlchemy session
2. Yield to route handler
3. Handler uses session for queries
4. After handler completes, close session
5. Cleanup happens in finally block

**Why Generator Pattern:**
- `yield` passes session to route
- `finally` ensures cleanup even if error occurs
- Automatic resource management
- One session per request

---

### User Model

**File:** `models.py`

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashedPassword = Column("hashed_password", String, nullable=False)
```

#### Fields

**`id: int`**
- Primary key, auto-incrementing
- Indexed for fast lookups
- Foreign key reference for user isolation in vectorstore

**`username: str`**
- Unique constraint (no duplicate usernames)
- Indexed for fast login queries
- Cannot be null

**`hashedPassword: str`**
- Column name: "hashed_password" (mapped to ORM attribute `hashedPassword`)
- Stores bcrypt hash, never plaintext password
- Cannot be null

#### Database Schema

Generated SQL (SQLite):
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL
);
CREATE INDEX ix_users_id ON users(id);
CREATE INDEX ix_users_username ON users(username);
```

---

### User Isolation Architecture

**Goal:** Ensure users only see their own documents

**Implementation Across Stack:**

**1. Authentication Layer (BackendAPI.py)**
- `getCurrentUser()` extracts user_id from JWT token
- Only authenticated requests have access to protected endpoints

**2. Ingestion Layer (ingest.py)**
- `runIngestion(userId)` attaches `user_id` metadata to every document chunk

**3. Vectorstore Layer (ChromaDB)**
- Every chunk stored with `user_id` metadata
- Queries use filter: `{"user_id": current_user.id}`

**4. Query Layer (index.py)**
- `query(question, userId)` filters retriever: `search_kwargs={'filter': {'user_id': userId}}`
- User can only search their own documents

**Example Query Flow:**
```
User 1 asks: "What is X?"
↓
getCurrentUser() → User(id=1, username="user1")
↓
RAGEngine.query("What is X?", userId=1)
↓
ChromaDB search with filter: user_id=1
↓
Only User 1's documents searched
↓
User 1 gets answer from their documents only
```

---

### Database Initialization

**Process:**
1. When BackendAPI.py starts, it calls:
   ```python
   Base.metadata.create_all(bind=engine)
   ```
2. SQLAlchemy checks if `users` table exists
3. If not, creates table and indexes
4. If exists, no changes made
5. Database is now ready for queries

---

### Query Examples

**Find User by Username:**
```python
user = db.query(User).filter(User.username == username).first()
```

**Create New User:**
```python
new_user = User(
    username="john",
    hashedPassword=hash_password("secret123")
)
db.add(new_user)
db.commit()
db.refresh(new_user)  # Load id from database
```

**Verify Password:**
```python
user = db.query(User).filter(User.username == username).first()
if user and verify_password(input_password, user.hashedPassword):
    # Login successful
```

---

## Data Flow Architecture

### Document Upload & Ingestion Flow

```
User uploads files (POST /upload)
        ↓
isPdfSafe() validates each PDF
        ↓
Files saved to DocsToIngest/
        ↓
runIngestion(userId) called
        ↓
For each file:
  - Extract text (format-specific extractor)
  - For PDFs: 3-tier fallback (RapidOCR → Basic → Image OCR)
  - For images: RapidOCR or Tesseract
  - For Office docs: python-docx/python-pptx
  - For TXT: Direct file read
        ↓
Attach metadata: user_id, filename, page_number
        ↓
Create NLTK parent/child sentence-aware chunks
        ↓
Embed chunks with OllamaEmbeddings
        ↓
Store in ChromaDB with metadata
        ↓
Update IngestedFiles.log
        ↓
RAGEngine reloaded (POST /refresh)
        ↓
Documents now searchable
```

### Query Flow

```
User asks question (POST /ask)
        ↓
getCurrentUser() validates JWT
        ↓
Agent Coordinator runs planner → retriever → responder/drafter
        ↓
Retriever searches user documents via MCP `search_docs`
        ↓
If document relevance is weak, fallback to MCP `search_web`
        ↓
Responder/Drafter generates final output
        ↓
Return answer + workflow steps (+ optional web source metadata)
```

---

## Performance Considerations

### Ingestion Performance

**Bottleneck:** LLM Embedding Generation
- OllamaEmbeddings runs locally, no API latency
- ~10-50ms per chunk depending on CPU
- Scales linearly with document size

**Optimization:** Chunk Size
- Current: sentence-aware parent/child chunking (NLTK splitter)
- Larger chunks = fewer embeddings = faster
- Smaller chunks = more precise retrieval

### Query Performance

**Bottleneck:** Semantic Search
- ChromaDB uses efficient vector search (approximate nearest neighbors)
- ~50-100ms for similarity search
- LLM generation: ~2-5 seconds (depends on answer length)

**Optimization Potential:**
- Adjust `top_k` results retrieved (current: implicit 4)
- Enable ChromaDB caching for frequent queries
- Implement query result caching

---

## Multi-Agent Workflow (MCP)

### Overview

The Multi-Agent Workflow system implements a Model Context Protocol (MCP) based architecture for coordinating multiple AI agents. The MCP server is **automatically spawned as a subprocess** when needed and exposes tools that agents call via JSON-RPC. The workflow executes **synchronously** within the `/ask` endpoint, returning the complete result (answer + agent steps) in a single response.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                          │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │  /ask Endpoint  │    │ Agent Coordinator (Singleton)       │ │
│  │  (Synchronous)  │───▶│  ┌─────────┐ ┌─────────┐ ┌────────────────┐ │ │
│  │                 │    │  │ Planner │→│Retriever│→│Responder/Drafter│ │ │
│  │  Returns full   │◀───│  └─────────┘ └─────────┘ └────────┘ │ │
│  │  result + steps │    └────────────────┬────────────────────┘ │
└──────────────────────────────────────────┼──────────────────────┘
                                           │ JSON-RPC (stdio)
                              ┌────────────▼────────────┐
                              │     MCP Server          │
                              │  (Auto-spawned Process) │
                              │  ┌──────────────────┐   │
                              │  │ Tool Handlers    │   │
                              │  │ - search_docs    │   │
                              │  │ - list_user_docs │   │
                              │  │ - get_doc_summary│   │
                              │  │ - answer_question│   │
                              │  │ - search_web     │   │
                              │  └────────┬─────────┘   │
                              └───────────┼─────────────┘
                                          │
                              ┌───────────▼─────────────┐
                              │  RAG Engine & ChromaDB  │
                              └─────────────────────────┘
```

### Components

#### 1. MCP Server (`mcp_server.py`)

A separate Python process communicating via JSON-RPC 2.0 over stdio (line-delimited JSON).

**Automatic Spawning:** The `MCPClient` in `agents.py` spawns the server as a subprocess when needed:
```python
subprocess.Popen(
    ["python3", "mcp_server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)
```

**Manual Testing (Optional):**
```bash
cd Backend
python mcp_server.py --test
```

**Protocol Methods:**
- `initialize` - Handshake with protocol version "2024-11-05"
- `tools/list` - List available tools
- `tools/call` - Execute a tool with arguments
- `ping` - Health check

**Lifecycle:**
- Started when agent coordinator runs a query
- Stopped after workflow completes (success or failure)
- Uses `terminate()` and `wait()` for graceful shutdown

---

#### 2. MCP Tools (`mcp_tools.py`)

Tool definitions that wrap RAG capabilities:

| Tool | Description | Parameters | Returns |
|------|-------------|------------|---------|
| `search_docs` | Semantic search over user's documents | `query` (str), `user_id` (str/int), `top_k` (int, default 5) | List of chunks with content (truncated to 500 chars), source, page, score |
| `list_user_docs` | List all uploaded documents | `user_id` (str/int) | List of filenames, count |
| `get_doc_summary` | Get preview of a specific document | `user_id` (str/int), `filename` (str) | Preview text (max 1000 chars), chunk count |
| `answer_question` | Generate RAG answer with citations | `question` (str), `user_id` (str/int), `context` (str, optional) | Generated answer with source citations |
| `search_web` | Search web when user documents are insufficient | `query` (str), `max_results` (int, default 5) | List of web result objects (title, url, snippet) |

**ToolResult Format:**
```python
{
  "success": bool,
  "data": Any,
  "error": Optional[str]
}
```

**User ID Handling:**
- Tools accept user_id as string or int
- Converts to int internally for metadata matching (stored as int during ingestion)
- Ensures compatibility with both string and numeric IDs

---

#### 3. Agent Coordinator (`agents.py`)

Orchestrates multi-agent workflow via singleton pattern (`get_coordinator()`).

**Singleton Pattern:**
```python
_coordinator: Optional[AgentCoordinator] = None

def get_coordinator() -> AgentCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = AgentCoordinator()
    return _coordinator
```

**Coordinator Components:**
- **LLM**: ChatOllama (gemma3:4b, temperature 0.1)
- **MCP Client**: Manages subprocess connection to MCP server
- **Workflows Dictionary**: In-memory storage (for potential async use, not currently used)

**Planner + Retriever + Responder/Drafter Pipeline:**

**1. Planner Agent**
- Lists user's available documents via `list_user_docs` tool
- Sends query + document list to LLM
- LLM creates 1-2 sentence execution plan
- Records plan in workflow step
- Example: "Plan: Search for contract terms and summarize key obligations"

**2. Retriever Agent**
- Calls `search_docs` tool with query and top_k=5
- Collects relevant chunks with source information
- If document relevance is weak, calls `search_web` as fallback
- Extracts unique sources (document or web)
- Records findings in workflow step
- Stores context in workflow for responder/drafter
- Example: "Found 5 relevant chunks from: contract.pdf (p.3), terms.pdf (p.7)"

**3. Responder or Drafter Agent**
- Planner first classifies whether the request is a normal query or a drafting request
- **Responder path:** Generates cited answer from retrieved context
- **Drafter path:** Produces first-draft legal document with placeholders and disclaimer
- Records final answer/draft in workflow
- Example: "Response generated with citations." / "Draft generated successfully."

**Workflow Execution:**
```python
async def run_query(query: str, user_id: str) -> WorkflowState:
    """Run synchronously and return completed workflow."""
    1. Create workflow state (PENDING)
    2. Start MCP client subprocess
    3. Run planner → retriever → responder/drafter sequentially
    4. Set status to COMPLETED or FAILED
    5. Stop MCP client
    6. Return workflow state with answer + steps
```

---

#### 4. Workflow State Machine

```
PENDING → RUNNING → COMPLETED
              ↓
           FAILED
```

**WorkflowState Fields:**
- `workflow_id`: str - UUID for uniqueness
- `query`: str - Original user question
- `user_id`: str - For document isolation
- `status`: WorkflowStatus enum - Current state
- `steps`: List[AgentStep] - Recorded agent actions
- `answer`: Optional[str] - Final response (populated on completion)
- `error`: Optional[str] - Error message (if failed)
- `created_at`: str - ISO timestamp
- `completed_at`: Optional[str] - ISO timestamp

**AgentStep Fields:**
- `agent`: AgentRole enum (PLANNER, RETRIEVER, RESPONDER, DRAFTER)
- `message`: str - Human-readable step description
- `timestamp`: str - ISO timestamp
- `tool_calls`: List[Dict] - Tools called with arguments
- `tool_results`: List[Dict] - Tool return values

---

### Integration with `/ask` Endpoint

The `/ask` endpoint in `BackendAPI.py` uses the agent coordinator:

```python
@app.post("/ask")
async def askQuestion(
    request: Request,
    queryRequest: QueryRequest,
    currentUser: User = Depends(getCurrentUser),
    csrf=Depends(_require_csrf)
):
    coordinator = get_coordinator()
    workflow = await coordinator.run_query(
        query=queryRequest.question,
        user_id=str(currentUser.id)
    )
    result = workflow.to_dict()
    return {
        "answer": result.get("answer", "No answer generated."),
        "steps": result.get("steps", []),
        "status": result.get("status", "failed"),
      "web_searched": result.get("used_web_search", False),
      "web_sources": result.get("web_sources", []),
    }
```

**Key Points:**
- **Synchronous execution**: `await coordinator.run_query()` blocks until complete
- **Single response**: Returns answer + all steps in one HTTP response
- **No polling required**: Frontend gets complete result immediately
- **MCP lifecycle**: Server spawned and terminated within request lifecycle

---

### Running the System

**No manual MCP server startup required.** The system auto-spawns the MCP server when needed.

**1. Start FastAPI Backend:**
```bash
cd Backend
uvicorn BackendAPI:app --reload --host 0.0.0.0 --port 8000
```

**2. Start Frontend:**
```bash
cd Frontend/RAGapp
npm run dev
```

**3. Test Multi-Agent Query:**
- Login to the app
- Upload some documents
- Ask a question in the search box
- Receive answer with agent steps displayed
- Agent steps show: planner → retriever → responder actions

**4. (Optional) Test MCP Server Standalone:**
```bash
cd Backend
python3 mcp_server.py --test
```

Output:
```
Testing MCP Server initialization...
✓ MCP Server initialized successfully
✓ RAG Engine: Available
✓ Tools available: ['search_docs', 'list_user_docs', 'get_doc_summary', 'answer_question', 'search_web']
```

---

### Error Handling

**MCP Server Connection Errors:**
- Subprocess fails to start → 500 error returned to frontend
- JSON-RPC communication timeout → Workflow marked as FAILED

**No Documents:**
- `list_user_docs` returns empty list
- Planner notes no documents available
- Retriever attempts web search fallback
- Responder either answers from web results or returns no-context message

**Tool Call Failures:**
- Tool returns `{"success": false, "error": "..."}` 
- Logged in agent step's tool_results
- Responder attempts fallback strategies

**LLM Errors:**
- Caught by try/except in `_run_workflow()`
- Workflow status set to FAILED
- Error message stored in workflow.error field
- 500 error returned with error details

---

### Performance Characteristics

**Latency Breakdown (typical query):**
1. **Planner**: ~2-3 seconds (list_user_docs + LLM planning)
2. **Retriever**: ~1-2 seconds (semantic search + source extraction)
3. **Responder/Drafter**: ~3-7 seconds (answer or draft generation)
4. **Total**: ~6-10 seconds for complete workflow

**Optimization Opportunities:**
- Cache user document lists (currently fetched every query)
- Parallel tool calls where dependencies allow
- Streaming responses for real-time agent step updates (requires WebSocket/SSE)

**Resource Usage:**
- MCP server process overhead: ~50-100MB RAM
- Subprocess creation/teardown: ~100-200ms
- LLM inference: CPU-bound (depends on Ollama configuration)

---

### Future Enhancements

**Async Execution with Polling:**
- Add `/workflow/start` and `/workflow/status` endpoints
- Store workflows in database (SQLite/PostgreSQL)
- Enable long-running queries without blocking HTTP request

**Streaming Updates:**
- WebSocket or Server-Sent Events (SSE)
- Stream agent steps as they complete
- Better UX for slow queries

**Additional MCP Tools:**
- `summarize_document` - Generate document summaries
- `compare_documents` - Highlight differences between files
- `extract_entities` - NER (Named Entity Recognition)
- `cross_doc_conflict_scan` - Cross-document party conflict scanning

**Custom Agent Chains:**
- User-defined agent workflows
- Conditional branching based on intermediate results
- Agent specialization (legal research, medical coding, etc.)

**Enhanced Agent Capabilities:**
- Multi-hop reasoning (iterative refinement)
- Self-correction (validate and revise answers)
- Chain-of-thought logging for explainability


