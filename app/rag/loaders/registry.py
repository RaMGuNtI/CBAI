import hashlib
from pathlib import Path
from typing import Dict, Type, List, Optional
from app.rag.loaders.base import BaseDocumentLoader, LoadedPage
from app.rag.loaders.pdf_loader import PDFLoader
from app.rag.loaders.docx_loader import DocxLoader
from app.rag.loaders.tabular_loader import TabularLoader
from app.rag.loaders.pptx_loader import PPTXLoader
from app.rag.loaders.text_loader import TextLoader
from app.core.config import settings


class LoaderRegistry:
    def __init__(self):
        self._loaders: Dict[str, Type[BaseDocumentLoader]] = {
            ".pdf": PDFLoader,
            ".docx": DocxLoader,
            ".doc": DocxLoader,
            ".csv": TabularLoader,
            ".xlsx": TabularLoader,
            ".xls": TabularLoader,
            ".pptx": PPTXLoader,
            ".ppt": PPTXLoader,
            ".txt": TextLoader,
            ".md": TextLoader,
            ".json": TextLoader,
        }

    def register_loader(self, extension: str, loader_cls: Type[BaseDocumentLoader]):
        ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        self._loaders[ext] = loader_cls

    def get_loader(self, extension: str) -> Optional[BaseDocumentLoader]:
        ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        loader_cls = self._loaders.get(ext)
        if loader_cls:
            return loader_cls()
        return None

    def calculate_file_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def validate_file(self, filename: str, file_size_bytes: int) -> None:
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format '.{ext}'. Allowed formats: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}"
            )

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size_bytes > max_bytes:
            raise ValueError(
                f"File size ({file_size_bytes / (1024*1024):.2f}MB) exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )

    def load_document(self, file_path: Path, enable_ocr: bool = False) -> List[LoadedPage]:
        ext = file_path.suffix.lower()
        loader_cls = self._loaders.get(ext)
        if not loader_cls:
            raise ValueError(f"No document loader registered for extension '{ext}'")

        if ext == ".pdf":
            loader = PDFLoader(enable_ocr=enable_ocr)
        else:
            loader = loader_cls()

        return loader.load(file_path)


registry = LoaderRegistry()

