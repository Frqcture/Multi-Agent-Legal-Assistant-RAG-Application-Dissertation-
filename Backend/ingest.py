import os
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# Import LangChain components
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

# --- 1. Configuration ---
# Define the paths for your source documents, persistent storage, and log file (Stores previously ingested filenames).
SOURCE_DIRECTORY = "DocsToIngest"
PERSIST_DIRECTORY = "chroma_db"
LOG_FILE = "IngestedFiles.log"

# Load environment variables (for OpenAI API key)
load_dotenv()
if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("OpenAI API key not found. Please set it in the .env file.")

# --- 2. Helper Functions ---
def get_processed_files():
    try:
        with open(LOG_FILE, 'r') as f:
            # Use a set for efficient checking (O(1) average time complexity)
            return set(line.strip() for line in f)
    except FileNotFoundError:
        # If the log file doesn't exist, no files have been processed yet.
        return set()

def update_processed_files(filename):
    """Appends a new filename to the log file."""
    with open(LOG_FILE, 'a') as f:
        f.write(filename + '\n')

# --- 3. Main Ingestion Logic ---
# ... (all your existing imports)

def run_ingestion(user_id: str):
    """Programmatic entry point for the API"""
    # Initialize components
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

    # Ensure directories exist
    if not os.path.exists(SOURCE_DIRECTORY):
        os.makedirs(SOURCE_DIRECTORY)

    # Initialize the vectorstore
    vectorstore = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embedding_model
    )

    processed_files = get_processed_files()
    all_files = [f for f in os.listdir(SOURCE_DIRECTORY) if f.endswith(".pdf")]
    new_files = [f for f in all_files if f not in processed_files]

    if not new_files:
        return "No new documents found."

    for filename in new_files:
        file_path = os.path.join(SOURCE_DIRECTORY, filename)
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splits = text_splitter.split_documents(docs)

        # CRITICAL: Attach the user_id to the metadata of every single chunk
        # THIS DISS-ALLOWS USERS SEEING EACH OTHERS DATA
        for split in splits:
            split.metadata["user_id"] = user_id
            split.metadata["document_name"] = filename

        vectorstore.add_documents(documents=splits)
        update_processed_files(filename)

    return f"Successfully ingested {len(new_files)} files."