import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request
from fastapi.responses import JSONResponse
from auth_utils import verify_password, create_access_token, hash_password, ALGORITHM, SECRET_KEY
from jose import jwt, JWTError
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from index import RAGEngine
from ingest import run_ingestion
import shutil
from sqlalchemy.orm import Session
from pathlib import Path
from database import engine, Base, get_db
from models import User
from pypdf import PdfReader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

Base.metadata.create_all(bind=engine)

MAX_FILE_SIZE = 15 * 1024 * 1024
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="BackendAPI")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [
    "http://localhost:5173",  # Default React port
    "http://127.0.0.1:5173",
    "http://0.0.0.0:5173",
    "http://192.168.0.137:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # In production, use your specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Validates the JWT token and returns the user's data."""

    token = request.cookies.get("access_token")

    if not token:
        print(f"DEBUG: Cookies received: {request.cookies}")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise HTTPException(status_code=401)

        user = db.query(User).filter(User.username == username).first()
        if user is None: raise HTTPException(status_code=401)
        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

def is_pdf_safe(file_path):
    #TODO - Add functionality to see if the PDF is a "ZIP Bomb" by creating a seperate instance with limited resources.

    try:
        reader = PdfReader(file_path)
        # Attempt to access the number of pages to trigger basic parsing
        _ = len(reader.pages)
        # Check for encrypted files which can break ingestion
        if reader.is_encrypted:
            return False, "Encrypted PDFs are not supported."
        return True, "Safe"
    except Exception:
        return False, "Malformed or corrupted PDF structure."

# Start the engine
rag_app = RAGEngine()

# Define exactly what the user should send
class QueryRequest(BaseModel):
    question: str

@app.get("/me")
@limiter.limit("6/minute")
async def get_me( request: Request, current_user: User = Depends(get_current_user)):
    """
    Returns the current user's information
    This is used to validate if the user is logged in when the site is initially loaded
    """

    return {
        "id": current_user.id,
        "username": current_user.username,
        "message": "Authenticated"
    }

@app.post("/login")
@limiter.limit("5/minute")
async def login( response: Response, request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username})

    content = {"message": "Login Successful"}
    response = JSONResponse(content=content)

    response.set_cookie(
        key = "access_token",
        value = access_token,
        httponly = True,
        max_age = 60 * 60 * 24,
        expires = 60 * 60 * 24,
        samesite = "lax",
        secure = False # Set this to true in production, it requires SSL Certificate
    )

    return response

@app.post("/logout")
@limiter.limit("5/minute")
async def logout(response: Response, request: Request):
    """Clears the session cookies related to the current user"""

    content = {"message": "Logout Successful"}
    response = JSONResponse(content=content)

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
        path="/"  # Must match the path used when the cookie was set
    )

    return response

@app.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.username == form_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Create new user with hashed password
    new_user = User(
        username=form_data.username,
        hashed_password=hash_password(form_data.password)  # From your auth_utils
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/ask")
@limiter.limit("20/minute")
async def ask_question(request: Request, query_request: QueryRequest, current_user: dict = Depends(get_current_user)):
    """
    Takes a question, searches the PDF, and returns an answer.
    """
    try:
        # We access the question via request.question thanks to Pydantic
        answer = rag_app.query(query_request.question, user_id=current_user.id)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refresh")
@limiter.limit("5/minute")
async def refresh(request: Request):
    """Reloads the vector store if the PDF has changed."""
    global rag_app
    rag_app = RAGEngine()
    return {"message": "Success: Knowledge base updated."}

UPLOAD_DIR = "DocsToIngest"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
@limiter.limit("5/minute")
async def upload_file(request: Request, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    filename = os.path.basename(file.filename)

    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Validate file size
    # file.size is available in modern FastAPI/Starlette versions
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE / (1024 * 1024)}MB."
        )

    # Extract only the base name (prevents ../../ logic)
    safe_filename = os.path.basename(file.filename)

    # Create absolute paths for comparison
    base_dir = Path(UPLOAD_DIR).resolve()
    file_path = (base_dir / safe_filename).resolve()

    # Security Check: Ensure the file path is actually inside base_dir
    if not str(file_path).startswith(str(base_dir)):
        raise HTTPException(status_code=400, detail="Invalid filename detected.")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    if not(is_pdf_safe(file_path)):
        raise HTTPException(status_code=400, detail="PDF is not safe.")

    # Trigger Ingestion
    try:
        ingest_status = run_ingestion(user_id=current_user.id)

        # Refresh the RAG Engine so it sees the new vectors
        global rag_app
        rag_app = RAGEngine()

        return {"message": "File uploaded and ingested successfully", "status": ingest_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/files")
async def list_files(current_user: dict = Depends(get_current_user)):
    """Returns a list of all files the current user has uploaded."""
    try:
        files = rag_app.list_user_files(user_id=current_user.id)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/files/{filename}")
async def delete_file(filename: str, current_user: dict = Depends(get_current_user)):
    """Removes a specific file from the vector store and the ingestion log."""
    try:
        # Remove from ChromaDB
        deleted = rag_app.delete_file(user_id=current_user.id, filename=filename)

        if not deleted:
            raise HTTPException(status_code=404, detail="File not found in vector store.")

        # This allows the user to re-upload the same filename later
        from ingest import LOG_FILE

        # Remove from IngestedFiles.log
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
            with open(LOG_FILE, "w") as f:
                for line in lines:
                    if line.strip() != filename:
                        f.write(line)

        # Remove from local storage
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        return {"message": f"Successfully deleted {filename}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))