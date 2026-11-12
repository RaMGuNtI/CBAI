import json
from pathlib import Path
from typing import List
from app.rag.loaders.base import BaseDocumentLoader, LoadedPage


class TextLoader(BaseDocumentLoader):
    def load(self, file_path: Path, **kwargs) -> List[LoadedPage]:
        ext = file_path.suffix.lower()
        content = ""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1", errors="replace") as f:
                content = f.read()

        if ext == ".json":
            try:
                parsed = json.loads(content)
                content = json.dumps(parsed, indent=2)
            except Exception:
                pass  # Use raw content if json is malformed

        return [
            LoadedPage(
                content=content.strip() or "[Empty Text Document]",
                page_number=1,
                metadata={
                    "format": ext.replace(".", "").upper(),
                    "char_count": len(content)
                }
            )
        ]

