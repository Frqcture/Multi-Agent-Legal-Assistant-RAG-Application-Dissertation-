"""
Robust OCR processor for scanned PDFs using Tesseract.
Provides fallback OCR when PyPDFLoader with RapidOCR fails.
"""

import logging
from pdf2image import convert_from_path
import pytesseract

logger = logging.getLogger(__name__)

def extract_text_from_scanned_pdf(pdf_path: str) -> str:
    """
    Extract text from a scanned PDF using Tesseract OCR.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text from all pages
    """
    try:
        logger.info(f"Converting PDF to images: {pdf_path}")
        images = convert_from_path(pdf_path, dpi=300)
        logger.info(f"Converted {len(images)} pages to images at 300 DPI")

        all_text = []

        for page_num, image in enumerate(images, 1):
            try:
                logger.info(f"Processing page {page_num}/{len(images)} with Tesseract")

                # Run Tesseract OCR on the PIL image
                page_text = pytesseract.image_to_string(image)

                if page_text.strip():
                    all_text.append(f"--- Page {page_num} ---\n{page_text}")
                    logger.info(f"Page {page_num}: Extracted {len(page_text)} characters")
                else:
                    logger.warning(f"Page {page_num}: No text extracted")

            except Exception as e:
                logger.error(f"Error processing page {page_num}: {e}")
                all_text.append(f"--- Page {page_num} ---\n[Error: {str(e)[:50]}]")

        full_text = "\n\n".join(all_text)
        logger.info(f"Total extracted: {len(full_text)} characters from {len(images)} pages")
        return full_text

    except Exception as e:
        logger.error(f"Failed to extract text from scanned PDF: {e}")
        raise

