from pathlib import Path
from typing import List
from pptx import Presentation
from app.rag.loaders.base import BaseDocumentLoader, LoadedPage


class PPTXLoader(BaseDocumentLoader):
    def load(self, file_path: Path, **kwargs) -> List[LoadedPage]:
        prs = Presentation(str(file_path))
        pages: List[LoadedPage] = []

        for slide_idx, slide in enumerate(prs.slides, 1):
            slide_texts: List[str] = []
            
            # Extract title if present
            if slide.shapes.title and slide.shapes.title.text.strip():
                slide_texts.append(f"Slide Title: {slide.shapes.title.text.strip()}")

            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        text = paragraph.text.strip()
                        if text and text not in slide_texts:
                            slide_texts.append(text)

            # Check speaker notes
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes = slide.notes_slide.notes_text_frame.text.strip()
                if notes:
                    slide_texts.append(f"Speaker Notes: {notes}")

            content = "\n".join(slide_texts).strip()
            if not content:
                content = f"[Slide {slide_idx}: Empty or Graphical Content]"

            pages.append(
                LoadedPage(
                    content=content,
                    page_number=slide_idx,
                    metadata={
                        "slide_number": slide_idx,
                        "total_slides": len(prs.slides),
                        "format": "PPTX"
                    }
                )
            )

        if not pages:
            pages.append(
                LoadedPage(
                    content="[Empty Presentation]",
                    page_number=1,
                    metadata={"total_slides": 0, "format": "PPTX"}
                )
            )

        return pages

