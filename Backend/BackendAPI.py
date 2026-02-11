import asyncio
import os
import secrets
from pathlib import Path
from typing import List
import logging

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pypdf import PdfReader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from auth_utils import verifyPassword, createAccessToken, hashPassword, ALGORITHM, SECRET_KEY
from jose import jwt, JWTError
from database import engine, Base, getDb
from models import User
from index import RAGEngine
from ingest import runIngestion
from agents import get_coordinator
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# Setup
Base.metadata.create_all(bind=engine)

MAX_FILE_SIZE = 15 * 1024 * 1024
UPLOAD_DIR = "DocsToIngest"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ACCESS_COOKIE_NAME = "access_token"
CSRF_COOKIE_NAME = "csrf_token"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_samesite(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"lax", "strict", "none"}:
        return normalized
    return "lax"


COOKIE_SECURE = _env_bool("COOKIE_SECURE", True)
COOKIE_SAMESITE = _normalize_samesite(os.getenv("COOKIE_SAMESITE", "lax"))

# CORS origins
_allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if _allowed_origins_env.strip():
    ALLOWED_ORIGINS = [origin.strip() for origin in _allowed_origins_env.split(",") if origin.strip()]
else:
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

# FastAPI setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="BackendAPI")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2Scheme = OAuth2PasswordBearer(tokenUrl="login")
ragApp = RAGEngine()


class QueryRequest(BaseModel):
    question: str


async def getCurrentUser(request: Request, db: Session = Depends(getDb)):
    """Extract and validate JWT token from cookies."""
    token = request.cookies.get("access_token")
    if not token:
        print("No token")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)

        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401)
        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


def isPdfSafe(filePath: str) -> tuple:
    """Validate PDF structure and safety."""
    try:
        reader = PdfReader(filePath)
        _ = len(reader.pages)  # Verify pages are readable
        if reader.is_encrypted:
            return False, "Encrypted PDFs not supported"
        return True, "Safe"
    except Exception:
        return False, "Malformed or corrupted PDF"


def _get_user_upload_dir(user_id: int) -> Path:
    base_dir = Path(UPLOAD_DIR).resolve()
    user_dir = (base_dir / str(user_id)).resolve()
    user_dir.mkdir(parents=True, exist_ok=True)
    if not str(user_dir).startswith(str(base_dir)):
        raise HTTPException(status_code=400, detail="Invalid upload directory")
    return user_dir


def _ensure_csrf_cookie(response: Response, existing_token: str | None) -> str:
    if existing_token:
        return existing_token
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        max_age=60 * 60 * 24,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
        path="/",
    )
    return token


def _require_csrf(request: Request):
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get("x-csrf-token")
    if not cookie_token or not header_token or cookie_token != header_token:
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")


def _looks_like_pdf(upload: UploadFile) -> bool:
    try:
        header = upload.file.read(5)
        upload.file.seek(0)
        return header == b"%PDF-"
    except Exception:
        return False


def _save_upload_file(upload: UploadFile, destination: Path, max_bytes: int) -> int:
    total = 0
    with destination.open("wb") as buffer:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise HTTPException(status_code=413, detail=f"{upload.filename} is too large")
            buffer.write(chunk)
    return total


@app.get("/me")
@limiter.limit("6/minute")
async def getMe(request: Request, response: Response, currentUser: User = Depends(getCurrentUser)):
    """Return authenticated user info."""
    _ensure_csrf_cookie(response, request.cookies.get(CSRF_COOKIE_NAME))
    return {
        "id": currentUser.id,
        "username": currentUser.username,
        "message": "Authenticated"
    }


@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(getDb)):
    """Authenticate user and set JWT cookie."""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verifyPassword(form_data.password, user.hashedPassword):
        raise HTTPException(status_code=400, detail="Incorrect credentials")

    accessToken = createAccessToken(data={"sub": user.username})

    response = JSONResponse(content={"message": "Login Successful"})
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=accessToken,
        httponly=True,
        max_age=60 * 60 * 24,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
        path="/"
    )
    _ensure_csrf_cookie(response, request.cookies.get(CSRF_COOKIE_NAME))
    return response


@app.post("/logout")
@limiter.limit("5/minute")
async def logout(request: Request, csrf=Depends(_require_csrf)):
    """Clear JWT cookie."""
    response = JSONResponse(content={"message": "Logout Successful"})
    response.delete_cookie(
        key=ACCESS_COOKIE_NAME,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
        path="/"
    )
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        httponly=False,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
        path="/"
    )
    return response


@app.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(getDb)):
    """Register new user."""
    if db.query(User).filter(User.username == form_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    newUser = User(
        username=form_data.username,
        hashedPassword=hashPassword(form_data.password)
    )
    db.add(newUser)
    db.commit()
    db.refresh(newUser)
    return {"message": "User created successfully"}


@app.post("/ask")
@limiter.limit("20/minute")
async def askQuestion(
    request: Request,
    queryRequest: QueryRequest,
    currentUser: User = Depends(getCurrentUser),
    csrf=Depends(_require_csrf)
):
    """Query knowledge base with context filtering by user."""
    try:
        answer = ragApp.query(queryRequest.question, userId=currentUser.id)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refresh")
@limiter.limit("5/minute")
async def refresh(request: Request, currentUser: User = Depends(getCurrentUser), csrf=Depends(_require_csrf)):
    """Reload RAG engine."""
    global ragApp
    ragApp = RAGEngine()
    return {"message": "Knowledge base updated"}


@app.post("/upload")
@limiter.limit("5/minute")
async def uploadFile(
    request: Request,
    files: List[UploadFile] = File(...),
    currentUser: User = Depends(getCurrentUser),
    csrf=Depends(_require_csrf)
):
    """Upload and ingest documents."""
    savedFiles = []
    fileStatuses = []
    user_dir = _get_user_upload_dir(currentUser.id)

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF")
        if not _looks_like_pdf(file):
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a valid PDF")

        safeFilename = os.path.basename(file.filename)
        filePath = (user_dir / safeFilename).resolve()

        if not str(filePath).startswith(str(user_dir)):
            raise HTTPException(status_code=400, detail="Invalid filename")
        if filePath.exists():
            raise HTTPException(status_code=409, detail=f"{file.filename} already exists")

        try:
            _save_upload_file(file, filePath, MAX_FILE_SIZE)

            isSafe, statusMsg = isPdfSafe(str(filePath))
            if not isSafe:
                os.remove(filePath)
                raise HTTPException(status_code=400, detail=f"PDF validation failed: {statusMsg}")

            savedFiles.append(safeFilename)
            fileStatuses.append({"filename": safeFilename, "status": statusMsg})

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save {file.filename}")

    # Ingest all files
    try:
        ingestStatus = runIngestion(userId=currentUser.id)
        global ragApp
        ragApp = RAGEngine()
        return {
            "message": f"{len(savedFiles)} files uploaded",
            "ingestionStatus": ingestStatus,
            "files": fileStatuses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/files")
async def listFiles(currentUser: User = Depends(getCurrentUser)):
    """List user's uploaded files."""
    try:
        files = ragApp.listUserFiles(userId=currentUser.id)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/files/{filename}")
async def deleteFile(
    filename: str,
    currentUser: User = Depends(getCurrentUser),
    csrf=Depends(_require_csrf)
):
    """Delete file from vectorstore and local storage."""
    try:
        deleted = ragApp.deleteFile(userId=currentUser.id, filename=filename)
        if not deleted:
            raise HTTPException(status_code=404, detail="File not found")

        # Remove from log
        from ingest import get_user_log_file
        log_file = get_user_log_file(currentUser.id)
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                lines = f.readlines()
            with open(log_file, "w") as f:
                for line in lines:
                    if line.strip() != filename:
                        f.write(line)

        # Remove from disk
        user_dir = _get_user_upload_dir(currentUser.id)
        filePath = (user_dir / os.path.basename(filename)).resolve()
        if str(filePath).startswith(str(user_dir)) and filePath.exists():
            filePath.unlink()

        return {"message": f"Deleted {filename}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Multi-Agent Workflow Endpoints (MCP-coordinated)
# ============================================================================

class WorkflowRequest(BaseModel):
    question: str


@app.post("/workflow/start")
@limiter.limit("10/minute")
async def startWorkflow(
    request: Request,
    workflowRequest: WorkflowRequest,
    currentUser: User = Depends(getCurrentUser),
    csrf=Depends(_require_csrf)
):
    """
    Start an async multi-agent workflow.
    Returns a workflow_id for polling status.
    """
    try:
        coordinator = get_coordinator()
        workflow_id = await coordinator.start_workflow(
            query=workflowRequest.question,
            user_id=str(currentUser.id)
        )
        return {
            "workflow_id": workflow_id,
            "status": "pending",
            "message": "Workflow started. Poll /workflow/status/{workflow_id} for updates."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/status/{workflow_id}")
@limiter.limit("60/minute")
async def getWorkflowStatus(
    request: Request,
    workflow_id: str,
    currentUser: User = Depends(getCurrentUser)
):
    """
    Poll workflow status and get step-by-step progress.
    """
    coordinator = get_coordinator()
    workflow = coordinator.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Verify user owns this workflow
    if workflow.user_id != str(currentUser.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this workflow")

    return workflow.to_dict()


@app.get("/workflow/list")
@limiter.limit("20/minute")
async def listWorkflows(
    request: Request,
    currentUser: User = Depends(getCurrentUser)
):
    """
    List all workflows for the current user.
    """
    coordinator = get_coordinator()
    user_workflows = [
        w.to_dict() for w in coordinator.workflows.values()
        if w.user_id == str(currentUser.id)
    ]

    # Sort by created_at descending
    user_workflows.sort(key=lambda x: x["created_at"], reverse=True)

    return {"workflows": user_workflows[:20]}  # Limit to last 20


# ============================================================================
# Proactive Insights Engine (Dashboard)
# ============================================================================

import json as _json
import time as _time

# Shared LLM instance for proactive analysis
_insights_llm = ChatOllama(model="gemma3:4b", temperature=0.2, num_predict=1024)

# Simple TTL cache: { user_id: { "ts": float, "data": dict } }
_insights_cache: dict = {}
_CACHE_TTL = 3600  # seconds – serve cached result for 1 hour


def _extract_document_context(rag: RAGEngine, user_id, sample_limit: int = 6) -> str:
    """Pull representative chunks from user documents for analysis."""
    try:
        results = rag.vectorstore.get(
            where={"user_id": user_id},
            include=["metadatas", "documents"],
            limit=sample_limit,
        )
        if not results["documents"]:
            return ""

        parts = []
        for doc, meta in zip(results["documents"], results["metadatas"]):
            src = meta.get("document_name", "Unknown")
            page = meta.get("page_number", "?")
            parts.append(f"[{src}, p.{page}]: {doc[:300]}")  # tighter cap
        return "\n\n".join(parts)
    except Exception:
        return ""


def _parse_json_block(text: str, key: str) -> list:
    """Extract a JSON array that follows a key label in the LLM output."""
    # Try to find the key followed by a JSON array
    import re
    # Look for "key": [...] or key: [...]
    patterns = [
        rf'"{key}"\s*:\s*(\[.*?\])(?=\s*[,\}}"])',
        rf'{key}\s*:\s*(\[.*?\])(?=\s*[,\}}"])',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL)
        if m:
            try:
                return _json.loads(m.group(1))
            except _json.JSONDecodeError:
                continue
    return []


def _parse_combined_response(text: str) -> dict:
    """Parse the combined JSON response from the single LLM call."""
    text = text.strip()
    # Try full JSON parse first
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            parsed = _json.loads(text[start:end + 1])
            if isinstance(parsed, dict):
                return parsed
        except _json.JSONDecodeError:
            pass

    # Fallback: extract each section individually
    return {
        "next_actions": _parse_json_block(text, "next_actions"),
        "related_statutes": _parse_json_block(text, "related_statutes"),
        "checklist": _parse_json_block(text, "checklist"),
        "info_gaps": _parse_json_block(text, "info_gaps"),
    }


_COMBINED_SYSTEM = "You are a legal-clinic case advisor. Respond ONLY with valid JSON. No markdown, no explanation."

_COMBINED_PROMPT = """Analyse these legal documents and return a SINGLE JSON object with exactly 4 keys.
Be concise. Keep strings short (under 15 words each).

Documents:
{context}

{query_line}

Return this exact JSON structure:
{{
  "next_actions": [
    {{"action": "...", "priority": "high|medium|low", "reason": "..."}}
  ],
  "related_statutes": [
    {{"statute": "...", "relevance": "...", "jurisdiction": "..."}}
  ],
  "checklist": [
    {{"item": "...", "completed": false, "category": "Intake|Filing|Evidence|General"}}
  ],
  "info_gaps": [
    {{"field": "...", "severity": "high|medium|low", "suggestion": "..."}}
  ]
}}

Rules:
- next_actions: 3-4 items
- related_statutes: 3-4 items
- checklist: 4-6 items
- info_gaps: 3-4 items
- Return ONLY the JSON object, nothing else."""


_EMPTY_INSIGHTS = {
    "next_actions": [{"action": "Upload case documents to get started", "priority": "high", "reason": "No documents found"}],
    "related_statutes": [],
    "checklist": [{"item": "Upload case documents", "completed": False, "category": "Setup"}],
    "info_gaps": [{"field": "Client documents", "severity": "high", "suggestion": "Upload relevant case files to begin analysis."}],
}


async def _generate_all_insights(context: str, query: str) -> dict:
    """Single LLM call that produces all four insight sections."""
    if not context:
        return _EMPTY_INSIGHTS

    query_line = f"Current query context: {query}" if query else ""
    prompt = _COMBINED_PROMPT.format(context=context, query_line=query_line)

    resp = await _insights_llm.ainvoke([
        SystemMessage(content=_COMBINED_SYSTEM),
        HumanMessage(content=prompt),
    ])

    parsed = _parse_combined_response(resp.content)

    # Fill in defaults for any missing sections
    defaults = _EMPTY_INSIGHTS
    return {
        "next_actions": parsed.get("next_actions") or defaults["next_actions"],
        "related_statutes": parsed.get("related_statutes") or defaults["related_statutes"],
        "checklist": parsed.get("checklist") or defaults["checklist"],
        "info_gaps": parsed.get("info_gaps") or defaults["info_gaps"],
    }


class InsightsRequest(BaseModel):
    query: str = ""


@app.post("/proactive-insights")
@limiter.limit("10/minute")
async def getProactiveInsights(
    request: Request,
    body: InsightsRequest,
    currentUser: User = Depends(getCurrentUser),
    csrf=Depends(_require_csrf),
):
    """
    Single LLM call to produce all four proactive insight panels.
    Results are cached per-user for 2 minutes.
    """
    try:
        uid = currentUser.id
        now = _time.time()

        # Check cache
        cached = _insights_cache.get(uid)
        if cached and (now - cached["ts"]) < _CACHE_TTL:
            return cached["data"]

        context = _extract_document_context(ragApp, uid)
        result = await _generate_all_insights(context, body.query)

        # Store in cache
        _insights_cache[uid] = {"ts": now, "data": result}

        return result
    except Exception as e:
        logging.exception("Proactive insights error")
        raise HTTPException(status_code=500, detail=str(e))

