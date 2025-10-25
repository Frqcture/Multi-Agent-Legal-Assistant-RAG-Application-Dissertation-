import os
from dotenv import load_dotenv

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

def main():
    print("🚀 Starting ingestion process...")

    # Ensure the source directory exists
    if not os.path.isdir(SOURCE_DIRECTORY):
        print(f"Error: Source directory '{SOURCE_DIRECTORY}' not found.")
        print("Please create it and add your PDF files.")
        return

    # Check if the ChromaDB already exists. If not, this script can't append.
    if not os.path.isdir(PERSIST_DIRECTORY):
        print(f"Error: ChromaDB directory '{PERSIST_DIRECTORY}' not found.")
        print("Please run your main RAG application first to create the database.")
        return

    # Get the list of files to process
    processed_files = get_processed_files()
    all_files = [f for f in os.listdir(SOURCE_DIRECTORY) if f.endswith(".pdf")]
    new_files = [f for f in all_files if f not in processed_files]

    if not new_files:
        print("✅ No new documents to ingest. Database is up to date.")
        return

    print(f"📥 Found {len(new_files)} new document(s) to add: {', '.join(new_files)}")

    # Initialize the embedding model
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

    # Load the existing vector store
    vectorstore = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embedding_model
    )

    # Process and add each new document
    for filename in new_files:
        try:
            print(f"Processing '{filename}'...")
            file_path = os.path.join(SOURCE_DIRECTORY, filename)

            # Load the new PDF
            loader = PyPDFLoader(file_path)
            docs = loader.load()

            # Split the document into chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            splits = text_splitter.split_documents(docs)

            # Add the new document chunks to the existing vector store
            vectorstore.add_documents(documents=splits)

            # Log the file as processed *after* successful ingestion
            update_processed_files(filename)
            print(f"Successfully added '{filename}' to the vector store.")
        except Exception as e:
            print(f"❌ Failed to process '{filename}'. Error: {e}")

    print("\nIngestion complete!")

if __name__ == "__main__":
    main()