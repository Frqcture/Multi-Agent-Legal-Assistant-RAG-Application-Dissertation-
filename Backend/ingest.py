import os
import logging
import threading
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_community.document_loaders.parsers import RapidOCRBlobParser
from langchain_ollama import OllamaEmbeddings

# Multi-format support imports
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

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOURCE_DIRECTORY = "DocsToIngest"
PERSIST_DIRECTORY = "chroma_db"
LOG_FILE = "IngestedFiles.log"

load_dotenv()


def loadPdfWithTimeout(filePath: str, useOcr: bool = True, timeoutSeconds: int = 30):
    """Load PDF with threading-based timeout to handle hanging files."""
    result = [None]
    error = [None]

    def loadPdf():
        try:
            loader = (
                PyPDFLoader(
                    filePath,
                    mode="page",
                    images_inner_format="markdown-img",
                    images_parser=RapidOCRBlobParser() if useOcr else None,
                )
                if useOcr
                else PyPDFLoader(filePath, mode="page")
            )
            result[0] = loader.load()
        except Exception as e:
            error[0] = e
            logger.error(f"Error loading PDF: {str(e)[:100]}")

    thread = threading.Thread(target=loadPdf, daemon=True)
    thread.start()
    thread.join(timeout=timeoutSeconds)

    if thread.is_alive():
        logger.warning(f"PDF loading timed out after {timeoutSeconds} seconds")
        return None

    if error[0]:
        logger.error(f"PDF loading failed: {error[0]}")
        return None

    return result[0]


def get_user_source_directory(user_id: str) -> str:
    """Return per-user upload directory path."""
    base_dir = Path(SOURCE_DIRECTORY).resolve()
    user_dir = (base_dir / str(user_id)).resolve()
    user_dir.mkdir(parents=True, exist_ok=True)
    if not str(user_dir).startswith(str(base_dir)):
        raise ValueError("Invalid user upload directory")
    return str(user_dir)


def get_user_log_file(user_id: str) -> str:
    """Return per-user ingestion log path."""
    user_dir = Path(get_user_source_directory(user_id))
    return str((user_dir / LOG_FILE).resolve())


def getProcessedFiles(log_file: str):
    """Get set of already-processed filenames from log file."""
    try:
        with open(log_file, "r") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()


def updateProcessedFiles(log_file: str, filename: str):
    """Append filename to processed log."""
    with open(log_file, "a") as f:
        f.write(filename + "\n")


def extractDocx(filePath: str) -> str:
    """Extract text from DOCX files."""
    if not DOCX_AVAILABLE:
        return ""
    try:
        doc = DocxDocument(filePath)
        text = "\n".join([para.text for para in doc.paragraphs])
        logger.info(f"Extracted {len(text)} chars from DOCX: {Path(filePath).name}")
        return text
    except Exception as e:
        logger.error(f"Error extracting DOCX: {e}")
        return ""


def extractPptx(filePath: str) -> str:
    """Extract text from PPTX files."""
    if not PPTX_AVAILABLE:
        return ""
    try:
        prs = Presentation(filePath)
        textParts = [f"--- Slide {i} ---" for i in range(1, len(prs.slides) + 1)]
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    textParts.append(shape.text)
        text = "\n".join(textParts)
        logger.info(f"Extracted {len(text)} chars from PPTX: {Path(filePath).name}")
        return text
    except Exception as e:
        logger.error(f"Error extracting PPTX: {e}")
        return ""


def preprocessImageForOcr(imagePath: str) -> Optional[np.ndarray]:
    """Preprocess image (CLAHE, denoise, binary threshold) for better OCR."""
    if not IMAGE_PROCESSING_AVAILABLE:
        return None

    try:
        image = cv2.imread(imagePath)
        if image is None:
            return None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        logger.info(f"Preprocessed image: {Path(imagePath).name}")
        return binary
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        return None


def extractImage(filePath: str) -> str:
    """Extract text from image files using OCR."""
    try:
        from langchain_community.document_loaders import UnstructuredImageLoader

        loader = UnstructuredImageLoader(filePath)
        docs = loader.load()
        text = "\n".join([doc.page_content for doc in docs])
        logger.info(f"Extracted {len(text)} chars from image: {Path(filePath).name}")
        return text
    except Exception as e:
        logger.error(f"Error extracting image: {e}")
        return ""


def extractTxt(filePath: str) -> str:
    """Extract text from TXT files."""
    try:
        with open(filePath, "r", encoding="utf-8") as f:
            text = f.read()
        logger.info(f"Extracted {len(text)} chars from TXT: {Path(filePath).name}")
        return text
    except Exception as e:
        logger.error(f"Error extracting TXT: {e}")
        return ""


def ocrWithTesseract(image) -> str:
    """Extract text using Tesseract OCR."""
    if not TESSERACT_AVAILABLE:
        return ""
    try:
        return pytesseract.image_to_string(image)
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        return ""


def extractPdfWithOcr(filePath: str, useHighDpi: bool = True) -> str:
    """Extract text from PDF by converting to images and applying OCR chain."""
    if not PDF_TO_IMAGE_AVAILABLE:
        logger.warning("pdf2image not available")
        return ""

    try:
        dpi = 300 if useHighDpi else 150
        logger.info(f"Converting PDF to images at {dpi} DPI")
        images = convert_from_path(filePath, dpi=dpi, timeout=60)

        allText = []
        for pageNum, image in enumerate(images, 1):
            try:
                logger.info(f"Processing page {pageNum}/{len(images)}")

                # Preprocess image if available
                if IMAGE_PROCESSING_AVAILABLE:
                    import tempfile

                    with tempfile.NamedTemporaryFile(
                        suffix=".png", delete=False
                    ) as tmp:
                        image.save(tmp.name)
                        preprocessed = preprocessImageForOcr(tmp.name)
                        if preprocessed is not None:
                            image = Image.fromarray(preprocessed)
                        os.remove(tmp.name)

                # Try Tesseract first
                if TESSERACT_AVAILABLE:
                    text = ocrWithTesseract(image)
                    if text.strip():
                        allText.append(f"--- Page {pageNum} (Tesseract) ---\n{text}")
                        logger.info(
                            f"Page {pageNum}: Tesseract extracted {len(text)} chars"
                        )
                        continue

                # Fallback to RapidOCR
                try:
                    from langchain_community.document_loaders import (
                        UnstructuredImageLoader,
                    )
                    import tempfile

                    with tempfile.NamedTemporaryFile(
                        suffix=".png", delete=False
                    ) as tmp:
                        image.save(tmp.name)
                        loader = UnstructuredImageLoader(tmp.name)
                        docs = loader.load()
                        text = "\n".join([doc.page_content for doc in docs])
                        if text.strip():
                            allText.append(f"--- Page {pageNum} (RapidOCR) ---\n{text}")
                            logger.info(
                                f"Page {pageNum}: RapidOCR extracted {len(text)} chars"
                            )
                        os.remove(tmp.name)
                except Exception as e:
                    logger.warning(f"Page {pageNum} RapidOCR failed: {e}")

            except Exception as e:
                logger.error(f"Error processing page {pageNum}: {e}")

        result = "\n\n".join(allText)
        logger.info(f"OCR complete: {len(result)} total chars")
        return result

    except Exception as e:
        logger.error(f"PDF to image OCR failed: {e}")
        return ""


def processPdf(filePath: str, filename: str):
    """Process PDF with 3-tier fallback: RapidOCR -> Basic extraction -> Image OCR."""
    # Tier 1: RapidOCR
    try:
        logger.info("Tier 1: Attempting RapidOCR")
        docs = loadPdfWithTimeout(filePath, useOcr=True, timeoutSeconds=30)

        if docs:
            contentLength = sum(
                len(doc.page_content) for doc in docs if doc.page_content
            )
            if contentLength > 100:
                logger.info(f"Tier 1 success: {len(docs)} pages")
                return docs
            logger.warning(
                f"Tier 1: insufficient content ({contentLength} chars), trying Tier 2"
            )
        else:
            logger.warning("Tier 1: timeout or failed")
    except Exception as e:
        logger.warning(f"Tier 1 failed: {str(e)[:80]}")

    # Tier 2: Basic extraction
    try:
        logger.info("Tier 2: Basic PDF extraction")
        docs = loadPdfWithTimeout(filePath, useOcr=False, timeoutSeconds=30)

        if docs:
            contentLength = sum(
                len(doc.page_content) for doc in docs if doc.page_content
            )
            if contentLength > 100:
                logger.info(
                    f"Tier 2 success: {len(docs)} pages with {contentLength} chars"
                )
                return docs
            logger.warning(
                f"Tier 2: insufficient content ({contentLength} chars), trying Tier 3"
            )
        else:
            logger.warning("Tier 2: timeout or failed")
    except Exception as e:
        logger.warning(f"Tier 2 failed: {str(e)[:80]}")

    # Tier 3: Image-based OCR
    try:
        logger.info("Tier 3: Image-based OCR")
        textContent = extractPdfWithOcr(filePath, useHighDpi=True)

        if textContent and len(textContent.strip()) > 50:
            logger.info(f"Tier 3 success: {len(textContent)} chars")
            
            # Split the OCR text back into individual Document objects per page 
            # so the downstream metadata attacher can accurately track the page numbers
            docs = []
            import re
            
            # extractPdfWithOcr labels pages like "--- Page 1 (Tesseract) ---"
            # We split on that pattern to map text back to distinct pages
            page_blocks = re.split(r'---\s+Page\s+(\d+).*?---', textContent)
            
            if len(page_blocks) > 1:
                # page_blocks[0] is empty or text before first page
                # page_blocks[1] is page number "1"
                # page_blocks[2] is the content of page 1, and so on...
                for i in range(1, len(page_blocks), 2):
                    if i + 1 < len(page_blocks):
                        page_num_str = page_blocks[i]
                        page_text = page_blocks[i + 1].strip()
                        
                        if page_text:
                            # Safely cast page number
                            try:
                                p_num = int(page_num_str)
                            except ValueError:
                                p_num = 1
                                
                            docs.append(Document(
                                page_content=page_text, 
                                metadata={"source": filePath, "page_number": p_num}
                            ))
                            
                if docs:
                    return docs
                    
            # Fallback if regex split fails
            return [Document(page_content=textContent, metadata={"source": filePath, "page_number": 1})]

        logger.warning(f"Tier 3: insufficient content ({len(textContent)} chars)")
        return None

    except Exception as e:
        logger.error(f"Tier 3 failed: {str(e)[:80]}")
        return None


def runIngestion(userId: str):
    """Main ingestion pipeline supporting multiple document formats."""
    embeddingModel = OllamaEmbeddings(model="embeddinggemma")

    source_directory = get_user_source_directory(userId)
    log_file = get_user_log_file(userId)

    vectorstore = Chroma(
        persist_directory=PERSIST_DIRECTORY, embedding_function=embeddingModel
    )

    processedFiles = getProcessedFiles(log_file)
    supportedExtensions = (
        ".pdf",
        ".docx",
        ".pptx",
        ".txt",
        ".png",
        ".jpg",
        ".jpeg",
        ".tiff",
        ".bmp",
    )

    allFiles = [
        f
        for f in os.listdir(source_directory)
        if any(f.lower().endswith(ext) for ext in supportedExtensions)
    ]
    newFiles = [f for f in allFiles if f not in processedFiles]

    if not newFiles:
        return "No new documents found."

    ingestedCount = 0
    failedFiles = []

    for filename in newFiles:
        safeFilename = os.path.basename(filename)
        filePath = os.path.join(source_directory, safeFilename)
        fileExt = Path(filePath).suffix.lower()

        try:
            logger.info(f"Processing: {filename}")
            docs = None

            if fileExt == ".pdf":
                docs = processPdf(filePath, filename)
            elif fileExt == ".docx":
                text = extractDocx(filePath)
                docs = (
                    [
                        Document(
                            page_content=text,
                            metadata={"source": filePath, "document_name": filename},
                        )
                    ]
                    if text.strip()
                    else None
                )
            elif fileExt == ".pptx":
                text = extractPptx(filePath)
                docs = (
                    [
                        Document(
                            page_content=text,
                            metadata={"source": filePath, "document_name": filename},
                        )
                    ]
                    if text.strip()
                    else None
                )
            elif fileExt == ".txt":
                text = extractTxt(filePath)
                docs = (
                    [
                        Document(
                            page_content=text,
                            metadata={"source": filePath, "document_name": filename},
                        )
                    ]
                    if text.strip()
                    else None
                )
            elif fileExt in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
                text = extractImage(filePath)
                docs = (
                    [
                        Document(
                            page_content=text,
                            metadata={"source": filePath, "document_name": filename},
                        )
                    ]
                    if text.strip()
                    else None
                )

            if not docs:
                logger.warning(f"No content extracted from {filename}")
                failedFiles.append((filename, "No extractable text"))
                continue

            docs = [
                doc for doc in docs if doc.page_content and doc.page_content.strip()
            ]
            if not docs:
                failedFiles.append((filename, "Empty after filtering"))
                continue

            logger.info(f"Extracted {len(docs)} sections")

            # Attach metadata for user isolation
            for doc in docs:
                # PyPDFLoader attaches page property 0-indexed, we want to normalize it globally
                extracted_page = doc.metadata.get("page")
                if extracted_page is not None:
                    # Adjust zero-index to match human readable 1-index for PyPDFLoader
                    page_num = extracted_page + 1
                else:
                    # Fallback to the text-based page_number we injected for Tier 3 OCR, or default 1
                    page_num = doc.metadata.get("page_number", 1)

                doc.metadata.update(
                    {
                        "user_id": userId,
                        "document_name": filename,
                        "file_type": fileExt,
                        "page_number": page_num,
                    }
                )

            # Natural Language/Context-Aware Chunking for OCR robustness
            # Replaces fixed character limits with NLP sentence boundary detection.
            from langchain_text_splitters import NLTKTextSplitter
            import uuid

            # 1. First Pass: Create larger "Parent" context blocks
            # Groups ~3-5 sentences together as a continuous logical thought
            # 2000 chars is just a ceiling safegaurd, it splits natively at the sentence boundary nearest to it.
            parent_splitter = NLTKTextSplitter(chunk_size=2000, chunk_overlap=0)
            parent_chunks = parent_splitter.split_documents(docs)

            # 2. Second Pass: Create highly specific "Child" sentence clusters for precise vector retrieval
            # Groups 1-3 sentences. Overlap is tiny to just catch boundary context.
            child_splitter = NLTKTextSplitter(chunk_size=600, chunk_overlap=50)

            final_splits = []

            for parent_idx, parent in enumerate(parent_chunks):
                # Unique ID for parent group
                parent_id = str(uuid.uuid4())
                
                # Tag Parent
                parent.metadata["chunk_level"] = "parent"
                parent.metadata["chunk_id"] = parent_id
                parent.metadata["parent_chunk_id"] = None
                parent.metadata["chunk_index"] = parent_idx
                final_splits.append(parent)
                
                # Split parent into child sentences implicitly ignoring broken inner newlines
                children = child_splitter.split_documents([parent])
                for child_idx, child in enumerate(children):
                    child.metadata["chunk_level"] = "child"
                    child.metadata["chunk_id"] = str(uuid.uuid4())
                    child.metadata["parent_chunk_id"] = parent_id
                    child.metadata["chunk_index"] = child_idx
                    final_splits.append(child)

            splits = [
                split
                for split in final_splits
                if split.page_content and split.page_content.strip()
            ]

            if not splits:
                failedFiles.append((filename, "No chunks"))
                continue

            vectorstore.add_documents(documents=splits)
            updateProcessedFiles(log_file, filename)
            logger.info(f"Ingested {filename}: {len(splits)} chunks")
            ingestedCount += 1

        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            failedFiles.append((filename, str(e)[:60]))

    if failedFiles:
        errorMsg = "; ".join([f"{f[0]} ({f[1]})" for f in failedFiles])
        return f"Ingested {ingestedCount} files. Failed: {errorMsg}"

    return f"Successfully ingested {ingestedCount} files."
