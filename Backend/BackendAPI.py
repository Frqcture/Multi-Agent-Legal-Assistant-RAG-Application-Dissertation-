import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
# This assumes your RAG class is in a file named rag_engine.py
from index import RAGEngine
from ingest import run_ingestion
import shutil
from pathlib import Path

app = FastAPI(title="BackendAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, use your specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Start the engine
rag_app = RAGEngine()

# 2. Define exactly what the user should send
class QueryRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask_question(request: QueryRequest):
    """
    Takes a question, searches the PDF, and returns an answer.
    """
    try:
        # We access the question via request.question thanks to Pydantic
        answer = rag_app.query(request.question)
        print(answer)
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
async def upload_file(file: UploadFile = File(...)):
    # 1. Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # 2. Save the file to the source directory
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # 3. Trigger Ingestion
    try:
        ingest_status = run_ingestion()

        # 4. Refresh the RAG Engine so it sees the new vectors
        global rag_app
        rag_app = RAGEngine()

        return {"message": "File uploaded and ingested successfully", "status": ingest_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")