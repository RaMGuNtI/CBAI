import pymupdf as fitz
from pathlib import Path
from typing import List
from app.rag.loaders.base import BaseDocumentLoader, LoadedPage


class PDFLoader(BaseDocumentLoader):
    def __init__(self, enable_ocr: bool = False):
        self.enable_ocr = enable_ocr

    def load(self, file_path: Path, **kwargs) -> List[LoadedPage]:
        pages: List[LoadedPage] = []
        doc = fitz.open(str(file_path))

        try:
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                text = page.get_text("text").strip()

                # Optional OCR fallback for scanned/empty pages
                if not text and self.enable_ocr:
                    try:
                        import pytesseract
                        from PIL import Image
                        import io

                        pix = page.get_pixmap()
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        text = pytesseract.image_to_string(img).strip()
                    except Exception:
                        pass

                if text:
                    pages.append(
                        LoadedPage(
                            content=text,
                            page_number=page_idx + 1,
                            metadata={
                                "total_pages": len(doc),
                                "format": "PDF",
                                "page": page_idx + 1
                            }
                        )
                    )
        finally:
            doc.close()

        if not pages:
            # Fallback for empty or scanned PDF without OCR
            pages.append(
                LoadedPage(
                    content="[Scanned or empty PDF - no extractable text found]",
                    page_number=1,
                    metadata={"total_pages": 0, "format": "PDF"}
                )
            )

        return pages
