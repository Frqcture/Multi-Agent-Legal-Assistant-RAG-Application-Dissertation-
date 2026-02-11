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

---

## Document Ingestion System (`ingest.py`)

### Overview

The ingestion system handles loading documents of multiple formats, extracting text, converting to embeddings, and storing in ChromaDB. It supports PDFs (with OCR), DOCX, PPTX, TXT, and image files.

### Configuration Constants

- `SOURCE_DIRECTORY`: "DocsToIngest" - Directory where uploaded files are stored
- `PERSIST_DIRECTORY`: "chroma_db" - Directory where ChromaDB vectorstore is persisted
- `LOG_FILE`: "IngestedFiles.log" - File tracking already-processed documents

### Multi-Format Support Flags

Optional dependencies are checked at import time:
- `DOCX_AVAILABLE`: python-docx library available
- `PPTX_AVAILABLE`: python-pptx library available
- `IMAGE_PROCESSING_AVAILABLE`: PIL, cv2, numpy available
- `TESSERACT_AVAILABLE`: pytesseract available
- `PDF_TO_IMAGE_AVAILABLE`: pdf2image available

---

### Helper Functions

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

#### `getProcessedFiles() → Set[str]`

**Purpose:** Load list of already-processed filenames from log file to prevent duplicate ingestion.

**Returns:** Set of filenames that have been processed

**Logic Flow:**
1. Try to open `IngestedFiles.log`
2. Read each line, strip whitespace, add to set
3. If file doesn't exist, return empty set
4. Return set of processed filenames

**Why Set:** O(1) lookup time when checking if file already processed

---

#### `updateProcessedFiles(filename: str) → None`

**Purpose:** Append filename to processed log after successful ingestion.

**Parameters:**
- `filename: str` - Filename to add to log

**Logic Flow:**
1. Open `IngestedFiles.log` in append mode
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

**Purpose:** Main entry point for document ingestion. Processes all new files and stores in vectorstore.

**Parameters:**
- `userId: str` - User ID for metadata isolation

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
- Create `DocsToIngest/` directory if doesn't exist
- Connect to ChromaDB vectorstore

**2. File Discovery**
- Get set of already-processed files from log
- List all supported file types in `DocsToIngest/`
- Filter to only new, unprocessed files

**3. Per-File Processing**
For each new file:
- Extract file extension
- Route to appropriate extraction function based on type
- Validate extracted text is not empty
- Filter out empty documents
- Attach metadata:
  - `user_id` - For data isolation
  - `document_name` - Original filename
  - `file_type` - Extension (e.g., ".pdf")
  - `page_number` - Page/position in document

**4. Chunking**
- Split documents into 1000-character chunks
- 100-character overlap between chunks
- Filter empty chunks

**5. Embedding & Storage**
- Generate embeddings for each chunk using OllamaEmbeddings
- Store chunks in ChromaDB with metadata
- Update processed files log

**6. Error Handling**
- Per-file errors logged but don't stop pipeline
- Failed files tracked with error reason
- Return comprehensive status message

**Return Message Example:**
```
Ingested 3 files. Failed: corrupted.pdf (Malformed PDF), empty.txt (No extractable text)
```

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
Split into 1000-char chunks (100-char overlap)
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
RAGEngine.query(question, userId)
        ↓
Embed question with OllamaEmbeddings
        ↓
ChromaDB semantic search (filtered by user_id)
        ↓
Retrieve top-4 most similar chunks
        ↓
Format chunks with source headers
        ↓
Pass to ChatOllama LLM with system prompt
        ↓
LLM generates cited answer
        ↓
Return answer to frontend
```

---

## Performance Considerations

### Ingestion Performance

**Bottleneck:** LLM Embedding Generation
- OllamaEmbeddings runs locally, no API latency
- ~10-50ms per chunk depending on CPU
- Scales linearly with document size

**Optimization:** Chunk Size
- Current: 1000 characters with 100 overlap
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

The Multi-Agent Workflow system implements a Model Context Protocol (MCP) based architecture for coordinating multiple AI agents. The MCP server runs as a **separate process** and exposes tools that agents can call. The workflow executes **asynchronously** with polling for status updates.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                          │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │ Workflow        │    │ Agent Coordinator                   │ │
│  │ Endpoints       │───▶│  ┌─────────┐ ┌─────────┐ ┌────────┐ │ │
│  │ /workflow/start │    │  │ Planner │→│Retriever│→│Responder│ │
│  │ /workflow/status│    │  └─────────┘ └─────────┘ └────────┘ │ │
│  └─────────────────┘    └────────────────┬────────────────────┘ │
└──────────────────────────────────────────┼──────────────────────┘
                                           │ JSON-RPC (stdio)
                              ┌────────────▼────────────┐
                              │     MCP Server          │
                              │  (Separate Process)     │
                              │  ┌──────────────────┐   │
                              │  │ Tool Handlers    │   │
                              │  │ - search_docs    │   │
                              │  │ - list_user_docs │   │
                              │  │ - answer_question│   │
                              │  └────────┬─────────┘   │
                              └───────────┼─────────────┘
                                          │
                              ┌───────────▼─────────────┐
                              │  RAG Engine & ChromaDB  │
                              └─────────────────────────┘
```

### Components

#### 1. MCP Server (`mcp_server.py`)

Runs as a separate Python process, communicating via JSON-RPC over stdio.

**Starting the Server:**
```bash
python mcp_server.py
```

**Protocol:** JSON-RPC 2.0 over stdio (line-delimited JSON)

**Supported Methods:**
- `initialize` - Handshake with protocol version
- `tools/list` - List available tools
- `tools/call` - Execute a tool with arguments
- `ping` - Health check

---

#### 2. MCP Tools (`mcp_tools.py`)

Tool definitions that wrap RAG capabilities:

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_docs` | Semantic search over user's documents | `query`, `user_id`, `top_k` |
| `list_user_docs` | List all uploaded documents | `user_id` |
| `get_doc_summary` | Get preview of a specific document | `user_id`, `filename` |
| `answer_question` | Generate RAG answer with citations | `question`, `user_id` |

---

#### 3. Agent Coordinator (`agents.py`)

Orchestrates the multi-agent workflow with three specialized agents:

**Planner Agent**
- Analyzes the user's query
- Lists available documents
- Creates execution plan using LLM

**Retriever Agent**
- Searches documents using MCP tools
- Collects relevant chunks with sources
- Reports what was found

**Responder Agent**
- Generates final answer using RAG
- Includes citations from sources
- Handles fallback if RAG fails

---

#### 4. Workflow State Machine

```
PENDING → RUNNING → COMPLETED
              ↓
           FAILED
```

**WorkflowState Fields:**
- `workflow_id` - Unique identifier
- `query` - Original user question
- `user_id` - For document isolation
- `status` - Current state
- `steps` - List of agent actions
- `answer` - Final response (when completed)
- `error` - Error message (if failed)
- `created_at` / `completed_at` - Timestamps

---

### API Endpoints

#### `POST /workflow/start`

Start an asynchronous multi-agent workflow.

**Request:**
```json
{
  "question": "Summarize the key points from my documents"
}
```

**Response:**
```json
{
  "workflow_id": "abc-123-def",
  "status": "pending",
  "message": "Workflow started. Poll /workflow/status/{workflow_id} for updates."
}
```

---

#### `GET /workflow/status/{workflow_id}`

Poll for workflow progress and results.

**Response (Running):**
```json
{
  "workflow_id": "abc-123-def",
  "query": "Summarize the key points",
  "status": "running",
  "steps": [
    {
      "agent": "planner",
      "message": "Plan: List docs, search for summaries, synthesize.",
      "timestamp": "2026-02-09T10:30:00",
      "tool_calls": [{"tool": "list_user_docs", "args": {"user_id": "1"}}],
      "tool_results": [{"success": true, "data": {"files": ["doc1.pdf"]}}]
    }
  ],
  "answer": null,
  "created_at": "2026-02-09T10:30:00"
}
```

**Response (Completed):**
```json
{
  "workflow_id": "abc-123-def",
  "status": "completed",
  "steps": [...],
  "answer": "The key points are: 1) ... [doc1.pdf, p.3] 2) ... [doc2.pdf, p.7]",
  "completed_at": "2026-02-09T10:30:15"
}
```

---

#### `GET /workflow/list`

List recent workflows for the current user.

**Response:**
```json
{
  "workflows": [
    {"workflow_id": "abc-123", "status": "completed", "query": "...", ...},
    {"workflow_id": "def-456", "status": "failed", "query": "...", ...}
  ]
}
```

---

### Frontend Integration

The frontend includes a `WorkflowTrigger` component that:
1. Starts a workflow via `POST /workflow/start`
2. Polls `GET /workflow/status/{id}` every second
3. Displays real-time agent step updates
4. Shows final answer when completed

**Toggle Agent Mode:**
- Click "Agent Mode" button in navbar
- When active, shows "Run Multi-Agent" button
- Workflow panel appears below search input

---

### Running the System

The MCP server is **automatically spawned** as a subprocess when a workflow starts. You don't need to run it manually.

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

---

## Proactive Insights Dashboard

### Overview

The Proactive Insights feature provides clinic staff with automatic, actionable guidance based on uploaded case documents. It runs a single LLM analysis to generate **four complementary insight panels**: next best actions, related statutes, case checklists, and information gaps.

The dashboard appears on the `/search` page below the main title when no messages are present (the default landing state). It serves as a "knowledge assistant" that helps staff understand what to do next with a case.

### Architecture

```
Frontend (ProactiveDashboard.tsx)
    ↓
POST /proactive-insights
    ↓
Backend: Single LLM Call
  - Extract document context (6 sample chunks)
  - Query combined prompt (all 4 sections)
  - Parse structured JSON response
  - Check cache, store if fresh
    ↓
Return: {
  next_actions: [...],
  related_statutes: [...],
  checklist: [...],
  info_gaps: [...]
}
```

### Backend: `/proactive-insights` Endpoint

**File:** `BackendAPI.py`

**Request:**
```json
{
  "query": "optional context about current case"
}
```

**Response:**
```json
{
  "next_actions": [
    {
      "action": "Gather client income documentation",
      "priority": "high",
      "reason": "Required for eligibility assessment"
    }
  ],
  "related_statutes": [
    {
      "statute": "Family Law Act 1996",
      "relevance": "Governs spousal support calculations",
      "jurisdiction": "UK"
    }
  ],
  "checklist": [
    {
      "item": "Verify client identity documents",
      "completed": false,
      "category": "Intake"
    }
  ],
  "info_gaps": [
    {
      "field": "Client employment history",
      "severity": "high",
      "suggestion": "Request last 3 payslips and employer contact info"
    }
  ]
}
```

**Rate Limit:** 10 requests per minute

**Performance:** Under 10 seconds (optimized as described below)

---

### Optimization Strategy

**Original (Slow: 13-14 minutes):**
- 4 separate LLM calls (one per insight type)
- Each call synchronous → blocked event loop
- ~180 seconds per call × 4 = ~720 seconds total

**Optimized (Fast: <10 seconds):**

1. **Single LLM Call** (replaces 4 calls)
   - All four insight sections in one prompt
   - Returns complete JSON object
   - Cuts LLM latency from 4× to 1×

2. **True Async with `ainvoke`** (instead of `invoke`)
   - Uses async/await properly
   - Doesn't block FastAPI event loop
   - Other requests can proceed while this runs

3. **Smaller Context Window** (6 chunks × 300 chars, was 10 × 500)
   - Less context = faster tokenization + generation
   - Still sufficient for accurate insights

4. **Token Limit** (`num_predict=1024`)
   - Caps output at 1024 tokens
   - Prevents model from rambling
   - Speeds up generation

5. **TTL Cache** (2-minute lifetime)
   - Repeated requests → instant response
   - Cache per `user_id`, stores timestamp
   - Automatic invalidation after 120 seconds
   - Refresh button still works (shows stale data for 2 min)

---

### Helper Functions

#### `_extract_document_context(rag, user_id, sample_limit=6) → str`

**Purpose:** Pull a representative sample of document chunks for LLM analysis.

**Parameters:**
- `rag: RAGEngine` - RAG instance with vectorstore
- `user_id` - User ID for isolation (int, matches storage type)
- `sample_limit: int` - Max chunks to extract (default: 6)

**Returns:** String with formatted document excerpts

**Logic Flow:**
1. Query ChromaDB filtered by `user_id`
2. Retrieve up to 6 chunks with metadata
3. For each chunk:
   - Extract source filename and page number
   - Truncate content to 300 characters (avoid token explosion)
   - Format as `[source, p.page]: content`
4. Join chunks with double newlines
5. Return formatted string

**Example Output:**
```
[Contract.pdf, p.1]: This agreement is entered on 1 January 2026...

[EmailChain.docx, p.2]: Following the discussion, we agreed to...
```

---

#### `_parse_json_block(text, key) → list`

**Purpose:** Extract a specific JSON array from LLM output when full JSON parse fails.

**Parameters:**
- `text: str` - Full LLM response text
- `key: str` - JSON key to extract (e.g., "next_actions")

**Returns:** Parsed list or empty list if not found

**Fallback Strategy:**
1. Try regex to find `"key": [...]` or `key: [...]`
2. Extract matched array string
3. Parse as JSON
4. Return list, or empty [] on failure

**Why Needed:** Sometimes LLM outputs malformed JSON. This extracts individual sections even if the complete object is broken.

---

#### `_parse_combined_response(text) → dict`

**Purpose:** Parse the complete JSON response from single LLM call.

**Parameters:**
- `text: str` - Full LLM response

**Returns:** Dict with 4 keys (next_actions, related_statutes, checklist, info_gaps)

**Two-Tier Parsing:**

**Tier 1 - Full Object Parse:**
- Find first `{` and last `}`
- Try to parse entire section as JSON
- If successful, return as dict

**Tier 2 - Per-Key Extraction:**
- If full parse fails, extract each key individually
- Use `_parse_json_block()` for each of 4 sections
- Combine into dict
- Less robust but handles malformed responses

**Fallback:** Returns dict with empty lists for all sections if parsing completely fails

---

#### `_generate_all_insights(context, query) → dict`

**Purpose:** Single async call to LLM that generates all four insight types.

**Parameters:**
- `context: str` - Formatted document excerpts
- `query: str` - Additional context from user's search

**Returns:** Dict with next_actions, related_statutes, checklist, info_gaps

**Prompt Structure:**
```
System: "You are a legal clinic advisor. Respond ONLY with valid JSON."

User: "Analyse these documents and return this exact JSON structure:
{
  "next_actions": [...queries...],
  "related_statutes": [...],
  "checklist": [...],
  "info_gaps": [...]
}

<rules for each section>
Documents:
<user's uploaded documents>
<optional: current query context>"
```

**LLM Settings:**
- Model: `gemma3:4b` (local, no API)
- Temperature: 0.2 (some creativity, mostly deterministic)
- Max tokens: 1024 (prevents rambling)

**Async Execution:**
- Uses `await _insights_llm.ainvoke()`
- Doesn't block event loop
- Returns when LLM finishes

---

#### Cache Management

**Global Cache:**
```python
_insights_cache: dict = {}  # { user_id: { "ts": float, "data": dict } }
_CACHE_TTL = 120  # seconds
```

**Cache Check in Endpoint:**
```python
cached = _insights_cache.get(uid)
if cached and (now - cached["ts"]) < _CACHE_TTL:
    return cached["data"]  # Return instantly
```

**Cache Store:**
```python
_insights_cache[uid] = {"ts": time.time(), "data": result}
```

**Features:**
- **Per-user:** Each user has own cache entry
- **Time-based:** 2-minute TTL, then expires
- **Automatic:** Checked on every request
- **No invalidation needed:** Handles document updates gracefully after 2 min

**Example:**
1. User uploads new document at 10:00:00
2. Calls `/proactive-insights` → LLM runs → result cached
3. Calls again at 10:00:30 → cache hit, instant response
4. Calls again at 10:02:01 → cache expired, LLM runs again

---

### Frontend: ProactiveDashboard Component

**File:** `Frontend/RAGapp/src/Components/Search/ProactiveDashboard.tsx`

#### Component Props

```typescript
interface ProactiveDashboardProps {
  baseUrl: string;  // API base URL (from env)
  latestQuery?: string;  // Current search query for context
}
```

#### State Management

**Key States:**
- `insights` - Parsed insights data
- `loading` - Request in progress
- `error` - Error message if any
- `checklist` - Checklist items with completion state (local)

#### Data Fetching

```typescript
const fetchInsights = useCallback(async () => {
  const res = await fetch(`${baseUrl}/proactive-insights`, {
    method: 'POST',
    credentials: 'include',  // Include auth cookie
    body: JSON.stringify({ query: latestQuery }),
  });
  const data = await res.json();
  setInsights(data);
  setChecklist(mergeChecklist(data.checklist));  // Restore saved state
}, [baseUrl, latestQuery]);
```

**Triggers:**
- On component mount
- When `latestQuery` changes

---

#### Checklist Persistence

**Storage Key:** `'proactive_checklist'` in localStorage

**Functions:**
- `loadSavedChecklist()` - Retrieve JSON map of item → completed
- `saveChecklist(items)` - Save current state
- `mergeChecklist(fresh)` - Merge fresh items with saved completion state

**Flow:**
1. Dashboard loads fresh checklist from API
2. Look up each item in localStorage
3. If item exists and was completed, restore `completed: true`
4. User toggles item → call `saveChecklist()` immediately
5. On page refresh, checklist state is preserved

**Example:**
```typescript
// Fresh from API
[{ item: "Verify identity", completed: false }]

// localStorage has
{ "Verify identity": true }

// Merged result
[{ item: "Verify identity", completed: true }]

// User toggles checkbox
[{ item: "Verify identity", completed: false }]

// Saved immediately
localStorage = { "Verify identity": false }
```

---

#### UI Components

**Card Structure:**
- Header (expandable/collapsible)
- Body (collapsible list)
- Each item formatted per type

**Four Sub-Components:**

##### 1. NextActionsCard

**Displays:** Action items with priority badges

**Properties per item:**
- `action` - What to do
- `priority` - "high" (red), "medium" (orange), "low" (green)
- `reason` - Why it matters

**Example:**
```
[HIGH] Gather income documentation
      Required for eligibility assessment
```

##### 2. StatutesCard

**Displays:** Relevant laws and regulations

**Properties per item:**
- `statute` - Name/number of law
- `relevance` - Why it applies
- `jurisdiction` - Where it applies (e.g., "UK")

**Example:**
```
Family Law Act 1996
Governs spousal support calculations
UK
```

##### 3. ChecklistCard

**Displays:** Interactive to-do list

**Properties per item:**
- `item` - Task description
- `completed` - Checkbox state (persistent)
- `category` - Tag (Intake, Filing, Evidence, General)

**Features:**
- Checkbox toggleable
- Items strike-through when complete
- Category labels
- Progress counter (e.g. "3/5")

##### 4. InfoGapsCard

**Displays:** Missing information alerts

**Properties per item:**
- `field` - What's missing
- `severity` - Alert level
- `suggestion` - How to get it

**Example:**
```
[HIGH] Client employment history
      Request last 3 payslips and employer contact info
```

---

#### Styling

**File:** `ProactiveDashboard.module.css`

**Design Principles:**
- Dark theme (matches search page)
- 2-column grid layout (responsive to 1 column on mobile)
- Collapsible cards for space efficiency
- Loading shimmer effects
- Color-coded badges (red/orange/green for priority/severity)

**Key CSS Classes:**
- `.dashboard` - Container
- `.grid` - Responsive 2×1 layout
- `.card` - Individual card container
- `.badge` - Priority/severity indicator
- `.shimmer` - Loading skeleton animation

---

### Integration with Search Page

**Location:** Bottom of landing state (no messages)

**Code Changes to Search.tsx:**
1. Import ProactiveDashboard component
2. Track `lastAskedQuery` state
3. Update on user submit
4. Render dashboard below header when `messages.length === 0`
5. Adjust page padding to accommodate dashboard

**Visibility:**
- Shows when chat is empty (landing page)
- Hides when user starts messaging
- Reappears if user clears all messages

---

### Type Definitions

```typescript
interface NextAction {
  action: string;
  priority: 'high' | 'medium' | 'low';
  reason: string;
}

interface RelatedStatute {
  statute: string;
  relevance: string;
  jurisdiction: string;
}

interface ChecklistItem {
  item: string;
  completed: boolean;
  category: string;
}

interface InfoGap {
  field: string;
  severity: 'high' | 'medium' | 'low';
  suggestion: string;
}

interface ProactiveInsights {
  next_actions: NextAction[];
  related_statutes: RelatedStatute[];
  checklist: ChecklistItem[];
  info_gaps: InfoGap[];
}
```

---

### Error Handling

**Backend:**
- Invalid context → returns default empty insights
- LLM parse failure → fills missing sections with defaults
- Network error → HTTP 500

**Frontend:**
- 401 Unauthorized → redirect to login
- Network error → error banner displayed
- JSON parse failure → graceful fallback to empty state

**User Experience:**
- Loading state shows shimmer placeholders
- Error messages non-blocking (dashboard still visible)
- Refresh button always available to retry

---

### Performance Summary

| Operation | Time |
|-----------|------|
| Extract context (6 chunks) | ~50ms |
| LLM generation (single call) | ~3-8 seconds |
| Parse JSON response | ~10ms |
| Total first request | ~4-9 seconds |
| Cache hit | <1ms |

**Typical User Experience:**
1. Upload document → `POST /upload` (varies by size)
2. Click refresh or navigate back → `POST /proactive-insights`
3. Wait ~5-8 seconds → insights appear
4. Return to page later → instant load (cached)

---

### Future Enhancements

1. **Incremental Loading:** Stream insights as each panel completes
2. **Custom Prompts:** Let users specify what insights they want
3. **Historical Comparison:** Track insights over time, highlight changes
4. **AI Confidence Scores:** Show how confident LLM is in each insight
5. **Manual Overrides:** Allow staff to flag incorrect auto-generated insights
6. **Legal Knowledge Base:** Integrate external statute database for better statute suggestions

**3. (Optional) Test MCP Server:**
```bash
cd Backend
python3 mcp_server.py --test
```

**4. Test Workflow:**
- Login to the app
- Toggle "Agent Mode" ON
- Type a question
- Click "Run Multi-Agent"
- Watch the agent steps appear in real-time

---

### Error Handling

- **MCP Server Not Running:** Workflow fails with connection error
- **No Documents:** Agents report empty results, responder provides fallback message
- **Timeout:** Each agent step has implicit timeout via subprocess communication
- **LLM Errors:** Caught and logged, workflow marked as failed

---

### Future Enhancements

- **Persistent Storage:** Store workflows in database instead of memory
- **Streaming:** Use WebSockets for real-time updates instead of polling
- **Custom Agents:** Allow users to define custom agent chains
- **Tool Extensions:** Add more MCP tools (web search, calculations, etc.)


