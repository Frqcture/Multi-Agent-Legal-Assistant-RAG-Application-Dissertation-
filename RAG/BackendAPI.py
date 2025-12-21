import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# This assumes your RAG class is in a file named rag_engine.py
from index import RAGEngine

app = FastAPI(title="BackendAPI")

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
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refresh")
async def refresh():
    """Reloads the vector store if the PDF has changed."""
    global rag_app
    rag_app = RAGEngine()
    return {"message": "Success: Knowledge base updated."}