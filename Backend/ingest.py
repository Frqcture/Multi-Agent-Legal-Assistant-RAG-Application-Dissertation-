import os
import logging
import signal
import threading
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

# ...existing code...
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_community.document_loaders.parsers import RapidOCRBlobParser
from langchain_ollama import OllamaEmbeddings

# Import multi-format support
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

try:
    from PIL import Image
    import cv2
    import numpy as np
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF_TO_IMAGE_AVAILABLE = True
except ImportError:
    PDF_TO_IMAGE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_pdf_with_timeout(file_path: str, use_ocr: bool = True, timeout_seconds: int = 30):
    """
    Load PDF with timeout to handle problematic PDFs that hang.
    Uses threading since signal alarms don't work well with PyPDFLoader.

    Args:
        file_path: Path to PDF file
        use_ocr: Whether to use RapidOCR
        timeout_seconds: Maximum time to wait for PDF loading

    Returns:
        List of documents or None if timeout/error
    """
    result = [None]
    error = [None]

    def load_pdf():
        try:
            if use_ocr:
                logger.info("Loading PDF with RapidOCR...")
                loader = PyPDFLoader(
                    file_path,
                    mode="page",
                    images_inner_format="markdown-img",
                    images_parser=RapidOCRBlobParser(),
                )
            else:
                logger.info("Loading PDF without OCR...")
                loader = PyPDFLoader(file_path, mode="page")

            docs = loader.load()
            result[0] = docs
        except Exception as e:
            error[0] = e
            logger.error(f"Error loading PDF: {str(e)[:100]}")

    # Start loading in a thread
    thread = threading.Thread(target=load_pdf, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)

    # Check if thread is still alive (timeout occurred)
    if thread.is_alive():
        logger.warning(f"PDF loading timed out after {timeout_seconds} seconds (thread still running)")
        return None

    if error[0]:
        logger.error(f"PDF loading failed: {error[0]}")
        return None

    return result[0]

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

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX files."""
    try:
        if not DOCX_AVAILABLE:
            return ""
        doc = DocxDocument(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        logger.info(f"Extracted {len(text)} chars from DOCX: {Path(file_path).name}")
        return text
    except Exception as e:
        logger.error(f"Error extracting DOCX: {e}")
        return ""

def extract_text_from_pptx(file_path: str) -> str:
    """Extract text from PPTX files."""
    try:
        if not PPTX_AVAILABLE:
            return ""
        prs = Presentation(file_path)
        text_parts = []
        for slide_num, slide in enumerate(prs.slides, 1):
            text_parts.append(f"--- Slide {slide_num} ---")
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text_parts.append(shape.text)
        text = "\n".join(text_parts)
        logger.info(f"Extracted {len(text)} chars from PPTX: {Path(file_path).name}")
        return text
    except Exception as e:
        logger.error(f"Error extracting PPTX: {e}")
        return ""

def preprocess_image_for_ocr(image_path: str) -> Optional[np.ndarray]:
    """Preprocess image to improve OCR accuracy."""
    try:
        if not IMAGE_PROCESSING_AVAILABLE:
            return None

        # Read image
        image = cv2.imread(image_path)
        if image is None:
            return None

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Increase contrast with CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

        # Threshold to binary (helps with low-quality scans)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        logger.info(f"Preprocessed image: {Path(image_path).name}")
        return binary
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        return None

def extract_text_from_image(file_path: str) -> str:
    """Extract text from image files using OCR."""
    try:
        from langchain_community.document_loaders import UnstructuredImageLoader
        loader = UnstructuredImageLoader(file_path)
        docs = loader.load()
        text = "\n".join([doc.page_content for doc in docs])
        logger.info(f"Extracted {len(text)} chars from image: {Path(file_path).name}")
        return text
    except Exception as e:
        logger.error(f"Error extracting image: {e}")
        return ""

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        logger.info(f"Extracted {len(text)} chars from TXT: {Path(file_path).name}")
        return text
    except Exception as e:
        logger.error(f"Error extracting TXT: {e}")
        return ""

def _ocr_with_tesseract(image) -> str:
    """Use Tesseract OCR on a PIL Image."""
    try:
        if not TESSERACT_AVAILABLE:
            return ""
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        return ""

def _extract_text_from_pdf_with_ocr(file_path: str, use_high_dpi: bool = True) -> str:
    """
    Extract text from PDF by converting to images and applying OCR.
    This handles scanned PDFs that have no extractable text layer.
    """
    try:
        if not PDF_TO_IMAGE_AVAILABLE:
            logger.warning("pdf2image not available, skipping image-based OCR")
            return ""

        dpi = 300 if use_high_dpi else 150
        logger.info(f"Converting PDF to images at {dpi} DPI for OCR")
        images = convert_from_path(file_path, dpi=dpi, timeout=60)

        all_text = []
        for page_num, image in enumerate(images, 1):
            try:
                logger.info(f"Processing page {page_num}/{len(images)} with OCR")

                # Preprocess image if available
                if IMAGE_PROCESSING_AVAILABLE:
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        image.save(tmp.name)
                        preprocessed = preprocess_image_for_ocr(tmp.name)
                        if preprocessed is not None:
                            # Convert back to PIL Image for OCR
                            image = Image.fromarray(preprocessed)
                        os.remove(tmp.name)

                # Try Tesseract first if available
                if TESSERACT_AVAILABLE:
                    text = _ocr_with_tesseract(image)
                    if text.strip():
                        all_text.append(f"--- Page {page_num} (Tesseract) ---\n{text}")
                        logger.info(f"Page {page_num}: Tesseract extracted {len(text)} chars")
                        continue

                # Fallback to UnstructuredImageLoader (RapidOCR)
                try:
                    from langchain_community.document_loaders import UnstructuredImageLoader
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        image.save(tmp.name)
                        loader = UnstructuredImageLoader(tmp.name)
                        docs = loader.load()
                        text = "\n".join([doc.page_content for doc in docs])
                        if text.strip():
                            all_text.append(f"--- Page {page_num} (RapidOCR) ---\n{text}")
                            logger.info(f"Page {page_num}: RapidOCR extracted {len(text)} chars")
                        os.remove(tmp.name)
                except Exception as e:
                    logger.warning(f"Page {page_num} RapidOCR fallback failed: {e}")

            except Exception as e:
                logger.error(f"Error processing page {page_num}: {e}")

        result = "\n\n".join(all_text)
        logger.info(f"OCR extraction complete: {len(result)} total characters")
        return result

    except Exception as e:
        logger.error(f"PDF to image OCR failed: {e}")
        return ""



def run_ingestion(user_id: str):
    """
    Programmatic entry point for the API.
    Supports multiple document formats:
    - PDFs (text and scanned with OCR)
    - DOCX files
    - PPTX files
    - TXT files
    - Image files (PNG, JPG, etc.)
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

    # Supported file extensions
    supported_extensions = ('.pdf', '.docx', '.pptx', '.txt', '.png', '.jpg', '.jpeg', '.tiff', '.bmp')

    all_files = [f for f in os.listdir(SOURCE_DIRECTORY)
                 if any(f.lower().endswith(ext) for ext in supported_extensions)]
    new_files = [f for f in all_files if f not in processed_files]

    if not new_files:
        return "No new documents found."

    ingested_count = 0
    failed_files = []

    for filename in new_files:
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(SOURCE_DIRECTORY, safe_filename)
        file_ext = Path(file_path).suffix.lower()

        try:
            logger.info(f"Processing document: {filename}")
            docs = None

            # Route to appropriate handler based on file type
            if file_ext == '.pdf':
                docs = _process_pdf(file_path, filename)
            elif file_ext == '.docx':
                text = extract_text_from_docx(file_path)
                docs = [Document(page_content=text, metadata={"source": file_path, "document_name": filename})] if text.strip() else None
            elif file_ext == '.pptx':
                text = extract_text_from_pptx(file_path)
                docs = [Document(page_content=text, metadata={"source": file_path, "document_name": filename})] if text.strip() else None
            elif file_ext == '.txt':
                text = extract_text_from_txt(file_path)
                docs = [Document(page_content=text, metadata={"source": file_path, "document_name": filename})] if text.strip() else None
            elif file_ext in ('.png', '.jpg', '.jpeg', '.tiff', '.bmp'):
                text = extract_text_from_image(file_path)
                docs = [Document(page_content=text, metadata={"source": file_path, "document_name": filename})] if text.strip() else None

            if not docs:
                logger.warning(f"No content extracted from {filename}")
                failed_files.append((filename, "No extractable text"))
                continue

            # Filter out completely empty documents
            docs = [doc for doc in docs if doc.page_content and doc.page_content.strip()]

            if not docs:
                failed_files.append((filename, "No extractable text after filtering"))
                continue

            logger.info(f"Extracted content from {len(docs)} sections")

            # CRITICAL: Attach the user_id to metadata for data isolation
            for doc in docs:
                doc.metadata["user_id"] = user_id
                doc.metadata["document_name"] = filename
                doc.metadata["file_type"] = file_ext
                doc.metadata["page_number"] = doc.metadata.get("page_number", 1)

            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            splits = text_splitter.split_documents(docs)

            # Filter empty chunks
            splits = [split for split in splits if split.page_content and split.page_content.strip()]

            if not splits:
                failed_files.append((filename, "No content after chunking"))
                continue

            vectorstore.add_documents(documents=splits)
            update_processed_files(filename)

            logger.info(f"Successfully ingested {filename}: {len(splits)} chunks")
            ingested_count += 1

        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            failed_files.append((filename, str(e)[:60]))

    # Return detailed status
    if failed_files:
        error_msg = "; ".join([f"{f[0]} ({f[1]})" for f in failed_files])
        return f"Ingested {ingested_count} files. Failed: {error_msg}"

    return f"Successfully ingested {ingested_count} files."

def _process_pdf(file_path: str, filename: str):
    """
    Process PDF files with multi-tier fallback strategy:
    1. RapidOCR via PyPDFLoader (fast, handles embedded images)
    2. Basic text extraction (for text-based PDFs)
    3. Convert to images and use Tesseract + RapidOCR (handles pure scanned PDFs)
    """
    # Tier 1: Try RapidOCR with timeout
    try:
        logger.info(f"Tier 1: Attempting to load PDF {filename} with RapidOCR support")
        docs = load_pdf_with_timeout(file_path, use_ocr=True, timeout_seconds=30)

        if docs:
            content_length = sum(len(doc.page_content) for doc in docs if doc.page_content)
            if content_length > 100:
                logger.info(f"Tier 1 success: Loaded {len(docs)} pages with RapidOCR")
                return docs
            else:
                logger.warning(f"Tier 1 returned {len(docs)} pages but <100 chars total, trying Tier 2")
        else:
            logger.warning(f"Tier 1: PDF loading timed out or failed")

    except Exception as ocr_error:
        logger.warning(f"Tier 1 failed: {str(ocr_error)[:80]}")

    # Tier 2: Try basic PDF extraction with timeout
    try:
        logger.info(f"Tier 2: Attempting basic PDF text extraction")
        docs = load_pdf_with_timeout(file_path, use_ocr=False, timeout_seconds=30)

        if docs:
            content_length = sum(len(doc.page_content) for doc in docs if doc.page_content)
            if content_length > 100:
                logger.info(f"Tier 2 success: Extracted {len(docs)} pages with {content_length} chars")
                return docs
            else:
                logger.warning(f"Tier 2 returned {len(docs)} pages but <100 chars, trying Tier 3")
        else:
            logger.warning(f"Tier 2: PDF loading timed out or failed")

    except Exception as basic_error:
        logger.warning(f"Tier 2 failed: {str(basic_error)[:80]}")

    # Tier 3: Convert PDF to images and use Tesseract + RapidOCR
    try:
        logger.info(f"Tier 3: Converting PDF to images for OCR (scanned document handling)")
        text_content = _extract_text_from_pdf_with_ocr(file_path, use_high_dpi=True)

        if text_content and len(text_content.strip()) > 50:
            logger.info(f"Tier 3 success: Extracted {len(text_content)} chars via image OCR")
            # Return as single document since we combined all pages
            return [Document(
                page_content=text_content,
                metadata={"source": file_path}
            )]
        else:
            logger.warning(f"Tier 3: Insufficient text extracted ({len(text_content)} chars)")
            return None

    except Exception as image_ocr_error:
        logger.error(f"Tier 3 failed: {str(image_ocr_error)[:80]}")
        return None

