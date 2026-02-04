import os
import logging
from dotenv import load_dotenv

# Import LangChain components
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders.parsers import RapidOCRBlobParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Define the paths for your source documents, persistent storage, and log file (Stores previously ingested filenames).
SOURCE_DIRECTORY = "DocsToIngest"
PERSIST_DIRECTORY = "chroma_db"
LOG_FILE = "IngestedFiles.log"

# Load environment variables (for OpenAI API key)
load_dotenv()

# --- Helper Functions ---
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


def run_ingestion(user_id: str):
    """
    Programmatic entry point for the API.
    Uses PyPDFLoader with RapidOCRBlobParser for robust handling of:
    - Text-based PDFs (fast extraction)
    - Scanned/image-based PDFs (OCR with RapidOCR)
    """
    # Initialize components
    embedding_model = OllamaEmbeddings(model="embeddinggemma")

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

    ingested_count = 0
    failed_files = []

    for filename in new_files:
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(SOURCE_DIRECTORY, safe_filename)

        try:
            logger.info(f"Processing document: {filename}")

            # PyPDFLoader with RapidOCRBlobParser handles both:
            # 1. Text-based PDFs: Extracts text directly
            # 2. Scanned PDFs: Uses OCR on embedded images/pages
            loader = PyPDFLoader(
                file_path,
                mode="page",
                images_inner_format="markdown-img",
                images_parser=RapidOCRBlobParser(),  # Local OCR - no external service needed
            )

            docs = loader.load()
            logger.info(f"Loaded {len(docs)} pages from {filename}")

            # CRITICAL: Attach the user_id to the metadata of every single chunk
            # THIS DISALLOWS USERS SEEING EACH OTHERS DATA
            for doc in docs:
                doc.metadata["user_id"] = user_id
                doc.metadata["document_name"] = filename
                doc.metadata["page_number"] = doc.metadata.get("page", 0) + 1

            # Split documents into chunks for better retrieval
            # Metadata automatically propagates to each chunk
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            splits = text_splitter.split_documents(docs)

            vectorstore.add_documents(documents=splits)
            update_processed_files(filename)

            logger.info(f"Successfully ingested {filename}: {len(splits)} chunks")
            ingested_count += 1

        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            failed_files.append((filename, str(e)))

    # Return detailed status
    if failed_files:
        error_msg = "; ".join([f"{f[0]} ({f[1]})" for f in failed_files])
        return f"Ingested {ingested_count} files. Failed: {error_msg}"

    return f"Successfully ingested {ingested_count} files."
