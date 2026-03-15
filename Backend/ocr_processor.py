"""OCR processor for scanned PDFs using Tesseract."""

import logging
from pdf2image import convert_from_path
import pytesseract

logger = logging.getLogger(__name__)


def extractTextFromScannedPdf(pdfPath: str) -> str:
    """Extract text from scanned PDF using Tesseract OCR at 300 DPI."""
    try:
        logger.info(f"Converting PDF to images: {pdfPath}")
        images = convert_from_path(pdfPath, dpi=300)
        logger.info(f"Converted {len(images)} pages at 300 DPI")

        allText = []
        for pageNum, image in enumerate(images, 1):
            try:
                logger.info(f"Processing page {pageNum}/{len(images)}")
                pageText = pytesseract.image_to_string(image)

                if pageText.strip():
                    allText.append(f"--- Page {pageNum} ---\n{pageText}")
                    logger.info(f"Page {pageNum}: Extracted {len(pageText)} chars")
                else:
                    logger.warning(f"Page {pageNum}: No text extracted")

            except Exception as e:
                logger.error(f"Error processing page {pageNum}: {e}")
                allText.append(f"--- Page {pageNum} ---\n[Error: {str(e)[:50]}]")

        fullText = "\n\n".join(allText)
        logger.info(f"Total: {len(fullText)} chars from {len(images)} pages")
        return fullText

    except Exception as e:
        logger.error(f"Failed to extract text: {e}")
        raise
