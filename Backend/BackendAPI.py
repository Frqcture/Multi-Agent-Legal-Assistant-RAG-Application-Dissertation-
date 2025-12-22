import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
# This assumes your RAG class is in a file named rag_engine.py
from index import RAGEngine

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