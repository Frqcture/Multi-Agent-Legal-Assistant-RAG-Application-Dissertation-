import os
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
import shutil

from auth_utils import verifyPassword, createAccessToken, hashPassword, ALGORITHM, SECRET_KEY
from jose import jwt, JWTError
from database import engine, Base, getDb
from models import User
from index import RAGEngine
from ingest import runIngestion
from agents import get_coordinator, WorkflowStatus

# Setup
Base.metadata.create_all(bind=engine)

MAX_FILE_SIZE = 15 * 1024 * 1024
UPLOAD_DIR = "DocsToIngest"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# CORS origins
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://0.0.0.0:5173",
    "http://192.168.0.137:5173",
    "http://192.168.0.193:5173"
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


@app.get("/me")
@limiter.limit("6/minute")
async def getMe(request: Request, currentUser: User = Depends(getCurrentUser)):
    """Return authenticated user info."""
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
        key="access_token",
        value=accessToken,
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="lax",
        secure=False,
        path="/"
    )
    return response


@app.post("/logout")
@limiter.limit("5/minute")
async def logout(request: Request):
    """Clear JWT cookie."""
    response = JSONResponse(content={"message": "Logout Successful"})
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False,
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
async def askQuestion(request: Request, queryRequest: QueryRequest, currentUser: User = Depends(getCurrentUser)):
    """Query knowledge base with context filtering by user."""
    try:
        answer = ragApp.query(queryRequest.question, userId=currentUser.id)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refresh")
@limiter.limit("5/minute")
async def refresh(request: Request):
    """Reload RAG engine."""
    global ragApp
    ragApp = RAGEngine()
    return {"message": "Knowledge base updated"}


@app.post("/upload")
@limiter.limit("5/minute")
async def uploadFile(request: Request, files: List[UploadFile] = File(...), currentUser: User = Depends(getCurrentUser)):
    """Upload and ingest documents."""
    savedFiles = []
    fileStatuses = []

    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF")

        if file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"{file.filename} is too large")

        safeFilename = os.path.basename(file.filename)
        baseDir = Path(UPLOAD_DIR).resolve()
        filePath = (baseDir / safeFilename).resolve()

        if not str(filePath).startswith(str(baseDir)):
            raise HTTPException(status_code=400, detail="Invalid filename")

        try:
            with open(filePath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

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
async def deleteFile(filename: str, currentUser: User = Depends(getCurrentUser)):
    """Delete file from vectorstore and local storage."""
    try:
        deleted = ragApp.deleteFile(userId=currentUser.id, filename=filename)
        if not deleted:
            raise HTTPException(status_code=404, detail="File not found")

        # Remove from log
        from ingest import LOG_FILE
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
            with open(LOG_FILE, "w") as f:
                for line in lines:
                    if line.strip() != filename:
                        f.write(line)

        # Remove from disk
        filePath = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(filePath):
            os.remove(filePath)

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
    currentUser: User = Depends(getCurrentUser)
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

