from fastapi import FastAPI
from index import RAGEngine # Import the class

app = FastAPI()

# INITIALIZE ONCE: This runs when the server starts
rag_app = RAGEngine()

@app.post("/ask")
async def ask_question(data: dict):
    user_query = data.get("question")
    # This call is now very fast because everything is already loaded
    answer = rag_app.query(user_query)
    return {"Answer": answer}