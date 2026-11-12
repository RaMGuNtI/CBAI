from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path


@dataclass
class LoadedPage:
    content: str
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseDocumentLoader(ABC):
    @abstractmethod
    def load(self, file_path: Path, **kwargs) -> List[LoadedPage]:
        """
        Extract pages/sections and metadata from file.
        """
        pass

