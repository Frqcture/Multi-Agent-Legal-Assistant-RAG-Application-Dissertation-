import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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

Base.metadata.create_all(bind=engine)

MAX_FILE_SIZE = 15 * 1024 * 1024
app = FastAPI(title="BackendAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, use your specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Validates the JWT token and returns the user's data."""
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

# 1. Start the engine
rag_app = RAGEngine()

# 2. Define exactly what the user should send
class QueryRequest(BaseModel):
    question: str

@app.post("/login")
# @limiter.limit("5/minute") # Allow 5 attempts per minute per IP
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register")
async def register(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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
async def ask_question(request: QueryRequest, current_user: dict = Depends(get_current_user)):
    """
    Takes a question, searches the PDF, and returns an answer.
    """
    try:
        # We access the question via request.question thanks to Pydantic
        answer = rag_app.query(request.question, user_id=current_user.id)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refresh")
async def refresh():
    """Reloads the vector store if the PDF has changed."""
    global rag_app
    rag_app = RAGEngine()
    return {"message": "Success: Knowledge base updated."}

UPLOAD_DIR = "DocsToIngest"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
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