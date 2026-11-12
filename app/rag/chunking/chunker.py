from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from app.rag.loaders.base import LoadedPage
from app.rag.preprocessing.cleaner import TextCleaner


@dataclass
class DocumentChunk:
    id: str
    chatbot_id: str
    document_id: str
    filename: str
    page_number: Optional[int]
    chunk_index: int
    content: str
    metadata: Dict[str, Any]


class DocumentChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = max(100, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, self.chunk_size // 2))

    def chunk_pages(
        self,
        pages: List[LoadedPage],
        chatbot_id: str,
        document_id: str,
        filename: str
    ) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        global_index = 0

        for page in pages:
            cleaned_text = TextCleaner.clean(page.content)
            if not cleaned_text:
                continue

            splits = self._recursive_split(
                text=cleaned_text,
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap
            )

            for split in splits:
                if not split.strip():
                    continue

                chunk_id = f"{document_id}_{global_index}"
                chunk_hash = TextCleaner.chunk_hash(split)

                meta = {
                    "chatbot_id": chatbot_id,
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": page.page_number if page.page_number is not None else 1,
                    "chunk_index": global_index,
                    "chunk_hash": chunk_hash,
                    **page.metadata
                }

                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        chatbot_id=chatbot_id,
                        document_id=document_id,
                        filename=filename,
                        page_number=page.page_number,
                        chunk_index=global_index,
                        content=split,
                        metadata=meta
                    )
                )
                global_index += 1

        return chunks

    def _recursive_split(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Splits text hierarchically using paragraphs, sentences, words, and characters.
        """
        separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]
        return self._split_with_separators(text, separators, chunk_size, overlap)

    def _split_with_separators(
        self, text: str, separators: List[str], chunk_size: int, overlap: int
    ) -> List[str]:
        if len(text) <= chunk_size:
            return [text]

        if not separators:
            # Fallback hard chunking
            return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

        sep = separators[0]
        remaining_seps = separators[1:]

        if sep == "":
            return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

        splits = text.split(sep)
        chunks = []
        current_chunk = []
        current_len = 0

        for piece in splits:
            piece_len = len(piece) + (len(sep) if current_chunk else 0)
            if current_len + piece_len <= chunk_size:
                current_chunk.append(piece)
                current_len += piece_len
            else:
                if current_chunk:
                    joined = sep.join(current_chunk)
                    chunks.append(joined)
                    # Handle overlap by keeping the trailing pieces
                    overlap_acc = []
                    acc_len = 0
                    for rev_piece in reversed(current_chunk):
                        if acc_len + len(rev_piece) <= overlap:
                            overlap_acc.insert(0, rev_piece)
                            acc_len += len(rev_piece) + len(sep)
                        else:
                            break
                    current_chunk = overlap_acc
                    current_len = sum(len(p) for p in current_chunk) + (len(sep) * max(0, len(current_chunk) - 1))

                if len(piece) > chunk_size:
                    # Deeper split with remaining separators
                    sub_chunks = self._split_with_separators(piece, remaining_seps, chunk_size, overlap)
                    chunks.extend(sub_chunks)
                    current_chunk = []
                    current_len = 0
                else:
                    current_chunk.append(piece)
                    current_len += len(piece) + (len(sep) if len(current_chunk) > 1 else 0)

        if current_chunk:
            chunks.append(sep.join(current_chunk))

        return chunks

