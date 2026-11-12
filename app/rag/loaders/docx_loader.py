from pathlib import Path
from typing import List
import docx
from app.rag.loaders.base import BaseDocumentLoader, LoadedPage


class DocxLoader(BaseDocumentLoader):
    def load(self, file_path: Path, **kwargs) -> List[LoadedPage]:
        doc = docx.Document(str(file_path))
        full_text_blocks: List[str] = []

        # Extract paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                full_text_blocks.append(text)

        # Extract tables
        for table_idx, table in enumerate(doc.tables, 1):
            table_rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                table_rows.append(" | ".join(cells))
            if table_rows:
                full_text_blocks.append(f"[Table {table_idx}]\n" + "\n".join(table_rows))

        combined_text = "\n\n".join(full_text_blocks)
        if not combined_text:
            combined_text = "[Empty Word Document]"

        return [
            LoadedPage(
                content=combined_text,
                page_number=1,
                metadata={
                    "format": "DOCX",
                    "paragraphs_count": len(doc.paragraphs),
                    "tables_count": len(doc.tables)
                }
            )
        ]

