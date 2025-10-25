import os
from dotenv import load_dotenv

# Import LangChain components
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
# CHANGED: Import PyPDFLoader instead of TextLoader
from langchain_community.document_loaders import PyPDFLoader

# --- 1. Load Environment Variables ---
load_dotenv()
if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("OpenAI API key not found. Please set it in the .env file.")

# --- 2. Initialize Models ---
# We can initialize these once, as they are used in both cases
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model_name="gpt-5-mini", temperature=0)

# --- 3. Define Paths ---
pdf_path = "testPDFinput.pdf"
persist_directory = "chroma_db"  # The directory to save the DB

# --- 4. Load or Create the Vector Store ---
vectorstore = None
if os.path.exists(persist_directory):
    # If the directory exists, load the existing vector store
    print(f"Loading existing vector store from: {persist_directory}")
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )
else:
    # If the directory doesn't exist, create a new one
    print(f"Creating new vector store from: {pdf_path}")
    print("This will take a moment...")

    # Load the document
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # Split the document into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)

    # Create the vector store and persist it
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embedding_model,
        persist_directory=persist_directory
    )
    print(f"Vector store created and saved to: {persist_directory}")

# Ensure vectorstore is initialized before proceeding
if not vectorstore:
    raise ValueError("Vector store could not be initialized.")

# --- 5. Create the RAG Chain ---
print("Creating the RAG chain...")
retriever = vectorstore.as_retriever()

template = """
You are a helpful assistant. Answer the question based only on the following context.
If you don't know the answer, just say that you don't know.

Context:
{context}

Question:
{question}
"""
prompt = ChatPromptTemplate.from_template(template)

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --- 6. Ask Questions ---
print("Ready to answer questions.")
question = "What is the main topic of the document?" # Example question
print(f"Question: {question}")

answer = rag_chain.invoke(question)
print(f"Answer: {answer}")

question = "When was the most recent update to this document?"
print(f"Question: {question}")

answer = rag_chain.invoke(question)
print(f"Answer: {answer}")