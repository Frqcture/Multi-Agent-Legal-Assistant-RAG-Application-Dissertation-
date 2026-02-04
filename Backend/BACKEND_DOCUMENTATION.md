# Backend API Documentation

## Overview

This document provides detailed explanations of all functions and endpoints in the FastAPI backend. The backend handles authentication, document ingestion, vector storage, and RAG (Retrieval-Augmented Generation) queries.

---

## Table of Contents

1. [Authentication Functions](#authentication-functions)
2. [API Endpoints](#api-endpoints)
3. [Helper Functions](#helper-functions)
4. [Module Imports & Configuration](#module-imports--configuration)

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
- `samesite`: "lax" (sent on same-site requests)
- `secure`: False (works over HTTP for development)
- `max_age`: 86400 (24 hours)
- `path`: "/" (valid for entire domain)

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
1. Create JSON response with logout message
2. Delete `access_token` cookie with same parameters as login
3. Return response with empty cookie (browser removes it)

**Status Codes:**
- `200 OK` - Logout successful

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

**Purpose:** Queries the RAG engine with a question, returns answer based on ingested documents.

**Rate Limit:** 20 requests per minute

**Dependencies:** `getCurrentUser` (requires valid auth token)

**Request Body:**
```json
{
  "question": "What is the capital of France?"
}
```

**Response (200 OK):**
```json
{
  "answer": "The capital of France is Paris. [document_name, page_number]"
}
```

**Logic Flow:**
1. Validate authentication via `getCurrentUser` dependency
2. Extract question from request body (QueryRequest model)
3. Call `ragApp.query()` with question and user_id
4. RAG engine performs similarity search in ChromaDB filtered by user_id
5. LLM generates answer based on retrieved context
6. Return answer in response

**Status Codes:**
- `200 OK` - Query successful
- `401 Unauthorized` - Invalid token
- `500 Internal Server Error` - RAG query failed

**Security:** User isolation via user_id metadata filtering

---

### `POST /refresh`

**Purpose:** Reloads RAG engine after document ingestion. Called after file upload to make new documents searchable.

**Rate Limit:** 5 requests per minute

**Dependencies:** None (no auth required)

**Response (200 OK):**
```json
{
  "message": "Knowledge base updated"
}
```

**Logic Flow:**
1. Create new RAGEngine instance
2. Assign it to global `ragApp` variable
3. New instance loads latest ChromaDB vectorstore
4. Return success message

**Status Codes:**
- `200 OK` - Engine reloaded

---

### `POST /upload`

**Purpose:** Uploads multiple PDF files, validates them, and triggers ingestion into vectorstore.

**Rate Limit:** 5 requests per minute

**Dependencies:** `getCurrentUser` (requires valid auth token)

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
1. Validate authentication via `getCurrentUser`
2. For each uploaded file:
   - Check filename ends with `.pdf`
   - Check file size ≤ 15MB
   - Sanitize filename using `os.path.basename()`
   - Validate file path doesn't escape upload directory
   - Save file to `DocsToIngest/` directory
   - Run `isPdfSafe()` validation
   - If unsafe, delete file and raise error
3. After all files saved, call `runIngestion(userId)` from ingest.py
4. Reload RAG engine with `RAGEngine()`
5. Return detailed status with per-file results

**Status Codes:**
- `200 OK` - Files uploaded and ingested
- `400 Bad Request` - Invalid file or filename
- `401 Unauthorized` - Invalid token
- `413 Payload Too Large` - File exceeds 15MB
- `500 Internal Server Error` - Save or ingestion failed

**Security:**
- Path traversal prevention via resolve()
- File type validation (PDF only)
- File size limit (15MB)
- User isolation via userId in ingestion

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

**Purpose:** Deletes a specific file from vectorstore and local storage.

**Rate Limit:** No explicit limit

**Dependencies:** `getCurrentUser` (requires valid auth token)

**Path Parameters:**
- `filename` - Name of file to delete (URL-encoded)

**Response (200 OK):**
```json
{
  "message": "Deleted document.pdf"
}
```

**Logic Flow:**
1. Validate authentication via `getCurrentUser`
2. Call `ragApp.deleteFile(userId=current_user.id, filename=filename)`
   - RAG engine queries ChromaDB for chunks matching user_id AND filename
   - Deletes all matching chunks from ChromaDB
3. If no chunks found, raise 404 "File not found"
4. Remove filename from `IngestedFiles.log` to allow re-upload
5. Delete actual PDF file from `DocsToIngest/` directory if it exists
6. Return success message

**Status Codes:**
- `200 OK` - File deleted
- `401 Unauthorized` - Invalid token
- `404 Not Found` - File not found in vectorstore
- `500 Internal Server Error` - Deletion failed

**Security:**
- User isolation via user_id metadata filtering
- Only deletes files associated with authenticated user

---

## Helper Functions

### `isPdfSafe(filePath: str) → tuple`

**Purpose:** Validates PDF structure and safety before ingestion.

**Parameters:**
- `filePath: str` - Path to PDF file to validate

**Returns:** Tuple of (bool, str)
- `(True, "Safe")` - PDF is valid
- `(False, "Encrypted PDFs not supported")` - PDF is encrypted
- `(False, "Malformed or corrupted PDF structure.")` - PDF is invalid

**Logic Flow:**
1. Try to read PDF using PyPDFReader
2. Access page count to trigger parsing
3. Check if PDF is encrypted
4. Return success if valid, failure if any exception occurs

**Used By:** `/upload` endpoint

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
- `UPLOAD_DIR`: "DocsToIngest"
- `ALLOWED_ORIGINS`: List of frontend origins for CORS

**Instances:**
- `limiter`: Slowapi limiter for rate limiting
- `app`: FastAPI application instance
- `ragApp`: RAGEngine instance (global, reloaded on file upload)

**Middleware:**
- CORS enabled with credentials support
- Rate limiting on all endpoints
- SQLAlchemy session management

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

## Security Considerations

### Authentication
- All protected endpoints require valid JWT token in cookies
- Tokens expire after 24 hours
- Passwords are hashed with bcrypt before storage

### Authorization
- User isolation via `user_id` metadata in vectorstore
- Users can only see/delete their own documents
- Users can only query documents they uploaded

### Input Validation
- File path traversal prevention via `resolve()`
- File type validation (PDF only)
- File size limits (15MB max)
- Form data validation via Pydantic models

### CORS
- Only allows requests from whitelisted frontend origins
- Credentials required to access protected endpoints

---

## Error Handling

All endpoints follow standard HTTP status code conventions:

- `200 OK` - Success
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication failed or missing token
- `404 Not Found` - Resource not found
- `413 Payload Too Large` - File too large
- `500 Internal Server Error` - Server error

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

